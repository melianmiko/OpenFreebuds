set unstable

set windows-shell := ["powershell.exe", "-c"]
set script-interpreter := ["python"]

# Tools
python := require(if os_family() == "windows" { "python.exe" } else { "python" })
pip := which(if os_family() == "windows" { "pip.exe" } else { "pip" })
pdm := which(if os_family() == "windows" { "pdm.exe" } else { "pdm" })

lrelease := which(if os_family() == "windows" { \
    `pdm run python -c "
import os
try:
    import PySide6
    print(os.path.dirname(PySide6.__file__))
except ModuleNotFoundError:
    print('.')
"` / 'lrelease.exe'
} else if path_exists("/usr/lib64/qt6/bin/lrelease") == "true" {
    "/usr/lib64/qt6/bin/lrelease"
} else if path_exists("/usr/lib/qt6/bin/lrelease") == "true" {
    "/usr/lib/qt6/bin/lrelease"
} else {
    "lrelease"
})

# Env
dest_dir := env("DESTDIR", "/usr")
python_lib := env("PYTHONLIBDIR", `python -c 'import site; print(site.getsitepackages()[0])'`)
python_venv := env("VIRTUAL_ENV", "")
flatpak_dir := absolute_path(env("FLATPAKBUILDDIR", './.flatpak'))

# Version auto-detect
version := `python -c "import tomllib
try:
    print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])
except Exception:
    print('0.0')
"`

# ------------------------------------------------
# Shortcuts
# ------------------------------------------------

# List available actions
@default:
    just -l

# Start Qt version without instalation
start:
    just build
    pdm run openfreebuds_qt -vcs

# Start command shell without instalation
start_cmd:
    pdm run openfreebuds_cmd

# Start PyTest
test:
    pdm run pytest

# Prepare project environment (all build dependencies should exist at this time)
prepare:
    pdm install

clean:
    rm -rf dist scripts/dist scripts/build .pdm-build

vg_destroy:
    vagrant destroy -f

vg_all:
    vagrant halt -f
    vagrant up --parallel

    # Grab files from windows due to rsync back isn't implemented
    vagrant ssh-config > .vagrant/sshconfig
    scp -F .vagrant/sshconfig windows:/openfreebuds/dist/*.exe dist


# ------------------------------------------------
# Project auto-install staff
# ------------------------------------------------

# Install OpenFreebuds
[linux]
install: install_check
    mkdir -p "{{python_lib}}"
    {{pip}} install -q --upgrade --no-dependencies --target "{{python_lib}}" \
        "./dist/openfreebuds-{{version}}-py3-none-any.whl"
    mkdir -p "{{dest_dir}}/bin" \
             "{{dest_dir}}/share/applications" \
             "{{dest_dir}}/share/metainfo" \
             "{{dest_dir}}/share/icons/hicolor/256x256/apps"
    # Install binaries
    cp "{{python_lib}}/bin/openfreebuds_qt" "{{dest_dir}}/bin/openfreebuds_qt"
    cp "{{python_lib}}/bin/openfreebuds_cmd" "{{dest_dir}}/bin/openfreebuds_cmd"
    ln -sf ./openfreebuds_qt "{{dest_dir}}/bin/openfreebuds"
    # Install desktop integration
    cp "{{python_lib}}/openfreebuds_qt/assets/pw.mmk.OpenFreebuds.desktop" \
       "{{dest_dir}}/share/applications"
    cp "{{python_lib}}/openfreebuds_qt/assets/pw.mmk.OpenFreebuds.metainfo.xml" \
       "{{dest_dir}}/share/metainfo"
    cp "{{python_lib}}/openfreebuds_qt/assets/pw.mmk.OpenFreebuds.png" \
       "{{dest_dir}}/share/icons/hicolor/256x256/apps"

# Check Linux instalation restrictions
[private,linux,script]
install_check:
    import os
    assert os.path.isfile("./dist/openfreebuds-{{version}}-py3-none-any.whl"), \
        "Prebuilt wheel not found, did you called `just build` before?"
    assert "{{python_venv}}" == "" or os.environ.get("PYTHONLIBDIR", "") != "", \
        "Leave virtualenv or set PYTHONLIBDIR to install"



# ------------------------------------------------
# Project build staff
# ------------------------------------------------

# Build everything
build: qt_i18n
    pdm run pyuic6 ./openfreebuds_qt/designer/
    pdm build --no-clean

# Compile Qt Linguist translation files
[script]
qt_i18n:
    import subprocess
    from pathlib import Path
    files_to_compile = []
    command = [r"{{lrelease}}"]
    for translation in Path("openfreebuds_qt/assets/i18n").iterdir():
        if translation.name.endswith(".ts"):
            command.append(str(translation))
    print("{{BOLD}}" + ' '.join(command) + "{{NORMAL}}")
    subprocess.run(command)

# Check that all build requirements are resolved
[private,script]
build_check:
    assert "{{pdm}}" != "", "PDM not found"
    assert "{{lrelease}}" != "", "Qt lrelease not found"



# ------------------------------------------------
# Flatpak linux packaging
# ------------------------------------------------

# Install dependencies for Flatpak build
[linux]
flatpak_deps:
    flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    flatpak install --user org.flatpak.Builder

# Install OpenFreebuds as Flatpak package
[linux]
flatpak_install:
    just build || true
    mkdir -p {{flatpak_dir}}
    echo "*" > {{flatpak_dir}}/.gitignore
    flatpak run org.flatpak.Builder \
            --force-clean --user --install \
            --install-deps-from=flathub \
            --repo={{flatpak_dir}}/repo \
            --state-dir={{flatpak_dir}}/state \
        {{flatpak_dir}}/builddir \
        ./scripts/pw.mmk.OpenFreebuds.yml

# Build Flatpak package file
[linux]
flatpak: flatpak_install
    mkdir -p dist/flatpak
    flatpak build-bundle \
        {{flatpak_dir}}/repo \
        ./dist/flatpak/openfreebuds_{{version}}.flatapk \
        pw.mmk.OpenFreebuds

# Sync Python dependencies for Flatpak
[linux]
sync_flatpak:
    mkdir -p ./.flatpak
    python -m venv ./.flatpak/venv
    ./.flatpak/venv/bin/pip install req2flatpak==0.3.1
    # TODO: Move inside Justfile
    ./.flatpak/venv/bin/python ./scripts/bump_version.py flatpak_deps
    sed -i \
        's/--verbose --exists-action=i/--verbose --no-deps --exists-action=i/g' \
        scripts/python3-requirements.json

# (Internal) Install OpenFreebuds inside Flatpak
[private,linux]
internal_flatpakinstall:
    # Unify release name (version constant won't work inside Flatpak)
    mkdir -p ./dist
    find ./dist -name '*.whl' -type f | head -1 | \
        xargs -I {} cp {} ./dist/openfreebuds-0.0-py3-none-any.whl
    # Install to /app
    touch /app/is_container
    DESTDIR=/app PYTHONLIBDIR=/app/lib/python3.12/site-packages just install



# ------------------------------------------------
# Debian staff
# ------------------------------------------------

# Build Debian binary package
[linux]
debian:
    mkdir -p dist/debian
    dpkg-buildpackage -b
    cp ../openfreebuds_*.deb ./dist

# Build Debian source and binary package (use with causion, may remove files in parent folder)
[linux]
debian_full:
    mkdir -p dist/debian
    # Remove old build artifacts
    bash -c 'rm -f ../openfreebuds_*.{deb,changes,buildinfo,dsc} dist/debian/*'
    # Build and move to ./dist/debian
    dpkg-buildpackage -b
    cp ../openfreebuds_* ./dist/debian/

# Install build dependencies for Debian\Ubuntu
[linux]
deps_debian:
    sudo apt install -y --no-install-recommends \
        build-essential \
        debhelper-compat \
        python3-dbus-next \
        python3-pyqt6 \
        python3-pil \
        python3-qasync \
        python3-aiohttp \
        python3-psutil \
        python3-pip \
        qt6-l10n-tools \
        fakeroot \
        make \
        git



# ------------------------------------------------
# Windows staff
# ------------------------------------------------

# Make windows portable & installer
[windows]
win32: win32_installer win32_portable

# Make windows installer
[windows]
win32_installer: win32_bundle
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts; & "C:\Program Files (x86)\NSIS\Bin\makensis.exe" openfreebuds.nsi
    mv -Force ./scripts/dist/openfreebuds.install.exe ./dist/openfreebuds_{{version}}_win32.exe

# Make windows portable executable
[windows]
win32_portable:
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts; & pdm run pyinstaller -y openfreebuds_portable.spec
    mv -Force ./scripts/dist/openfreebuds_portable.exe ./dist/openfreebuds_{{version}}_win32_portable.exe

# Prepare ./dist/ for win32 installer build
[windows,private]
win32_bundle:
    cd ./scripts; pdm run pyinstaller -y openfreebuds.spec



# ------------------------------------------------
# Project maintainer staff
# ------------------------------------------------

# Bump application version
[positional-arguments]
bump_version code:
    python ./scripts/bump_version.py {{code}}

# Bump application version to git commit identifier
bump_version_git:
    python ./scripts/bump_version.py git

# Sync Qt Linguist translation files
[script]
sync_qt_translations:
    import subprocess
    from pathlib import Path
    for ts_file in Path("./openfreebuds_qt/assets/i18n").iterdir():
        if not ts_file.name.endswith(".ts"):
            continue
        print(f"Sync {ts_file}")
        result = subprocess.run([r"{{pdm}}", "run", "pylupdate6",
                                 "--no-obsolete",
                                 "--exclude", "scripts",
                                 "--exclude", "debian",
                                 "--ts", ts_file, "."])
        if result.returncode != 0:
            print("-- pylupdate6 failed")
            raise SystemExit(1)
