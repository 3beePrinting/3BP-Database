# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['db_v01.py'],
    pathex=[],
    binaries=[],
    datas=[('images\\*', 'images')],
    hiddenimports=['PyQt5.sip', 'openpyxl', 'openpyxl.workbook', 'openpyxl.worksheet', 'openpyxl.reader.excel', 'openpyxl.writer.excel'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='db_v01',
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
)
