import "./vars.just"

export WINEPATH := "C:\\openfreebuds_buildtools;C:\\openfreebuds_buildtools\\Scripts"
export WINEDEBUG := '-all'
export WINEARCH := env("WINEARCH", "win64")

wineprefix := env("WINEPREFIX", sources_dir + "/build/wineprefix")
wine := "WINEPREFIX=\"" + wineprefix + "\" " + env("WINE", "/usr/bin/wine")
winetools := wineprefix + '/drive_c/openfreebuds_buildtools'
winesystem32 := wineprefix + "/drive_c/windows/system32"
w32_python_ver := "3.14.7"

[private,linux,script("bash")]
get_winearch:
    WINARCH="amd64"
    ({{wine}} systeminfo | grep "ARM64-based PC" > /dev/null) && WINARCH="arm64"
    echo "$WINARCH"

[private,linux,script("bash")]
get_winearch2:
    WINARCH="x86_64"
    ({{wine}} systeminfo | grep "ARM64-based PC" > /dev/null) && WINARCH="aarch64"
    echo "$WINARCH"

[private,linux]
winecmd:
    {{ wine }} cmd.exe

# Make windows installer
[group("os_windows"),linux]
win32_installer: build
    # Do 'just enable_cc prepare' first!
    [ ! -f build/enable_cc ] && exit 1 || true
    mkdir -p ./dist {{ nsis_builddir }}
    cd ./scripts/windows && {{ wine }} {{pyinstaller}} -y openfreebuds.spec
    cd ./scripts/windows && makensis openfreebuds.nsi
    mv {{ nsis_builddir }}/openfreebuds.install.exe ./dist/openfreebuds_{{version}}_`just get_winearch2`_windows.exe

# Make windows installer
[group("os_windows"),linux]
win32_portable: build
    # Do 'just enable_cc prepare' first!
    [ ! -f build/enable_cc ] && exit 1 || true
    mkdir -p ./dist
    cd ./scripts/windows && {{ wine }} {{pyinstaller}} -y openfreebuds_portable.spec
    mv {{ pyinstaller_distdir }}/openfreebuds_portable.exe ./dist/openfreebuds_{{version}}_`just get_winearch2`_windows_portable.exe

# Wrapper for wine-arm64 environment
[group("os_windows"),linux,private]
win32_arm64 action:
    WINEARCH=wow64 \
        WINEPREFIX="{{ sources_dir }}/build/wineprefix-arm64" \
        WINE=/usr/bin/wine-arm64 \
        just {{ action }}

# Add ICU libraries to wineprefix
[private,linux]
setup_wine_env_icu:
    mkdir -p "{{ winesystem32 }}"
    mkdir -p "{{ build_dir }}/wineprefix/temp_icudl"
    curl -sLo "{{ build_dir }}/wineprefix/temp_icudl/dl.zip" {{ icuuc_nuget_url }}
    cd "{{ build_dir }}/wineprefix/temp_icudl" && unzip dl.zip
    find "{{ build_dir }}/wineprefix/temp_icudl" \
        -name '*.dll' \
        -exec mv {} "{{ winesystem32 }}/" \;
    cp "{{ winesystem32 }}/icuuc72.dll" "{{ winesystem32 }}/icuuc.dll"

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

    echo "[--] Prepare icuuc.dll's..."
    just setup_wine_env_icu

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
     {{ wine }} pdm config venv.in_project false
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
