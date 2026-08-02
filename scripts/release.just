# Prepare project environment (linux)
[linux,script("/usr/bin/bash")]
prepare:
    set -euxo pipefail
    [ -f /usr/bin/apt ] && just deps_debian
    [ -f /usr/bin/flatpak ] && just deps_flatpak
    pdm install

# Prepare project environment (windows)
[windows]
prepare: deps_winget
    pdm install

# Cleanup project directory
[linux]
clean:
    rm -rf dist scripts/dist scripts/build .pdm-build

# Cleanup project directory
[windows]
clean:
    -rmdir build dist .pdm-build /s /q

# Build release binaries (linux)
[linux,script("/usr/bin/bash")]
release: clean
    set -euxo pipefail
    [ -f /usr/bin/apt ] && just debian_full
    [ -f /usr/bin/flatpak ] && just flatpak

# Build release binaries (windows)
[windows]
release: clean win32
