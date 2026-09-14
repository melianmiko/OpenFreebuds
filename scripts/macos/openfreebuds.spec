# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None
py_version = sys.version_info
py_version_string = f"{py_version.major}.{py_version.minor}"

a = Analysis(
    ["../../openfreebuds_qt/launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ('../../openfreebuds/assets', 'openfreebuds/assets'),
        ('../../openfreebuds_qt/assets', 'openfreebuds_qt/assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OpenFreebuds',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['openfreebuds.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenFreebuds',
)
app = BUNDLE(
    coll,
    name='OpenFreebuds.app',
    icon='openfreebuds.png',
    bundle_identifier='pw.mmk.OpenFreebuds',
    target_arch=None,
    info_plist={
        'NSBluetoothAlwaysUsageDescription': 'Bluetooth required to interact with HUAWEI earphones connected to this machine',
    },
)
