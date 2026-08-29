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

# Build Qt staff and Python wheel
build: qt_i18n
    pdm run pyuic6 ./openfreebuds_qt/designer/
    pdm build --no-clean

# Compile Qt Linguist translation files
[script,private]
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

# Cleanup project directory
[group("release"),script]
clean:
    import shutil
    for name in ["build", "dist", ".pdm-build"]:
        shutil.rmtree(f"{{ sources_dir }}/{name}")

# Build release binaries (windows)
[group("release"),windows]
release: win32_installer win32_portable

# Build all possible release binaries (linux)
[group("release"),linux,script("bash")]
release:
    set -euxo pipefail
    just debian fedora
    [ -f /usr/bin/flatpak ] && just flatpak
    [ -f /usr/bin/wine ] && [ -f build/enable_cc ] && just win32
    [ -f /usr/bin/wine-arm64 ] && [ -f build/enable_cc ] && just win32-arm64 win32
