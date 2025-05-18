#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
App 3BP Database using PyQt5
This is the main script. Run this to launch the App.
V10 22/04/2025
@author: feder
"""

import sys
from PyQt5.QtWidgets import QApplication, QInputDialog
from cd_DataBase import DatabaseApp
from db_initialize import initialize_db
import json
import os
from settings_dialog import SettingsDialog, load_settings
from PyQt5.QtWidgets import QApplication, QDialog

SETTINGS_FILE = "settings.json" #input settings file


def main():
    app = QApplication(sys.argv)

    # 1) Load or prompt for database file
    settings = load_settings()
    if not settings.get("database_path"):
        dlg = SettingsDialog()
        if dlg.exec_() == QDialog.Accepted:
            settings = load_settings()
        else:
            sys.exit()

    # 2) Use exactly that .db path
    dbfile = settings["database_path"]

    # 3) Make sure the file’s parent folder exists (and create if needed)
    dbdir = os.path.dirname(dbfile)
    os.makedirs(dbdir, exist_ok=True)

    # 4) Initialize and launch
    initialize_db(dbfile)
    win = DatabaseApp(dbfile, settings)
    win.showMaximized()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
