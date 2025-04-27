# -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 13:19:37 2024

@author: feder
"""

import sqlite3
from PyQt5.QtWidgets import ( QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QLineEdit, QTextEdit, QGridLayout, QComboBox, QMessageBox, QDialog  )
from PyQt5.QtGui import QIcon

def open_handle_customers_window(self):
    # Open a new window for customer modifications
    self.handle_window_customer = QDialog(self)
    self.handle_window_customer.setWindowTitle("Handle Customers")
    self.handle_window_customer.resize(300, 200)
    
    layout = QVBoxLayout()

    # See customer button
    see_customers_button = QPushButton("See Customers")
    see_customers_button.clicked.connect(lambda: self.show_table("customers"))
    layout.addWidget(see_customers_button)

    # Add New customer button
    add_new_customer_button = QPushButton("Add New Customer")
    add_new_customer_button.clicked.connect(self.open_add_customer_window)
    layout.addWidget(add_new_customer_button)

    # Modify customer button
    modify_customer_button = QPushButton("Modify Customer")
    modify_customer_button.clicked.connect(self.open_modify_customer_window)
    layout.addWidget(modify_customer_button)

    # Remove customer button
    remove_customer_button = QPushButton("Remove Customer")
    remove_customer_button.clicked.connect(self.open_remove_customer_window)
    layout.addWidget(remove_customer_button)
    
    self.handle_window_customer.setLayout(layout)
    self.handle_window_customer.show()

#%% WIDGET
def customer_widget(self, window, modify_customer_flag = False):
    layout = QVBoxLayout()

    ## Function to fetch customer from database and fill in all data
    def fetch_customer_to_modify():
        customer_id = self.modify_customer_id_entry.text()
        if customer_id:
            try:
                self.cursor.execute("SELECT * FROM customers WHERE CustomerID = ?", (customer_id,))
                customer = self.cursor.fetchone()
                if customer:
                    for i, (key, entry) in enumerate(self.entries_customer.items(), start=1):
                        value = str(customer[i])
                        if isinstance(entry, QComboBox):
                            # Set to 'Neutral' if value is not one of the options
                            if value in [entry.itemText(j) for j in range(entry.count())]:
                                entry.setCurrentText(value)
                        else:
                            entry.setText(value)
                else:
                    QMessageBox.warning(self, "Customer Not Found", "No customer found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch customer data: {e}")

    if modify_customer_flag:  # MODIFY CUSTOMER
        modify_layout = QHBoxLayout()
        label = QLabel("Customer ID to Modify:")
        self.modify_customer_id_entry = QLineEdit()
        self.modify_customer_id_entry.setReadOnly(True)
        search_button = QPushButton("Search Table")
        search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("customers", self.modify_customer_id_entry))
        fetch_button = QPushButton("Fetch Customer")
        fetch_button.clicked.connect(fetch_customer_to_modify)

        modify_layout.addWidget(label)
        modify_layout.addWidget(self.modify_customer_id_entry)
        modify_layout.addWidget(search_button)
        modify_layout.addWidget(fetch_button)
        layout.addLayout(modify_layout)

    # Dictionary to store entry fields
    entries_customer = {}

    ## --- SECTION 1: GENERAL INFORMATION ---
    general_group = QGroupBox("General Information")
    general_layout = QGridLayout()

    first_name_label = QLabel("First Name")
    last_name_label = QLabel("Last Name")
    company_label = QLabel("Company")

    first_name_entry = QLineEdit()
    last_name_entry = QLineEdit()
    company_entry = QLineEdit()

    general_layout.addWidget(first_name_label, 0, 0)
    general_layout.addWidget(first_name_entry, 0, 1)
    general_layout.addWidget(last_name_label, 0, 2)
    general_layout.addWidget(last_name_entry, 0, 3)
    general_layout.addWidget(company_label, 1, 0)
    general_layout.addWidget(company_entry, 1, 1, 1, 3)  # Company takes full row width

    general_group.setLayout(general_layout)
    layout.addWidget(general_group)

    entries_customer["first_name"] = first_name_entry
    entries_customer["last_name"] = last_name_entry
    entries_customer["company"] = company_entry

    ## --- SECTION 2: CONTACT INFORMATION ---
    contact_group = QGroupBox("Contact Information")
    contact_layout = QGridLayout()

    email_label = QLabel("Email (*)")
    phone_label = QLabel("Phone")

    email_entry = QLineEdit()
    phone_entry = QLineEdit()

    contact_layout.addWidget(email_label, 0, 0)
    contact_layout.addWidget(email_entry, 0, 1)
    contact_layout.addWidget(phone_label, 0, 2)
    contact_layout.addWidget(phone_entry, 0, 3)

    contact_group.setLayout(contact_layout)
    layout.addWidget(contact_group)

    entries_customer["email"] = email_entry
    entries_customer["phone"] = phone_entry

    ## --- SECTION 3: ADDRESS INFORMATION ---
    address_group = QGroupBox("Address")
    address_layout = QGridLayout()

    address_label = QLabel("Address")
    zip_label = QLabel("ZIP Code")
    city_label = QLabel("City")
    country_label = QLabel("Country")

    address_entry = QLineEdit()
    zip_entry = QLineEdit()
    city_entry = QLineEdit()
    country_entry = QLineEdit()

    address_layout.addWidget(address_label, 0, 0)
    address_layout.addWidget(address_entry, 0, 1, 1, 3)
    address_layout.addWidget(zip_label, 1, 0)
    address_layout.addWidget(zip_entry, 1, 1)
    address_layout.addWidget(city_label, 1, 2)
    address_layout.addWidget(city_entry, 1, 3)
    address_layout.addWidget(country_label, 2, 0)
    address_layout.addWidget(country_entry, 2, 1, 1, 3)

    address_group.setLayout(address_layout)
    layout.addWidget(address_group)

    entries_customer["address"] = address_entry
    entries_customer["zip_code"] = zip_entry
    entries_customer["city"] = city_entry
    entries_customer["country"] = country_entry

    ## --- SECTION 4: OTHER INFORMATION ---
    others_group = QGroupBox("Others")
    others_layout = QGridLayout()

    notes_label = QLabel("Notes")
    notes_entry = QTextEdit()
    notes_entry.setFixedHeight(80)

    experience_label = QLabel("Experience")
    self.experiencecost_combobox = QComboBox()
    self.experiencecost_combobox.addItems(["Very Positive", "Positive", "Neutral", "Negative"])
    self.experiencecost_combobox.setCurrentText("Neutral")

    others_layout.addWidget(notes_label,0,0)
    others_layout.addWidget(notes_entry,0,1,1,3)
    others_layout.addWidget(experience_label,1,0)
    others_layout.addWidget(self.experiencecost_combobox,1,1,1,3)

    others_group.setLayout(others_layout)
    layout.addWidget(others_group)

    entries_customer["notes"] = notes_entry
    entries_customer["experience"] = self.experiencecost_combobox

    icon_path = self.resource_path("images/save_button.png")  
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    ## --- SAVE / MODIFY BUTTONS ---
    if modify_customer_flag:
        modify_button = QPushButton("Modify Customer")
        modify_button.setIcon(icon) 
        modify_button.clicked.connect(lambda: self.save_customer(modify_customer_flag=True))
        layout.addWidget(modify_button)
    else:
        save_button = QPushButton("Save New Customer")
        save_button.setIcon(icon) 
        save_button.clicked.connect(self.save_customer)
        layout.addWidget(save_button)

    self.entries_customer = entries_customer
    window.setLayout(layout)

    window.closeEvent = lambda event: self.close_event(event, window)
    window.show()


#%% ADD CUSTOMER
def open_add_customer_window(self):
    # Create a new window for adding a new customer
    self.add_customer_window = QDialog(self)
    self.add_customer_window.setWindowTitle("Add New Customer")
    # self.add_customer_window.resize(500, 600)
        
    # Get the customer entry fields 
    self.customer_widget(self.add_customer_window)
    


#%% MODIFY CUSTOMER WINDOW    
def open_modify_customer_window(self):
    # Ask for customer ID to modify
    self.modify_window_customer = QDialog(self)
    self.modify_window_customer.setWindowTitle("Modify Customer")
    # self.modify_window_customer.resize(500, 600)
    
    # Get the customer entry fields 
    self.customer_widget(self.modify_window_customer, modify_customer_flag = True)
    
       
#%% SAVE CUSTOMER (NEW/MODIFIED)
def save_customer(self, modify_customer_flag = False):
    try:
        entries = self.entries_customer
        
        values = {key: entry.toPlainText() if isinstance(entry, QTextEdit) 
              else entry.text() if isinstance(entry, QLineEdit) 
              else entry.currentText() if isinstance(entry, QComboBox) 
              else ""  # Default empty string for unknown widget types
              for key, entry in entries.items()}
    
        # Fields validation
        if not (values["phone"].isdigit() or (values["phone"][1:].isdigit() and values["phone"][0]=='+') or values["phone"]==''): # includes possibility of +
            QMessageBox.critical(self, "Validation Error", "The phone number is incorrect.")
            return
    
        if not self.is_valid_email(values["email"]): # MANDATORY FIELD
            QMessageBox.critical(self, "Validation Error", "The email is not filled or incorrect.")
            return
        
        selected_experience = entries["experience"].currentText()
        valid_experience_values = [entries["experience"].itemText(i) for i in range(entries["experience"].count())]
        if selected_experience not in valid_experience_values:
            QMessageBox.critical(self, "Validation Error", "Invalid Condition selected in Experience.")
            return
        
        if modify_customer_flag:
            try:
                self.cursor.execute("""UPDATE customers
                    SET FirstName = ?, LastName = ?, Email = ?, Phone = ?, Company = ?, Address = ?, ZIPCode = ?, City = ?, Country = ?, Experience =?, Notes = ?
                    WHERE CustomerID = ?""", 
                    (values["first_name"], values["last_name"], values["email"], values["phone"],
                     values["company"], values["address"], values["zip_code"], values["city"], values["country"], values["experience"], values["notes"],
                     self.modify_customer_id_entry.text()))
                self.connection.commit()
                QMessageBox.information(self, "Success", "Customer modified successfully")
                self.modify_window_customer.destroy()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to modify customer: {e}")
        else:
            try:
                # Insert new customer into database
                self.cursor.execute('''INSERT INTO customers (FirstName, LastName, Email, Phone, Company, Address, ZIPCode, City, Country, Experience, Notes)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                    (values["first_name"], values["last_name"], values["email"], values["phone"],
                                     values["company"], values["address"], values["zip_code"], values["city"], values["country"], values["experience"], values["notes"]))
                self.connection.commit()
                QMessageBox.information(self, "Success", "New customer added successfully!")
                self.add_customer_window.destroy()  # Close customer window
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to add customer: {e}")
                
        self.show_table("customers")  # Refresh the customers table view
        self.handle_window_customer.destroy()
    except ValueError as e:
        QMessageBox.critical(None, "Input Error", str(e))
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to add/update expense: {e}")
   
#%% REMOVE CUSTOMER
def open_remove_customer_window(self):
    self.remove_window = QDialog(self)
    self.remove_window.setWindowTitle("Remove Customer")
    self.remove_window.resize(300, 200)

    layout = QVBoxLayout()
    
    def remove_customer(customer_id):
        # Remove customer logic
        try:
            self.cursor.execute("DELETE FROM customers WHERE CustomerID = ?", (customer_id,))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Customer removed successfully")
            self.show_table("customers")  # Refresh the customers table view
            self.handle_window_customer.destroy()  # Close handle customer window
            self.remove_window.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to remove customer: {e}")
            
    def fetch_customer_to_remove():
        # Fetch the customer to be removed and show confirmation
        customer_id = self.remove_customer_id_entry.text()
        if customer_id:
            try:
                self.cursor.execute("SELECT FirstName, LastName FROM customers WHERE CustomerID = ?", (customer_id,))
                customer = self.cursor.fetchone()

                if customer:
                    confirmation = QMessageBox.question(
                        self, "Confirm Deletion",
                        f"Are you sure you want to delete customer {customer[0]} {customer[1]} with customer ID {customer_id}?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if confirmation == QMessageBox.Yes:
                        remove_customer(customer_id)
                else:
                    QMessageBox.warning(self, "Customer Not Found", "No customer found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch customer data: {e}")
    
    # Specify CustomerID, fetch it and remove it
    label = QLabel("Customer ID to Remove:")
    self.remove_customer_id_entry = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(self.remove_customer_id_entry)
    
    # Button to open customer selection table
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("customers", self.remove_customer_id_entry))
    layout.addWidget(search_button)
    
    fetch_button = QPushButton("Remove Customer")
    fetch_button.clicked.connect(fetch_customer_to_remove)
    layout.addWidget(fetch_button)
    
    self.remove_window.setLayout(layout)
    self.remove_window.show()
