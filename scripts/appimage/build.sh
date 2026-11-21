#!/usr/bin/env bash
# Build an x86_64 AppImage from the wheel in ./dist.
#
# Needs: curl, sha256sum, tar, git; zsyncmake for the .zsync update file.
# Environment:
#   OFB_APPIMAGE_REPO   GitHub "owner/repo" whose releases provide updates
#                       (default: $GITHUB_REPOSITORY, then melianmiko/OpenFreebuds)
#   OFB_REQUIREMENTS    pinned requirements file (default: pdm export)
set -euo pipefail

PYTHON_RELEASE="20261013"
PYTHON_VERSION="3.14.8"
PYTHON_SHA256="d8faa1b588506b9e3e5a3f57807bb056d534a1641a6b10d15b6ea3f0b413b960"
APPIMAGETOOL_VERSION="1.9.1"
APPIMAGETOOL_SHA256="ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/build/appimage"
TOOLS="$BUILD/tools"
APPDIR="$BUILD/AppDir"
DIST="$ROOT/dist"
REPO="${OFB_APPIMAGE_REPO:-${GITHUB_REPOSITORY:-melianmiko/OpenFreebuds}}"
ARCH="x86_64"

fetch() {
    local url="$1" out="$2" sha="$3"
    if [ ! -f "$out" ] || ! echo "$sha  $out" | sha256sum -c --quiet - 2>/dev/null; then
        echo "-- Download $url"
        curl -fsSL -o "$out" "$url"
        echo "$sha  $out" | sha256sum -c --quiet -
    fi
}

mkdir -p "$TOOLS" "$DIST"

WHEEL="$(find "$DIST" -maxdepth 1 -name 'openfreebuds-*-py3-none-any.whl' | sort | tail -1)"
[ -n "$WHEEL" ] || { echo "No wheel in $DIST, run 'just build' first"; exit 1; }
VERSION="$(sed -n "s/^VERSION = '\(.*\)'$/\1/p" "$ROOT/openfreebuds_qt/version_info.py")"

PYTHON_TAR="$TOOLS/python-$PYTHON_VERSION.tar.gz"
fetch "https://github.com/astral-sh/python-build-standalone/releases/download/$PYTHON_RELEASE/cpython-$PYTHON_VERSION+$PYTHON_RELEASE-$ARCH-unknown-linux-gnu-install_only_stripped.tar.gz" \
    "$PYTHON_TAR" "$PYTHON_SHA256"
APPIMAGETOOL="$TOOLS/appimagetool-$APPIMAGETOOL_VERSION"
fetch "https://github.com/AppImage/appimagetool/releases/download/$APPIMAGETOOL_VERSION/appimagetool-$ARCH.AppImage" \
    "$APPIMAGETOOL" "$APPIMAGETOOL_SHA256"
chmod +x "$APPIMAGETOOL"

echo "-- Prepare AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr"
tar -xzf "$PYTHON_TAR" -C "$APPDIR/usr" --strip-components=1
PY="$APPDIR/usr/bin/python3"

REQUIREMENTS="${OFB_REQUIREMENTS:-$BUILD/requirements.txt}"
if [ -z "${OFB_REQUIREMENTS:-}" ]; then
    (cd "$ROOT" && pdm export --format=requirements --without-hashes --with no_flatpak) > "$REQUIREMENTS"
fi
# mmk-updater talks to the upstream update server; the AppImage updates itself from GitHub Releases.
# The extra index only serves Windows wheels.
grep -v -i -E '^(mmk-updater|winsdk|pyobjc|#|--)' "$REQUIREMENTS" > "$BUILD/requirements.filtered.txt"

echo "-- Install application"
"$PY" -m pip install -q --no-cache-dir --no-deps --no-compile -r "$BUILD/requirements.filtered.txt"
"$PY" -m pip install -q --no-cache-dir --no-deps --no-compile "$WHEEL"

echo "-- Prune"
SITE="$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
PYLIB="$(dirname "$SITE")"
rm -rf "$PYLIB"/{test,idlelib,tkinter,turtledemo,ensurepip,lib2to3} "$APPDIR"/usr/{include,share/man} \
       "$APPDIR"/usr/lib/{libtcl*,libtk*,tcl*,tk*,itcl*,thread*} "$PYLIB"/lib-dynload/_tkinter*
"$PY" -m pip uninstall -q -y pip
QT="$SITE/PyQt6"
# The app imports QtCore, QtGui and QtWidgets only. Drop other bindings and the Qt libraries they need.
find "$QT" -maxdepth 1 -name 'Qt*.abi3.so' \
    ! -name 'QtCore.abi3.so' ! -name 'QtGui.abi3.so' ! -name 'QtWidgets.abi3.so' ! -name 'QtDBus.abi3.so' -delete
rm -rf "$QT"/Qt6/qml "$QT"/Qt6/plugins/{qmltooling,qmllint,qmlls,sqldrivers,multimedia,position,sensors,texttospeech,canbus,designer,assetimporters,renderers,renderplugins,sceneparsers,geometryloaders,scxmldatamodel,printsupport,webview,help,egldeviceintegrations,networkinformation,tls}
rm -f "$QT"/Qt6/plugins/platforms/libq{eglfs,linuxfb,minimal,minimalegl,vkkhrdisplay,vnc}.so
for lib in Quick Qml QmlModels QmlMeta QmlWorkerScript Pdf Multimedia MultimediaWidgets SpatialAudio \
           Positioning Sensors Bluetooth Nfc SerialPort Sql Test Help Designer UiTools RemoteObjects \
           TextToSpeech ShaderTools 3D WebChannel WebSockets Charts DataVisualization Graphs Scxml \
           StateMachine SvgWidgets QuickWidgets OpenGLWidgets PrintSupport Network Xml Concurrent \
           Labs FFmpegStub EglFS; do
    rm -f "$QT"/Qt6/lib/libQt6"$lib"*.so*
done
rm -f "$QT"/Qt6/lib/lib{avcodec,avformat,avutil,swresample,swscale}.so*
find "$QT/Qt6/translations" -name '*.qm' ! -name 'qtbase_*' -delete

# Every libQt6 dependency must resolve inside the bundle: ldd falls back to the host Qt otherwise
foreign_qt() {
    LD_LIBRARY_PATH="$QT/Qt6/lib" ldd "$1" 2>/dev/null \
        | awk -v lib="$QT/Qt6/lib/" '$1 ~ /^libQt6/ && index($3, lib) != 1 {print $1}'
}
find "$QT/Qt6/plugins" -name '*.so' | while read -r plugin; do
    [ -z "$(foreign_qt "$plugin")" ] || rm -f "$plugin"
done
missing="$(find "$QT" -name '*.so*' -type f | while read -r so; do foreign_qt "$so"; done | sort -u)"
[ -z "$missing" ] || { echo "Qt libraries missing from the bundle:"; echo "$missing"; exit 1; }
"$PY" -m compileall -q -j0 "$PYLIB" >/dev/null

echo "-- Desktop integration"
ASSETS="$SITE/openfreebuds_qt/assets"
install -m 755 "$ROOT/scripts/appimage/AppRun" "$APPDIR/AppRun"
sed -e 's/^Comment=.*(Flatpak)$/Comment=Open-source client app for HUAWEI FreeBuds earphones/' \
    -e '/^Comment\[ru\]=/d' "$ASSETS/pw.mmk.OpenFreebuds.desktop" > "$APPDIR/pw.mmk.OpenFreebuds.desktop"
cp "$ASSETS/pw.mmk.OpenFreebuds.png" "$APPDIR/pw.mmk.OpenFreebuds.png"
ln -sf pw.mmk.OpenFreebuds.png "$APPDIR/.DirIcon"
echo "$REPO" > "$APPDIR/update-repo"

echo "-- Build AppImage"
OUT="$DIST/OpenFreebuds-$VERSION-$ARCH.AppImage"
UPDATE_INFO="gh-releases-zsync|${REPO%%/*}|${REPO##*/}|latest|OpenFreebuds-*-$ARCH.AppImage.zsync"
rm -f "$OUT" "$OUT.zsync" "$OUT.sha256"
args=()
if command -v zsyncmake >/dev/null; then
    args=(-u "$UPDATE_INFO")
else
    echo "-- zsyncmake not found, building without update information"
fi
(cd "$DIST" && ARCH="$ARCH" APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" --no-appstream "${args[@]}" "$APPDIR" "$OUT")
(cd "$DIST" && sha256sum "$(basename "$OUT")" > "$OUT.sha256")
echo "-- Done: $OUT ($(du -h "$OUT" | cut -f1))"
