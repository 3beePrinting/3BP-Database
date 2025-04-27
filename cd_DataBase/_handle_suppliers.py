# -*- coding: utf-8 -*-
"""
Handling suppliers window: add, modify, remove

@author: feder
"""

import sqlite3
from PyQt5.QtWidgets import ( 
    QVBoxLayout, QGroupBox, QGridLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QMessageBox, QDialog  
    )
from PyQt5.QtGui import QIcon

def open_handle_suppliers_window(self):
    # Open a new window for supplier modifications
    self.handle_supplier_window = QDialog(self)
    self.handle_supplier_window.setWindowTitle("Handle Suppliers")
    self.handle_supplier_window.resize(300, 200)
    
    layout = QVBoxLayout()

    # See supplier button
    see_supplier_button = QPushButton("See Suppliers")
    see_supplier_button.clicked.connect(lambda: self.show_table("suppliers"))
    layout.addWidget(see_supplier_button)

    # Add New supplier button
    add_supplier_button = QPushButton("Add New Supplier")
    add_supplier_button.clicked.connect(self.open_add_supplier_window)
    layout.addWidget(add_supplier_button)

    # Modify supplier button
    modify_supplier_button = QPushButton("Modify Supplier")
    modify_supplier_button.clicked.connect(self.open_modify_supplier_window)
    layout.addWidget(modify_supplier_button)

    # Remove supplier button
    remove_supplier_button = QPushButton("Remove Supplier")
    remove_supplier_button.clicked.connect(self.open_remove_supplier_window)
    layout.addWidget(remove_supplier_button)
    
    self.handle_supplier_window.setLayout(layout)
    self.handle_supplier_window.show()
    
#%% WIDGET    
def supplier_widget(self, window, modify_supplier_flag=False):
    layout = QVBoxLayout()

    ## Function to fetch supplier from database and fill in all data
    def fetch_supplier_to_modify():
        supplier_id = self.modify_supplier_id_entry.text()
        if supplier_id:
            try:
                self.cursor.execute("SELECT * FROM suppliers WHERE SupplierID = ?", (supplier_id,))
                supplier = self.cursor.fetchone()
                if supplier:
                    for i, (key, entry) in enumerate(self.entries_supplier.items(), start=1):
                        value = str(supplier[i])
                        if isinstance(entry, QComboBox):
                            if value in [entry.itemText(j) for j in range(entry.count())]:
                                entry.setCurrentText(value)
                            else:
                                if key == 'products':
                                    entry.setCurrentText('Others')
                        else:
                            entry.setText(value)  # For normal text fields
                else:
                    QMessageBox.warning(self, "Supplier Not Found", "No supplier found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch supplier data: {e}")

    if modify_supplier_flag:  # MODIFY SUPPLIER
        modify_layout = QHBoxLayout()
        label = QLabel("Supplier ID to Modify:")
        self.modify_supplier_id_entry = QLineEdit()
        self.modify_supplier_id_entry.setReadOnly(True)
        search_button = QPushButton("Search Table")
        search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("suppliers", self.modify_supplier_id_entry))
        fetch_button = QPushButton("Fetch Supplier")
        fetch_button.clicked.connect(fetch_supplier_to_modify)

        modify_layout.addWidget(label)
        modify_layout.addWidget(self.modify_supplier_id_entry)
        modify_layout.addWidget(search_button)
        modify_layout.addWidget(fetch_button)
        layout.addLayout(modify_layout)

    # Dictionary to store entry fields
    entries_supplier = {}

    ## --- SECTION 1: GENERAL INFORMATION ---
    general_group = QGroupBox("General Information")
    general_layout = QGridLayout()

    general_labels = ["Company", "Website", "Description", "Products", "Company Email", "Company Phone"]
    for i, label in enumerate(general_labels):
        label_widget = QLabel(label + " (*)" if label in ["Company", "Website", "Description", "Products", "Company Email"] else label)
        entry = QComboBox() if label == "Products" else QLineEdit()
        if label == "Products":
            entry.addItems(["Shipping", "Materials and tools", "Filaments", "Printers and parts", "Marketing", "Office provider", "Others"])

        general_layout.addWidget(label_widget, i // 2, (i % 2) * 2)  # Row alternates, columns shift by 2
        general_layout.addWidget(entry, i // 2, (i % 2) * 2 + 1)
        entries_supplier[label.lower().replace(" ", "_")] = entry

    general_group.setLayout(general_layout)
    layout.addWidget(general_group)

    ## --- SECTION 2: CONTACT INFORMATION ---
    contact_group = QGroupBox("Contact Information")
    contact_layout = QGridLayout()

    contact_labels = ["Contact Name", "Contact Email", "Contact Phone", "Address", "ZIP Code", "City", "Country"]
    for i, label in enumerate(contact_labels):
        if label == "Country":
            label_widget = QLabel("Country (*)")
        else:
            label_widget = QLabel(label)
        entry = QLineEdit()

        if label == "Contact Name":  # First row alone
            contact_layout.addWidget(label_widget, 0, 0)
            contact_layout.addWidget(entry, 0, 1, 1, 3)  # Spans all columns
        else:  # Remaining 2 by 2 layout
            contact_layout.addWidget(label_widget, (i+1) // 2, ((i-1) % 2) * 2)  
            contact_layout.addWidget(entry, (i+1) // 2, ((i-1) % 2) * 2 + 1)

        entries_supplier[label.lower().replace(" ", "_")] = entry

    contact_group.setLayout(contact_layout)
    layout.addWidget(contact_group)

    ## --- SECTION 3: OTHERS ---
    others_group = QGroupBox("Others")
    others_layout = QGridLayout()

    notes_label = QLabel("Notes")
    notes_entry = QTextEdit()
    notes_entry.setFixedHeight(80)

    experience_label = QLabel("Experience")
    self.experiencesuppl_combobox = QComboBox()
    self.experiencesuppl_combobox.addItems(["Very Positive", "Positive", "Neutral", "Negative"])
    self.experiencesuppl_combobox.setCurrentText("Neutral")

    others_layout.addWidget(notes_label,0,0)
    others_layout.addWidget(notes_entry,0,1,1,3)
    others_layout.addWidget(experience_label,1,0)
    others_layout.addWidget(self.experiencesuppl_combobox,1,1,1,3)

    others_group.setLayout(others_layout)
    layout.addWidget(others_group)

    entries_supplier["notes"] = notes_entry
    entries_supplier["experience"] = self.experiencesuppl_combobox

    icon_path = self.resource_path("images/save_button.png") 
    icon = QIcon(icon_path) 
    ## --- SAVE / MODIFY BUTTONS ---
    if modify_supplier_flag:
        modify_button = QPushButton("Modify Supplier")
        modify_button.setIcon(icon) 
        modify_button.clicked.connect(lambda: self.save_supplier(modify_supplier_flag=True))
        layout.addWidget(modify_button)
        
    else:
        save_button = QPushButton("Save New Supplier")
        save_button.setIcon(icon) 
        save_button.clicked.connect(self.save_supplier)
        layout.addWidget(save_button)
    self.entries_supplier = entries_supplier
    window.setLayout(layout)

    window.closeEvent = lambda event: self.close_event(event, window)  
    window.show()

#%% ADDING SUPPLIER
def open_add_supplier_window(self):
    # Create a new window for adding an employee
    self.add_supplier_window = QDialog(self)
    self.add_supplier_window.setWindowTitle("Add New Supplier")
    # self.add_suppliers_window.resize(500, 600)
    
    # Get the customer entry fields 
    self.supplier_widget(self.add_supplier_window)
    
#%% SAVE SUPPLIER
def save_supplier(self, modify_supplier_flag = False): 
    try:    
        # Get entries
        entries = self.entries_supplier
        
        values = {key: entry.toPlainText() if isinstance(entry, QTextEdit) 
              else entry.text() if isinstance(entry, QLineEdit) 
              else entry.currentText() if isinstance(entry, QComboBox) 
              else ""  # Default empty string for unknown widget types
              for key, entry in entries.items()}
    
        # Check entries for format and type
        if not values["company"] or not values["country"]:
            QMessageBox.critical(self, "Validation Error", "Mandatory fields missing.")
            return    
        if not self.is_valid_email(values["company_email"]): # MANDATORY FIELD
            QMessageBox.critical(self, "Validation Error", "The company email is not filled or incorrect.")
            return
        if not (self.is_valid_email(values["contact_email"]) or values["contact_email"]==''):
             QMessageBox.critical(self, "Validation Error", "The contact email is not filled or incorrect.")
             return   
        if not (values["company_phone"].isdigit() or (values["company_phone"][1:].isdigit() and values["company_phone"][0]=='+') or values["company_phone"]==''): # includes possibility of +
            QMessageBox.critical(self, "Validation Error", "The company phone number is incorrect.")
            return
        if not (values["contact_phone"].isdigit() or (values["contact_phone"][1:].isdigit() and values["contact_phone"][0]=='+') or values["contact_phone"]==''): # includes possibility of +
            QMessageBox.critical(self, "Validation Error", "The contact phone number is incorrect.")
            return
        
        # Check dropdown options
        selected_experience = entries["experience"].currentText()
        valid_experience_values = [entries["experience"].itemText(i) for i in range(entries["experience"].count())]
        if selected_experience not in valid_experience_values:
            QMessageBox.critical(self, "Validation Error", "Invalid Condition selected in Experience.")
            return
    
        
        # Submit entries values to db
        if modify_supplier_flag:
            try:
                self.cursor.execute("""UPDATE suppliers
                    SET Company = ?, Website = ?, Description = ?, Products = ?, CompanyEmail = ?, CompanyPhone = ?, 
                        ContactName = ?, ContactEmail = ?, ContactPhone = ?, Address = ?, ZIPCode = ?, City = ?, 
                        Country = ?, Experience = ?, Notes = ?
                    WHERE SupplierID = ?""",
                    (values["company"], values["website"], values["description"], values["products"], values["company_email"], values["company_phone"],
                     values["contact_name"], values["contact_email"], values["contact_phone"], values["address"], values["zip_code"], 
                     values["city"], values["country"], values["experience"], values["notes"],
                     self.modify_supplier_id_entry.text()))
                self.connection.commit()
                QMessageBox.information(self, "Success", "Supplier modified successfully")
                self.modify_supplier_window.destroy()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to modify supplier: {e}")
        else:
            try:
                # Insert new supplier into database
                self.cursor.execute('''INSERT INTO suppliers (Company, Website, Description, Products, CompanyEmail, CompanyPhone, 
                                        ContactName, ContactEmail, ContactPhone, Address, ZIPCode, City, Country, Experience, Notes)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                    (values["company"], values["website"], values["description"], values["products"], values["company_email"], values["company_phone"],
                                     values["contact_name"], values["contact_email"], values["contact_phone"], values["address"], values["zip_code"], 
                                     values["city"], values["country"], values["experience"], values["notes"]))
                self.connection.commit()
                QMessageBox.information(self, "Success", "New supplier added successfully!")
                self.add_supplier_window.destroy()  # Close supplier window
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to add supplier: {e}")
        
        self.show_table("suppliers")  # Refresh the suppliers table view
        # Close other windows if any
        try:
            self.handle_supplier_window.close()
        except AttributeError:
            pass  # or log the error if needed
    except ValueError as e:
        QMessageBox.critical(None, "Input Error", str(e))
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to add/update expense: {e}")
 
#%% MODIFY SUPPLIER
def open_modify_supplier_window(self):
    # Ask for SupplierID to modify
    self.modify_supplier_window = QDialog(self)
    self.modify_supplier_window.setWindowTitle("Modify Supplier")
    # self.modify_supplier_window.resize(500, 600)
    
    # Get the supplier entry fields 
    self.supplier_widget(self.modify_supplier_window, modify_supplier_flag = True)

#%% REMOVE SUPPLIER
def open_remove_supplier_window(self):    
    self.remove_supplier_window = QDialog(self)
    self.remove_supplier_window.setWindowTitle("Remove Supplier")
    self.remove_supplier_window.resize(300, 200)

    layout = QVBoxLayout()
    
    def remove_supplier(supplier_id):
        try:
            self.cursor.execute("DELETE FROM suppliers WHERE SupplierID = ?", (supplier_id,))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Supplier removed successfully")
            self.show_table("suppliers")  # Refresh the table view
            self.remove_supplier_window.destroy()
            self.handle_supplier_window.destroy()  # Close handle window
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to remove supplier: {e}")
            
    def fetch_supplier_to_remove():
        # Fetch the supplier to be removed and show confirmation
        supplier_id = self.remove_supplier_id_entry.text()
        if supplier_id:
            try:
                self.cursor.execute("SELECT Company FROM suppliers WHERE SupplierID = ?", (supplier_id,))
                supplier = self.cursor.fetchone()

                if supplier:
                    confirmation = QMessageBox.question(
                        self, "Confirm Deletion",
                        f"Are you sure you want to delete supplier {supplier[0]} with Supplier ID {supplier_id}?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if confirmation  == QMessageBox.Yes:
                        remove_supplier(supplier_id)
                else:
                    QMessageBox.warning(self, "Supplier Not Found", "No supplier found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch supplier data: {e}")
    
    # Specify SupplierID, fetch it and remove it
    label = QLabel("Supplier ID to Remove:")
    self.remove_supplier_id_entry = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(self.remove_supplier_id_entry)
    
    # Button to open selection table
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("suppliers", self.remove_supplier_id_entry))
    layout.addWidget(search_button)
    
    fetch_button = QPushButton("Remove Supplier")
    fetch_button.clicked.connect(fetch_supplier_to_remove)
    layout.addWidget(fetch_button)
    
    self.remove_supplier_window.setLayout(layout)
    self.remove_supplier_window.show()

