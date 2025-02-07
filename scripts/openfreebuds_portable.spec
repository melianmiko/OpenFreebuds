# -*- mode: python ; coding: utf-8 -*-


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
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='openfreebuds_portable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['.\\pw.mmk.OpenFreebuds.ico'],
)
