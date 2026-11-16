"""Local custom tone library tests (decoupled from earbud transfer)."""
import io
import json
import zipfile

import pytest

from openfreebuds.driver.huawei.prompt_tone import TONE_MAX_BYTES, is_custom_tone_id
from openfreebuds.driver.huawei.tone_library import (
    CUSTOM_SUPPORT,
    ToneLibrary,
    ToneLibraryError,
)

PCM = bytes([0x10, 0x00] * 160)  # 10ms @16k


def make_library(tmp_path):
    return ToneLibrary(root=tmp_path / "lib").ensure()


def test_ensure_seeds_builtin_config(tmp_path):
    lib = make_library(tmp_path)
    assert lib.config_path.exists()
    assert lib.tones_dir.is_dir()
    raw = json.loads(lib.config_path.read_text(encoding="utf-8"))
    assert raw["version"] == 3
    assert len(lib.entries()) == 66


def test_first_custom_id_is_in_100_range(tmp_path):
    """50-99 is reserved: new entries come from 100-199, shifted after bundled entries are allocated."""
    lib = make_library(tmp_path)
    preset_ids = {e.id for e in lib.entries()}
    new_id = lib.allocate_id()
    assert 100 <= new_id <= 199
    assert new_id not in preset_ids


def test_legacy_display_name_folds_into_zh_cn(tmp_path):
    """The internal displayName field written by older versions is moved into official zhCn and removed by ensure."""
    lib = make_library(tmp_path)
    raw = json.loads(lib.custom_config_path.read_text(encoding="utf-8"))
    raw["data"].append({"id": 160, "name": "Legacy", "displayName": "旧名字",
                        "support": "custom"})
    lib.custom_config_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    (lib.custom_tones_dir / "Legacy.pcm").write_bytes(PCM)

    lib = ToneLibrary(root=lib.root).ensure()
    entry = lib.find(160)
    assert entry.display_name == "旧名字"
    migrated = [e for e in json.loads(
        lib.custom_config_path.read_text(encoding="utf-8"))["data"] if int(e["id"]) == 160][0]
    assert set(migrated) == {"id", "name", "zhCn", "support"}
    assert migrated["zhCn"] == "旧名字"


def test_reserved_ids_migrate_to_end_of_100_range(tmp_path):
    """Entries historically in 50-99 are shifted to the end of 100-199 by ensure, preserving old id order."""
    lib = make_library(tmp_path)
    raw = json.loads(lib.custom_config_path.read_text(encoding="utf-8"))
    max_id = max(int(e["id"]) for e in raw["data"])
    raw["data"].append({"id": 55, "name": "Old55", "zhCn": "旧五五", "support": "custom"})
    raw["data"].append({"id": 52, "name": "Old52", "zhCn": "旧五二", "support": "custom"})
    lib.custom_config_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    for n in ("Old55", "Old52"):
        (lib.custom_tones_dir / f"{n}.pcm").write_bytes(PCM)

    lib = ToneLibrary(root=lib.root).ensure()
    ids = [e.id for e in lib.custom_entries()]
    assert 52 not in ids and 55 not in ids
    # 52 comes before 55; each shifts by one
    assert lib.find(max_id + 1).name == "Old52"
    assert lib.find(max_id + 2).name == "Old55"
    assert lib.find(max_id + 1).display_name == "旧五二"


    # Idempotent: a second ensure does not change anything
    lib2 = ToneLibrary(root=lib.root).ensure()
    assert [e.id for e in lib2.custom_entries()] == ids


def test_add_tone(tmp_path):
    lib = make_library(tmp_path)
    entry = lib.add(PCM, "MyChime", "我的铃声")

    assert 100 <= entry.id <= 199
    assert entry.support == CUSTOM_SUPPORT
    assert (lib.tones_dir / "MyChime.pcm").read_bytes() == PCM

    entries = lib.entries()
    custom = [e for e in entries if lib.is_user_custom(e)]
    assert len(custom) == 47  # 46 bundled custom tones + 1 user-created tone
    assert [e.id for e in custom if e.id == entry.id] == [entry.id]
    assert custom[-1].display_name == "我的铃声"
    # The custom layer writes only official fields; the display name goes to zhCn (the official App reads it too)
    raw = json.loads(lib.custom_config_path.read_text(encoding="utf-8"))
    added = [e for e in raw["data"] if int(e["id"]) == entry.id][0]
    assert set(added) == {"id", "name", "zhCn", "support"}
    assert added["zhCn"] == "我的铃声"


def test_add_rejects_chinese_name(tmp_path):
    lib = make_library(tmp_path)
    with pytest.raises(ToneLibraryError, match="不能出现中文"):
        lib.add(PCM, "铃声", "铃声")


def test_add_rejects_duplicate_name(tmp_path):
    lib = make_library(tmp_path)
    lib.add(PCM, "MyChime", "")
    with pytest.raises(ToneLibraryError, match="已被"):
        lib.add(PCM, "mychime", "")


def test_add_rejects_invalid_pcm(tmp_path):
    lib = make_library(tmp_path)
    with pytest.raises(ToneLibraryError, match="PCM"):
        lib.add(b"", "Empty", "")
    with pytest.raises(ToneLibraryError, match="6 秒"):
        lib.add(b"\x00\x00" * (TONE_MAX_BYTES // 2 + 1), "TooLong", "")


def test_ids_continue_and_overflow_range(tmp_path):
    lib = make_library(tmp_path)
    first = lib.add(PCM, "A1", "")
    second = lib.add(PCM, "A2", "")
    assert second.id == first.id + 1

    # After a number is explicitly reserved, allocate skips it and continues
    third = lib.add(PCM, "B190", "", tone_id=190)
    assert third.id == 190
    assert lib.allocate_id() == second.id + 1


def test_delete_tone(tmp_path):
    lib = make_library(tmp_path)
    entry = lib.add(PCM, "Gone", "")
    lib.delete(entry.id)
    assert lib.find(entry.id) is None
    assert not (lib.tones_dir / "Gone.pcm").exists()


def test_delete_builtin_rejected(tmp_path):
    lib = make_library(tmp_path)
    with pytest.raises(ToneLibraryError, match="不能删除"):
        lib.delete(0)


def test_update_rename_and_replace(tmp_path):
    lib = make_library(tmp_path)
    tone = lib.add(PCM, "Old", "旧")
    new_pcm = bytes([0x20, 0x00] * 200)
    entry = lib.update(tone.id, file_name="New", display_name="新", pcm=new_pcm)

    assert entry.name == "New"
    assert (lib.tones_dir / "New.pcm").read_bytes() == new_pcm
    assert not (lib.tones_dir / "Old.pcm").exists()
    assert lib.find(tone.id).display_name == "新"


def test_update_keeps_display_when_only_pcm_changes(tmp_path):
    """Replace audio without changing the name: file name and display name stay."""
    lib = make_library(tmp_path)
    tone = lib.add(PCM, "Keep", "原名")
    new_pcm = bytes([0x01, 0x00] * 100)
    entry = lib.update(tone.id, pcm=new_pcm)

    assert entry.name == "Keep"
    assert entry.display_name == "原名"
    assert (lib.tones_dir / "Keep.pcm").read_bytes() == new_pcm


def test_update_builtin_rejected(tmp_path):
    lib = make_library(tmp_path)
    with pytest.raises(ToneLibraryError, match="只有自定义"):
        lib.update(0, file_name="X")


def test_export_zip_structure(tmp_path):
    lib = make_library(tmp_path)
    lib.add(PCM, "Zip1", "导出")
    dest = lib.export_zip(tmp_path / "out.zip")

    with zipfile.ZipFile(dest) as z:
        names = z.namelist()
        cfg = json.loads(z.read("promptToneConfig/tone_config.json").decode("utf-8"))
    assert "promptToneConfig/tone_config.json" in names
    assert "promptTone/Zip1.pcm" in names

    # Exported JSON must contain only fields the official App understands; do not include displayName
    mine = [e for e in cfg["data"] if e["name"] == "Zip1"][0]
    assert set(mine) == {"id", "name", "zhCn", "support"}
    assert mine["zhCn"] == "导出"
    assert mine["name"] == "Zip1"


def test_preset_custom_ids_migrate_to_custom(tmp_path):
    lib = make_library(tmp_path)
    builtin = json.loads(lib.builtin_config_path.read_text(encoding="utf-8"))
    custom = json.loads(lib.custom_config_path.read_text(encoding="utf-8"))

    assert all(not is_custom_tone_id(e["id"]) for e in builtin["data"])
    assert any(is_custom_tone_id(e["id"]) for e in custom["data"])
    assert len(lib.entries()) == 66

    lib.delete(100)
    assert lib.find(100) is None


# --- Three-layer separation (official / custom) --------------------------

def _config_zip(entries, official=None):
    raw = {"version": 3, "data": entries, "officialData": official or []}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("00000A_promptToneConfig/tone_config.json",
                   json.dumps(raw, ensure_ascii=False))
    return buf.getvalue()


def _tones_zip(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name in names:
            z.writestr(f"00000A_promptTone/{name}.pcm", PCM)
    return buf.getvalue()


def test_entries_merge_official_then_custom(tmp_path):
    lib = make_library(tmp_path)
    lib.add(PCM, "Mine", "我的")
    entries = lib.entries()
    assert entries[0].id == 0                 # Official layer first, original order preserved
    assert 100 <= entries[-1].id <= 199       # Custom layer after it
    assert len(entries) == 67


def test_pcm_file_layers(tmp_path):
    lib = make_library(tmp_path)
    official = lib.find(4)
    assert lib.pcm_file(official).parent == lib.official_tones_dir
    custom = lib.add(PCM, "Mine", "")
    assert lib.pcm_file(custom).parent == lib.custom_tones_dir


def test_refresh_keeps_custom_layer(tmp_path):
    lib = make_library(tmp_path)
    mine = lib.add(PCM, "Mine", "我的")

    result = lib.refresh_official(
        config_bytes=_config_zip([{"id": 300, "name": "NewTone", "zhCn": "新音"}]),
        tones_bytes=_tones_zip(["NewTone"]),
    )

    assert 300 in result.added
    assert lib.find(300).zh_cn == "新音"
    assert lib.find(mine.id).name == "Mine"   # Custom layer untouched
    assert (lib.custom_tones_dir / "Mine.pcm").is_file()
    assert (lib.official_tones_dir / "NewTone.pcm").is_file()
    assert len(lib.entries()) == 68           # 66 built-in + 1 new official + 1 custom


def test_refresh_updates_existing_name_in_place(tmp_path):
    lib = make_library(tmp_path)
    # First pass: create the official snapshot (built-in layer already has id 4, but the official layer is empty -> counts as added)
    lib.refresh_official_config(
        config_bytes=_config_zip([{"id": 4, "name": "Bongo", "zhCn": "邦戈手鼓"}]))
    # Second pass: same id with changed content -> counts as updated
    result = lib.refresh_official_config(
        config_bytes=_config_zip([{"id": 4, "name": "Bongo2", "zhCn": "邦戈2"}]))
    assert 4 in result.updated
    entry = lib.find(4)
    assert entry.name == "Bongo2"
    # Position unchanged: still third (determined by built-in order), not moved to the end by an update
    assert [e.id for e in lib.entries()][2] == 4


def test_refresh_is_idempotent(tmp_path):
    """Refresh the same official content twice; the second refresh must be 0 added, 0 updated."""
    lib = make_library(tmp_path)
    payload = _config_zip([{"id": 4, "name": "Bongo", "zhCn": "邦戈手鼓"}],
                          [{"id": 200, "name": "Chopin", "zhCn": "肖邦"}])

    first = lib.refresh_official_config(config_bytes=payload)
    assert set(first.added) == {4, 200}

    second = lib.refresh_official_config(config_bytes=payload)
    assert second.added == []
    assert second.updated == []


def test_official_layer_mirrors_cloud_verbatim(tmp_path):
    """The official layer must mirror the cloud exactly and not merge with the built-in layer (otherwise every refresh reports adds)."""
    lib = make_library(tmp_path)
    lib.refresh_official_config(
        config_bytes=_config_zip([{"id": 4, "name": "Bongo", "zhCn": "邦戈手鼓"}],
                                 [{"id": 200, "name": "Chopin", "zhCn": "肖邦"}]))
    raw = json.loads(lib.official_config_path.read_text(encoding="utf-8"))
    assert [e["id"] for e in raw["data"]] == [4]
    assert [e["id"] for e in raw["officialData"]] == [200]
    # The merged view shown by the UI still contains the 66 built-in entries
    assert len([e for e in lib.entries() if not lib.is_user_custom(e)]) == 20


def test_refresh_tones_writes_pcm_files(tmp_path):
    lib = make_library(tmp_path)
    result = lib.refresh_official_tones(tones_bytes=_tones_zip(["Bongo", "NewTone"]))
    assert "Bongo.pcm" in result.pcm_written
    assert (lib.official_tones_dir / "NewTone.pcm").read_bytes() == PCM



def test_refresh_dedupes_official_data(tmp_path):
    """When the same id is in data and officialData, keep only the data entry."""
    lib = make_library(tmp_path)
    assert lib.find(200) is not None            # Built-in layer already contains 200
    lib.refresh_official(
        config_bytes=_config_zip([], [{"id": 200, "name": "Chopin", "zhCn": "肖邦"}]),
        tones_bytes=_tones_zip(["Chopin"]),
    )
    rows = [e for e in lib.entries() if e.id == 200]
    assert len(rows) == 1


def test_migrate_legacy_layout(tmp_path):
    root = tmp_path / "lib"
    legacy_tones = root / "promptTone"
    legacy_cfg_dir = root / "promptToneConfig"
    legacy_tones.mkdir(parents=True)
    legacy_cfg_dir.mkdir(parents=True)
    (legacy_tones / "Bongo.pcm").write_bytes(PCM)
    (legacy_tones / "Mine.pcm").write_bytes(PCM)
    (legacy_cfg_dir / "tone_config.json").write_text(json.dumps({
        "version": 3,
        "data": [
            {"id": 4, "name": "Bongo", "zhCn": "邦戈"},
            {"id": 50, "name": "Mine", "zhCn": "我的", "support": "custom"},
        ],
        "officialData": [],
    }, ensure_ascii=False), encoding="utf-8")

    lib = ToneLibrary(root=root).ensure()

    assert lib.find(4).support == ""
    mine = next(e for e in lib.entries() if e.name == "Mine")
    assert mine.support == CUSTOM_SUPPORT
    assert 100 <= mine.id <= 199              # 50 from the old layout has been moved out of the reserved range
    assert (lib.official_tones_dir / "Bongo.pcm").is_file()
    assert (lib.custom_tones_dir / "Mine.pcm").is_file()
    assert (root / "legacy_backup" / "promptToneConfig" / "tone_config.json").is_file()
    assert not legacy_cfg_dir.exists()        # The old layout has moved as a whole

