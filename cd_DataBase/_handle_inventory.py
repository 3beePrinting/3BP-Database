# -*- coding: utf-8 -*-
"""
Handling Printer and filament inventories 

@author: feder
"""
import sqlite3
from PyQt5.QtWidgets import (  QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit, QTextEdit,
    QGridLayout, QComboBox, QMessageBox, QDialog, QDateEdit, QCheckBox, QScrollArea, QWidget  )
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, QDate, Qt
import os
import win32com.client as win32

#%% PRINTER OPTION MENU
def open_handle_printers_window(self):
    # Open a new window for printers modifications
    self.handle_printers_window = QDialog(self)
    self.handle_printers_window.setWindowTitle("Handle Printers")
    self.handle_printers_window.resize(300, 200)
    
    layout = QVBoxLayout()

    # See button
    see_printer_button = QPushButton("See Printers")
    def _show_and_wire_printers():
        # 1) populate the table
        self.show_table("printers")
        # 2) remove any old handler
        try:
            self.table.cellDoubleClicked.disconnect()
        except TypeError:
            pass
        # 3) wire the new handler
        self.table.cellDoubleClicked.connect(self._on_printer_doubleclick)

    see_printer_button.clicked.connect(_show_and_wire_printers)
    layout.addWidget(see_printer_button)

    # Add New button
    add_printer_button = QPushButton("Add New Printer")
    add_printer_button.clicked.connect(self.open_add_printer_window)
    layout.addWidget(add_printer_button)

    # Modify button
    modify_printer_button = QPushButton("Modify Printer")
    modify_printer_button.clicked.connect(self.open_modify_printer_window)
    layout.addWidget(modify_printer_button)

    # Remove button
    remove_printer_button = QPushButton("Remove Printer")
    remove_printer_button.clicked.connect(self.open_remove_printer_window)
    layout.addWidget(remove_printer_button)
    
    self.handle_printers_window.setLayout(layout)
    self.handle_printers_window.show()

def _on_printer_doubleclick(self, row, col):
    # 1) grab the CustomerID from column 0
    prnt_id = self.table.item(row, 0).text()
    if not prnt_id:
        return

    # 2) open the Modify Customer window (this creates self.modify_customer_id_entry)
    self.open_modify_printer_window()

    # 3) now fill that dialog’s ID-entry with your selected ID
    self.modify_printer_id_entry.setText(prnt_id)
    # now immediately fetch & populate all other fields
    self.fetch_printer_to_modify()
    
## Function to fetch printer from database and fill in all data
def fetch_printer_to_modify(self):
    printer_id = self.modify_printer_id_entry.text()
    self.printer_id = printer_id
    
    # check suppliers and expenses exist
    self.cursor.execute("SELECT SupplierID FROM suppliers")
    suppliers = self.cursor.fetchall()
    supplier_list = [x[0] for x in suppliers]
    self.cursor.execute("SELECT OCnumber FROM expenses")
    expenses = self.cursor.fetchall()
    expenses_list = [x[0] for x in expenses]
    if printer_id:
        try:
            self.cursor.execute("SELECT * FROM printers WHERE PrinterID = ?", (self.printer_id,))
            printer = self.cursor.fetchone()
            if printer:
                for (key, entry), value in zip(self.printer_entries.items(), printer[1:]):  
                    if isinstance(entry, QLineEdit):  
                        if key == 'oc_number': 
                            if value in expenses_list:
                                entry.setText(str(value))
                            else:
                                incorrect_info_flag = True
                        elif key == 'supplierid':
                            if value in supplier_list:
                                entry.setText(str(value))
                            else:
                                incorrect_info_flag = True
                        elif key in ["power", "print_size_x", "print_size_y", "print_size_z", "total_hours", "total_hours_after_last_maintenance"]:
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
                            entry.setCurrentText(value)
                        else:
                            incorrect_info_flag = True
                            
                    elif isinstance(entry, QDateEdit):  
                        date = QDate.fromString(value, "yyyy-MM-dd")
                        if date.isValid():
                            entry.setDate(date)
                        else:
                            incorrect_info_flag = True
                        
                # Update image label instead of replacing it
                if printer[-1]:  # Assuming the last column is 'Picture'
                    self.image_label.setText("Image exists in database. If you attach a new picture, the old one will be lost.")
                    self.image_label.setStyleSheet("font-style: italic; color: gray;")
                else:
                    self.image_label.setText("No image on database for this ID.")
                    self.image_label.setStyleSheet("font-style: italic; color: gray;")
            else:
                QMessageBox.warning(self, "Printer Not Found", "No printer found with the given ID.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch printer data: {e}")

    # If data inputted were not ok, say it here with a warning message
    if incorrect_info_flag:
        QMessageBox.warning(None, "Data format/content warning", "Some values fetched in the database for this ID are incorrect. They are automatically removed and set to default in this form.")

    
#%% PRINTER WIDGET
def printer_widgets(self, window, modify_printer_flag=False):
    # make it scrollable in case resizing needed
    dialog_layout = QVBoxLayout(window)## Main layout
    
    scroll_area = QScrollArea(window) #scroll area
    scroll_area.setWidgetResizable(True)
    
    # Content inside scroll
    scroll_content = QWidget()
    layout = QVBoxLayout(scroll_content)
    


    ## MODIFY PRINTER - ID SELECTION
    if modify_printer_flag:
        modify_layout = QHBoxLayout()
        label = QLabel("Printer ID to Modify:")
        self.modify_printer_id_entry = QLineEdit()
        self.modify_printer_id_entry.setReadOnly(True)
        search_button = QPushButton("Search Table")
        search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("printers", self.modify_printer_id_entry))
        fetch_button = QPushButton("Fetch Printer")
        fetch_button.clicked.connect(self.fetch_printer_to_modify)

        modify_layout.addWidget(label)
        modify_layout.addWidget(self.modify_printer_id_entry)
        modify_layout.addWidget(search_button)
        modify_layout.addWidget(fetch_button)
        layout.addLayout(modify_layout)
        
    printer_entries = {}
    
    ## --- SECTION 1: ORDER DETAILS ---
    order_group = QGroupBox("Order Details")
    order_layout = QGridLayout()
    
    # Called when supplier is selected directly
    def handle_supplier_change():
        self.oc_number_search.setText("NA")
        self.supplier_id_search.setEnabled(True)

    oc_label = QLabel("OC Number")
    self.oc_number_search = QLineEdit()
    self.oc_number_search.setReadOnly(True)
    
    # "Search Expense" Button
    search_expense_button = QPushButton("Search Expense")
    search_expense_button.setIcon(QIcon( self.resource_path("images/search_expense.png") )) # Optional: icon
    # search_expense_button.setIconSize(QSize(20, 20))
    search_expense_button.clicked.connect( lambda: (self.open_modifyfromtable_selection("expenses", self.oc_number_search, fillin_supplier = True)) )
    
    # "New Expense" Button
    icon_path = self.resource_path("images/add_expense.png") 
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    add_expense_button = QPushButton("New Expense")
    add_expense_button.setIcon(icon)  # Assign the icon
    # add_expense_button.setIconSize(QSize(20, 20))  # Adjust icon size
    add_expense_button.clicked.connect(self.open_add_expense_window)
    
    OCnumber_help_text = "The OCnumber of the expense for this printer must be filled in, if any. \nThe SupplierID is automatically filled from the value in the expenses database. If you want to manually select a SupplierID, the OCnumber will be disconnected automatically."
    
    supplier_label = QLabel("Supplier ID (*)")
    self.supplier_id_search = QLineEdit()
    self.supplier_id_search.setReadOnly(True)

    search_supplier_button = QPushButton("Search Supplier")
    search_supplier_button.setIcon(QIcon( self.resource_path("images/search_supplier.png") ))  # Optional: icon
    # search_supplier_button.setIconSize(QSize(20, 20))
    search_supplier_button.clicked.connect( lambda: (self.open_modifyfromtable_selection("suppliers", self.supplier_id_search), handle_supplier_change()) )

    # "New Supplier" Button
    icon_path =  self.resource_path("images/add_supplier.png") 
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    add_supplier_button = QPushButton("New Supplier")
    add_supplier_button.setIcon(icon)  # Assign the icon
    # add_supplier_button.setIconSize(QSize(20, 20))  # Adjust icon size
    add_supplier_button.clicked.connect(self.open_add_supplier_window)

    # Layout arrangement
    order_layout.addWidget(oc_label, 0, 0)
    order_layout.addWidget(self.oc_number_search, 0, 1)
    order_layout.addWidget(search_expense_button, 0, 2)
    order_layout.addWidget(add_expense_button, 0, 3)
    order_layout.addWidget(supplier_label, 1, 0)
    order_layout.addWidget(self.supplier_id_search, 1, 1)
    order_layout.addWidget(search_supplier_button, 1, 2)
    order_layout.addWidget(add_supplier_button, 1, 3)  
    self.create_label_with_help(OCnumber_help_text, order_layout, 0, 4)
    
    order_group.setLayout(order_layout)
    layout.addWidget(order_group)
    
    # Store in dictionary
    printer_entries["oc_number"] = self.oc_number_search
    printer_entries["supplierid"] = self.supplier_id_search
    
    ## --- SECTION 2: TECHNICAL SPECIFICATIONS ---
    tech_group = QGroupBox("Technical Specifications")
    tech_layout = QGridLayout()

    fields = [
        ("Printer Name", "entry", None),
        ("Power", "entry", "W"),
        ("Print Size X", "entry", "mm"),
        ("Print Size Y", "entry", "mm"),
        ("Print Size Z", "entry", "mm"),
        ("Nozzle Size On", "combobox", ["0.25 mm", "0.4 mm", "0.6 mm", "0.8 mm"]),
        ("Status", "combobox", ["Busy", "Planned print", "Free", "NA"]),
        ("Condition", "combobox", ["Working", "Not working", "Under maintenance", "To sell", "Sold"])  ]

    for row, (label_text, field_type, unit) in enumerate(fields):
        label = QLabel(str(label_text + " (*)"))  # Convert label to string explicitly
        tech_layout.addWidget(label, row, 0)
    
        if field_type == "entry":
            widget = QLineEdit()
        elif field_type == "combobox":
            widget = QComboBox()
            widget.addItems(unit)  # `unit` is a list, but correctly used here
   
        tech_layout.addWidget(widget, row, 1)
        printer_entries[label_text.lower().replace(" ", "_")] = widget
    
        if unit and isinstance(unit, str):  # Make sure unit is a string before QLabel
            unit_label = QLabel(unit)
            tech_layout.addWidget(unit_label, row, 2)
        else:
            tech_layout.addWidget(QLabel(""), row, 2)

    tech_group.setLayout(tech_layout)
    layout.addWidget(tech_group)

    ## --- SECTION 3: MAINTENANCE ---
    maintenance_group = QGroupBox("Maintenance")
    maintenance_layout = QGridLayout()

    maintenance_fields = [
        ("Total Hours", "entry", "hours"),
        ("Total Hours After Last Maintenance", "entry", "hours"),
        ("Date Last Maintenance", "date", None) ]

    for row, (label_text, field_type, unit) in enumerate(maintenance_fields):
        label = QLabel(str(label_text))  # Convert label to string explicitly
        maintenance_layout.addWidget(label, row, 0)
    
        if field_type == "entry":
            widget = QLineEdit()
            widget.setText("0")
        elif field_type == "date":
            widget = QDateEdit()
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setCalendarPopup(True)
    
        maintenance_layout.addWidget(widget, row, 1)
        printer_entries[label_text.lower().replace(" ", "_")] = widget
    
        if unit and isinstance(unit, str):  # Make sure unit is a string before QLabel
            unit_label = QLabel(unit)
            maintenance_layout.addWidget(unit_label, row, 2)
        else:
            tech_layout.addWidget(QLabel(""), row, 2)
        
        if label_text == "Date Last Maintenance":
            maintenance_date = "In this section specify, if known, the cumulative operational hours of the printer, the operational hours after last maintenance and the date of the last time full maintenance of the printer was made. Use the notes field if you want to add any remarks on the matter.\nIf the maintenance date is 2000-01-01 it means no last maintenance date was recorded in the database."
            self.create_label_with_help(maintenance_date, maintenance_layout, row, 3)

    maintenance_group.setLayout(maintenance_layout)
    layout.addWidget(maintenance_group)

    ## --- SECTION 4: OTHERS (NOTES) ---
    others_group = QGroupBox("Others")
    others_layout = QGridLayout()

    notes_label = QLabel("Notes")
    notes_entry = QTextEdit()
    notes_entry.setFixedHeight(80)
    image_label = QLabel("Image")
    self.image_label = QLabel("No image selected")
    self.image_label.setStyleSheet("font-style: italic; color: gray;")

    others_layout.addWidget(notes_label, 0, 0)
    others_layout.addWidget(notes_entry, 0, 1,1,3)
    
    others_layout.addWidget(image_label, 1, 0)
    others_layout.addWidget(self.image_label, 1, 1,1,3)

    others_group.setLayout(others_layout)
    layout.addWidget(others_group)

    printer_entries["notes"] = notes_entry

    ## UPDATE STATUS BASED ON CONDITION
    def update_status_based_on_condition():
        selected_condition = printer_entries["condition"].currentText()
        if selected_condition == "Working":
            printer_entries["status"].setEnabled(True)
            printer_entries["status"].clear()
            printer_entries["status"].addItems(["Busy", "Planned print", "Free"])
        else:
            printer_entries["status"].clear()
            printer_entries["status"].addItem("NA")
            printer_entries["status"].setEnabled(False)

    printer_entries["condition"].currentTextChanged.connect(update_status_based_on_condition)

    # === ATTACH PICTURE BUTTON ===
    icon_path = self.resource_path("images/add_picture.png")
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    attach_picture_button = QPushButton("Attach Picture")
    attach_picture_button.setIcon(icon) 
    attach_picture_button.clicked.connect(self.attach_picture)  # Call attach picture function
    layout.addWidget(attach_picture_button)  # Add it above Save/Modify button

    icon_path = self.resource_path("images/save_button.png")
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    ## SAVE / MODIFY BUTTONS
    if modify_printer_flag:
        modify_button = QPushButton("Modify Printer")
        modify_button.setIcon(icon) 
        modify_button.clicked.connect(lambda: self.save_printer(modify_printer_flag=True))
        layout.addWidget(modify_button)
    else:
        save_button = QPushButton("Save New Printer")
        save_button.setIcon(icon) 
        save_button.clicked.connect(self.save_printer)
        layout.addWidget(save_button)
        
    self.printer_entries = printer_entries
    
    #set layout
    scroll_area.setWidget(scroll_content)
    dialog_layout.addWidget(scroll_area)

    window.closeEvent = lambda event: self.close_event(event, window)  
    window.show()
    

#%% ADDING NEW printer
def open_add_printer_window(self):
    # Create a new window for adding a new printer
    self.add_printer_window = QDialog(None)
    self.add_printer_window.setWindowTitle("Add New Printer")
    self.add_printer_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.add_printer_window.resize(500, 600)
        
    # Get the customer entry fields 
    self.printer_widgets(self.add_printer_window)

    # Generate a new ID
    try:
        self.cursor.execute("SELECT MAX(PrinterID) FROM printers;")
        max_printer_id = self.cursor.fetchone()[0]
        self.printer_id = (max_printer_id or 0) + 1  
    except sqlite3.Error as e:
        QMessageBox.critical(self, "Error", f"Failed to generate PrinterID: {e}")
        return
    
#%% SAVE PRINTER
def save_printer(self, modify_printer_flag = False):
    try:
        # Get entries
        entries = self.printer_entries
        values = {
            key: entry.toPlainText() if isinstance(entry, QTextEdit)  # Extract text from QTextEdit
            else entry.text() if isinstance(entry, QLineEdit)  # Extract text from QLineEdit
            else entry.currentText() if isinstance(entry, QComboBox)  # Extract selected text from QComboBox
            else entry.date().toString("yyyy-MM-dd") if isinstance(entry, QDateEdit)  # Extract date from QDateEdit
            else ""  # Default empty string for unknown widget types
            for key, entry in entries.items()   }
        
        # --- Validation ---
        required_fields = ["supplierid", "printer_name", "power", "print_size_x", "print_size_y", "print_size_z", 
                           "nozzle_size_on", "condition", "status"]
    
        for field in required_fields:
            if not values.get(field):
                QMessageBox.critical(self, "Validation Error", "Mandatory fields missing.")
                return
            
        # Validate mandatory numeric fields 
        numeric_fields = ["power", "print_size_x", "print_size_y", "print_size_z", "total_hours", "total_hours_after_last_maintenance"]
        for field in numeric_fields:
            if values[field]:
                try:
                    float(values[field])  # Allow decimals
                except ValueError:
                    QMessageBox.critical(self, "Validation Error", f"'{field.replace('_', ' ').title()}' must be a number.")
                    return
            
        # Validate dropdown fields        
        combobox_fields = ["condition", "status"]        
        for field in combobox_fields:
            # Check if the value is in the options list
            if not (entries[field].currentText() in [entries[field].itemText(i) for i in range(entries[field].count())]):
                QMessageBox.critical(self, "Validation Error", f"Invalid {field.replace('_', ' ').title()} selected.")
                return
           
        data = [values["oc_number"], values["supplierid"], values["printer_name"], values["power"],
                values["print_size_x"], values["print_size_y"], values["print_size_z"],
                values["condition"], values["condition"], values["status"],
                values["total_hours"], values["total_hours_after_last_maintenance"], 
                values["date_last_maintenance"], values["notes"]] 
       
        if modify_printer_flag == False:
            # Insert new printer into the database
            self.cursor.execute('''INSERT INTO printers (OCnumber, SupplierID, PrinterName, Power, PrintSizeX, PrintSizeY, PrintSizeZ,
                                    NozzleSizeOn, Condition, Status, TotalHours, TotalHoursAfterLastMaintenance,
                                    DateLastMaintenance, Notes)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',  tuple(data) )
            self.connection.commit()
                
            QMessageBox.information(self,  "Success", "New printer added successfully!")
            self.add_printer_window.destroy()  # Close add printer window
        elif modify_printer_flag == True:
            self.cursor.execute('''UPDATE printers
                                SET OCnumber=?, SupplierID=?, PrinterName=?, Power=?, PrintSizeX=?, PrintSizeY=?, PrintSizeZ=?,
                                    NozzleSizeOn=?, Condition=?, Status=?, TotalHours=?, TotalHoursAfterLastMaintenance=?,
                                    DateLastMaintenance=?, Notes=?
                                WHERE PrinterID=?''',
                                (tuple(data) + (self.printer_id,)))
            self.connection.commit()
            
            QMessageBox.information(self, "Success", "Printer details updated successfully!")
            self.modify_printer_window.destroy()  # Close modify printer window
            
        # If a picture was selected, attach it to the db
        if hasattr(self, 'selected_image_path'):
            # The variable exists and a picture has been selected
            if os.path.exists(self.selected_image_path):
                try:
                    self.cursor.execute(""" UPDATE printers SET Picture = ? WHERE PrinterID = ?""", (self.empPhoto, self.printer_id))
                    self.connection.commit() 
                    
                    # reset pic path
                    del self.empPhoto, self.selected_image_path
    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to read picture: {e}")
                    return
            else:
                QMessageBox.critical(self, "Error", "Selected picture path does not exist.")
                return
            
        self.show_table("printers")  # Refresh the printers table view
        self.handle_printers_window.destroy()
    except ValueError as e:
        QMessageBox.critical(None, "Input Error", str(e))
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to add/update printer: {e}")
    
    
#%% MODIFY PRINTER   
def open_modify_printer_window(self):
    # Ask for ID to modify
    self.modify_printer_window = QDialog(None)
    self.modify_printer_window.setWindowTitle("Modify Printer")
    self.modify_printer_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.modify_printer_window.resize(500, 600)
    
    # Get the entry fields 
    self.printer_widgets(self.modify_printer_window, modify_printer_flag = True)

#%% REMOVE PRINTER
def open_remove_printer_window(self):
    self.remove_printer_window = QDialog(None)
    self.remove_printer_window.setWindowTitle("Remove Printer")
    self.remove_printer_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.remove_printer_window.resize(300, 200)

    layout = QVBoxLayout()
    
    def remove_printer(printer_id):
        # Remove customer logic
        try:
            self.cursor.execute("DELETE FROM printers WHERE PrinterID = ?", (printer_id,))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Printer removed successfully")
            self.show_table("printers")  # Refresh the customers table view
            self.handle_printers_window.destroy()  # Close handle customer window
            self.remove_printer_window.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to remove printer: {e}")
            
    def fetch_printer_to_remove():
        # Fetch the customer to be removed and show confirmation
        printer_id = self.remove_printer_id_entry.text()
        if printer_id:
            try:
                self.cursor.execute("SELECT PrinterName FROM printers WHERE PrinterID = ?", (printer_id,))
                printer = self.cursor.fetchone()

                if printer:
                    confirmation = QMessageBox.question(
                        self, "Confirm Deletion",
                        f"Are you sure you want to delete printer {printer[0]} with PrinterID {printer_id}?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if confirmation == QMessageBox.Yes:
                        remove_printer(printer_id)
                else:
                    QMessageBox.warning(self, "Printer Not Found", "No printer found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch printer data: {e}")
    
    # Specify ID, fetch it and remove it
    label = QLabel("Printer ID to Remove:")
    self.remove_printer_id_entry = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(self.remove_printer_id_entry)
    
    # Button to open selection table
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("printers", self.remove_printer_id_entry))
    layout.addWidget(search_button)
    
    fetch_button = QPushButton("Remove Printer")
    fetch_button.clicked.connect(fetch_printer_to_remove)
    layout.addWidget(fetch_button)
    
    self.remove_printer_window.setLayout(layout)
    self.remove_printer_window.show()
    
  
#%%##########################################################################################################################################
#############################################################################################################################################   
############################################################################################################################################# 
#############################################################################################################################################

#%% FILAMENTS INVENTORY
def open_handle_filaments_window(self):
    # Open a new window for filament modifications]
    self.handle_filaments_window = QDialog(self)
    self.handle_filaments_window.setWindowTitle("Handle Filaments")
    self.handle_filaments_window.resize(300, 200)
    
    layout = QVBoxLayout()

    # See Filaments button
    see_filaments_button = QPushButton("See Filaments")
    def _show_and_wire_filaments():
        # 1) populate the table
        self.show_table("filaments")
        # 2) remove any old handler
        try:
            self.table.cellDoubleClicked.disconnect()
        except TypeError:
            pass
        # 3) wire the new handler
        self.table.cellDoubleClicked.connect(self._on_filament_doubleclick)

    see_filaments_button.clicked.connect(_show_and_wire_filaments)
    layout.addWidget(see_filaments_button)

    # Add New Filament button
    add_filament_button = QPushButton("Add New Filament")
    add_filament_button.clicked.connect(self.open_add_filament_window)
    layout.addWidget(add_filament_button)

    # Modify Filament button
    modify_filament_button = QPushButton("Modify Filament")
    modify_filament_button.clicked.connect(self.open_modify_filament_window)
    layout.addWidget(modify_filament_button)

    # Remove Filament button
    remove_filament_button = QPushButton("Remove Filament")
    remove_filament_button.clicked.connect(self.open_remove_filament_window)
    layout.addWidget(remove_filament_button)
    
    self.handle_filaments_window.setLayout(layout)
    self.handle_filaments_window.show()
    
def _on_filament_doubleclick(self, row, col):
    # 1) grab the CustomerID from column 0
    fila_id = self.table.item(row, 0).text()
    if not fila_id:
        return

    # 2) open the Modify Customer window (this creates self.modify_customer_id_entry)
    self.open_modify_filament_window()

    # 3) now fill that dialog’s ID-entry with your selected ID
    self.modify_filament_id_entry.setText(fila_id)
    # now immediately fetch & populate all other fields
    self.fetch_filament_to_modify()
    
#%% functions for filaments
# This function calculates the price per gram of the filament, if the expense and quantity are specified. Also the SupplierID is filled in if the expense is given.
def update_price(self, price_widget):
    # Find 
    selected_expense_id = self.filament_entries["oc_number"].text().strip()
    # Auto-calculate Price Per Gram
    try:
        self.cursor.execute("SELECT CostIncBTW FROM expenses WHERE OCnumber = ?", (selected_expense_id,))
        cost = self.cursor.fetchone()
        if cost and cost[0]:
            cost_value = cost[0]
            try:
                grams = float(self.filament_entries["grams_per_roll"].text() or 0)
                quantity = float(self.filament_entries["quantity_order"].text() or 0)

                if grams > 0 and quantity > 0:
                    total_grams = grams * quantity
                    price_per_gram = cost_value / total_grams
                    price_widget.setText(f"{price_per_gram:.4f}")
                else:
                    price_widget.setText("Invalid Grams/Qty")
            except ValueError:
                price_widget.setText("Invalid Input")
        else:
            price_widget.setText("No Cost Found")
    except sqlite3.Error as e:
        print(f"Database error (PricePerGram): {e}")
        self.filament_entries["price_per_gram"].setReadOnly(False)

# Send a reminder via email to restock a specific filament
def restock_filament(self):
    recipient = "info@3beeprinting.com"

    subject = "Need to restock filament" 
    
    try:
        # Writing email body
        supplier_id = self.filament_entries["supplierid"].text()
        
        self.cursor.execute("SELECT Company, Website FROM suppliers WHERE SupplierID = ?", (supplier_id,))
        result = self.cursor.fetchone()
        
        if not result:
            QMessageBox.warning(self, "Supplier Not Found", f"No supplier found with ID {supplier_id}.")
            return     
        supplier_name, supplier_website = result

        body = f"""Let's restock filament: {self.filament_entries["filament_name"].text()}!

Currently only {self.filament_entries["quantity_in_stock"].text()} are in stock according to the database.

Details:
    • Material: {self.filament_entries["material"].currentText()}
    • Color: {self.filament_entries["color"].text()}
    • Supplier: {supplier_name} (ID {supplier_id})
    • Website: {supplier_website}
"""

        lastsupply = self.filament_entries["oc_number"].text()
        if lastsupply != "NA": # if string not empty
            self.cursor.execute("SELECT DateOrdered, Link, CostIncBTW, CostShipping FROM expenses WHERE OCnumber = ?", (lastsupply,))
            date_lastsupply, link_lastsupply, costincbtw_lastsupply, shipcost_lastsupply = self.cursor.fetchone()
            body = body +f"""
    • Last supply had OCnumber {lastsupply}, was ordered on {date_lastsupply} at {link_lastsupply} (cost: {costincbtw_lastsupply} € + shipping {shipcost_lastsupply} €) """
        else:
            body = body + """
    • No data about last supply found in the database."""

    
        outlook = win32.Dispatch('outlook.application') # Connect to Outlook
        mail = outlook.CreateItem(0)  # Create a new email

        # Set recipient, subject, and body
        mail.To = recipient
        mail.Subject = subject
        mail.Body = body
        
        mail.Display()  # Opens the email window in Outlook for editing

        print("Email created successfully in Outlook.")
    except Exception as e:
        print(f"An error occurred in creating restock email: {e}")

# Get list of filament properties from the checkboxes
def get_selected_properties(self):
    selected_properties = [service for service, var in self.prop_vars.items() if var.get()]
    return ", ".join(selected_properties)

## Function to fetch printer from database and fill in all data
def fetch_filament_to_modify(self):
    filament_id = self.modify_printer_id_entry.text()
    self.filament_id = filament_id
    
    # check suppliers and expenses exist
    self.cursor.execute("SELECT SupplierID FROM suppliers")
    suppliers = self.cursor.fetchall()
    supplier_list = [x[0] for x in suppliers]
    self.cursor.execute("SELECT OCnumber FROM expenses")
    expenses = self.cursor.fetchall()
    expenses_list = [x[0] for x in expenses]
    
    if filament_id:
        try:
            self.cursor.execute("SELECT * FROM filaments WHERE FilamentID = ?", (self.filament_id,))
            filament = self.cursor.fetchone()
            if filament:
                # Assuming the DB columns are in correct order and match your keys
                # Skip FilamentID (index 0)
                keys = ["oc_number", "supplierid", "filament_name", "material", "color",
                    "quantity_order", "quantity_in_stock", "grams_per_roll", "price_per_gram",
                    "nozzle_temperature", "bed_temperature", "properties", "notes", "picture" ]
                notes_addition = ''
                for key, value in zip(keys, filament[1:]):
                    if key in self.filament_entries:
                        entry = self.filament_entries[key]

                        if isinstance(entry, QLineEdit):
                            if key == 'notes':
                                value = value + notes_addition
                                
                            if key == 'oc_number': 
                                if value in expenses_list:
                                    entry.setText(str(value))
                                else:
                                    incorrect_info_flag = True
                            elif key == 'supplierid':
                                if value in supplier_list:
                                    entry.setText(str(value))
                                else:
                                    incorrect_info_flag = True
                            elif key in ["quantity_order", "quantity_in_stock", "grams_per_roll", "price_per_gram", "nozzle_temperature", "bed_temperature"] and value!= "":
                                try: # check its a number, otherwise remove
                                    entry.setText(str(float(value)))
                                except ValueError:
                                    incorrect_info_flag = True
                            else:
                                entry.setText(str(value) if value is not None else "")
                        
                        elif isinstance(entry, QTextEdit):
                            entry.setPlainText(str(value) if value is not None else "")
                            
                        elif isinstance(entry, QComboBox):
                            text = str(value) if value is not None else "NA"
                            entry.setEditable(True)
                            
                            index = entry.findText(text)
                            if index != -1:
                                entry.setCurrentIndex(index)
                            else:
                                entry.setEditText(text)  # Show custom value not in list
                        elif key == "properties" and isinstance(entry, dict):
                            # Reset all first
                            for cb in entry.values():
                                cb.setChecked(False)
                            # Check relevant ones
                            if value:
                                for prop in value.split(','):
                                    prop = prop.strip()
                                    if prop in entry:
                                        entry[prop].setChecked(True)
                                        value_new = value.replace(prop, '')
                                    else:
                                        notes_addition = f'\nNB: These properties are not within the checkboxes options: {value_new}.'

                # Image handling
                if filament[-1]:  # Assuming last field is 'picture'
                    self.image_label.setText("Image exists in database. If you attach a new picture, the old one will be lost.")
                    self.image_label.setStyleSheet("font-style: italic; color: gray;")
                else:
                    self.image_label.setText("No image on database for this ID.")
                    self.image_label.setStyleSheet("font-style: italic; color: gray;")
            else:
                QMessageBox.warning(self, "Filament Not Found", "No filament found with the given ID.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch filament data: {e}")

    # If data inputted were not ok, say it here with a warning message
    if incorrect_info_flag:
        QMessageBox.warning(None, "Data format/content warning", "Some values fetched in the database for this ID are incorrect. They are automatically removed and set to default in this form.")


#%% FILAMENT WIDGETS
def filament_widgets(self, window, modify_filament_flag=False):
    # make it scrollable in case resizing needed
    dialog_layout = QVBoxLayout(window)## Main layout
    
    scroll_area = QScrollArea(window) #scroll area
    scroll_area.setWidgetResizable(True)
    
    # Content inside scroll
    scroll_content = QWidget()
    layout = QVBoxLayout(scroll_content)



    ## MODIFY FILAMENT - ID SELECTION
    if modify_filament_flag:
        modify_layout = QHBoxLayout()
        label = QLabel("Filament ID to Modify:")
        self.modify_printer_id_entry = QLineEdit()
        search_button = QPushButton("Search Table")
        search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("filaments", self.modify_printer_id_entry))
        fetch_button = QPushButton("Fetch Filament")
        fetch_button.clicked.connect(self.fetch_filament_to_modify)

        modify_layout.addWidget(label)
        modify_layout.addWidget(self.modify_printer_id_entry)
        modify_layout.addWidget(search_button)
        modify_layout.addWidget(fetch_button)
        layout.addLayout(modify_layout)
        
    self.filament_entries = {} #list of all widgets
    ## --- SECTION 1: ORDER DETAILS ---
    order_group = QGroupBox("Order Details")
    order_layout = QGridLayout()
    
    # Called when supplier is selected directly
    def handle_supplier_change():
        self.oc_number_search.setText("NA")
        self.supplier_id_search.setEnabled(True)

    oc_label = QLabel("OC Number")
    self.oc_number_search = QLineEdit()
    self.oc_number_search.setReadOnly(True)
    
    # "Search Expense" Button
    search_expense_button = QPushButton("Search Expense")
    search_expense_button.setIcon(QIcon( self.resource_path("images/search_expense.png") ))  # Optional: icon
    # search_expense_button.setIconSize(QSize(20, 20))
    search_expense_button.clicked.connect( lambda: (self.open_modifyfromtable_selection("expenses", self.oc_number_search, fillin_supplier = True)) )
    
    # "New Expense" Button
    icon_path = self.resource_path("images/add_expense.png") 
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    add_expense_button = QPushButton("New Expense")
    add_expense_button.setIcon(icon)  # Assign the icon
    # add_expense_button.setIconSize(QSize(20, 20))  # Adjust icon size
    add_expense_button.clicked.connect(self.open_add_expense_window)
    
    OCnumber_help_text = "The OCnumber of the latest expense for this filament must be filled in, if any. Notice that this will affect the calculation of the Price Per Gram.\nThe SupplierID is automatically filled from the value in the expenses database. If you want to manually select a SupplierID, the OCnumber will be disconnected automatically."
    
    supplier_label = QLabel("Supplier ID (*)")
    self.supplier_id_search = QLineEdit()
    self.supplier_id_search.setReadOnly(True)

    search_supplier_button = QPushButton("Search Supplier")
    search_supplier_button.setIcon(QIcon( self.resource_path("images/search_supplier.png") ))  # Optional: icon
    # search_supplier_button.setIconSize(QSize(20, 20))
    search_supplier_button.clicked.connect( lambda: (self.open_modifyfromtable_selection("suppliers", self.supplier_id_search), handle_supplier_change()) )

    # "New Supplier" Button
    icon_path = self.resource_path("images/add_supplier.png") 
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    add_supplier_button = QPushButton("New Supplier")
    add_supplier_button.setIcon(icon)  # Assign the icon
    # add_supplier_button.setIconSize(QSize(20, 20))  # Adjust icon size
    add_supplier_button.clicked.connect(self.open_add_supplier_window)

    # Layout arrangement
    order_layout.addWidget(oc_label, 0, 0)
    order_layout.addWidget(self.oc_number_search, 0, 1)
    order_layout.addWidget(search_expense_button, 0, 2)
    order_layout.addWidget(add_expense_button, 0, 3)
    order_layout.addWidget(supplier_label, 1, 0)
    order_layout.addWidget(self.supplier_id_search, 1, 1)
    order_layout.addWidget(search_supplier_button, 1, 2)
    order_layout.addWidget(add_supplier_button, 1, 3)  
    self.create_label_with_help(OCnumber_help_text, order_layout, 0, 4)
    
    order_group.setLayout(order_layout)
    layout.addWidget(order_group)
    
    # Store in dictionary
    self.filament_entries["oc_number"] = self.oc_number_search
    self.filament_entries["supplierid"] = self.supplier_id_search

    ## --- SECTION 2: TECHNICAL SPECIFICATIONS ---
    tech_group = QGroupBox("Technical Specifications")
    tech_layout = QGridLayout()

    filamentname_label = QLabel("Filament Name (*)")
    material_label = QLabel("Material (*)")
    color_label = QLabel("Color (*)")
    quantityord_label = QLabel("Quantity Order")
    rolls_unit = QLabel("rolls")
    quantitystock_label = QLabel("Quantity In Stock (*)")
    rolls_unit2 = QLabel("rolls")
    grams_label = QLabel("Grams Per Roll (*)")
    grams_unit = QLabel("g/roll")
    price_label = QLabel("Price Per Gram (*)")
    price_unit = QLabel("€/g")

    filamentname_entry = QLineEdit()
    material_entry = QComboBox()
    material_entry.setEditable(True)
    material_entry.addItems(["PLA", "ASA", "ABS", "PETG", "FLEXIBLE"])
    color_entry = QLineEdit()
    quantityord_entry = QLineEdit()
    quantitystock_entry = QLineEdit()
    grams_entry = QLineEdit()
    price_entry = QLineEdit()
    
    # Connect to update function on text change
    quantityord_entry.textChanged.connect(lambda: self.update_price(price_entry))
    grams_entry.textChanged.connect(lambda: self.update_price(price_entry))

    
    self.filament_entries["filament_name"] = filamentname_entry
    self.filament_entries["material"] = material_entry
    self.filament_entries["color"] = color_entry
    self.filament_entries["quantity_order"] = quantityord_entry
    self.filament_entries["quantity_in_stock"] = quantitystock_entry
    self.filament_entries["grams_per_roll"] = grams_entry
    self.filament_entries["price_per_gram"] = price_entry
    
    # "Restock button" Button
    icon_path = self.resource_path("images/email.png") 
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon

    # Create the button with icon
    restock_button = QPushButton("Restock reminder")
    restock_button.setIcon(icon)  # Assign the icon
    restock_button.setIconSize(QSize(20, 20))  # Adjust icon size
    restock_button.clicked.connect(self.restock_filament)

    tech_layout.addWidget(filamentname_label, 0, 0)
    tech_layout.addWidget(filamentname_entry, 0, 1, 1, 3)
    tech_layout.addWidget(material_label, 1, 0)
    tech_layout.addWidget(material_entry, 1, 1)
    tech_layout.addWidget(color_label, 1, 2)
    tech_layout.addWidget(color_entry, 1, 3)

    tech_layout.addWidget(quantityord_label, 2, 0)
    tech_layout.addWidget(quantityord_entry, 2, 1)
    tech_layout.addWidget(rolls_unit, 2, 2)
    tech_layout.addWidget(quantitystock_label, 3, 0)
    tech_layout.addWidget(quantitystock_entry, 3, 1)
    tech_layout.addWidget(rolls_unit2, 3, 2)
    tech_layout.addWidget(restock_button, 3, 3)

    tech_layout.addWidget(grams_label, 4, 0)
    tech_layout.addWidget(grams_entry, 4, 1)
    tech_layout.addWidget(grams_unit, 4, 2)

    tech_layout.addWidget(price_label, 5, 0)
    tech_layout.addWidget(price_entry, 5, 1)
    tech_layout.addWidget(price_unit, 5, 2)
    pricefilament_help_text = "The filament Price Per Gram is calculated from the cost declared on expenses, using: OCnumber, Quantity Order and Grams Per Roll.\nYou can also modify it or input it manually. Overwrite the value and fill in at least the mandatory fields."
    self.create_label_with_help(pricefilament_help_text, tech_layout, 5, 3)


    tech_group.setLayout(tech_layout)
    layout.addWidget(tech_group)

    ## --- SECTION 3: MATERIAL SPECIFICATIONS ---
    material_group = QGroupBox("Material Specifications")
    material_layout = QGridLayout()

    # Nozzle Temperature
    nozzle_temp_label = QLabel("Nozzle Temperature")
    nozzle_temp_entry = QLineEdit()
    nozzle_temp_unit = QLabel("°C")

    material_layout.addWidget(nozzle_temp_label, 0, 0)
    material_layout.addWidget(nozzle_temp_entry, 0, 1)
    material_layout.addWidget(nozzle_temp_unit, 0, 2)

    # Bed Temperature
    bed_temp_label = QLabel("Bed Temperature")
    bed_temp_entry = QLineEdit()
    bed_temp_unit = QLabel("°C")

    material_layout.addWidget(bed_temp_label, 1, 0)
    material_layout.addWidget(bed_temp_entry, 1, 1)
    material_layout.addWidget(bed_temp_unit, 1, 2)

    # Properties Section (CheckBoxes)
    properties_label = QLabel("Properties")
    properties_layout = QGridLayout()  # Use grid for 2 rows x 2 cols
    
    self.prop_vars = {
        "Flexible": QCheckBox("Flexible"),
        "Impact resistant": QCheckBox("Impact Resistant"),
        "High strength": QCheckBox("High Strength"),
        "Durable": QCheckBox("Durable"),
    }
    
    # Add checkboxes to grid layout: 2 per row
    row, col = 0, 0
    for i, checkbox in enumerate(self.prop_vars.values()):
        properties_layout.addWidget(checkbox, row, col)
        col += 1
        if col > 1:
            col = 0
            row += 1
    
    # Add label and grid layout to main layout
    material_layout.addWidget(properties_label, 2, 0, Qt.AlignTop)
    material_layout.addLayout(properties_layout, 2, 1, 1, 2)  # spans 2 columns


    # Set Layout & Add to Main Window
    material_group.setLayout(material_layout)
    layout.addWidget(material_group)

    # Store all entries in self.filament_entries
    self.filament_entries["nozzle_temperature"] = nozzle_temp_entry
    self.filament_entries["bed_temperature"] = bed_temp_entry
    self.filament_entries["properties"] = self.prop_vars  # Store checkboxes as a dictionary

    ## --- SECTION 4: OTHERS (NOTES) ---
    others_group = QGroupBox("Others")
    others_layout = QVBoxLayout()

    notes_label = QLabel("Notes")
    notes_entry = QTextEdit()
    notes_entry.setFixedHeight(80)
    image_label = QLabel("Image")
    self.image_label = QLabel("No image selected")
    self.image_label.setStyleSheet("font-style: italic; color: gray;")

    others_layout.addWidget(notes_label)
    others_layout.addWidget(notes_entry)

    others_layout.addWidget(image_label)
    others_layout.addWidget(self.image_label)

    others_group.setLayout(others_layout)
    layout.addWidget(others_group)

    self.filament_entries["notes"] = notes_entry

    # === ATTACH PICTURE BUTTON ===
    icon_path = self.resource_path("images/add_picture.png") 
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    attach_picture_button = QPushButton("Attach Picture")
    attach_picture_button.setIcon(icon) 
    attach_picture_button.clicked.connect(self.attach_picture)  # Call attach picture function
    layout.addWidget(attach_picture_button)  # Add it above Save/Modify button

    icon_path = self.resource_path("images/save_button.png") 
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    ## SAVE / MODIFY BUTTONS
    if modify_filament_flag:
        modify_button = QPushButton("Modify Filament")
        modify_button.setIcon(icon) 
        modify_button.clicked.connect(lambda: self.save_filament(modify_filament_flag=True))
        layout.addWidget(modify_button)
    else:
        save_button = QPushButton("Save New Filament")
        save_button.setIcon(icon) 
        save_button.clicked.connect(self.save_filament)
        layout.addWidget(save_button)
        
    #set layout
    scroll_area.setWidget(scroll_content)
    dialog_layout.addWidget(scroll_area)

    window.closeEvent = lambda event: self.close_event(event, window)  
    window.show()

    
  
#%% ADD NEW FILAMENT
def open_add_filament_window(self):
    # Create a new window for adding a new filament
    self.add_filament_window = QDialog(None)
    self.add_filament_window.setWindowTitle("Add New Filament")
    self.add_filament_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.add_filament_window.resize(500, 600)
    
    # Generate a new filamentID - needed for image uploading
    self.cursor.execute("SELECT MAX(FilamentID) FROM filaments;")
    max_filament_id = self.cursor.fetchone()[0]
    self.filament_id = (max_filament_id or 0) + 1  
        
    # Get the entry fields 
    self.filament_widgets(self.add_filament_window)
    

#%% SAVE FILAMENTS TO DATABASE
def save_filament(self, modify_filament_flag = False):
    try:
        # Collect filament details from entries/widgets
        entries = self.filament_entries

        # Extract values from widgets
        values = {
            key: entry.toPlainText() if isinstance(entry, QTextEdit)
            else entry.text() if isinstance(entry, QLineEdit)
            else entry.currentText() if isinstance(entry, QComboBox)
            else "" for key, entry in entries.items()    }
        
        # Convert properties (checkbox dict) into comma-separated string
        values["properties"] = self.separate_checkbox_values(entries["properties"])
            
        # Mandatory fields validation
        mandatory_fields = ["filament_name", "material", "color",  "price_per_gram", "quantity_in_stock", "grams_per_roll"]
        for field in mandatory_fields:
            if not values.get(field):
                QMessageBox.critical(self, "Validation Error", f"'{field.replace('_', ' ').title()}' is required.")
                return
        # Numeric fields validation (accept floats where appropriate)
        numeric_fields = ["quantity_order", "quantity_in_stock", "grams_per_roll", "price_per_gram", "nozzle_temperature", "bed_temperature"]
        for field in numeric_fields:
            if values[field]:
                try:
                    float(values[field])
                except ValueError:
                    QMessageBox.critical(self, "Validation Error", f"'{field.replace('_', ' ').title()}' must be a number.")
                    return

        # Prepare SQL data
        data = [values["oc_number"], values["supplierid"], values["filament_name"], values["material"], values["color"],
                values["quantity_order"], values["quantity_in_stock"], values["grams_per_roll"], values["price_per_gram"],
                values["nozzle_temperature"], values["bed_temperature"], values["properties"], values["notes"]]

    
        if modify_filament_flag:
            # Update existing filament
            self.cursor.execute('''UPDATE filaments
                                   SET OCnumber = ?, SupplierID = ?, FilamentName = ?, Material = ?, Color = ?, QuantityOrder = ?,
                                       QuantityInStock = ?, GramsPerRoll =?, PricePerGram = ?, NozzleTemperature =?, BedTemperature =?, 
                                       Properties =?, Notes = ?
                                   WHERE FilamentID = ?''',
                                tuple(data + [self.filament_id]))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Filament details updated successfully!")
            self.modify_filament_window.destroy()
    
        else:
            # Insert new filament
            self.cursor.execute('''INSERT INTO filaments (OCnumber, SupplierID, FilamentName, Material, Color, QuantityOrder, 
                                                            QuantityInStock, GramsPerRoll, PricePerGram, NozzleTemperature, BedTemperature, 
                                                            Properties, Notes)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                tuple(data))
            self.connection.commit()
            QMessageBox.information(self, "Success", "New filament added successfully!")
            self.add_filament_window.destroy()
    
        # --- Handle image attachment ---
        if hasattr(self, 'selected_image_path'):
            if os.path.exists(self.selected_image_path):
                try:
                    with open(self.selected_image_path, 'rb') as f:
                        image_data = f.read()
                    self.cursor.execute("UPDATE filaments SET Picture=? WHERE FilamentID=?", (image_data, self.filament_id))
                    self.connection.commit()
                    del self.selected_image_path  # Clear after use
                except Exception as e:
                    QMessageBox.critical(self, "Image Error", f"Failed to attach image: {e}")
                    return
            else:
                QMessageBox.critical(self, "Image Error", "Selected image path does not exist.")
                return

        self.show_table("filaments")  # Refresh table
        self.handle_filaments_window.destroy()

    except sqlite3.Error as e:
        QMessageBox.critical(self, "Database Error", f"Failed to save filament: {e}")
      

#%% MODIFY EXISTING FILAMENT
def open_modify_filament_window(self):
    # Create a new window for modifying an existing filament
    self.modify_filament_window = QDialog(None)
    self.modify_filament_window.setWindowTitle("Modify Filament")
    self.modify_filament_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.modify_filament_window.resize(500, 600)
    
    # Get the entry fields 
    self.filament_widgets(self.modify_filament_window, modify_filament_flag = True)
   
    
#%% REMOVE FILAMENT 
def open_remove_filament_window(self):
    self.remove_filament_window = QDialog(None)
    self.remove_filament_window.setWindowTitle("Remove Filament")
    self.remove_filament_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.remove_filament_window.resize(300, 200)

    layout = QVBoxLayout()
    
    def remove_filament(filament_id):
        try:
            self.cursor.execute("DELETE FROM filaments WHERE FilamentID = ?", (filament_id,))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Filament removed successfully")
            self.show_table("filaments")  # Refresh the filaments table view
            self.handle_filaments_window.destroy()  # Close handle filament window
            self.remove_filament_window.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(self,"Error", f"Failed to remove filament: {e}")
            
    def fetch_filament_to_remove():
        # Fetch the filament to be removed and show confirmation
        filament_id = self.remove_filament_id_entry.text()
        if filament_id:
            try:
                self.cursor.execute("SELECT FilamentName FROM filaments WHERE FilamentID = ?", (filament_id,))
                filament = self.cursor.fetchone()

                if filament:
                    confirmation = QMessageBox.question(
                        self, "Confirm Deletion",
                        f"Are you sure you want to delete filament {filament[0]} with FilamentID {filament_id}?")
                    if confirmation == QMessageBox.Yes:
                        remove_filament(filament_id)
                else:
                    QMessageBox.warning(self, "Filament Not Found", "No filament found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch filament data: {e}")
   
    # Specify ID, fetch it and remove it
    label = QLabel("Filament ID to Remove:")
    self.remove_filament_id_entry = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(self.remove_filament_id_entry)
    
    # Button to open selection table
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("filaments", self.remove_filament_id_entry))
    layout.addWidget(search_button)
    
    fetch_button = QPushButton("Remove Filament")
    fetch_button.clicked.connect(fetch_filament_to_remove)
    layout.addWidget(fetch_button)
    
    self.remove_filament_window.setLayout(layout)
    self.remove_filament_window.show()
    
    
                    