"""Local prompt-tone library (PC side only; decoupled from earbud transfer).
Three-layer layout (second refactor, 2026-11-14: official config follows upstream, local additions are separate): builtin/promptToneConfig/tone_config.json is the APK built-in catalog (static, bundled, offline); official mirrors the cloud package; custom holds user edits.
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

# Custom tones use 100-199 (100-179 bundled, 180-199 for future additions);
# 50-99 is reserved for other uses and no longer allocated; legacy entries in that range are shifted by _migrate_custom_ids.
CUSTOM_ID_RANGES = ((100, 199),)
RESERVED_ID_RANGES = ((50, 99),)
log = logging.getLogger("ToneLibrary")
CUSTOM_SUPPORT = "custom"
BUILTIN_CONFIG_PATH = Path(__file__).resolve().parents[2] / "assets" / "tone_config.json"

OFFICIAL_CONFIG_URL = f"{CLOUD_BASE}/00000A/00000A_promptToneConfig.zip"
OFFICIAL_TONES_URL = f"{CLOUD_BASE}/00000A/00000A_promptTone.zip"
DOWNLOAD_TIMEOUT = 30

# English name: starts with a letter/digit; only letters, digits, spaces, underscores and hyphens; no non-ASCII characters
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$")


class ToneLibraryError(Exception):
    """Library operation failed (message can be shown to the user)."""


@dataclass
class RefreshResult:
    """Official-layer refresh result (compared with the previous official snapshot, so a repeated refresh should be 0/0)."""
    official_total: int = 0
    added: list[int] = field(default_factory=list)
    updated: list[int] = field(default_factory=list)
    pcm_written: list[str] = field(default_factory=list)


@dataclass
class ToneLibrary:
    root: Path = STORAGE_PATH / "prompt_tones"

    # --- Layout -------------------------------------------------------
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
        """Official audio directory (built-in and cloud tones both live here)."""
        return self.official_root / "promptTone"

    @property
    def custom_tones_dir(self) -> Path:
        return self.custom_root / "promptTone"

    # Legacy name kept: points to the custom layer (create/update/delete all land there)
    @property
    def config_dir(self) -> Path:
        return self.custom_root / "promptToneConfig"

    @property
    def config_path(self) -> Path:
        return self.custom_config_path

    @property
    def tones_dir(self) -> Path:
        return self.custom_tones_dir

    # --- Initialization -----------------------------------------------
    def ensure(self) -> "ToneLibrary":
        self._migrate_legacy()
        for path in (self.official_tones_dir, self.custom_tones_dir,
                     self.builtin_config_path.parent, self.official_config_path.parent,
                     self.custom_config_path.parent):
            path.mkdir(parents=True, exist_ok=True)

        # Upgrade from two layers to three: the old official directory was actually built-in + cloud merged,
        # treat it as the built-in layer and clear the cloud layer (the next refresh mirrors the official zip).
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
        """50-99 is no longer assigned to tones: legacy entries in that range are shifted after 100-199 in id order."""
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
        """Custom entries use official zhCn for the display name; legacy displayName values are moved into zhCn."""
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
        """Merge the 100-179 bundled custom entries into the user custom layer and drop the built-in custom category."""
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
        """Old single-layer layout -> layered layout. Idempotent; all original data moves to legacy_backup for reference."""
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

        # Old data mixed built-in + cloud; move it all into the built-in layer
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

    # --- Read/write ---------------------------------------------------
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

    # --- Merged view --------------------------------------------------
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
        """Official view after merging built-in and cloud layers (data and officialData are merged by id separately)."""
        builtin = self._read_builtin()
        official = self._read_official()
        data = self._merge_by_id(builtin.get("data", []), official.get("data", []))
        od = self._merge_by_id(builtin.get("officialData", []), official.get("officialData", []))
        # When an id exists in both data and officialData (the APK put model-specific tones in data), keep only the data entry
        data_ids = {int(e["id"]) for e in data}
        od = [e for e in od if int(e["id"]) not in data_ids]
        return {"data": data, "officialData": od}

    def official_entries(self) -> list[ToneEntry]:
        return parse_tone_config(self.merged_official_raw())

    def custom_entries(self) -> list[ToneEntry]:
        return parse_tone_config(self._read_custom())

    def entries(self) -> list[ToneEntry]:
        """Built-in/official original order + custom original order. The UI combo follows this order and does not sort by id."""
        self.ensure()
        return self.official_entries() + self.custom_entries()

    def custom_ids(self) -> list[int]:
        return [e.id for e in self.custom_entries() if self.is_user_custom(e)]

    @staticmethod
    def is_user_custom(entry: ToneEntry | None) -> bool:
        """User custom rule: explicit custom marker, or the 100-179 bundled custom range."""
        return entry is not None and (
            entry.support == CUSTOM_SUPPORT or is_custom_tone_id(entry.id)
        )

    def is_editable(self, entry: ToneEntry | None) -> bool:
        """Editable/deletable rule: any entry not in the current official Config is custom.
        Id 14 is such a case: it came from an old built-in package but the official Config removed it, so it is actually a user custom entry and must be editable/deletable; real official entries remain read-only.
        """
        if entry is None:
            return False
        if self.is_user_custom(entry):
            return True
        remote = self._read_official()
        remote_ids = {
            int(e["id"])
            for key in ("data", "officialData")
            for e in remote.get(key, [])
        }
        if not remote_ids:
            # Fall back to the built-in layer before the official Config is downloaded, so built-in entries are not all exposed
            remote_ids = {e.id for e in self.official_entries()}
        return entry.id not in remote_ids

    def find(self, tone_id: int) -> ToneEntry | None:
        for entry in self.entries():
            if entry.id == tone_id:
                return entry
        return None

    def is_custom(self, entry: ToneEntry | None) -> bool:
        return self.is_user_custom(entry)

    # --- Audio file lookup --------------------------------------------
    def pcm_file(self, entry: ToneEntry | int) -> Path:
        """PCM path for an entry: determined by whether it belongs to the custom or official layer."""
        entry = self.find(entry) if isinstance(entry, int) else entry
        if entry is None:
            raise ToneLibraryError("找不到该提示音。")
        layer = self.custom_tones_dir if self.is_user_custom(entry) else self.official_tones_dir
        return layer / f"{entry.name}.pcm"

    # Legacy name kept (pcm_path used by the GUI)
    def pcm_path(self, entry: ToneEntry | int) -> Path:
        return self.pcm_file(entry)

    def has_pcm(self, entry: ToneEntry | int) -> bool:
        try:
            return self.pcm_file(entry).is_file()
        except ToneLibraryError:
            return False

    # --- Validation ---------------------------------------------------
    def validate_name(self, name: str, exclude_id: int | None = None) -> str:
        """Validate the file name (without .pcm): it is also the on-disk name, so restrict it to ASCII."""
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
        """Display name: exactly what the user wrote, limited only by non-empty and length checks."""
        name = (name or "").strip()
        if not name:
            raise ToneLibraryError("显示名不能为空。")
        if len(name) > 64:
            raise ToneLibraryError("显示名最长 64 个字符。")
        return name

    # --- Id assignment -----------------------------------------------
    def allocate_id(self) -> int:
        used = {e.id for e in self.entries()}
        for start, end in CUSTOM_ID_RANGES:
            for tone_id in range(start, end + 1):
                if tone_id not in used:
                    return tone_id
        raise ToneLibraryError("自定义提示音 id 已用满（100–199 均被占用）。")

    # --- Create/update/delete (custom layer only) --------------------
    def _check_pcm(self, pcm: bytes) -> None:
        if len(pcm) == 0 or len(pcm) % 2 != 0:
            raise ToneLibraryError("PCM 数据无效（长度必须为非零偶数）。")
        if len(pcm) > TONE_MAX_BYTES:
            raise ToneLibraryError("提示音超过 6 秒上限。")

    def _ensure_custom_record(self, entry: ToneEntry) -> dict:
        """Bundled custom entries may still be in the official/built-in layer in old libraries; move them to the custom layer before update/delete."""
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
        """Create a custom tone: file_name determines <file>.pcm, display_name determines the UI label."""
        self._check_pcm(pcm)
        name = self.validate_name(file_name)
        display = self.validate_display_name(display_name or name)
        tone_id = self.allocate_id() if tone_id is None else int(tone_id)
        if self.find(tone_id) is not None:
            raise ToneLibraryError(f"id {tone_id} 已被占用，请换一个。")

        raw = self._read_custom()
        # Write official fields only: the official App reads zhCn as the name, and this app uses zhCn as the custom display name
        raw["data"].append({"id": tone_id, "name": name, "zhCn": display,
                            "support": CUSTOM_SUPPORT})
        (self.custom_tones_dir / f"{name}.pcm").write_bytes(pcm)
        self._write_custom(raw)
        return ToneEntry(tone_id, name, display, support=CUSTOM_SUPPORT)

    def update(self, tone_id: int, file_name: str | None = None,
               display_name: str | None = None, pcm: bytes | None = None) -> ToneEntry:
        """Update a custom tone: sync both file name and display name to config and the on-disk .pcm."""
        entry = self.find(tone_id)
        if entry is None:
            raise ToneLibraryError("找不到该提示音。")
        if not self.is_editable(entry):
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
                item["zhCn"] = new_display   # Shared by the official App and this app
                item.pop("displayName", None)   # Internal field written by older versions; keep the official schema clean
                item["support"] = CUSTOM_SUPPORT
        self._write_custom(raw)
        return ToneEntry(tone_id, new_name, new_display, support=CUSTOM_SUPPORT)

    def delete(self, tone_id: int) -> None:
        entry = self.find(tone_id)
        if entry is None:
            raise ToneLibraryError("找不到该提示音。")
        if not self.is_editable(entry):
            raise ToneLibraryError("内置/官方提示音不能删除。")
        raw = self._ensure_custom_record(entry)
        raw["data"] = [item for item in raw["data"] if int(item["id"]) != tone_id]
        self._write_custom(raw)
        for directory in (self.custom_tones_dir, self.official_tones_dir):
            pcm = directory / f"{entry.name}.pcm"
            if pcm.exists():
                pcm.unlink()

    # --- Official layer refresh ---------------------------------------
    @staticmethod
    def _diff_ids(prev: dict, cloud: dict) -> tuple[list[int], list[int]]:
        """Compare the previous official snapshot with the latest cloud data: return (added ids, changed ids)."""
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
        """Refresh only the official catalog: store data/officialData from the official zip as-is.
        Compare with the previous official snapshot to get added/updated, so a second click with unchanged content returns 0/0. Custom and built-in layers are untouched, and official updates never affect them.
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
        """Refresh only the official audio package: write every *.pcm from the zip into the official audio directory."""
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
        """Fetch catalog and audio in one call (CLI/scripting; the UI has two separate buttons)."""
        cfg = self.refresh_official_config(config_bytes=config_bytes, timeout=timeout)
        tones = self.refresh_official_tones(tones_bytes=tones_bytes, timeout=timeout)
        cfg.pcm_written = tones.pcm_written
        return cfg

    # --- Export -------------------------------------------------------
    def export_zip(self, dest: Path) -> Path:
        """Export the merged config plus all PCM files, in the same structure as the official distribution package, ready for a phone."""
        self.ensure()
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        merged = self.merged_official_raw()
        custom = self._read_custom()
        # The official App only understands {id, name, zhCn, support}; displayName is internal and removed on export,
        # and the display name is written to zhCn so phone and desktop show the same name
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
