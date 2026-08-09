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
flatpak_dir := absolute_path(env("FLATPAKBUILDDIR", './.flatpak'))
dest_dir := env("DESTDIR", "/usr/local")

sources_dir := absolute_path('.')
build_dir := sources_dir + "/build"
python_venv := env("VIRTUAL_ENV", "")

python_path := env("PYTHONLIBPATH", `python -c "
import site
try:
    v = site.getsitepackages()[0]
    print(v[11:] if v.startswith('/usr/local/') else v)
except SyntaxError:
    # Windows moment
    pass
"`)

# Version auto-detect
version := `python -c "import tomllib
try:
    print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])
except Exception:
    print('0.0')
"`

# List available actions
[private]
@default:
    just -l

# Imports
import? 'scripts/build.just'
import? 'scripts/manage.just'
import? 'scripts/linux.just'
import? 'scripts/flatpak/justfile'
import? 'scripts/windows/justfile'
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
    mkdir -p "{{dest_dir}}/{{python_path}}"
    {{pip}} install -q --upgrade --no-dependencies --target "{{dest_dir}}/{{python_path}}" \
        "./dist/openfreebuds-{{version}}-py3-none-any.whl"
    mkdir -p "{{dest_dir}}/bin" \
             "{{dest_dir}}/share/applications" \
             "{{dest_dir}}/share/metainfo" \
             "{{dest_dir}}/share/icons/hicolor/256x256/apps"
    # Install binaries
    cp "{{dest_dir}}/{{python_path}}/bin/openfreebuds_qt" "{{dest_dir}}/bin/openfreebuds_qt"
    cp "{{dest_dir}}/{{python_path}}/bin/openfreebuds_cmd" "{{dest_dir}}/bin/openfreebuds_cmd"
    # Install desktop integration
    cp "{{dest_dir}}/{{python_path}}/openfreebuds_qt/assets/pw.mmk.OpenFreebuds.desktop" \
       "{{dest_dir}}/share/applications"
    cp "{{dest_dir}}/{{python_path}}/openfreebuds_qt/assets/pw.mmk.OpenFreebuds.metainfo.xml" \
       "{{dest_dir}}/share/metainfo"
    cp "{{dest_dir}}/{{python_path}}/openfreebuds_qt/assets/pw.mmk.OpenFreebuds.png" \
       "{{dest_dir}}/share/icons/hicolor/256x256/apps"

# Check Linux instalation restrictions
[group("linux"),private,linux,script]
install_check:
    import os
    assert os.path.isfile("./dist/openfreebuds-{{version}}-py3-none-any.whl"), \
        "Prebuilt wheel not found, did you called `just build` before?"
    assert "{{python_venv}}" == "" or os.environ.get("PYTHONLIBPATH", "") != "", \
        "Leave virtualenv or set PYTHONLIBPATH to install"

# (Internal) Install OpenFreebuds inside Flatpak
[private,linux]
internal_flatpakinstall:
    # Unify release name (version constant won't work inside Flatpak)
    mkdir -p ./dist
    find ./dist -name '*.whl' -type f | head -1 | \
        xargs -I {} cp {} ./dist/openfreebuds-0.0-py3-none-any.whl
    # Install to /app
    touch /app/is_container
    DESTDIR=/app PYTHONLIBPATH=lib/python3.13/site-packages just install
