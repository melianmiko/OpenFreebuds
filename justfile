set unstable
set lists
set allow-duplicate-recipes

set windows-shell := ["powershell.exe", "-c"]
set script-interpreter := ["python"]

python := require(if os_family() == "windows" { "python.exe" } else { "python" })
pip := which(if os_family() == "windows" { "pip.exe" } else { "pip" })
pdm := which(if os_family() == "windows" { "pdm.exe" } else { "pdm" })

lrelease := which(if os_family() == "windows" && pdm { \
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
sources_dir := absolute_path('.')
flatpak_dir := absolute_path(env("FLATPAKBUILDDIR", './.flatpak'))

# Version auto-detect
version := `python -c "import tomllib
try:
    print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])
except Exception:
    print('0.0')
"`

# List available actions
@default:
    just -l

# Imports
import? 'scripts/build.just'
import? 'scripts/vagrant.just'
import? 'scripts/manage.just'

import? 'scripts/flatpak.just'
import? 'scripts/debian.just'
import? 'scripts/windows/justfile'
import? 'scripts/release.just'
import? 'scripts/ansible/justfile'

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

# Install OpenFreebuds
[group("linux"),linux]
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
[group("linux"),private,linux,script]
install_check:
    import os
    assert os.path.isfile("./dist/openfreebuds-{{version}}-py3-none-any.whl"), \
        "Prebuilt wheel not found, did you called `just build` before?"
    assert "{{python_venv}}" == "" or os.environ.get("PYTHONLIBDIR", "") != "", \
        "Leave virtualenv or set PYTHONLIBDIR to install"

# (Internal) Install OpenFreebuds inside Flatpak
[private,linux]
internal_flatpakinstall:
    # Unify release name (version constant won't work inside Flatpak)
    mkdir -p ./dist
    find ./dist -name '*.whl' -type f | head -1 | \
        xargs -I {} cp {} ./dist/openfreebuds-0.0-py3-none-any.whl
    # Install to /app
    touch /app/is_container
    DESTDIR=/app PYTHONLIBDIR=/app/lib/python3.13/site-packages just install
