# -*- coding: utf-8 -*-
"""
Handling employees window: add, modify, remove

@author: feder
"""


import sqlite3
from PyQt5.QtWidgets import ( QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QLineEdit, QTextEdit, QGridLayout, QComboBox, QMessageBox, QDialog, QScrollArea, QWidget  )
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

def open_handle_employees_window(self):
    # Open a new window for employee modifications
    self.handle_window_empl = QDialog(self)
    self.handle_window_empl.setWindowTitle("Handle Employees")
    self.handle_window_empl.resize(300, 200)
    
        # 2) Keep it on top of the main window
    # self.handle_window_empl.setWindowFlags(self.handle_window_empl.windowFlags() | Qt.WindowStaysOnTopHint)

    
    layout = QVBoxLayout()

    # See employees button
    see_employee_button = QPushButton("See Employees")
    def _show_and_wire_employees():
        # 1) populate the table
        self.show_table("employees")
        # 2) remove any old handler
        try:
            self.table.cellDoubleClicked.disconnect()
        except TypeError:
            pass
        # 3) wire the new handler
        self.table.cellDoubleClicked.connect(self._on_employee_doubleclick)

    see_employee_button.clicked.connect(_show_and_wire_employees)
    layout.addWidget(see_employee_button)

    # Add New employee button
    add_employee_button = QPushButton("Add New Employee")
    add_employee_button.clicked.connect(self.open_add_employee_window)
    layout.addWidget(add_employee_button)

    # Modify employee button
    modify_employee_button = QPushButton("Modify Employee")
    modify_employee_button.clicked.connect(self.open_modify_employee_window)
    layout.addWidget(modify_employee_button)

    # Remove employee button
    remove_employee_button = QPushButton("Remove Employee")
    remove_employee_button.clicked.connect(self.open_remove_employee_window)
    layout.addWidget(remove_employee_button)
    
    self.handle_window_empl.setLayout(layout)
    self.handle_window_empl.show()

def _on_employee_doubleclick(self, row, col):
    # 1) grab the CustomerID from column 0
    empl_id = self.table.item(row, 0).text()
    if not empl_id:
        return

    # 2) open the Modify Customer window (this creates self.modify_customer_id_entry)
    self.open_modify_employee_window()

    # 3) now fill that dialog’s ID-entry with your selected ID
    self.modify_employee_id_entry.setText(empl_id)
    # now immediately fetch & populate all other fields
    self.fetch_employee_to_modify()
    
def fetch_employee_to_modify(self):
    employee_id = self.modify_employee_id_entry.text().strip()
    self.employee_id = employee_id
    if employee_id:
        try:
            self.cursor.execute("SELECT * FROM employees WHERE EmployeeID = ?", (employee_id,))
            employee = self.cursor.fetchone()
            if employee:
                for (key, entry), value in zip(self.employee_entries.items(), employee[1:]):
                    if isinstance(entry, QLineEdit):
                        entry.setText(str(value) if value is not None else "")
                    elif isinstance(entry, QTextEdit):
                        entry.setPlainText(str(value) if value is not None else "")
                    elif isinstance(entry, QComboBox):
                        if value in [entry.itemText(j) for j in range(entry.count())]:
                            entry.setCurrentText(value)
    
                # Update image label instead of replacing it
                if employee[-1]:  # Assuming the last column is 'Picture'
                    self.image_label.setText("Image exists in database. If you attach a new picture, the old one will be lost.")
                    self.image_label.setStyleSheet("font-style: italic; color: gray;")
                else:
                    self.image_label.setText("No image on database for this ID.")
                    self.image_label.setStyleSheet("font-style: italic; color: gray;")
            else:
                QMessageBox.warning(self, "Employee Not Found", "No employee found with the given ID.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch employee data: {e}")
    
#%% EMPLOYEE WIDGET
def employee_widget(self, window, modify_employee_flag=False):
    # make it scrollable in case resizing needed
    dialog_layout = QVBoxLayout(window)## Main layout
    
    scroll_area = QScrollArea(window) #scroll area
    scroll_area.setWidgetResizable(True)
    
    # Content inside scroll
    scroll_content = QWidget()
    layout = QVBoxLayout(scroll_content)


    ## MODIFY EMPLOYEE - ID SELECTION
    if modify_employee_flag:
        modify_layout = QHBoxLayout()
        label = QLabel("Employee ID to Modify:")
        self.modify_employee_id_entry = QLineEdit()  # Fixed incorrect reference
        self.modify_employee_id_entry.setReadOnly(True)
        search_button = QPushButton("Search Table")
        search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("employees", self.modify_employee_id_entry))  # Fixed table reference
        fetch_button = QPushButton("Fetch Employee")
        fetch_button.clicked.connect(self.fetch_employee_to_modify)  # Fixed function reference
        # fetch_button.clicked.connect(self.fetch_customer_to_modify)

        modify_layout.addWidget(label)
        modify_layout.addWidget(self.modify_employee_id_entry)
        modify_layout.addWidget(search_button)
        modify_layout.addWidget(fetch_button)
        layout.addLayout(modify_layout)

    self.employee_entries = {}
    
    ## --- SECTION 1: GENERAL INFORMATION ---
    general_group = QGroupBox("General Information")
    general_layout = QGridLayout()
    
    first_name_label = QLabel("First Name (*)")
    last_name_label = QLabel("Last Name (*)")
    email_label = QLabel("Email (*)")
    phone_label = QLabel("Phone (*)")
    
    first_name_entry = QLineEdit()
    last_name_entry = QLineEdit()
    email_entry = QLineEdit()
    phone_entry = QLineEdit()
    
    general_layout.addWidget(first_name_label, 0, 0)
    general_layout.addWidget(first_name_entry, 0, 1)
    general_layout.addWidget(last_name_label, 0, 2)
    general_layout.addWidget(last_name_entry, 0, 3)
    general_layout.addWidget(email_label, 1, 0)
    general_layout.addWidget(email_entry, 1, 1)
    general_layout.addWidget(phone_label, 1, 2)
    general_layout.addWidget(phone_entry, 1, 3)
    
    general_group.setLayout(general_layout)
    layout.addWidget(general_group)
    
    self.employee_entries["first_name"] = first_name_entry
    self.employee_entries["last_name"] = last_name_entry
    self.employee_entries["email"] = email_entry
    self.employee_entries["phone"] = phone_entry
    
    ## --- SECTION 2: ADDRESS INFORMATION ---
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
    address_layout.addWidget(address_entry, 0, 1, 1, 3)  # Address takes full row width
    address_layout.addWidget(zip_label, 1, 0)
    address_layout.addWidget(zip_entry, 1, 1)
    address_layout.addWidget(city_label, 1, 2)
    address_layout.addWidget(city_entry, 1, 3)
    address_layout.addWidget(country_label, 2, 0)
    address_layout.addWidget(country_entry, 2, 1, 1, 3)
    
    address_group.setLayout(address_layout)
    layout.addWidget(address_group)
    
    self.employee_entries["address"] = address_entry
    self.employee_entries["zip_code"] = zip_entry
    self.employee_entries["city"] = city_entry
    self.employee_entries["country"] = country_entry
    
    ## --- SECTION 3: EMPLOYMENT INFORMATION ---
    employment_group = QGroupBox("Employment")
    employment_layout = QGridLayout()
    
    job_label = QLabel("Job Title")
    availab_label = QLabel("Availability")
    availab_unit = QLabel("hours/week")  # Unit label
    status_label = QLabel("Current Status")
    notes_label = QLabel("Notes")
    image_label = QLabel("Image")
    
    job_entry = QLineEdit()
    availab_entry = QLineEdit()
    status_entry = QComboBox()
    status_entry.addItems(["Available", "Not available", "Remote", "Dismissed"])
    notes_entry = QTextEdit()
    notes_entry.setFixedHeight(80)
    
    # Image field (not editable)
    self.image_label = QLabel("No image selected")
    self.image_label.setStyleSheet("font-style: italic; color: gray;")  # Make it stand out as a placeholder

    
    employment_layout.addWidget(job_label, 0, 0)
    employment_layout.addWidget(job_entry, 0, 1, 1, 3)
    
    employment_layout.addWidget(availab_label, 1, 0)
    employment_layout.addWidget(availab_entry, 1, 1)
    employment_layout.addWidget(availab_unit, 1, 2)  # Keeps unit aligned properly
    
    employment_layout.addWidget(status_label, 2, 0)
    employment_layout.addWidget(status_entry, 2, 1)
    
    employment_layout.addWidget(notes_label, 3, 0)
    employment_layout.addWidget(notes_entry, 3, 1, 1, 3)  # Notes takes full row width
    
    # Add Image label field below Notes
    employment_layout.addWidget(image_label, 4, 0)
    employment_layout.addWidget(self.image_label, 4, 1, 1, 3)  # Image field spans across multiple columns
    
    employment_group.setLayout(employment_layout)
    layout.addWidget(employment_group)
    
    self.employee_entries["job_title"] = job_entry
    self.employee_entries["availability"] = availab_entry
    self.employee_entries["status"] = status_entry
    self.employee_entries["notes"] = notes_entry


    # === ATTACH PICTURE BUTTON ===
    icon_path = self.resource_path("images/add_picture.png") #self.icons_path + r"\add_picture.png" # Load the icon
    icon = QIcon(icon_path)
    attach_picture_button = QPushButton("Attach Picture")
    attach_picture_button.setIcon(icon) 
    attach_picture_button.clicked.connect(self.attach_picture)  # Call attach picture function
    layout.addWidget(attach_picture_button)  # Add it above Save/Modify button

    icon_path = self.resource_path("images/save_button.png") #self.icons_path + r"\save_button.png" # Load the icon
    icon = QIcon(icon_path)
    ## --- SAVE / MODIFY BUTTONS ---
    if modify_employee_flag:
        modify_button = QPushButton("Modify Employee")
        modify_button.setIcon(icon) 
        modify_button.clicked.connect(lambda: self.save_employee(modify_employee_flag=True))
        layout.addWidget(modify_button)
    else:
        save_button = QPushButton("Save New Employee")
        save_button.setIcon(icon) 
        save_button.clicked.connect(self.save_employee)
        layout.addWidget(save_button)

    #set layout
    scroll_area.setWidget(scroll_content)
    dialog_layout.addWidget(scroll_area)

    window.closeEvent = lambda event: self.close_event(event, window)  
    window.show()

    


#%% ADD EMPLOYEE
def open_add_employee_window(self):
    # Create a new window for adding a new employee
    self.add_window_empl = QDialog(None)
    self.add_window_empl.setWindowTitle("Add New Employee")
    self.add_window_empl.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.add_window_empl.resize(500, 600)
    
    # 2) Keep it on top of the main window
    # self.add_window_empl.setWindowFlags(self.add_window_empl.windowFlags() | Qt.WindowStaysOnTopHint)

    
    # Define employeeID
    self.cursor.execute("SELECT MAX(EmployeeID) FROM employees;")
    max_employee_id = self.cursor.fetchone()[0]
    self.employee_id = (max_employee_id or 0) + 1 
        
    # Get the employee entry fields 
    self.employee_widget(self.add_window_empl)
    
 
#%% SAVE
def save_employee(self, modify_employee_flag = False):
    try:
        # Get entries
        entries = self.employee_entries
        
        values = {key: entry.toPlainText() if isinstance(entry, QTextEdit) 
              else entry.text() if isinstance(entry, QLineEdit) 
              else entry.currentText() if isinstance(entry, QComboBox) 
              else ""  # Default empty string for unknown widget types
              for key, entry in entries.items()}
        
        # Mandatory fields
        required_fields = ["first_name", "last_name", "email", "phone"]
        for field in required_fields:
            if not values.get(field):
                QMessageBox.critical(self, "Validation Error", "Mandatory fields missing.")
                return  
        
        # Fields validation
        if not (values["phone"].isdigit() or (values["phone"][1:].isdigit() and values["phone"][0]=='+') or values["phone"]==''): # includes possibility of +
            QMessageBox.critical(self,"Validation Error", "The phone number is incorrect.")
            return
    
        if not (self.is_valid_email(values["email"]) or values["email"]==''):
            QMessageBox.critical(self,"Validation Error", "The email is incorrect.")
            return
        
        if not ((entries["status"].currentText() in [entries["status"].itemText(i) for i in range(entries["status"].count())]) 
            or (entries["status"].currentText() == '')):
            QMessageBox.critical(self, "Validation Error", "Invalid Condition selected in Current Status.")
            return
        
        if not (values["availability"].isdigit() or values["availability"]==''): 
            QMessageBox.critical(self,"Validation Error", "The availability must be an integer.")
            return
        
        if modify_employee_flag:
            try:
                self.cursor.execute("""UPDATE employees
                    SET FirstName = ?, LastName = ?, Email = ?,  Phone = ?, Address = ?, ZIPCode = ?, City = ?, Country = ?, 
                    JobTitle = ?, Availability =?, CurrentStatus =?, Notes = ?
                    WHERE EmployeeID = ?
                """, (values["first_name"], values["last_name"], values["email"], values["phone"],
                 values["address"], values["zip_code"], values["city"], values["country"],
                 values["job_title"], values["availability"], values["status"], values["notes"], self.employee_id))
                self.connection.commit()
                
                QMessageBox.information(self, "Success", "Employee modified successfully")
                try: self.add_window_empl.close()
                except: pass
        
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to modify employee: {e}")
        
        else:
            try:
                # Insert the new employee into the database
                self.cursor.execute('''INSERT INTO employees (FirstName, LastName, Email, Phone, Address, ZIPCode, City, Country, JobTitle, Availability, CurrentStatus, Notes)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                    (values["first_name"], values["last_name"], values["email"], values["phone"],
                                     values["address"], values["zip_code"], values["city"], values["country"],
                                     values["job_title"], values["availability"], values["status"], values["notes"]))
                self.connection.commit()
                
                QMessageBox.information(self, "Success", "New employee added successfully!")
                # self.add_window_empl.destroy()
                try: self.add_window_empl.close()
                except: pass
            except sqlite3.Error as e:
                QMessageBox.critical(self,  "Error", f"Failed to add employee: {e}")
               
        # If a picture was selected, attach it to the db
        if hasattr(self, 'selected_image_path'):
            # The variable exists and a picture has been selected
            if os.path.exists(self.selected_image_path):
                try:
                    self.cursor.execute(""" UPDATE employees SET Picture = ? WHERE EmployeeID = ?""", (self.empPhoto, self.employee_id))
                    self.connection.commit() 
                    
                    # reset pic path
                    del self.empPhoto, self.selected_image_path
    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to read picture: {e}")
                    return
            else:
                QMessageBox.critical(self, "Error", "Selected picture path does not exist.")
                return
            
        # self.show_table("employees")  # Refresh the employees table view
        # Refresh the customer table in-place
        self.show_table("employees")

        # Re-wire double-click so you can edit another immediately
        try:
            self.table.cellDoubleClicked.disconnect()
        except TypeError:
            pass
        self.table.cellDoubleClicked.connect(self._on_employee_doubleclick)
    except ValueError as e:
        QMessageBox.critical(None, "Input Error", str(e))
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to add/update expense: {e}")


#%% MODIFY WINDOW
def open_modify_employee_window(self):
    # Ask for employee ID to modify
    self.modify_window_empl = QDialog(None)
    self.modify_window_empl.setWindowTitle("Modify Employee")
    self.modify_window_empl.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.modify_window_empl.resize(500, 600)
    
    # 2) Keep it on top of the main window
    # self.modify_window_empl.setWindowFlags(self.modify_window_empl.windowFlags() | Qt.WindowStaysOnTopHint)

    
    # Get the entry fields 
    self.employee_widget(self.modify_window_empl, modify_employee_flag = True)
    

#%% REMOVE EMPLOYEE WINDOW
def open_remove_employee_window(self):
    self.remove_window_empl = QDialog(None)
    self.remove_window_empl.setWindowTitle("Remove Employee")
    self.remove_window_empl.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.remove_window_empl.resize(300, 200)

    layout = QVBoxLayout()
    
    def remove_employee(employee_id):
        try:
            self.cursor.execute("DELETE FROM employees WHERE EmployeeID = ?", (employee_id,))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Employee removed successfully")
            self.show_table("employees")  # Refresh the  table view
            self.handle_window_empl.destroy()  # Close handle  window
            self.remove_window_empl.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to remove employee: {e}")
            
    def fetch_employee_to_remove():
        # Fetch the employee to be removed and show confirmation
        employee_id = self.remove_employee_id_entry.text()
        if employee_id:
            try:
                self.cursor.execute("SELECT FirstName, LastName FROM employees WHERE EmployeeID = ?", (employee_id,))
                employee = self.cursor.fetchone()

                if employee:
                    confirmation = QMessageBox.question(
                        self, "Confirm Deletion",
                        f"Are you sure you want to delete employee {employee[0]} {employee[1]} with Employee ID {employee_id}?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No )
                    if confirmation == QMessageBox.Yes:
                        remove_employee(employee_id)
                else:
                    QMessageBox.warning(self, "Employee Not Found", "No employee found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch employee data: {e}")
    
    # Specify ID, fetch it and remove it
    label = QLabel("Employee ID to Remove:")
    self.remove_employee_id_entry = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(self.remove_employee_id_entry)
    
    # Button to open selection table
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("employees", self.remove_employee_id_entry))
    layout.addWidget(search_button)
    
    fetch_button = QPushButton("Remove Employee")
    fetch_button.clicked.connect(fetch_employee_to_remove)
    layout.addWidget(fetch_button)
    
    self.remove_window_empl.setLayout(layout)
    self.remove_window_empl.show()
    
