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
lrelease := which(lrelease_fn)
python := require(python_fn)
pip := require(pip_fn)
poetry := which(poetry_fn)

[linux]
default: build

env:
    @echo DESTDIR={{dest_dir}}
    @echo PYTHONLIBDIR={{python_lib}}
    @echo LRELEASE_EXECUTABLE={{lrelease}}
    @echo POETRY_EXECUTABLE={{poetry}}
    @echo PYTHON_EXECUTABLE={{python}}

test:
    poetry run pytest

# Bump application version
[positional-arguments]
bump_version code:
    python ./scripts/bump_version.py {{code}}

# Bump application version to git commit identifier
bump_version_git:
    python ./scripts/bump_version.py git

# Sync Python dependencies for Flatpak
[linux]
sync_flatpak:
    python ./scripts/bump_version.py flatpak_deps

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

# Compile Qt Desinger layout files (old pyuic method)
[script]
build_qt_designer_legacy:
    import subprocess
    from pathlib import Path
    for ui_file in Path("openfreebuds_qt/designer").iterdir():
        if not ui_file.name.endswith(".ui"):
            continue
        print(f"Compile {ui_file}")
        result = subprocess.run([r"{{poetry}}", "run", "pyuic6",
                                 "-o", str(ui_file).replace(".ui", ".py"),
                                 ui_file])
        if result.returncode != 0:
            print("-- PyUiC failed")
            raise SystemExit(1)

# Compile Python wheel
build: build_qt_designer build_qt_translations
    poetry build
    cp ./dist/openfreebuds-{{version}}-py3-none-any.whl ./dist/openfreebuds-0.0-py3-none-any.whl

# Check Linux instalation restrictions
[linux,script]
install_check:
    import os
    if "{{python_venv}}" != "" and os.environ.get("PYTHONLIBDIR", "") == "":
        print("Install isn't possible in venv")
        raise SystemExit(1)

# Install Python wheek to PYTHON_LIB
[linux]
install_wheel: install_check
    mkdir -p "{{python_lib}}"
    {{pip}} install -q --upgrade --no-dependencies --target "{{python_lib}}" \
        "./dist/openfreebuds-{{version}}-py3-none-any.whl"

# Install OpenFreebuds
[linux]
install: env install_wheel
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

# Start without instalation
start: build
    poetry run openfreebuds_qt -vcs

# Start command shell without instalation
cmd:
    poetry run openfreebuds_cmd

# Build Flatpak package
[linux]
build_flatpak: build
    cd scripts/build_flatpak && flatpak run org.flatpak.Builder \
        --force-clean --user --install-deps-from=flathub --repo=repo --install builddir \
        pw.mmk.OpenFreebuds.yml

# Build Flatpak bundle
[linux]
make_flatpak: build_flatpak
    flatpak build-bundle \
        scripts/build_flatpak/repo \
        dist/openfreebuds_{{version}}.flatapk \
        pw.mmk.OpenFreebuds

# Build Debian packages
[linux]
make_debian: env
    sudo bash ./scripts/install_dpkg_dependencies.sh
    dpkg-buildpackage -S
    dpkg-buildpackage -b
    cp ../openfreebuds_*.deb ./dist

# Prepare ./dist/ for win32 installer build
[windows]
make_win32_bundle: build
    cd ./scripts/build_win32; poetry run pyinstaller openfreebuds.spec

# Make windows installer
[windows]
make_win32_installer: make_win32_bundle
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts/build_win32; & "C:\Program Files (x86)\NSIS\Bin\makensis.exe" openfreebuds.nsi
    mv ./scripts/build_win32/dist/openfreebuds.install.exe ./dist/openfreebuds_{{version}}_win32.exe

# Make windows portable executable
[windows]
make_win32_portable: build
    New-Item -ItemType Directory -Force -Path ./dist
    cd ./scripts/build_win32; & poetry run pyinstaller openfreebuds_portable.spec
    mv ./scripts/build_win32/dist/openfreebuds_portable.exe ./dist/openfreebuds_{{version}}_win32_portable.exe

# Make windows portable & installer
[windows]
make_win32: make_win32_installer make_win32_portable

# GitHub Actions: Auto-build (linux)
[linux]
gh_autobuild:
    just bump_version_git
    just make_debian

# GitHub Actions: Auto-build (windows)
[windows]
gh_autobuild:
    just bump_version_git
    just make_win32_portable
