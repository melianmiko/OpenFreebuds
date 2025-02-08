# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ["..\\openfreebuds_qt\\launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ('..\\openfreebuds\\assets', 'openfreebuds\\assets'),
        ('..\\openfreebuds_qt\\assets', 'openfreebuds_qt\\assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6'],
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
    name='openfreebuds',
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
    icon=['.\\pw.mmk.OpenFreebuds.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='openfreebuds',
)
