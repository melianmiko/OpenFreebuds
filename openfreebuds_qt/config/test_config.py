import codecs
import importlib
import json

import pytest

pytest.importorskip("PyQt6")

import openfreebuds_qt.config.main as config_main


@pytest.fixture
def config_parser(tmp_path, monkeypatch):
    importlib.reload(config_main)
    monkeypatch.setattr(config_main, "CONFIG_PATH", tmp_path / "openfreebuds_qt.json")

    def factory():
        assert config_main.CONFIG_PATH.parent == tmp_path, \
            f"config path escaped tmp_path: {config_main.CONFIG_PATH}"
        config_main.OfbQtConfigParser.instance = None
        return config_main.OfbQtConfigParser()

    yield factory
    config_main.OfbQtConfigParser.instance = None


def _write(path, data, bom=False):
    raw = json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")
    path.write_bytes((codecs.BOM_UTF8 + raw) if bom else raw)


def test_bom_prefixed_config_loads(config_parser, tmp_path):
    _write(tmp_path / "openfreebuds_qt.json", {"ui": {"background": False}}, bom=True)

    parser = config_parser()

    assert not parser.config_load_failed
    assert parser.get("ui", "background") is False


def test_malformed_config_still_reported(config_parser, tmp_path):
    (tmp_path / "openfreebuds_qt.json").write_bytes(b"{not json")

    parser = config_parser()

    assert parser.config_load_failed
    assert parser.get("ui", "background", True) is True


def test_save_writes_utf8_without_bom(config_parser, tmp_path):
    _write(tmp_path / "openfreebuds_qt.json", {"ui": {"language": "ru"}})

    parser = config_parser()
    parser.set("device", "name", "Беспроводные наушники")
    parser.save()

    raw = (tmp_path / "openfreebuds_qt.json").read_bytes()
    assert not raw.startswith(codecs.BOM_UTF8)

    reloaded = config_parser()
    assert not reloaded.config_load_failed
    assert reloaded.get("device", "name") == "Беспроводные наушники"
    assert reloaded.get("ui", "language") == "ru"