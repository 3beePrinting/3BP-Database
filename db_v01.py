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

SETTINGS_FILE = "settings.json" #input settings file

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
        return settings
    else:
        return None

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def ask_initial_questions():
    settings = {}
    
    one_drive_local_path, ok = QInputDialog.getText(None, "Initialization", "Enter the path to your local 3BP OneDrive (example C:\\Users\\feder\\3BeePrinting(2aim2)\\3Bee Printing - 01 3BEE_PRINTING):")
    if not ok:
        sys.exit()

    design_hourly_rate, ok = QInputDialog.getInt(None, "Initialization", "Enter the hourly rate for 3D designing (€):")
    if not ok:
        sys.exit()
        
    labour_hourly_rate, ok = QInputDialog.getInt(None, "Initialization", "Enter the hourly rate for labour (€):")
    if not ok:
        sys.exit()

    settings["one_drive_local_path"] = one_drive_local_path
    settings["design_hourly_rate"] = design_hourly_rate
    settings["labour_hourly_rate"] = labour_hourly_rate

    save_settings(settings)
    return settings

if __name__ == "__main__":    
    
    app = QApplication(sys.argv)
    
    # Load inputs
    settings = load_settings()
    if not settings:
        settings = ask_initial_questions()
        
    # Initialize database file name and structure
    dbfile_name = os.path.join(settings["one_drive_local_path"], "09 Development", "04 Python Database 2025", "3beeprinting.db")
    # dbfile_name = os.path.join(settings["one_drive_local_path"], "3beeprinting2.db")
    # dbfile_name = "3beeprinting2.db"
    initialize_db(dbfile_name)
    
    # Create main window instance (DatabaseApp is a QMainWindow subclass)
    main_window = DatabaseApp(dbfile_name, settings)
    
    # Show the window maximized
    main_window.showMaximized()
    
    sys.exit(app.exec_())
