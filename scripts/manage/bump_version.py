import subprocess
import sys
import yaml
from datetime import date
from pathlib import Path

BASE_CHANGELOG_URL = "https://github.com/melianmiko/OpenFreebuds/blob/main/docs/CHANGELOG.md"
PROJECT_ROOT = Path(__file__).parents[2]

if len(sys.argv) < 2:
    print("Usage: ./bump_version.py [<version>|git]")
    raise SystemExit(1)

NEW_VERSION = sys.argv[1]
if NEW_VERSION == "git":
    NEW_VERSION = f"0.99.git.{subprocess.getoutput('git rev-parse HEAD')}"

with open(PROJECT_ROOT / "docs/changelog.yml", "r") as changelog_file:
    RELEASE_LIST = list(yaml.load(changelog_file, Loader=yaml.Loader))
    RELEASE_INFO = RELEASE_LIST[0]

NEW_VERSION_SHORT = ".".join(NEW_VERSION.replace("git", '99').split(".")[0:3])


def write_file(path: Path | str, new_data: list[str], win32_le: bool = False):
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
def bump_nfpm(line: str):
    """
    Replaces version in nfpm.yaml
    """
    if line.startswith("version: "):
        return f"version: \"{NEW_VERSION_SHORT}\""
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
    export_data = subprocess.getoutput("pdm export --format=requirements --without-hashes --with no_flatpak")
    libraries = []
    for line in export_data.replace("\r", "").splitlines():
        if line.startswith("#"):
            continue
        libraries.append(f"  '{line}',")

    write_file(path, [
        f"VERSION = '{NEW_VERSION}'",
        "LIBRARIES = [",
        *libraries,
        "]",
        ""
    ])


@file_mutator
def bump_metainfo(line: str):
    if not line.strip().startswith('<releases>'):
        return line
    non_nerd_changelog = 'Not provided'
    if 'title' in RELEASE_INFO:
        non_nerd_changelog = RELEASE_INFO['title']
    new_data = [
        line,
        f'    <release version="{NEW_VERSION}" date="{date.today()}">',
        f'      <url type="details">{BASE_CHANGELOG_URL}#v{NEW_VERSION}</url>',
        f'      <description>',
        f'        <p>{non_nerd_changelog}</p>',
        f'      </description>',
        f'    </release>',
    ]

    return "\n".join(new_data)


def main():
    if NEW_VERSION[0] == "v":
        print("Version shouldn't start with v")
        raise SystemExit(1)

    if RELEASE_INFO["semver"] != NEW_VERSION and "git" not in NEW_VERSION:
        raise KeyError(f"Changelog for {NEW_VERSION} not provided")

    # Launch everything
    bump_pyproject(str(PROJECT_ROOT / "pyproject.toml"))
    bump_nfpm(str(PROJECT_ROOT / "scripts/linux/nfpm.yaml"))
    bump_nsis(str(PROJECT_ROOT / "scripts/windows/openfreebuds.nsi"))
    bump_metainfo(str(PROJECT_ROOT / "openfreebuds_qt/assets/pw.mmk.OpenFreebuds.metainfo.xml"))
    create_version_info(PROJECT_ROOT / "openfreebuds_qt/version_info.py")

    print('-- Done')


if __name__ == "__main__":
    main()
