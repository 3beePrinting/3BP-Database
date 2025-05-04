# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 14:31:20 2025

Code for order tab1

@author: feder
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QTableWidget,QWidget,
    QTableWidgetItem, QMenu, QDateEdit, QFileDialog, QMessageBox, QGridLayout, QTextEdit, QScrollArea)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDate
import os
import win32com.client as win32
import shutil
import subprocess
from .invoice_pyqt import InvoiceWindow

#%% TAB 1 - Order details widgets        
def tab1_widgets(self, frame, modify_flag = False):
    self.incorrect_info_flag = False        
    order_entries_tab1 = {} 

    # Create a container widget inside the scroll area
    container_widget = QWidget()

    layout = QGridLayout(container_widget)
    
    def check_fields_before_fileUpload():
        # Enable button only if all required fields are filled
        if order_entries_tab1["customerid"].text().strip() and order_entries_tab1["description"].text().strip():
            folder_upl_button.setEnabled(True)
        else:
            folder_upl_button.setEnabled(False)
    
    # --- Customer Fields ---
    row_nr = 1
    layout.addWidget(QLabel("Customer ID (*)"), row_nr, 0)
    self.customer_id_entry = QLineEdit()
    self.customer_id_entry.setFixedWidth(200)
    self.customer_id_entry.setReadOnly(True)
    layout.addWidget(self.customer_id_entry, row_nr, 1)
    
    search_customer_button = QPushButton("Search Customer")
    search_customer_button.setIcon(QIcon( self.resource_path("images/search_customer.png") ))  # Optional: icon
    # search_customer_button.setIconSize(QSize(20, 20))
    search_customer_button.clicked.connect( lambda: (self.open_modifyfromtable_selection("customers", self.customer_id_entry, fillin_customer=True)) )
    layout.addWidget(search_customer_button, row_nr, 2)

    add_customer_button = QPushButton("New Customer")
    add_customer_button.setIcon(QIcon( self.resource_path("images/add_customer.png") ))
    # add_customer_button.setIconSize(QSize(20, 20))
    add_customer_button.clicked.connect( self.open_add_customer_window )
    layout.addWidget(add_customer_button, row_nr, 3)
    
    row_nr+=1
    self.first_last_name_label = QLabel("First Name and Last Name will appear here")
    self.first_last_name_label.setWordWrap(False)
    self.first_last_name_label.setFixedHeight(20)
    layout.addWidget(self.first_last_name_label, row_nr, 1)  # Just one cell
    self.customer_id_entry.textChanged.connect(check_fields_before_fileUpload)

    order_entries_tab1["customerid"] = self.customer_id_entry

    # --- Services Checkboxes ---
    row_nr+=1
    layout.addWidget(QLabel("Services"), row_nr, 0)
    service_checkboxes = {}
    service_names = ["3D Printing", "3D Design", "3D Scanning"]
    service_layout = QVBoxLayout()
    for i, name in enumerate(service_names):
        cb = QCheckBox(name)
        service_checkboxes[name] = cb
        service_layout.addWidget(cb)
    layout.addLayout(service_layout, row_nr, 1)
    self.service_vars = service_checkboxes
    order_entries_tab1["services"] = self.service_vars

    # --- Description ---
    row_nr+=1
    layout.addWidget(QLabel("Description"), row_nr, 0)
    description_entry = QLineEdit()
    layout.addWidget(description_entry, row_nr, 1)
    order_entries_tab1["description"] = description_entry
    order_entries_tab1["description"].textChanged.connect(check_fields_before_fileUpload)
    
    # --- Dates ---
    row_nr+=1
    layout.addWidget(QLabel("Date Ordered"), row_nr, 0)
    date_ordered = QDateEdit()
    date_ordered.setCalendarPopup(True)
    date_ordered.setDisplayFormat("yyyy-MM-dd")
    if not modify_flag:
        date_ordered.setDate(QDate.currentDate())
    layout.addWidget(date_ordered, row_nr, 1)
    order_entries_tab1["date_ordered"] = date_ordered
    
    # FOLDER BUTTON 
    folder_upl_button = QPushButton("Upload Files")
    folder_upl_button.setIcon(QIcon( self.resource_path("images/add_folder.png") ))
    folder_upl_button.clicked.connect( self.fun_folder_upload )
    folder_upl_button.setEnabled(False)
    layout.addWidget(folder_upl_button, row_nr, 2)

    row_nr+=1
    layout.addWidget(QLabel("Date Required"), row_nr, 0)
    date_required = QDateEdit()
    date_required.setCalendarPopup(True)
    date_required.setDisplayFormat("yyyy-MM-dd")
    if not modify_flag:
        date_required.setDate(QDate.currentDate())
    layout.addWidget(date_required, row_nr, 1)
    order_entries_tab1["date_required"] = date_required

    # --- Stage & Status Comboboxes ---
    # Function to update the Status dropdown based on the selected Stage
    def update_status_options(event=None):
        stage = self.stage_combobox.currentText()
        if stage == "Closed":
            status_options = ["Not accepted", "Closed"]
        elif stage == "Order":
            status_options = ["Accepted", "Invoice Sent", "Invoice Paid", "Designing", "Printing", "Ready", "Shipped"]
        elif stage == "Request":
            status_options = ["Received", "Price Estimation", "Email Sent", "Reminder Sent"]
        else:
            status_options = []

        # Update the Status dropdown
        self.status_combobox.clear()
        self.status_combobox.addItems(status_options)
        if status_options:
            self.status_combobox.setCurrentIndex(0)
        
    row_nr+=1
    layout.addWidget(QLabel("Stage"), row_nr, 0)
    self.stage_combobox = QComboBox()
    self.stage_combobox.addItems(["Request", "Order", "Closed"])
    self.stage_combobox.currentTextChanged.connect(update_status_options)
    layout.addWidget(self.stage_combobox, row_nr, 1)
    order_entries_tab1["stage"] = self.stage_combobox
    
    row_nr+=1
    layout.addWidget(QLabel("Status"), row_nr, 0)
    self.status_combobox = QComboBox()
    layout.addWidget(self.status_combobox, row_nr, 1)
    update_status_options()
    order_entries_tab1["status"] = self.status_combobox
    
    # — Invoice button on the same row, next column —
    self.invoice_button = QPushButton("Invoice…")
    layout.addWidget(self.invoice_button, row_nr, 2)
    self.invoice_button.clicked.connect(self._open_invoice_window)
    
    # --- Invoice ---
    row_nr+=1
    layout.addWidget(QLabel("Invoice Number"), row_nr, 0)
    invoice_num = QLineEdit()
    layout.addWidget(invoice_num, row_nr, 1)
    order_entries_tab1["invoice_number"] = invoice_num
    
    # Disable invoice number field by default
    invoice_num.setEnabled(False)
    
    # INVOICE BUTTON 
    invoice_upl_button = QPushButton("Upload Invoice")
    invoice_upl_button.setIcon(QIcon( self.resource_path("images/add_folder.png") ))
    invoice_upl_button.clicked.connect(lambda: self.fun_invoice_upload(order_flag=True) )
    layout.addWidget(invoice_upl_button, row_nr, 2)
    invoice_upl_button.setEnabled(False)
    
    # Function to enable/disable invoice number based on status
    def toggle_invoiceentry():
        invoice_num.setEnabled(self.status_combobox.currentText() == 'Closed')
        invoice_upl_button.setEnabled(self.status_combobox.currentText() == 'Closed')
    
    # Connect the combo box change to toggle function
    self.status_combobox.currentIndexChanged.connect(toggle_invoiceentry)
    
    # --- Responsible ---
    row_nr+=1
    layout.addWidget(QLabel("Responsible"), row_nr, 0)
    self.cursor.execute("SELECT FirstName || ' ' || LastName FROM employees")
    employee_names = [row[0] for row in self.cursor.fetchall()]
    responsible_combobox = QComboBox()
    responsible_combobox.addItems(employee_names)
    layout.addWidget(responsible_combobox, row_nr, 1)
    order_entries_tab1["responsible"] = responsible_combobox
    
    # Assign task to employee button
    job_assignment_outlook = QPushButton("Assign Task")
    job_assignment_outlook.setIcon(QIcon( self.resource_path("images/email.png") ))
    job_assignment_outlook.clicked.connect( self.fun_task_assignment )
    layout.addWidget(job_assignment_outlook, row_nr, 2)

    # --- Last Updated (read-only, default to today's date) ---
    row_nr+=1
    layout.addWidget(QLabel("Last Updated"), row_nr, 0)
    last_update = QDateEdit()
    last_update.setDisplayFormat("yyyy-MM-dd")
    last_update.setDate(QDate.currentDate())
    last_update.setDisabled(True)  # Makes it non-editable
    last_update.setStyleSheet("QDateEdit { background-color: lightgray; }")  # Grey background
    layout.addWidget(last_update, row_nr, 1)
    order_entries_tab1["last_updated"] = last_update
    
    self.order_entries_tab1 = order_entries_tab1
    self.order_entries_tab1["customer_name"] = " " 
     
    if modify_flag:
        # check customers exist
        self.cursor.execute("SELECT CustomerID FROM customers")
        customers = self.cursor.fetchall()
        customer_list = [x[0] for x in customers]
        
        # Fill entries in tab1
        for key, widget in self.order_entries_tab1.items():
            value = self.order_data.get(key, "")

            if isinstance(widget, QLineEdit):
                if key == 'customerid':
                    if value in customer_list:
                        widget.setText(str(value))
                    else:
                        self.incorrect_info_flag = True
                else:
                    widget.setText(str(value) if value is not None else "")
    
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(str(value) if value is not None else "")
                
            elif isinstance(widget, QComboBox):
                if value in [widget.itemText(j) for j in range(widget.count())]:
                    widget.setCurrentText(value)
                else:
                    self.incorrect_info_flag = True
                    widget.setCurrentIndex(0)
                
                # index = widget.findText(str(value))
                # widget.setCurrentIndex(index if index != -1 else 0)
                
            elif isinstance(widget, QDateEdit):
                if key in ["date_ordered", "date_required"]:
                    date = QDate.fromString(value, "yyyy-MM-dd")
                    if date.isValid():
                        widget.setDate(date)
                    else:
                        self.incorrect_info_flag = True

            # --- Set service checkboxes ---
            if key == "services":
                service_string = self.order_data["services"]
                for name, cb in self.service_vars.items():
                    cb.setChecked(False)  # Reset first
                if service_string:
                    for name in service_string.split(","):
                        name = name.strip()
                        if name in self.service_vars:
                            self.service_vars[name].setChecked(True)
            
        # Additions
        self.cursor.execute("SELECT FirstName, LastName FROM customers WHERE CustomerID = ?", (self.order_data["customerid"],))
        row = self.cursor.fetchone()
        if row:
            self.first_last_name_label.setText(f"Check customer's name: {row[0]} {row[1]}")
            self.order_entries_tab1["customer_name"] = f"{row[0]} {row[1]}"
                
    
    #%% --- Parts Table ---
    self.create_parts_table_tab1(layout, modify_flag)
    
    # Upload final layout
    layout.setColumnStretch(0, 0)  # Label column
    layout.setColumnStretch(1, 0)  # Input field
    layout.setColumnStretch(2, 0)  # Search button
    layout.setColumnStretch(3, 0)  # Add button
    layout.setColumnStretch(4, 1)  # Table column — give it all remaining space
    
    def go_to_tab2():
        if self.validate_fields_tab1():
            self.go_to_next_tab()
    next_button = QPushButton("Next Tab")
    next_button.setFixedWidth(100)
    next_button.setStyleSheet("QPushButton { background-color: lightgray; }")

    layout.addWidget(next_button, 12, 5, alignment=Qt.AlignRight)
    next_button.clicked.connect(go_to_tab2)
    
    frame.setWidget(container_widget)
    
    
#%% Make parts table in tab1
def create_parts_table_tab1(self, layout, modify_flag=False):
    columns = ["PartID", "OrderID", "PartNr", "PartName", "Material", "Color", "QuantityOrdered", "QuantityPrinted", "PrintSettings"]
    self.parts_table = QTableWidget()
    self.parts_table.setColumnCount(len(columns))
    self.parts_table.setHorizontalHeaderLabels(columns)
    self.parts_table.setEditTriggers(QTableWidget.NoEditTriggers)
    self.parts_table.setSelectionBehavior(QTableWidget.SelectRows)
    self.parts_table.setSelectionMode(QTableWidget.SingleSelection)
    layout.addWidget(self.parts_table, 1, 4, 10, 1)

    # Load parts from DB if modifying
    if modify_flag:
        try:
            self.cursor.execute("SELECT * FROM orderparts WHERE OrderID = ?", (self.orderid,))
            db_parts = self.cursor.fetchall()
            col_names = [desc[0] for desc in self.cursor.description]
            self.parts = [dict(zip(col_names, row)) for row in db_parts]

            self.parts_table.setRowCount(len(self.parts))
            for row_idx, part in enumerate(self.parts):
                for col_idx, col in enumerate(columns):
                    value = str(part.get(col, ""))
                    self.parts_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load parts: {e}")
            return
    else:
        self.parts = []
        
    # Find minimum partID to start numbering
    try:
        self.cursor.execute("SELECT MAX(PartID) FROM orderparts;")
        max_part_id = self.cursor.fetchone()[0]
        self.start_part_id = (max_part_id or 0)
    except Exception as e:
        QMessageBox.critical(None,"Error", f"Failed to generate PartID: {e}")
        return

    # --- Add/Remove Buttons ---
    add_row_button = QPushButton("Add Empty Row")
    delete_row_button = QPushButton("Delete Selected")
    button_row_layout = QHBoxLayout()
    button_row_layout.addWidget(add_row_button)
    button_row_layout.addWidget(delete_row_button)
    
    layout.addLayout(button_row_layout, 11, 4, 1, 1) 
    
    def renumber_rows():
        self.parts.clear() # Clear and rebuild the self.parts list
        current_part_id = self.start_part_id+1 # Use start_part_id as the starting point for PartID
    
        for row in range(self.parts_table.rowCount()):
            values = []
            for col in range(self.parts_table.columnCount()):
                item = self.parts_table.item(row, col)
                values.append(item.text() if item else "")
            values[0] = str(current_part_id)
            values[2] = str(row + 1)
            values[3] = f"Pt{current_part_id}"
            for col in range(len(values)):
                self.parts_table.setItem(row, col, QTableWidgetItem(values[col]))
            self.parts.append({columns[i]: values[i] for i in range(len(columns))})
            current_part_id += 1

    # Add Empty Row Button (adds a row to the table, not database)
    def add_empty_part_row():
        row = self.parts_table.rowCount()
        self.parts_table.insertRow(row)
        default_values = ["0", str(self.orderid), "0", "", "PLA", "any", "0", "0", "Default PLA"]
        for col, val in enumerate(default_values):
            self.parts_table.setItem(row, col, QTableWidgetItem(val))
        renumber_rows()

    # Delete selected row (only from the table, not database)
    def delete_selected_part_row():
        row = self.parts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", "No item selected!")
            return
        self.parts_table.removeRow(row)
        renumber_rows()
        
    # --- Edit on double-click ---
    def start_editing_item(row, col):
        if col in (3, 4, 5, 6, 7):
            item = self.parts_table.item(row, col)
            if item:
                self.parts_table.editItem(item)
            
    # Update self.parts only for editable columns (3, 4, 5)
    def on_item_changed(item):
        col = item.column()
        row = item.row()
    
        if col in (3, 4, 5, 6, 7):  # Editable columns
            if 0 <= row < len(self.parts):
                new_value = item.text()
                self.parts[row][columns[col]] = new_value
    
                # If column 4 was edited (Material)
                if col in [4,5]:
                    reply = QMessageBox.question(
                        self,
                        "Update All Parts?",
                        "Do you want to update all parts with this value?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.parts_table.blockSignals(True) 
                        for r in range(self.parts_table.rowCount()):
                            # Update table display
                            self.parts_table.item(r, col).setText(new_value)
                            # Update internal data
                            self.parts[r][columns[col]] = new_value
                        self.parts_table.blockSignals(False)
                        
                if col == 4:
                    groups = ['PLA', 'ABS', 'ASA', 'PETG', 'FLEXIBLE']
                    cell_value = self.parts[row][columns[col]].lower()
                    new_value = None  # Default value in case no match found
                    for group in groups:
                        if group.lower() in cell_value:
                            new_value = 'Default ' + group
                            reply = QMessageBox.question(
                                self,
                                "Update PrintSettings?",
                                f"Do you want to update the print setting to {new_value}?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            if reply == QMessageBox.Yes:
                                # Update table display
                                self.parts_table.item(row, 8).setText(new_value)
                                # Update internal data
                                self.parts[row][columns[8]] = new_value
                            break                   
            
    # Connect events
    self.parts_table.cellDoubleClicked.connect(start_editing_item)
    self.parts_table.itemChanged.connect(on_item_changed)
    add_row_button.clicked.connect(add_empty_part_row)
    delete_row_button.clicked.connect(delete_selected_part_row)
    
    # --- Print Settings Context Menu ---
    self.parts_table.setContextMenuPolicy(Qt.CustomContextMenu)
    
    self.printsettings_menu = QMenu()
    self.printsettings_menu.addAction("Edit Print Settings", self.open_print_settings_window)
    
    def show_context_menu(pos):
        index = self.parts_table.indexAt(pos)
        if index.isValid() and index.column() == 8:  # Only show on "PrintSettings" column
            self.printsettings_menu.exec_(self.parts_table.viewport().mapToGlobal(pos))
    
    self.parts_table.customContextMenuRequested.connect(show_context_menu)
    
#%% Check all fields are filled before moving on
def validate_fields_tab1(self):
    # Collect and trim values from widgets
    entries = self.order_entries_tab1
    mandatory_fields = {
        "Customer ID": entries["customerid"].text().strip(),
        "Description": entries["description"].text().strip(),
        "Date Ordered": entries["date_ordered"].date().toString("yyyy-MM-dd"),
        "Date Required": entries["date_required"].date().toString("yyyy-MM-dd"),
        "Stage": entries["stage"].currentText(),
        "Status": entries["status"].currentText(),
        "Responsible": entries["responsible"].currentText(),
        "Last Updated": entries["last_updated"].date().toString("yyyy-MM-dd")  }

    # Check for missing fields
    missing_fields = [field for field, value in mandatory_fields.items() if not value]

    # Check if at least one service is selected (assumes checkboxes stored in self.service_vars)
    if not any(checkbox.isChecked() for checkbox in self.service_vars.values()):
        missing_fields.append("Services (at least one must be selected)")

    if missing_fields:
        QMessageBox.critical(self, "Missing Information", "Mandatory fields are missing!")
        return False

    return True


# Function to create email to send task to the selected employee
def fun_task_assignment(self):
    order_id = self.orderid
    entries = self.order_entries_tab1
    
    # Check inputs
    try:
        employee_name = entries["responsible"].currentText()
    
        first_name, last_name = employee_name.split(" ", 1)  # Split into two parts
    
    
        # define recipient email
        self.cursor.execute("SELECT Email FROM employees WHERE FirstName = ? AND LastName = ?", (first_name, last_name))
        recipient = self.cursor.fetchone()[0]
        
        # Define text of message
        customerid = entries["customerid"].text()
        self.cursor.execute("SELECT FirstName, LastName, Email FROM customers WHERE CustomerID = ?", (customerid))
        customer_firstname, customer_lastname, customer_email = self.cursor.fetchone()
    
        subject = "Task assignment - to you, dear!" 
        body = f"""Dear {employee_name},
Please find attached the details of the assigned job.

    • OrderID: {order_id}
    • Customer: ID {customerid}, {customer_firstname} {customer_lastname}, {customer_email}
    • Description: {entries["description"].text()}
    • Date Order: {entries["date_ordered"].date().toString("yyyy-MM-dd")}
    • Current Status: {entries["status"].currentText()}  """

    except ValueError:
        print("Insufficient inputs provided for task assignment.")
        return None
    
    try:
        # Connect to Outlook
        outlook = win32.Dispatch('outlook.application')

        # Create a new email
        mail = outlook.CreateItem(0)  # 0 corresponds to a MailItem

        # Set recipient, subject, and body
        mail.To = recipient
        mail.Subject = subject
        mail.Body = body

        # Add an attachment
        # attachment_path = r'C:\path\to\your\file.txt'  # Replace with the file path
        # mail.Attachments.Add(attachment_path)

        # Open the email for review (doesn't send it automatically)
        mail.Display()  # Opens the email window in Outlook for editing

        print("Email created successfully in Outlook.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
# Function to create folder and upload files received
def fun_folder_upload(self):       
    order_id = self.orderid
        
    # Build the folder name using PyQt widgets
    date_str = self.order_entries_tab1["date_ordered"].date().toString("yyyy-MM-dd")
    customer_id = self.order_entries_tab1["customerid"].text()
    description = self.order_entries_tab1["description"].text()
    
    folder_name = f"{date_str}_OrderID{order_id}_CustomerID{customer_id}_{description}"
    
    #Ask to check good file name before creating
    confirmation = QMessageBox.question(
        self, "Confirm Deletion",
        f"The following folder will be created: {folder_name} \nClick Yes to continue.")
    if confirmation == QMessageBox.Yes:
        self.order_entries_tab1["folder_name"] = folder_name
        folder_path = os.path.join(self.upload_folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        # Create subfolders
        stl_folder_path = os.path.join(folder_path, "stl")
        gcode_folder_path = os.path.join(folder_path, "gcode")
        other_folder_path = os.path.join(folder_path, "other_files")
        os.makedirs(stl_folder_path, exist_ok=True)
        os.makedirs(gcode_folder_path, exist_ok=True)
        os.makedirs(other_folder_path, exist_ok=True)
        
        # Open file dialog to select files
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select files to upload")
    
        if not file_paths:
            QMessageBox.information(self, "No Files Selected", "No files were selected for upload.")
            return
        # Move selected files to the appropriate folder
        for file_path in file_paths:
            file_extension = os.path.splitext(file_path)[1].lower()
    
            try:
                if file_extension in [".stl", ".stp", ".step", ".obj", ".dwg", ".dxf"]:
                    shutil.copy(file_path, stl_folder_path)
                elif file_extension == ".gcode":
                    shutil.copy(file_path, gcode_folder_path)
                else:
                    shutil.copy(file_path, other_folder_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy file: {file_path}\n{str(e)}")
    
         # Open the folder automatically after upload**
        try:
            if os.name == "nt":  # Windows
                os.startfile(folder_path)
            elif os.name == "posix":  # macOS / Linux
                subprocess.Popen(["open", folder_path])  # macOS
                # subprocess.Popen(["xdg-open", folder_path])  # Linux alternative
            print(f"Folder opened: {folder_path}")
        except Exception as e:
            print(f"Error opening folder: {e}")

def _open_invoice_window(self):
        """
        Open the InvoiceWindow pre-loaded with the customer from the current order.
        """
        # 1) Find the customer field widget and extract its value
        cust_widget = self.order_entries_tab1.get("customer")
        cust_id = None
        if cust_widget:
            # QLineEdit vs QComboBox
            if hasattr(cust_widget, "text"):
                cust_id = cust_widget.text()
            elif hasattr(cust_widget, "currentText"):
                cust_id = cust_widget.currentText()

        # 2) Look up that customer's details from the DB
        cust_info = None
        if cust_id:
            try:
                query = """
                    SELECT FirstName, LastName, Email, BillingAddress, ShippingAddress
                      FROM customers
                     WHERE CustomerID = ?
                """
                self.cursor.execute(query, (cust_id,))
                row = self.cursor.fetchone()
                if row:
                    cust_info = {
                        "name":             f"{row[0]} {row[1]}",
                        "email":            row[2],
                        "billing_address":  row[3],
                        "shipping_address": row[4],
                    }
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Customer lookup failed",
                    f"Could not load customer data:\n{e}"
                )

        # 3) Build the dict to pass into InvoiceWindow
        if cust_info:
            customers_dict = {
                cust_info["name"]: {
                    "email":            cust_info["email"],
                    "billing_address":  cust_info["billing_address"],
                    "shipping_address": cust_info["shipping_address"],
                }
            }
        else:
            customers_dict = None  # will fall back to defaults in the invoice form

        # 4) Instantiate and show the invoice UI
        #    Pass customers_dict into the constructor so the dropdown is pre-populated
        self._invoice_win = InvoiceWindow(customers=customers_dict)

        # (Optional) Prefill invoice number from order ID if you have it:
        oid_widget = self.order_entries_tab1.get("order_id")
        if oid_widget and hasattr(oid_widget, "text"):
            try:
                self._invoice_win.invoice_number.setText(oid_widget.text())
            except Exception:
                pass

        self._invoice_win.show()


