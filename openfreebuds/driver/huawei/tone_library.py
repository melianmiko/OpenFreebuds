"""本地提示音库（只存上位机 PC 侧，与耳机端传输解耦）。

**三层布局**（2026-11-14 第二次重构：官方配置按官方走，本地增量单独放）::

    <root>/builtin/promptToneConfig/tone_config.json    ← APK 内置目录（静态，随包，不联网）
    <root>/official/promptToneConfig/tone_config.json   ← 云端配布目录（原样镜像官方 zip 内容）
    <root>/official/promptTone/*.pcm                    ← 官方音频（内置音 + 云端音都放这）
    <root>/custom/promptToneConfig/tone_config.json     ← 自定义层：预置自定义 + 用户新建
    <root>/custom/promptTone/*.pcm
    <root>/legacy_backup/                               ← 旧版单层布局的留档（只读）

读取顺序：内置层原序 → 云端层（同 id 覆盖、新 id 追加）→ 自定义层原序。
界面下拉直接照这个顺序排，不按 id 排序。

**为什么官方层要「原样镜像」而不是合并进去**：官方 zip 的 data 与 officialData 是它自己的口径，
直接存下来，下次刷新就能准确算出「新增/更新了哪几条」；和内置层混在一起会导致
每次刷新都把 officialData 里那条（如 200 肖邦）算成「新增」。

id 分段（用户指定）::

    0–49      官方内置
    50–99     预留（不再分配给提示音；历史落在该区间的条目启动时顺延出去）
    100–199   自定义提示音（100–179 为配布包预置，180–199 起为新建/顺延占用）
    200+      官方机型限定铃声（officialData）

自定义条目以 ``"support": "custom"`` 标记。真机实测：feature16 的 toneId 就是设备存音频的
槽位号，设备接受任意 id，所以本地 id 直接当槽位号用。
"""
import io
import json
import logging
import re
import shutil
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from openfreebuds.constants import STORAGE_PATH
from openfreebuds.driver.huawei.prompt_tone import (
    CLOUD_BASE,
    TONE_MAX_BYTES,
    ToneEntry,
    is_custom_tone_id,
    parse_tone_config,
)

# 自定义提示音统一占 100–199（100–179 为随包预置、180–199 为后续新增）；
# 50–99 保留给其它用途，不再分配，历史落在该区间的条目由 _migrate_custom_ids 顺延出去。
CUSTOM_ID_RANGES = ((100, 199),)
RESERVED_ID_RANGES = ((50, 99),)
log = logging.getLogger("ToneLibrary")
CUSTOM_SUPPORT = "custom"
BUILTIN_CONFIG_PATH = Path(__file__).resolve().parents[2] / "assets" / "tone_config.json"

OFFICIAL_CONFIG_URL = f"{CLOUD_BASE}/00000A/00000A_promptToneConfig.zip"
OFFICIAL_TONES_URL = f"{CLOUD_BASE}/00000A/00000A_promptTone.zip"
DOWNLOAD_TIMEOUT = 30

# 英文名：字母/数字开头，只允许字母、数字、空格、下划线、连字符；不含任何非 ASCII 字符
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$")


class ToneLibraryError(Exception):
    """库操作失败（消息可直接展示给用户）。"""


@dataclass
class RefreshResult:
    """官方层刷新结果（与「上一次的官方快照」比较，因此重复刷新应为 0/0）。"""
    official_total: int = 0
    added: list[int] = field(default_factory=list)
    updated: list[int] = field(default_factory=list)
    pcm_written: list[str] = field(default_factory=list)


@dataclass
class ToneLibrary:
    root: Path = STORAGE_PATH / "prompt_tones"

    # --- 布局 ---------------------------------------------------------
    @property
    def builtin_root(self) -> Path:
        return self.root / "builtin"

    @property
    def official_root(self) -> Path:
        return self.root / "official"

    @property
    def custom_root(self) -> Path:
        return self.root / "custom"

    @property
    def builtin_config_path(self) -> Path:
        return self.builtin_root / "promptToneConfig" / "tone_config.json"

    @property
    def official_config_path(self) -> Path:
        return self.official_root / "promptToneConfig" / "tone_config.json"

    @property
    def custom_config_path(self) -> Path:
        return self.custom_root / "promptToneConfig" / "tone_config.json"

    @property
    def official_tones_dir(self) -> Path:
        """官方音频目录（内置音 + 云端音都在这里）。"""
        return self.official_root / "promptTone"

    @property
    def custom_tones_dir(self) -> Path:
        return self.custom_root / "promptTone"

    # 旧名保留：指向自定义层（用户新建/修改/删除都落在这里）
    @property
    def config_dir(self) -> Path:
        return self.custom_root / "promptToneConfig"

    @property
    def config_path(self) -> Path:
        return self.custom_config_path

    @property
    def tones_dir(self) -> Path:
        return self.custom_tones_dir

    # --- 初始化 -------------------------------------------------------
    def ensure(self) -> "ToneLibrary":
        self._migrate_legacy()
        for path in (self.official_tones_dir, self.custom_tones_dir,
                     self.builtin_config_path.parent, self.official_config_path.parent,
                     self.custom_config_path.parent):
            path.mkdir(parents=True, exist_ok=True)

        # 从「两层」升级到「三层」：旧的 official 目录其实是内置+云端合并结果，
        # 直接当成内置层，云端层清空（下次刷新时原样镜像官方 zip）。
        if not self.builtin_config_path.exists():
            if self.official_config_path.is_file():
                src = self.official_config_path
                raw = self._read_raw(src)
                self._write_raw(self.builtin_config_path, raw)
                self._write_raw(self.official_config_path, self._empty_raw())
            else:
                shutil.copyfile(BUILTIN_CONFIG_PATH, self.builtin_config_path)
                self._write_raw(self.official_config_path, self._empty_raw())

        if not self.official_config_path.exists():
            self._write_raw(self.official_config_path, self._empty_raw())
        if not self.custom_config_path.exists():
            self._write_raw(self.custom_config_path, self._empty_raw())
        self._migrate_preset_custom()
        self._migrate_display_name()
        self._migrate_custom_ids()
        return self

    def _migrate_custom_ids(self) -> None:
        """50–99 不再分配给提示音：把历史落在该区间的条目按 id 顺序顺延到 100–199 末尾之后。"""
        raw = self._read_custom()
        items = raw.get("data", [])
        legacy = sorted(int(e["id"]) for e in items if 50 <= int(e["id"]) <= 99)
        if not legacy:
            return
        used = {int(e["id"]) for e in items}
        next_id = max([i for i in used if i >= 100] or [99]) + 1
        mapping = {}
        for old in legacy:
            while next_id in used:
                next_id += 1
            if next_id > 199:
                raise ToneLibraryError("自定义提示音 id 已用满（100–199），无法完成 id 迁移。")
            mapping[old] = next_id
            used.add(next_id)
        for item in items:
            old = int(item["id"])
            if old in mapping:
                item["id"] = mapping[old]
        self._write_custom(raw)
        log.info("Migrated custom tone ids out of reserved 50–99: %s", mapping)

    def _migrate_display_name(self) -> None:
        """自定义条目统一用官方字段 zhCn 存显示名；旧版本写过的 displayName 收进 zhCn。"""
        custom_raw = self._read_custom()
        changed = False
        for item in custom_raw.get("data", []):
            display = (item.get("displayName") or item.get("zhCn")
                       or item.get("name", "")).strip()
            if not display:
                continue
            if item.get("zhCn") != display:
                item["zhCn"] = display
                changed = True
            if "displayName" in item:
                item.pop("displayName")
                changed = True
        if changed:
            self._write_custom(custom_raw)

    def _migrate_preset_custom(self) -> None:
        """把 100–179 预置自定义条目并入用户自定义层，不再保留内置自定义类别。"""
        custom_raw = self._read_custom()
        custom_items = custom_raw.setdefault("data", [])
        known_ids = {int(e["id"]) for e in custom_items}

        for config_path in (self.builtin_config_path, self.official_config_path):
            raw = self._read_raw(config_path)
            kept = []
            for item in raw.get("data", []):
                tone_id = int(item["id"])
                if not is_custom_tone_id(tone_id):
                    kept.append(item)
                    continue
                item["support"] = CUSTOM_SUPPORT
                if tone_id not in known_ids:
                    custom_items.append(dict(item))
                    known_ids.add(tone_id)
                self._copy_preset_custom_pcm(item)
            raw["data"] = kept
            self._write_raw(config_path, raw)

        self._write_custom(custom_raw)

    def _copy_preset_custom_pcm(self, item: dict) -> None:
        name = item.get("name", "")
        if not name:
            return
        source = self.official_tones_dir / f"{name}.pcm"
        destination = self.custom_tones_dir / f"{name}.pcm"
        if source.is_file() and not destination.exists():
            shutil.copyfile(source, destination)

    @staticmethod
    def _empty_raw() -> dict:
        return {"version": 3, "data": [], "officialData": []}

    def _migrate_legacy(self) -> None:
        """旧版单层布局 → 分层。幂等，原数据整体移到 legacy_backup 留档。"""
        legacy_config = self.root / "promptToneConfig" / "tone_config.json"
        legacy_tones = self.root / "promptTone"
        backup = self.root / "legacy_backup"
        if not legacy_config.is_file() or backup.exists():
            return

        raw = json.loads(legacy_config.read_text(encoding="utf-8"))
        official = [e for e in raw.get("data", []) if e.get("support") != CUSTOM_SUPPORT]
        custom = [e for e in raw.get("data", []) if e.get("support") == CUSTOM_SUPPORT]
        official_data = raw.get("officialData", [])

        for entry in official + custom:
            name = entry["name"]
            src = legacy_tones / f"{name}.pcm"
            dst_dir = (self.custom_tones_dir if entry.get("support") == CUSTOM_SUPPORT
                       else self.official_tones_dir)
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f"{name}.pcm"
            if src.is_file() and not dst.is_file():
                shutil.copyfile(src, dst)

        # 旧数据都是「内置 + 云端」混在一起的，整体归入内置层
        self._write_raw(self.builtin_config_path,
                        {"version": 3, "data": official, "officialData": official_data})
        self._write_raw(self.official_config_path, self._empty_raw())
        self._write_raw(self.custom_config_path,
                        {"version": 3, "data": custom, "officialData": []})

        backup.mkdir(parents=True, exist_ok=True)
        if legacy_config.parent.is_dir():
            shutil.move(str(legacy_config.parent), str(backup / "promptToneConfig"))
        if legacy_tones.is_dir():
            shutil.move(str(legacy_tones), str(backup / "promptTone"))

    # --- 读写 ---------------------------------------------------------
    @staticmethod
    def _read_raw(path: Path) -> dict:
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw.setdefault("data", [])
        raw.setdefault("officialData", [])
        return raw

    @staticmethod
    def _write_raw(path: Path, raw: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        raw["version"] = 3
        path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _read_official(self) -> dict:
        return self._read_raw(self.official_config_path)

    def _read_builtin(self) -> dict:
        return self._read_raw(self.builtin_config_path)

    def _read_custom(self) -> dict:
        return self._read_raw(self.custom_config_path)

    def _write_custom(self, raw: dict) -> None:
        self._write_raw(self.custom_config_path, raw)

    # --- 合并视图 -----------------------------------------------------
    @staticmethod
    def _merge_by_id(base: list[dict], overlay: list[dict]) -> list[dict]:
        items = {int(e["id"]): dict(e) for e in base}
        order = [int(e["id"]) for e in base]
        for e in overlay:
            eid = int(e["id"])
            if eid in items:
                items[eid].update(e)
            else:
                items[eid] = dict(e)
                order.append(eid)
        return [items[i] for i in order if i in items]

    def merged_official_raw(self) -> dict:
        """内置层 + 云端层合并后的官方视图（data 与 officialData 各自按 id 合并）。"""
        builtin = self._read_builtin()
        official = self._read_official()
        data = self._merge_by_id(builtin.get("data", []), official.get("data", []))
        od = self._merge_by_id(builtin.get("officialData", []), official.get("officialData", []))
        # 同一 id 既在 data 又在 officialData（APK 把机型限定铃声放进了 data）时，只留 data 那条
        data_ids = {int(e["id"]) for e in data}
        od = [e for e in od if int(e["id"]) not in data_ids]
        return {"data": data, "officialData": od}

    def official_entries(self) -> list[ToneEntry]:
        return parse_tone_config(self.merged_official_raw())

    def custom_entries(self) -> list[ToneEntry]:
        return parse_tone_config(self._read_custom())

    def entries(self) -> list[ToneEntry]:
        """内置/官方层原序 + 自定义层原序。界面下拉直接照这个排，不按 id 重排。"""
        self.ensure()
        return self.official_entries() + self.custom_entries()

    def custom_ids(self) -> list[int]:
        return [e.id for e in self.custom_entries() if self.is_user_custom(e)]

    @staticmethod
    def is_user_custom(entry: ToneEntry | None) -> bool:
        """用户自定义口径：显式 custom 标记，或 100–179 预置自定义段。"""
        return entry is not None and (
            entry.support == CUSTOM_SUPPORT or is_custom_tone_id(entry.id)
        )

    def find(self, tone_id: int) -> ToneEntry | None:
        for entry in self.entries():
            if entry.id == tone_id:
                return entry
        return None

    def is_custom(self, entry: ToneEntry | None) -> bool:
        return self.is_user_custom(entry)

    # --- 音频文件定位 ---------------------------------------------------
    def pcm_file(self, entry: ToneEntry | int) -> Path:
        """条目对应的 PCM 路径：自定义层 / 官方层由条目归属决定。"""
        entry = self.find(entry) if isinstance(entry, int) else entry
        if entry is None:
            raise ToneLibraryError("找不到该提示音。")
        layer = self.custom_tones_dir if self.is_user_custom(entry) else self.official_tones_dir
        return layer / f"{entry.name}.pcm"

    # 旧名保留（GUI 里在用的 pcm_path）
    def pcm_path(self, entry: ToneEntry | int) -> Path:
        return self.pcm_file(entry)

    def has_pcm(self, entry: ToneEntry | int) -> bool:
        try:
            return self.pcm_file(entry).is_file()
        except ToneLibraryError:
            return False

    # --- 校验 ---------------------------------------------------------
    def validate_name(self, name: str, exclude_id: int | None = None) -> str:
        """校验「文件名」（不含 .pcm）：它同时是落盘文件名，因此限制为 ASCII。"""
        name = (name or "").strip()
        if not name:
            raise ToneLibraryError("文件名不能为空。")
        if any(ord(ch) > 0x7F for ch in name):
            raise ToneLibraryError("文件名里不能出现中文或其它非英文字符（中文请写进显示名）。")
        if not NAME_PATTERN.match(name):
            raise ToneLibraryError(
                "文件名只能用字母、数字、空格、下划线或连字符，且必须以字母或数字开头（最长 32 字符）。")
        lowered = name.lower()
        for entry in self.entries():
            if entry.id != exclude_id and entry.name.lower() == lowered:
                raise ToneLibraryError(f"文件名「{name}」已被 id {entry.id} 占用，请换一个。")
        return name

    @staticmethod
    def validate_display_name(name: str) -> str:
        """显示名：用户写什么就是什么，只做非空与长度限制。"""
        name = (name or "").strip()
        if not name:
            raise ToneLibraryError("显示名不能为空。")
        if len(name) > 64:
            raise ToneLibraryError("显示名最长 64 个字符。")
        return name

    # --- id 指派 -------------------------------------------------------
    def allocate_id(self) -> int:
        used = {e.id for e in self.entries()}
        for start, end in CUSTOM_ID_RANGES:
            for tone_id in range(start, end + 1):
                if tone_id not in used:
                    return tone_id
        raise ToneLibraryError("自定义提示音 id 已用满（100–199 均被占用）。")

    # --- 增删改（只碰自定义层） -----------------------------------------
    def _check_pcm(self, pcm: bytes) -> None:
        if len(pcm) == 0 or len(pcm) % 2 != 0:
            raise ToneLibraryError("PCM 数据无效（长度必须为非零偶数）。")
        if len(pcm) > TONE_MAX_BYTES:
            raise ToneLibraryError("提示音超过 6 秒上限。")

    def _ensure_custom_record(self, entry: ToneEntry) -> dict:
        """预置自定义段在旧库里可能仍留在官方/内置层，改/删前先落到自定义层。"""
        raw = self._read_custom()
        if any(int(item["id"]) == entry.id for item in raw.get("data", [])):
            return raw

        for config_path in (self.builtin_config_path, self.official_config_path):
            layer = self._read_raw(config_path)
            for item in layer.get("data", []):
                if int(item["id"]) != entry.id:
                    continue
                item["support"] = CUSTOM_SUPPORT
                raw.setdefault("data", []).append(dict(item))
                layer["data"].remove(item)
                self._write_raw(config_path, layer)
                self._copy_preset_custom_pcm(item)
                break
        self._write_custom(raw)
        return raw

    def add(self, pcm: bytes, file_name: str, display_name: str = "",
            tone_id: int | None = None) -> ToneEntry:
        """新增自定义提示音：file_name 决定 <file>.pcm，display_name 决定界面显示。"""
        self._check_pcm(pcm)
        name = self.validate_name(file_name)
        display = self.validate_display_name(display_name or name)
        tone_id = self.allocate_id() if tone_id is None else int(tone_id)
        if self.find(tone_id) is not None:
            raise ToneLibraryError(f"id {tone_id} 已被占用，请换一个。")

        raw = self._read_custom()
        # 只写官方字段：官方 App 读 zhCn 当名字，本程序也用 zhCn 当自定义条目的显示名
        raw["data"].append({"id": tone_id, "name": name, "zhCn": display,
                            "support": CUSTOM_SUPPORT})
        (self.custom_tones_dir / f"{name}.pcm").write_bytes(pcm)
        self._write_custom(raw)
        return ToneEntry(tone_id, name, display, support=CUSTOM_SUPPORT)

    def update(self, tone_id: int, file_name: str | None = None,
               display_name: str | None = None, pcm: bytes | None = None) -> ToneEntry:
        """改自定义提示音：文件名与显示名同时同步到 config 与磁盘上的 .pcm。"""
        entry = self.find(tone_id)
        if entry is None:
            raise ToneLibraryError("找不到该提示音。")
        if not self.is_user_custom(entry):
            raise ToneLibraryError("只有自定义提示音可以修改。")
        if pcm is not None:
            self._check_pcm(pcm)

        raw = self._ensure_custom_record(entry)
        new_name = entry.name if file_name is None else self.validate_name(
            file_name, exclude_id=tone_id)
        new_display = (entry.display_name if display_name is None
                       else self.validate_display_name(display_name))

        old_pcm = self.pcm_file(entry)
        new_pcm = self.custom_tones_dir / f"{new_name}.pcm"
        if pcm is not None:
            new_pcm.write_bytes(pcm)
            if old_pcm != new_pcm and old_pcm.exists():
                old_pcm.unlink()
        elif old_pcm != new_pcm:
            if new_pcm.exists():
                raise ToneLibraryError(f"文件 {new_pcm.name} 已存在，请换一个文件名。")
            if old_pcm.exists():
                old_pcm.rename(new_pcm)

        for item in raw["data"]:
            if int(item["id"]) == tone_id:
                item["name"] = new_name
                item["zhCn"] = new_display   # 官方 App 与本程序共用这一字段
                item.pop("displayName", None)   # 旧版本写过的内部字段，保持官方 schema 干净
                item["support"] = CUSTOM_SUPPORT
        self._write_custom(raw)
        return ToneEntry(tone_id, new_name, new_display, support=CUSTOM_SUPPORT)

    def delete(self, tone_id: int) -> None:
        entry = self.find(tone_id)
        if entry is None:
            raise ToneLibraryError("找不到该提示音。")
        if not self.is_user_custom(entry):
            raise ToneLibraryError("内置/官方提示音不能删除。")
        raw = self._ensure_custom_record(entry)
        raw["data"] = [item for item in raw["data"] if int(item["id"]) != tone_id]
        self._write_custom(raw)
        for directory in (self.custom_tones_dir, self.official_tones_dir):
            pcm = directory / f"{entry.name}.pcm"
            if pcm.exists():
                pcm.unlink()

    # --- 官方层刷新 -------------------------------------------------------
    @staticmethod
    def _diff_ids(prev: dict, cloud: dict) -> tuple[list[int], list[int]]:
        """对比「上一次官方快照」与「云端最新」：返回 (新增 id, 内容变化的 id)。"""
        prev_items: dict[int, dict] = {}
        for key in ("data", "officialData"):
            for e in prev.get(key, []):
                prev_items[int(e["id"])] = e
        added: list[int] = []
        updated: list[int] = []
        for key in ("data", "officialData"):
            for e in cloud.get(key, []):
                eid = int(e["id"])
                if eid not in prev_items:
                    added.append(eid)
                elif {k: v for k, v in prev_items[eid].items()} != {k: v for k, v in e.items()}:
                    updated.append(eid)
        return sorted(set(added)), sorted(set(updated))

    def refresh_official_config(self, *, config_bytes: bytes | None = None,
                                timeout: int = DOWNLOAD_TIMEOUT) -> RefreshResult:
        """只刷新「官方目录」：官方 zip 里的 data/officialData 原样存下来。

        与上一次官方快照比较得到「新增/更新」，所以内容没变时再点一次应是 0/0。
        自定义层、内置层都不参与，官方更新不会影响它们。
        """
        self.ensure()
        if config_bytes is None:
            config_bytes = urllib.request.urlopen(OFFICIAL_CONFIG_URL, timeout=timeout).read()
        try:
            with zipfile.ZipFile(io.BytesIO(config_bytes)) as z:
                names = [n for n in z.namelist() if n.endswith(".json")]
                cloud = json.loads(z.read(names[0]).decode("utf-8"))
        except (zipfile.BadZipFile, IndexError, json.JSONDecodeError) as exc:
            raise ToneLibraryError(f"官方提示音目录包解析失败：{exc}") from exc

        cloud.setdefault("data", [])
        cloud.setdefault("officialData", [])
        added, updated = self._diff_ids(self._read_official(), cloud)
        self._write_raw(self.official_config_path,
                        {"version": 3, "data": cloud["data"],
                         "officialData": cloud["officialData"]})
        merged = self.merged_official_raw()
        return RefreshResult(official_total=len(merged["data"]) + len(merged["officialData"]),
                             added=added, updated=updated)

    def refresh_official_tones(self, *, tones_bytes: bytes | None = None,
                               timeout: int = DOWNLOAD_TIMEOUT) -> RefreshResult:
        """只刷新「官方音频资源包」：zip 里所有 *.pcm 落到官方音频目录。"""
        self.ensure()
        if tones_bytes is None:
            tones_bytes = urllib.request.urlopen(OFFICIAL_TONES_URL, timeout=timeout).read()
        written: list[str] = []
        try:
            with zipfile.ZipFile(io.BytesIO(tones_bytes)) as z:
                for member in z.namelist():
                    if not member.lower().endswith(".pcm"):
                        continue
                    name = member.split("/")[-1]
                    (self.official_tones_dir / name).write_bytes(z.read(member))
                    written.append(name)
        except zipfile.BadZipFile as exc:
            raise ToneLibraryError(f"官方提示音音频包解析失败：{exc}") from exc
        merged = self.merged_official_raw()
        return RefreshResult(official_total=len(merged["data"]) + len(merged["officialData"]),
                             pcm_written=written)

    def refresh_official(self, *, config_bytes: bytes | None = None,
                         tones_bytes: bytes | None = None,
                         timeout: int = DOWNLOAD_TIMEOUT) -> RefreshResult:
        """一次拉齐目录 + 音频（命令行/脚本用；界面上是两个独立按钮）。"""
        cfg = self.refresh_official_config(config_bytes=config_bytes, timeout=timeout)
        tones = self.refresh_official_tones(tones_bytes=tones_bytes, timeout=timeout)
        cfg.pcm_written = tones.pcm_written
        return cfg

    # --- 导出 ---------------------------------------------------------
    def export_zip(self, dest: Path) -> Path:
        """导出「合并后的 config + 全部 PCM」，结构与官方配布包一致，可直接给手机用。"""
        self.ensure()
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        merged = self.merged_official_raw()
        custom = self._read_custom()
        # 官方 App 只认 {id, name, zhCn, support}；displayName 是本程序内部字段，导出时去掉，
        # 并把显示名落到 zhCn，保证手机端看到的名字与桌面端一致
        custom_items = []
        for item in custom.get("data", []):
            entry = {"id": item.get("id"), "name": item.get("name", "")}
            entry["zhCn"] = item.get("displayName") or item.get("zhCn") or item.get("name", "")
            entry["support"] = item.get("support", CUSTOM_SUPPORT)
            custom_items.append(entry)
        out = {"version": 3,
               "data": list(merged.get("data", [])) + custom_items,
               "officialData": list(merged.get("officialData", []))}
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("promptToneConfig/tone_config.json",
                       json.dumps(out, ensure_ascii=False, indent=2) + "\n")
            seen = set()
            for directory in (self.official_tones_dir, self.custom_tones_dir):
                for pcm in sorted(directory.glob("*.pcm")):
                    if pcm.name in seen:
                        continue
                    seen.add(pcm.name)
                    z.write(pcm, f"promptTone/{pcm.name}")
        return dest
