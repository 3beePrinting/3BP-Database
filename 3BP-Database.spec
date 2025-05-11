# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\2AIM2\\04_3D_PRINTING\\3BP-Database\\db_v01.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\2AIM2\\04_3D_PRINTING\\3BP-Database\\images', 'images'), ('D:\\2AIM2\\04_3D_PRINTING\\3BP-Database\\cd_DataBase', 'cd_DataBase'), ('D:\\2AIM2\\04_3D_PRINTING\\3BP-Database\\settings_dialog.py', '.'), ('D:\\2AIM2\\04_3D_PRINTING\\3BP-Database\\db_initialize.py', '.')],
    hiddenimports=['win32com', 'win32com.client', 'qrcode', 'PIL._imaging', 'reportlab.pdfgen.canvas', 'reportlab.lib.pagesizes', 'reportlab.lib.colors', 'flask', 'werkzeug'],
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
    name='3BP-Database',
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
