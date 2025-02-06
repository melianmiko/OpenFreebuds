# Settings
set unstable
set windows-shell := ["powershell.exe", "-c"]
set script-interpreter := ["python"]

# Misc
version := `python -c "import tomllib
try:
    print(tomllib.load(open('pyproject.toml', 'rb'))['tool']['poetry']['version'])
except Exception:
    print('0.0')
"`
dest_dir := env("DESTDIR", "/usr")
flatpak_dir := env("FLATPAKBUILDDIR", '.')
python_lib := env("PYTHONLIBDIR", `python -c 'import site; print(site.getsitepackages()[0])'`)
python_venv := env("VIRTUAL_ENV", "")

# Tools
lrelease_fn := if os_family() == "windows" { \
    "lrelease.exe"
} else if path_exists("/usr/lib64/qt6/bin/lrelease") == "true" {
    "/usr/lib64/qt6/bin/lrelease"
} else if path_exists("/usr/lib/qt6/bin/lrelease") == "true" {
    "/usr/lib/qt6/bin/lrelease"
} else {
    "lrelease"
}
poetry_fn := if os_family() == "windows" { "poetry.exe" } else { "poetry" }
python_fn := if os_family() == "windows" { "py.exe" } else { "python" }
pip_fn := if os_family() == "windows" { "pip.exe" } else { "pip" }

# Tools location
python := require(python_fn)
lrelease := which(lrelease_fn)
pip := which(pip_fn)
poetry := which(poetry_fn)

# ------------------------------------------------
# Shortcuts, external scripts and tools
# ------------------------------------------------

# List available actions
@default:
    just -l

# Start Qt version without instalation
start: build
    poetry run openfreebuds_qt -vcs

# Start command shell without instalation
start_cmd:
    poetry run openfreebuds_cmd

# Start PyTest
test:
    poetry run pytest

# Prepare project environment (all build dependencies should exist at this time)
prepare:
    mkdir -p ./dist
    poetry install

# Bump application version
[positional-arguments]
bump_version code:
    python ./scripts/bump_version.py {{code}}

# Bump application version to git commit identifier
bump_version_git:
    python ./scripts/bump_version.py git


# ------------------------------------------------
# Dependencies
# ------------------------------------------------

# Install build dependencies for Debian\Ubuntu
[linux]
dependencies_debian:
    # TODO: Move inside Justfile
    sudo bash ./scripts/install_dpkg_dependencies.sh


# ------------------------------------------------
# Sources build
# ------------------------------------------------

# Compile Qt Desinger layout files
build_qt_designer:
    poetry run pyuic6 ./openfreebuds_qt/designer/

# Compile Qt Linguist translation files
[script]
build_qt_translations:
    import subprocess
    from pathlib import Path
    files_to_compile = []
    command = [r"{{lrelease}}"]
    for translation in Path("openfreebuds_qt/assets/i18n").iterdir():
        if translation.name.endswith(".ts"):
            command.append(str(translation))
    print("{{BOLD}}" + ' '.join(command) + "{{NORMAL}}")
    subprocess.run(command)

# Build everything
build: build_qt_designer build_qt_translations
    poetry build


# ------------------------------------------------
# Automated install
# ------------------------------------------------

# Check Linux instalation restrictions
[linux,script]
install_check:
    import os
    if "{{python_venv}}" != "" and os.environ.get("PYTHONLIBDIR", "") == "":
        print("Install isn't possible in venv")
        raise SystemExit(1)
    if "{{pip}}" == "":
        print("pip executable not found")
        raise SystemExit(1)

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


# ------------------------------------------------
# Flatpak-related
# ------------------------------------------------

# (Internal) Install OpenFreebuds inside Flatpak
[linux]
internal_flatpakinstall:
    # Unify release name (version constant won't work inside Flatpak)
    mkdir -p ./dist
    find ./dist -name '*.whl' -type f | head -1 | \
        xargs -I {} cp {} ./dist/openfreebuds-0.0-py3-none-any.whl
    # Install to /app
    touch /app/is_container
    DESTDIR=/app PYTHONLIBDIR=/app/lib/python3.11/site-packages just install

# Install OpenFreebuds as Flatpak package
[linux]
install_flatpak:
    cd scripts/build_flatpak \
        && mkdir -p {{flatpak_dir}} \
        && flatpak run org.flatpak.Builder \
            --force-clean --user \
            --install-deps-from=flathub \
            --repo={{flatpak_dir}}/repo \
            --state-dir={{flatpak_dir}}/state \
            --install {{flatpak_dir}}/builddir \
        pw.mmk.OpenFreebuds.yml

# Build Flatpak package file
[linux]
pkg_flatpak: install_flatpak
    mkdir -p dist/flatpak
    cd scripts/build_flatpak && flatpak build-bundle \
        {{flatpak_dir}}/repo \
        ../../dist/flatpak/openfreebuds_{{version}}.flatapk \
        pw.mmk.OpenFreebuds


# ------------------------------------------------
# Linux native packaging
# ------------------------------------------------

# Build Debian binary package
[linux]
pkg_debian:
    mkdir -p dist/debian
    dpkg-buildpackage -b
    cp ../openfreebuds_*.deb ./dist


# Build Debian source and binary package (use with causion, may remove files in parent folder)
[linux]
pkg_debian_full:
    mkdir -p dist/debian
    # Remove old build artifacts
    bash -c 'rm -f ../openfreebuds_*.{deb,changes,buildinfo,dsc} dist/debian/*'
    # Build and move to ./dist/debian
    dpkg-buildpackage -b
    cp ../openfreebuds_* ./dist/debian/


# ------------------------------------------------
# Windows packaging
# ------------------------------------------------

# Prepare ./dist/ for win32 installer build
[windows]
pkg_win32_bundle:
    cd ./scripts/build_win32; poetry run pyinstaller openfreebuds.spec

# Make windows installer
[windows]
pkg_win32_installer: pkg_win32_bundle
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts/build_win32; & "C:\Program Files (x86)\NSIS\Bin\makensis.exe" openfreebuds.nsi
    mv ./scripts/build_win32/dist/openfreebuds.install.exe ./dist/openfreebuds_{{version}}_win32.exe

# Make windows portable executable
[windows]
pkg_win32_portable:
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts/build_win32; & poetry run pyinstaller openfreebuds_portable.spec
    mv ./scripts/build_win32/dist/openfreebuds_portable.exe ./dist/openfreebuds_{{version}}_win32_portable.exe

# Make windows portable & installer
[windows]
pkg_win32: pkg_win32_installer pkg_win32_portable


# ------------------------------------------------
# Utils
# ------------------------------------------------

# Sync Qt Linguist translation files
[script]
sync_qt_translations:
    import subprocess
    from pathlib import Path
    for ts_file in Path("./openfreebuds_qt/assets/i18n").iterdir():
        if not ts_file.name.endswith(".ts"):
            continue
        print(f"Sync {ts_file}")
        result = subprocess.run([r"{{poetry}}", "run", "pylupdate6",
                                 "--no-obsolete",
                                 "--exclude", "scripts",
                                 "--exclude", "debian",
                                 "--ts", ts_file, "."])
        if result.returncode != 0:
            print("-- pylupdate6 failed")
            raise SystemExit(1)

# Sync Python dependencies for Flatpak
[linux]
sync_flatpak:
    python ./scripts/bump_version.py flatpak_deps
