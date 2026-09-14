import "build.just"
import "windows/justfile"
import "linux/justfile"

winget_install := "winget install -e --no-upgrade --id"

# Install base project dependencies through WinGet
[group("prepare"),windows]
deps_winget:
    -{{ winget_install }} NSIS.NSIS
    -{{ winget_install }} UPX.UPX

# Download & unpack nfpm
[private,linux,script("bash")]
get_nfpm:
    set -euo pipefail
    if [ ! -f "{{ nfpm_local }}" ]
    then
        echo "[--] Downloading nfpm to {{ nfpm_local }}..."
        mkdir -p `dirname {{ nfpm_local }}`
        cd `dirname {{ nfpm_local }}`
        curl -sLo nfpm.tar https://github.com/goreleaser/nfpm/releases/download/v2.47.0/nfpm_2.47.0_Linux_{{ arch() }}.tar.gz
        tar xf nfpm.tar
        rm nfpm.tar
    fi

# Install build dependencies for Debian\Ubuntu
[group("prepare"),linux]
deps_debian:
    sudo apt install -y --no-install-recommends \
        python3-dbus-next \
        python3-pyqt6 \
        python3-pil \
        python3-aiohttp \
        python3-psutil \
        python3-yaml \
        python3-pip \
        python-is-python3 \
        curl \
        qt6-l10n-tools \
        git
    # Allow failure (safe for building)
    -sudo apt install -y --no-install-recommends \
        python3-qasync
    just get_nfpm

# Install win32 build dependencies for Debian\Ubuntu
[group("prepare"),linux]
deps_debian_cc:
    sudo dpkg --add-architecture i386
    sudo apt update
    sudo apt install -y \
        wine \
        win32:i386 \
        nsis \
        unzip

# Install build dependencies for Fedora
[group("prepare"),linux]
deps_fedora:
    sudo dnf install -y \
        python3-dbus-next \
        python3-pyqt6 \
        python3-pillow \
        python3-pillow-qt \
        python3-aiohttp \
        python3-psutil \
        python3-yaml \
        python3-pip \
        qt6-linguist \
        curl \
        git
    just get_nfpm

# Prepare development environment (windows)
[group("prepare"),windows]
prepare: deps_winget
    pdm install

# Prepare development environment (linux)
[group("prepare"),linux,script("/usr/bin/bash")]
prepare:
    set -euxo pipefail
    [ -f /usr/bin/apt ] && just deps_debian
    [ -f /usr/bin/dnf ] && just deps_fedora
    [ -f /usr/bin/flatpak ] && just deps_flatpak
    [ -f /usr/bin/wine ] && [ -f build/enable_cc ] && just setup_wine_env
    [ -f /usr/bin/wine-arm64 ] && [ -f build/enable_cc ] && just win32_arm64 setup_wine_env
    pdm install
