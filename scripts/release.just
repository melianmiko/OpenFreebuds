import "windows/justfile"

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
    [ -f /usr/bin/wine-arm64 ] && [ -f build/enable_cc ] && just win32_arm64 win32
