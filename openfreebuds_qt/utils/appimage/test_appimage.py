import os
import stat

import pytest

from openfreebuds_backend.linux.linux_misc import quote_exec
from openfreebuds_qt.utils.appimage import integration
from openfreebuds_qt.utils.appimage.updater import pick_release, version_key

RELEASE = {
    "tag_name": "v0.18.1.1",
    "html_url": "https://github.com/owner/OpenFreebuds/releases/tag/v0.18.1.1",
    "assets": [
        {"name": "OpenFreebuds-0.18.1.1-x86_64.AppImage.zsync",
         "browser_download_url": "https://example.invalid/a.zsync"},
        {"name": "OpenFreebuds-0.18.1.1-x86_64.AppImage",
         "browser_download_url": "https://example.invalid/a.AppImage",
         "digest": "sha256:" + "ab" * 32},
        {"name": "OpenFreebuds-0.18.1.1-x86_64.AppImage.sha256",
         "browser_download_url": "https://example.invalid/a.sha256"},
    ],
}


def test_version_key():
    assert version_key("0.18.1.1") > version_key("0.18.1")
    assert version_key("v0.18.10") > version_key("0.18.9")
    assert version_key("0.18.2") > version_key("0.18.1.1")
    assert version_key("unknown") == ()


def test_pick_release_uses_digest():
    release = pick_release(RELEASE, "x86_64")
    assert release.version == "0.18.1.1"
    assert release.url == "https://example.invalid/a.AppImage"
    assert release.sha256 == "ab" * 32
    assert release.checksum_url == "https://example.invalid/a.sha256"


def test_pick_release_without_digest_or_arch():
    data = {**RELEASE, "assets": [{k: v for k, v in a.items() if k != "digest"} for a in RELEASE["assets"]]}
    release = pick_release(data, "x86_64")
    assert release.sha256 is None
    assert release.checksum_url == "https://example.invalid/a.sha256"
    assert pick_release(RELEASE, "aarch64") is None


def test_quote_exec():
    assert quote_exec("/home/a b/OpenFreebuds.AppImage") == '"/home/a b/OpenFreebuds.AppImage"'
    assert quote_exec('/tmp/$x"`\\') == '"/tmp/\\$x\\"\\`\\\\"'


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    downloaded = tmp_path / "Downloads" / "OpenFreebuds-0.18.1.1-x86_64.AppImage"
    downloaded.parent.mkdir()
    downloaded.write_bytes(b"appimage")
    monkeypatch.setenv("APPIMAGE", str(downloaded))
    return tmp_path


def test_install_and_uninstall(home):
    assert not integration.is_installed()

    target = integration.install()
    assert target == home / "Applications" / "OpenFreebuds.AppImage"
    assert target.read_bytes() == b"appimage"
    assert os.stat(target).st_mode & stat.S_IXUSR

    entry = (home / ".local/share/applications/pw.mmk.OpenFreebuds.desktop").read_text()
    assert f'Exec="{target}"\n' in entry
    assert (home / ".local/share/icons/hicolor/256x256/apps/pw.mmk.OpenFreebuds.png").is_file()

    # Still running from Downloads
    assert not integration.is_installed()
    os.environ["APPIMAGE"] = str(target)
    assert integration.is_installed()

    integration.uninstall()
    assert not target.exists()
    assert not integration.desktop_entry_path().exists()
    assert not integration.icon_path().exists()
