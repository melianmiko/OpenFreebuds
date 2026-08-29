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

# Create wine prefix for windows corss-compilation
[private,linux,script("bash")]
setup_wine_env:
    set -euo pipefail

    if [ -f "{{ wineprefix }}/ready" ]
    then
        exit 0
    fi
    
    rm -rf "{{ wineprefix }}"

    echo "[--] Creating wine prefix"
    mkdir -p `basename {{ wineprefix }}`
    {{ wine }} cmd.exe /c "rem ready"
    mkdir -p "{{ winetools }}"
    cd "{{ winetools }}"
    WINARCH=`just get_winearch`
    echo "     Created, architecture is $WINARCH"

    echo "[--] Downloading Python..."
    curl -sL -o python.zip https://www.python.org/ftp/python/{{ w32_python_ver }}/python-{{ w32_python_ver }}-$WINARCH.zip
    unzip python.zip

    echo "[--] Downloading pip..."
    {{ wine }} cmd.exe /c "mkdir %APPDATA%\\Python\\Scripts" || true
    curl -s -o get-pip.py https://bootstrap.pypa.io/get-pip.py
    {{ wine }} python.exe get-pip.py
    {{ wine }} pip -h > test.log

    echo "[--] Installing PDM..."
    {{ wine }} pip install pdm

    if [[ "$WINARCH" == "amd64" ]]
    then
        echo "[--] Installing UPX..."
        curl -sL "https://github.com/upx/upx/releases/download/v5.2.0/upx-5.2.0-win64.zip" |
            busybox unzip - > last.log || true
        mv upx-*/* .
    fi

     echo "[--] Prepare app dependencies"...
     cd "{{ sources_dir }}"
     {{ wine }} pdm install

     touch "{{ wineprefix }}/ready"

# Allow cross-compiling for Windows using wine
[group("prepare"),script("bash")]
enable_cc:
    if [ ! -f "/usr/bin/wine" ] && [ ! -f "/usr/bin/wine-arm64" ]
    then
        echo "[!!] ERROR: wine not found, cross-compilation will fail"
        exit 1
    fi
    mkdir -p {{ build_dir }}
    touch {{ build_dir }}/enable_cc

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
    [ -f /usr/bin/wine-arm64 ] && [ -f build/enable_cc ] && just win32-arm64 setup_wine_env
    pdm install
