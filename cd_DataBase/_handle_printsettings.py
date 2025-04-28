# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 12:57:30 2025

@author: feder
"""

import sqlite3
from PyQt5.QtWidgets import ( 
    QWidget,  QTableWidget, QTableWidgetItem, QListWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QScrollArea,
    QGridLayout, QComboBox, QMessageBox, QDialog, QRadioButton, QButtonGroup
    )
import pandas as pd
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# Create widgets for print settings and fill it automatically with values 
def widget_printsettings(self, parent, modify_flag_printsettings = False, from_ordertab = False):
    # make it scrollable in case resizing needed
    dialog_layout = QVBoxLayout(parent)## Main layout
    
    scroll_area = QScrollArea(parent) #scroll area
    scroll_area.setWidgetResizable(True)
    
    # Content inside scroll
    scroll_content = QWidget()
    layout = QVBoxLayout(scroll_content)
    
    grid_layout = QGridLayout()  # Grid layout for proper alignment
    
    ## Function to fetch setting from database and fill in all data
    def fetch_printsettings_to_modify():
        prinset_id = self.modify_printset_id_entry.text()
        self.prinset_id = prinset_id
        if prinset_id:
            try:
                self.cursor.execute("SELECT * FROM printsettings WHERE PrintSettingID = ?", (prinset_id,))
                printset = self.cursor.fetchone()
                if printset:
                    # Mapping database columns to UI fields (excluding PrintSettingID)
                    for (key, entry), value in zip(self.modify_printset_entries.items(), printset[1:]):  
                        if isinstance(entry, QLineEdit): 
                            if key in ["NozzleSize", "Infill", "LayerHeight", "Speed", "NozzleTemperature", "BedTemperature"] and value!= "":
                                try: # check its a number, otherwise remove
                                    entry.setText(str(float(value)))
                                except ValueError:
                                    incorrect_info_flag = True
                            else:
                                entry.setText(str(value) if value is not None else "")
                            
                        elif isinstance(entry, QTextEdit):  
                            entry.setPlainText(str(value) if value is not None else "")
                            
                        elif isinstance(entry, QComboBox):  
                            if value in [entry.itemText(j) for j in range(entry.count())]:
                                entry.setCurrentText(str(value))
                            else:
                                incorrect_info_flag = True
                else:
                    QMessageBox.warning(self, "Print Setting Not Found", "No print settings found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch print setting data: {e}")
        # If data inputted were not ok, say it here with a warning message
        if incorrect_info_flag:
            QMessageBox.warning(None, "Data format/content warning", "Some values fetched in the database for this ID are incorrect. They are automatically removed and set to default in this form.")

    
    # Function to fecth default values already saved in db as ID1
    def fetch_default_values():
        # Function to fetch default values from the database
        self.cursor.execute("SELECT * FROM printsettings WHERE PrintSettingID = 1")
        row = self.cursor.fetchone()
        if row:
            # Map field names to their values based on column order in the database
            field_names = ["SettingName", "NozzleSize", "Infill", "LayerHeight", "Speed",
                "Support", "Brim", "Glue", "NozzleTemperature", "BedTemperature", "Notes" ]
            
            default_values = {field: row[i+1] for i, field in enumerate(field_names)}
            return default_values
        else:
            print("Default print settings not found!")
            return {}
    
    if modify_flag_printsettings:  # MODIFY PRINTSET
        modify_layout = QHBoxLayout()
        label = QLabel("PrintSetting ID to Modify:")
        self.modify_printset_id_entry = QLineEdit()
        self.modify_printset_id_entry.setReadOnly(True)
        search_button = QPushButton("Search Table")
        search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("printsettings", self.modify_printset_id_entry))
        fetch_button = QPushButton("Fetch Setting")
        fetch_button.clicked.connect(fetch_printsettings_to_modify)

        modify_layout.addWidget(label)
        modify_layout.addWidget(self.modify_printset_id_entry)
        modify_layout.addWidget(search_button)
        modify_layout.addWidget(fetch_button)
        layout.addLayout(modify_layout) # add the modify layout on top!
    
    printsettings_entries = {}
    default_values = fetch_default_values()
    
    ## --- Fields for Print Settings ---
    fields = [
        ("Setting's Name", None),
        ("NozzleSize", ["0.25 mm", "0.4 mm", "0.6 mm", "0.8 mm"]),
        ("Infill", "%"), 
        ("LayerHeight", "mm"),
        ("Speed", "mm/s"),
        ("Support", ["Yes", "No"]),  # Dropdown
        ("Brim", ["Yes", "No"]),     # Dropdown
        ("Glue", ["Yes", "No"]),     # Dropdown
        ("NozzleTemperature", "°C"),
        ("BedTemperature", "°C"),
        ("Notes", None) ]
    
    max_label_width = 120  # Set a max width for labels
    input_width = 100  # Set a standard width for input fields
    
    for row, (field, unit) in enumerate(fields):
        label = QLabel(field)
        label.setFixedWidth(max_label_width)  # Ensuring consistent label width
        grid_layout.addWidget(label, row, 0)
    
        if field == "Notes":
            widget = QTextEdit()  # Multi-line text field
            widget.setFixedHeight(50)  # Adjust height for 2 rows
            widget.setFixedWidth(input_width * 2)  # Make it a bit wider
            grid_layout.addWidget(widget, row, 1, 1, 2)  # Span across two columns
        elif isinstance(unit, list):  # If it's a dropdown (QComboBox)
            widget = QComboBox()
            widget.addItems(unit)
            if not modify_flag_printsettings:
                if field == "NozzleSize":
                    widget.setCurrentText(default_values.get(field, "0.4 mm"))
                else:
                    widget.setCurrentText(default_values.get(field, "No"))
            grid_layout.addWidget(widget, row, 1)  # Add in column 1
        else:  # If it's a normal text field (QLineEdit)
            widget = QLineEdit()
            widget.setFixedWidth(input_width)  # Uniform width for all input fields
            if not modify_flag_printsettings:
                widget.setText(str(default_values.get(field, "")))
            grid_layout.addWidget(widget, row, 1)  # Add in column 1

        printsettings_entries[field] = widget
    
        if unit and isinstance(unit, str) and field != "Notes":  # Add unit label if applicable
            unit_label = QLabel(unit)
            grid_layout.addWidget(unit_label, row, 2)  # Keep unit labels aligned


    layout.addLayout(grid_layout)

    icon_path =  self.resource_path("images/save_button.png") 
    icon = QIcon(icon_path) 
    ## --- SAVE / MODIFY BUTTONS ---
    if modify_flag_printsettings:
        modify_button = QPushButton("Modify Print Setting")
        modify_button.setIcon(icon) 
        modify_button.clicked.connect(lambda: self.save_printsettings(modify_flag_printsettings=True, from_ordertab=from_ordertab))
        layout.addWidget(modify_button)
        self.modify_printset_entries = printsettings_entries
    else:
        save_button = QPushButton("Save New Print Setting")
        save_button.setIcon(icon) 
        save_button.clicked.connect(lambda: self.save_printsettings(from_ordertab=from_ordertab))
        layout.addWidget(save_button)
        self.new_printset_entries = printsettings_entries

    #set layout
    scroll_area.setWidget(scroll_content)
    dialog_layout.addWidget(scroll_area)

    parent.closeEvent = lambda event: self.close_event(event, parent)  
    parent.show()
    
#%% OPEN & ASSIGN PRINT SETTINGS TO ORDER PARTS
def open_print_settings_window(self):
    """Opens a new window for editing PrintSettings."""
    self.printsettings_popup = QDialog(self)
    self.printsettings_popup.setWindowTitle("PrintSettings")
    self.printsettings_popup.resize(1200, 700)
    
    main_layout = QVBoxLayout(self.printsettings_popup)
    
    # --- Buttons above the table ---
    top_button_layout = QHBoxLayout()

    add_button = QPushButton("Add New Settings")
    add_button.clicked.connect(lambda: self.open_add_printsetting_window(from_ordertab=True))
    top_button_layout.addWidget(add_button)

    assign_button = QPushButton("Assign Print Setting")
    assign_button.clicked.connect(self.assign_printsetting)
    top_button_layout.addWidget(assign_button)
    
    # Left side - Table
    table_frame = QWidget()
    table_layout = QVBoxLayout()
    table_frame.setLayout(table_layout)

    # Fetch table data from DB
    try:
        query = "SELECT * FROM printsettings;"
        self.current_df = pd.read_sql_query(query, self.connection)

        if self.current_df.empty:
            QMessageBox.information(self, "Info", "No data available in the printsettings table.")
            return

        self.tree = QTableWidget()
        self.tree.setRowCount(len(self.current_df))
        self.tree.setColumnCount(len(self.current_df.columns))
        self.tree.setHorizontalHeaderLabels(self.current_df.columns)
        self.tree.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tree.setSelectionBehavior(QTableWidget.SelectRows)

        for row_idx, (_, row) in enumerate(self.current_df.iterrows()):
            for col_idx, val in enumerate(row):
                self.tree.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

        table_layout.addWidget(self.tree)

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load table data: {e}")
        return

    # Add everything to main layout
    main_layout.addLayout(top_button_layout)  # This shows your buttons at the top
    main_layout.addWidget(table_frame)        # Then the table below

    self.printsettings_popup.show()

    
def assign_printsetting(self):
    """Assign a selected print setting to PartIDs."""
    # Ensure a row is selected in the Treeview
    selected_items = self.tree.selectedItems()
    if not selected_items:
        QMessageBox.critical(self, "Selection Error", "Please select a print setting.")
        return
    
    row = selected_items[0].row()
    print_setting_id = self.tree.item(row, 0).text()

    self.assign_popup = QDialog(self)
    self.assign_popup.setWindowTitle("Assign Print Settings")
    self.assign_popup.resize(400, 400)
    
    layout = QVBoxLayout(self.assign_popup)
    layout.addWidget(QLabel(f"Assign PrintSetting ID {print_setting_id} to which PartNr?"))

    # Option: All, Selected, Multiple
    self.assign_option = QButtonGroup()
    radio_all = QRadioButton("All")
    radio_parts = QRadioButton("PartNr(s)")
    radio_all.setChecked(True)
    self.assign_option.addButton(radio_all)
    self.assign_option.addButton(radio_parts)

    layout.addWidget(radio_all)
    layout.addWidget(radio_parts)

    self.part_nrs_listbox = QListWidget()
    self.part_nrs_listbox.setSelectionMode(QListWidget.MultiSelection)
    for part in self.parts:
        self.part_nrs_listbox.addItem(str(part["PartNr"]))
    layout.addWidget(self.part_nrs_listbox)

    confirm_btn = QPushButton("Assign")
    confirm_btn.clicked.connect(lambda: self.confirm_assign(print_setting_id))
    layout.addWidget(confirm_btn)

    self.assign_popup.show()

def confirm_assign(self, print_setting_id):
    option = "All" if self.assign_option.buttons()[0].isChecked() else "PartNr(s)"
    selected_parts = [item.text() for item in self.part_nrs_listbox.selectedItems()]
    
    try:
        # Update self.parts
        self.cursor.execute("SELECT SettingName FROM printsettings WHERE PrintSettingID = ?", (int(print_setting_id),))
        prinsetname = self.cursor.fetchone()
        new_printsettings = f"{prinsetname[0]} (ID{print_setting_id})"
        selected_rows = [int(i)-1 for i in selected_parts]
        if option == "All":
            selected_rows = list(range(len(self.parts)))
            for row in self.parts:
                row["PrintSettings"] = new_printsettings
        else:
            selected_rows = [int(i)-1 for i in selected_parts]
            for part_nr in selected_parts:
                for row in self.parts:
                    if str(row["PartNr"]) == part_nr:
                        row["PrintSettings"] = new_printsettings
                        break
        
        # Update table display
        col_index = self.parts_table.columnCount() - 1  # Assuming PrintSettings is last column

        for row in selected_rows:
            if row < 0 or row >= self.parts_table.rowCount():
                continue  # Skip invalid rows

            # Update table
            self.parts_table.setItem(row, col_index, QTableWidgetItem(new_printsettings))

        self.assign_popup.accept()

        QMessageBox.information(self, "Success", "Print settings assigned successfully!")
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to assign print setting: {e}")


#%% HANDLE WINDOW
def open_handle_printsetting_window(self):
    self.handle_window_printset = QDialog(self)
    self.handle_window_printset.setWindowTitle("Handle Print Settings")
    self.handle_window_printset.resize(300, 200)
    
    layout = QVBoxLayout()

    # See button
    see_printset_button = QPushButton("See Print Settings")
    see_printset_button.clicked.connect(lambda: self.show_table("printsettings"))
    layout.addWidget(see_printset_button)

    # Add New button
    add_printset_button = QPushButton("Add New Print Setting")
    add_printset_button.clicked.connect(self.open_add_printsetting_window)
    layout.addWidget(add_printset_button)

    # Modify button
    modify_printset_button = QPushButton("Modify Print Setting")
    modify_printset_button.clicked.connect(self.open_modify_printsetting_window)
    layout.addWidget(modify_printset_button)

    # Remove button
    remove_printset_button = QPushButton("Remove Print Setting")
    remove_printset_button.clicked.connect(self.open_remove_printsettings_window)
    layout.addWidget(remove_printset_button)
    
    self.handle_window_printset.setLayout(layout)
    self.handle_window_printset.show()


#%% ADD SETTINGS, with default values in
def open_add_printsetting_window(self, from_ordertab = False):
    # Create a new window for adding
    self.add_window_printset = QDialog(None)
    self.add_window_printset.setWindowTitle("Add New Print Setting")
    self.add_window_printset.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.add_window_printset.resize(400, 500)

    # Generate a new PrintSettingID
    try:
        self.cursor.execute("SELECT MAX(PrintSettingID) FROM printsettings;")
        max_printset_id = self.cursor.fetchone()[0]
        self.printset_id = (max_printset_id or 0) + 1  
    except sqlite3.Error as e:
        QMessageBox.critical(self, "Error", f"Failed to generate PrintSettingID: {e}")
        return
    
    # Get the entry fields 
    self.widget_printsettings(self.add_window_printset, from_ordertab = from_ordertab)
  
#%% MODIFY SETTINGS
def open_modify_printsetting_window(self, from_ordertab = False):
    # Ask for ID to modify
    self.modify_window_printset = QDialog(None)
    self.modify_window_printset.setWindowTitle("Modify Print Setting")
    self.modify_window_printset.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.modify_window_printset.resize(400, 500)
    
    # Get the entry fields 
    self.widget_printsettings(self.modify_window_printset, modify_flag_printsettings = True)
  

#%% SAVE SETTINGS
def save_printsettings(self, modify_flag_printsettings = False, from_ordertab = False):
    if modify_flag_printsettings:
        entries = self.modify_printset_entries
    else:
        entries = self.new_printset_entries

    # Fields validation
    for key, widget in entries.items():
        if key == "Setting's Name":
            if not widget.text().strip():
                QMessageBox.critical(self, "Validation Error", "Mandatory fields missing.")
                return 
        elif key in ["Infill", "LayerHeight", "Speed", "NozzleTemperature", "BedTemperature"]:
            try:
                float(widget.text())
            except ValueError:
                QMessageBox.critical(None, "Validation Error", f"{key} must be a number.")
                return

    # Get values from entry fields
    values = tuple(
        widget.toPlainText() if isinstance(widget, QTextEdit) else
        widget.currentText() if isinstance(widget, QComboBox) else
        widget.text()
        for widget in entries.values()   )
    
    if modify_flag_printsettings:
        try:
            self.cursor.execute("""UPDATE printsettings
                SET SettingName = ?, NozzleSize = ?, Infill = ?, LayerHeight = ?, Speed = ?, Support = ?, Brim = ?, Glue = ?, NozzleTemperature = ?, BedTemperature = ?, Notes = ?
                WHERE PrintSettingID = ?
            """, values + (self.prinset_id,))
            self.connection.commit()
            
            QMessageBox.information(None, "Success", "Print setting modified successfully")
            self.modify_window_printset.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Error", f"Failed to modify print setting: {e}")
    
    else:
        try:
            # Insert the new employee into the database
            self.cursor.execute('''INSERT INTO printsettings (SettingName, NozzleSize, Infill, LayerHeight, Speed, Support, Brim, Glue, NozzleTemperature, BedTemperature, Notes)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', values)
            self.connection.commit()
            
            QMessageBox.information(None, "Success", "New print settings added successfully!")
            self.add_window_printset.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Error", f"Failed to add print setting: {e}")
           
    if from_ordertab:
        self.printsettings_popup.destroy()
        self.open_print_settings_window()
    else:
        self.show_table("printsettings")  # Refresh the employees table view
        self.handle_window_printset.destroy()
        
    
#%% REMOVE PRINT SETTING
def open_remove_printsettings_window(self, from_ordertab=False):
    self.remove_window_printset = QDialog(None)
    self.remove_window_printset.setWindowTitle("Remove Print Setting")
    self.remove_window_printset.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.remove_window_printset.resize(300, 200)

    layout = QVBoxLayout()
    
    def remove_printsettings(printset_id):
        # Remove print settings logic
        try:
            self.cursor.execute("DELETE FROM printsettings WHERE PrintSettingID = ?", (printset_id,))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Print Settings removed successfully")
            
            if from_ordertab:
                self.printsettings_popup.destroy()
                self.open_print_settings_window()
            else:
                self.show_table("printsettings")  # Refresh the table view
                self.handle_window_printset.destroy()
            
            self.remove_window_printset.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to remove Print Settings: {e}")

    def fetch_printset_to_remove():
        # Fetch the print setting to be removed and show confirmation
        printset_id = self.remove_printset_id_entry.text()
        if printset_id:
            try:
                self.cursor.execute("SELECT * FROM printsettings WHERE PrintSettingID = ?", (printset_id,))
                printsetting = self.cursor.fetchone()

                if printsetting:
                    confirmation = QMessageBox.question(
                        self, "Confirm Deletion",
                        f"Are you sure you want to delete Print Setting with ID {printset_id}?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if confirmation == QMessageBox.Yes:
                        remove_printsettings(printset_id)
                else:
                    QMessageBox.warning(self, "Print Setting Not Found", "No print setting found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch Print Settings data: {e}")

    # Specify PrintSettingID, fetch it and remove it
    label = QLabel("PrintSetting ID to Remove:")
    self.remove_printset_id_entry = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(self.remove_printset_id_entry)

    # Button to open print settings selection table
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("printsettings", self.remove_printset_id_entry))
    layout.addWidget(search_button)

    fetch_button = QPushButton("Remove Print Setting")
    fetch_button.clicked.connect(fetch_printset_to_remove)
    layout.addWidget(fetch_button)

    self.remove_window_printset.setLayout(layout)
    self.remove_window_printset.show()
