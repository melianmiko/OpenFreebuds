import plistlib
import sys

import pytest

if sys.platform != "darwin":
    pytest.skip("macOS backend", allow_module_level=True)

from openfreebuds_backend.darwin import misc_macos


@pytest.mark.parametrize("cli", [None, "/Volumes/External SSD/dev/bin/openfreebuds_qt"])
def test_frozen_autostart_uses_bundle_executable(monkeypatch, cli):
    executable = "/Volumes/External SSD/Apps/OpenFreebuds.app/Contents/MacOS/OpenFreebuds"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", executable)
    monkeypatch.setattr(misc_macos.shutil, "which", lambda _: cli)

    assert misc_macos._program_arguments() == [executable]


@pytest.mark.parametrize("cli", [None, "/Volumes/External SSD/dev/bin/openfreebuds_qt"])
def test_source_autostart_preserves_python_entry_point(monkeypatch, cli):
    executable = "/Volumes/External SSD/dev/bin/python"
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.setattr(sys, "executable", executable)
    monkeypatch.setattr(misc_macos.shutil, "which", lambda _: cli)

    expected = [cli] if cli else [executable, "-m", "openfreebuds_qt"]
    assert misc_macos._program_arguments() == expected


@pytest.mark.asyncio
async def test_disable_autostart_does_not_unload_running_app(monkeypatch, tmp_path):
    path = tmp_path / "pw.mmk.OpenFreebuds.plist"
    path.write_bytes(b"existing agent")
    calls = []
    monkeypatch.setattr(misc_macos, "_launch_agent_path", lambda: path)
    monkeypatch.setattr(misc_macos.os, "getuid", lambda: 501)
    monkeypatch.setattr(misc_macos, "_launchctl", lambda *args: calls.append(args))

    await misc_macos.set_run_at_boot(False)

    assert not path.exists()
    assert calls == [("disable", "gui/501/pw.mmk.OpenFreebuds")]


@pytest.mark.asyncio
async def test_enable_autostart_registers_bundle_for_next_login(monkeypatch, tmp_path):
    path = tmp_path / "LaunchAgents" / "pw.mmk.OpenFreebuds.plist"
    executable = "/Volumes/External SSD/Apps/OpenFreebuds.app/Contents/MacOS/OpenFreebuds"
    calls = []
    monkeypatch.setattr(misc_macos, "_launch_agent_path", lambda: path)
    monkeypatch.setattr(misc_macos.os, "getuid", lambda: 501)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", executable)
    monkeypatch.setattr(misc_macos, "_launchctl", lambda *args: calls.append(args))

    await misc_macos.set_run_at_boot(True)

    agent = plistlib.loads(path.read_bytes())
    assert agent["ProgramArguments"] == [executable]
    assert agent["RunAtLoad"] is True
    assert calls == [("enable", "gui/501/pw.mmk.OpenFreebuds")]
