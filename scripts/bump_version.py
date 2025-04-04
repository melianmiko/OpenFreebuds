import json
import os
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

DEB_CODENAMES = "bookworm noble oracular"
DEVELOPER_SIGN = "MelianMiko <support@mmk.pw>"
DEBUG = False

URL_FLATPAK_PIP_GENERATOR = ("https://github.com/flatpak/flatpak-builder-tools/raw/refs/heads/master"
                             "/pip/flatpak-pip-generator")
BASE_CHANGELOG_URL = "https://github.com/melianmiko/OpenFreebuds/blob/main/CHANGELOG.md"

PROJECT_ROOT = Path(__file__).parents[1]
FLATPAK_PIP_GENERATOR_PATH = PROJECT_ROOT / ".flatpak/flatpak-pip-generator"

if len(sys.argv) < 2:
    print("Usage: ./bump_version.py [<version>|git|flatpak_deps]")
    raise SystemExit(1)

NEW_VERSION = sys.argv[1]
CHANGELOG = []
if NEW_VERSION == "git":
    NEW_VERSION = f"0.99.git.{subprocess.getoutput('git rev-parse HEAD')}"

NEW_VERSION_SHORT = ".".join(NEW_VERSION.replace("git", '99').split(".")[0:3])


def write_file(path: Path | str, new_data: list[str], win32_le: bool = False):
    if DEBUG:
        print(f"-- Override {path} with following content")
        print("\n".join(new_data))
        print("")
        return

    with open(path, "w") as f:
        line_ending = "\r\n" if win32_le else "\n"
        f.write(line_ending.join(new_data) + line_ending)
    print(f"-- Modified {path}")


def file_mutator(_func):
    def _inner(path: Path, win32_le: bool = False):
        with open(path) as f:
            data = f.read()

        new_data = []
        for file_line in data.splitlines():
            new_data.append(_func(file_line))

        write_file(path, new_data, win32_le)

    return _inner


# === Mutators


@file_mutator
def bump_pyproject(line: str):
    """
    Replaces version in pyproject.toml
    """
    if line.startswith("version ="):
        return f"version = \"{NEW_VERSION_SHORT}\""
    return line


@file_mutator
def bump_nsis(line: str):
    """
    Replaces version in NSIS config
    """
    if line.startswith("!define APP_VERSION"):
        return f"!define APP_VERSION \"{NEW_VERSION}\""
    return line


def create_version_info(path: Path):
    export_data = subprocess.getoutput("poetry export --without-hashes -n --with extras --with no_flatpak")
    libraries = []
    for line in export_data.replace("\r", "").splitlines():
        libraries.append(f"  '{line}',")

    write_file(path, [
        f"VERSION = '{NEW_VERSION}'",
        "LIBRARIES = [",
        *libraries,
        "]",
        ""
    ])


def bump_debian(path: Path):
    with open(path) as f:
        exiting_data = f.read()

    debian_changelog = [f"  {line}" for line in CHANGELOG]
    write_file(path, [
        f"openfreebuds ({NEW_VERSION}-1) {DEB_CODENAMES}; urgency=medium",
        f"",
        *debian_changelog,
        f"",
        f" -- {DEVELOPER_SIGN}  {subprocess.getoutput('date -R')}",
        f"",
        *exiting_data.splitlines()
    ])


@file_mutator
def bump_metainfo(line: str):
    if not line.strip().startswith('<releases>'):
        return line
    non_nerd_changelog = 'Not provided'
    if '' in CHANGELOG:
        non_nerd_changelog = CHANGELOG[:CHANGELOG.index('')]
    new_data = [
        line,
        f'    <release version="{NEW_VERSION}" date="{date.today()}">',
        f'      <url type="details">{BASE_CHANGELOG_URL}#v{NEW_VERSION}</url>',
        f'      <description>',
        f'        <p>{" ".join(" ".join(non_nerd_changelog).split(" "))}</p>',
        f'      </description>',
        f'    </release>',
    ]

    return "\n".join(new_data)


def create_flatpak_staff():
    if sys.platform == "win32":
        print("-- Skip Flatpak staff: win32 not supported")
        return

    # Set up tools
    (PROJECT_ROOT / ".flatpak").mkdir(exist_ok=True, parents=True)
    if not FLATPAK_PIP_GENERATOR_PATH.is_file():
        print(f"-- Downloading flatpak-pip-generator")
        urllib.request.urlretrieve(URL_FLATPAK_PIP_GENERATOR, FLATPAK_PIP_GENERATOR_PATH)
        os.chmod(FLATPAK_PIP_GENERATOR_PATH, 0o755)

    export_data = subprocess.getoutput("pdm export --without-hashes --without no_flatpak --without dev").splitlines()
    new_export_data = []
    for line in export_data:
        if 'sys_platform == "win32"' in line or 'sys_platform == "darwin"' in line:
            continue
        new_export_data.append(line)

    with open(PROJECT_ROOT / ".flatpak/requirements.txt", "w") as f:
        f.write("\n".join(new_export_data))

    print('-- Create python3-requirements.txt for flatpak, will trigger flatpak-pip-generator')
    subprocess.run(
        [FLATPAK_PIP_GENERATOR_PATH,
         '-r', './.flatpak/requirements.txt',
         '-o', './scripts/python3-requirements'],
        cwd=PROJECT_ROOT,
    )


def main():
    if NEW_VERSION[0] == "v":
        print("Version shouldn't start with v")
        raise SystemExit(1)

    # Read changelog
    with open(PROJECT_ROOT / "CHANGELOG.md", "r") as changelog_file:
        reach_section = False
        for changelog_line in changelog_file:
            if not reach_section:
                reach_section = changelog_line.startswith(f"# v{NEW_VERSION}")
                continue
            if changelog_line[0] == "#":
                break

            CHANGELOG.append(changelog_line.strip())

    if len(CHANGELOG) == 0:
        CHANGELOG.append("- Changelog not provided")

    # Launch everything
    bump_pyproject(str(PROJECT_ROOT / "pyproject.toml"))
    bump_nsis(str(PROJECT_ROOT / "scripts/openfreebuds.nsi"))
    bump_debian(PROJECT_ROOT / "debian/changelog")
    bump_metainfo(str(PROJECT_ROOT / "openfreebuds_qt/assets/pw.mmk.OpenFreebuds.metainfo.xml"))
    create_version_info(PROJECT_ROOT / "openfreebuds_qt/version_info.py")
    # create_flatpak_staff()

    # Create release.json
    # with open(PROJECT_ROOT / "release.json", "w") as f:
    #     f.write(json.dumps({
    #         "version": NEW_VERSION,
    #         "changelog": CHANGELOG,
    #     }, indent=2))
    # print(f'-- Created {PROJECT_ROOT / "release.json"}')

    print('-- Done')


if __name__ == "__main__":
    if NEW_VERSION == "flatpak_deps":
        # TODO: Move inside Justfile
        create_flatpak_staff()
    else:
        main()
