#!/usr/bin/env python3
import os
import sys
import PyInstaller.__main__ as pyi
import PyQt5

# ------------------
# Build configuration
# ------------------
project_root = os.path.abspath(os.path.dirname(__file__))
main_script = os.path.join(project_root, 'db_v01.py')

# Output executable name
exe_name = '3BP-Database'

# Data files and folders to include
# Format: (source_path, destination_relative_folder)
data_items = [
    (os.path.join(project_root, 'images'), 'images'),
    (os.path.join(project_root, 'cd_DataBase'), 'cd_DataBase'),
    (os.path.join(project_root, 'settings_dialog.py'), '.'),
    (os.path.join(project_root, 'payment_system.py'), '.'),
    (os.path.join(project_root, 'db_initialize.py'), '.'),
]

# PyQt5 platforms plugin
plugin_src = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt', 'plugins', 'platforms')

# Hidden imports for modules PyInstaller may miss
hidden_imports = [
    'win32com',
    'win32com.client',
    'qrcode',
    'PIL._imaging',
    'reportlab.pdfgen.canvas',
    'reportlab.lib.pagesizes',
    'reportlab.lib.colors',
    'flask',
    'werkzeug',
]

# PyInstaller options
opts = [
    main_script,
    '--name=' + exe_name,
    '--onefile',
    '--windowed',
]

# Include icon if present
icon_path = os.path.join(project_root, 'images', '3bp_logo.ico')
if os.path.isfile(icon_path):
    opts.append(f'--icon={icon_path}')

# Add data items
for src, dest in data_items:
    if os.path.exists(src):
        # On Windows use ';', on others use ':'
        sep = os.pathsep
        opts.append(f'--add-data={src}{sep}{dest}')

# Add Qt platforms plugin
if os.path.isdir(plugin_src):
    opts.append(f'--add-data={plugin_src}{os.pathsep}platforms')

# Add hidden imports
for mod in hidden_imports:
    opts.append(f'--hidden-import={mod}')

if __name__ == '__main__':
    print('Building executable with PyInstaller...')
    pyi.run(opts)
    print('Build complete! Executable is in dist/ folder.')
