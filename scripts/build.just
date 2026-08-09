# Build everything
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

# Prepare project environment (linux)
[group("release"),linux,script("/usr/bin/bash")]
prepare:
    set -euxo pipefail
    [ -f /usr/bin/apt ] && just deps_debian
    [ -f /usr/bin/dnf ] && just deps_fedora
    [ -f /usr/bin/flatpak ] && just deps_flatpak
    pdm install

# Prepare project environment (windows)
[group("release"),windows]
prepare: deps_winget
    pdm install

# Cleanup project directory
[group("release"),linux]
clean:
    rm -rf dist scripts/dist scripts/build .pdm-build

# Cleanup project directory
[group("release"),windows]
clean:
    -rmdir build /s /q
    -rmdir dist /s /q
    -rmdir .pdm-build /s /q

# Build all release binaries (linux)
[group("release"),linux]
release: clean
    just debian fedora
    just flatpak

# Build release binaries (windows)
[group("release"),windows]
release: clean win32_installer win32_portable
