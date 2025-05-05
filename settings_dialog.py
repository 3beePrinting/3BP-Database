# settings_dialog.py

import os, json, sys
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QSpinBox, QDialogButtonBox,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox
)

from PyQt5.QtCore import QStandardPaths

# Determine a real folder for your app’s data
if getattr(sys, 'frozen', False):
    # running in exe
    appdata = QStandardPaths.writableLocation(
        QStandardPaths.AppDataLocation
    )
    # On Windows this is: C:/Users/<You>/AppData/Roaming/YourAppName
else:
    # running in script
    appdata = os.path.dirname(__file__)

os.makedirs(appdata, exist_ok=True)
SETTINGS_FILE = os.path.join(appdata, "settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(500, 300)

        self.tabs = QTabWidget(self)
        self._build_tabs()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            self
        )
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)

        self._load_into_fields()

    def _build_tabs(self):
        # ——— Database Tab ———
        self.tab_db = QWidget()
        form_db = QFormLayout(self.tab_db)
        h = QHBoxLayout()
        self.input_db_path = QLineEdit()
        btn = QPushButton("Browse…")
        btn.clicked.connect(self._browse_db)
        h.addWidget(self.input_db_path)
        h.addWidget(btn)
        form_db.addRow("Database file (.db):", h)
        self.tabs.addTab(self.tab_db, "Database")

        # ——— Price-defaults Tab ———
        self.tab_price = QWidget()
        form2 = QFormLayout(self.tab_price)
        self.spin_design = QSpinBox();  self.spin_design.setRange(0,1000)
        self.spin_labour = QSpinBox();  self.spin_labour.setRange(0,1000)
        form2.addRow("Design hourly rate (€):", self.spin_design)
        form2.addRow("Labour hourly rate (€):", self.spin_labour)
        self.tabs.addTab(self.tab_price, "Price defaults")

        # ——— Placeholder tabs ———
        for name in ("Advanced", "Integration", "About"):
            self.tabs.addTab(QWidget(), name)

    def _browse_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3beeprinting.db",
            "",
            "SQLite Databases (*.db);;All files (*)"
        )
        if path:
            if not path.lower().endswith(".db"):
                QMessageBox.warning(
                    self,
                    "Invalid file",
                    "Please select a file with the .db extension."
                )
                return
            self.input_db_path.setText(path)

    def _load_into_fields(self):
        s = load_settings()
        self.input_db_path.setText(s.get("database_path", ""))
        self.spin_design.setValue(s.get("design_hourly_rate", 0))
        self.spin_labour.setValue(s.get("labour_hourly_rate", 0))

    def _save_and_close(self):
        dbp = self.input_db_path.text()
        # Validate that the file exists and is .db
        if not dbp.lower().endswith(".db") or not os.path.isfile(dbp):
            QMessageBox.warning(
                self,
                "Invalid database",
                "You must select an existing .db file."
            )
            return

        s = {
            "database_path": dbp,
            "design_hourly_rate": self.spin_design.value(),
            "labour_hourly_rate": self.spin_labour.value(),
            # you can seed a default version here if you like:
            # "version": "1.0.0"
        }
        save_settings(s)
        self.accept()
