# -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 13:19:46 2024

@author: feder
"""
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QDateEdit,
    QVBoxLayout, QHBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QFileDialog, QDialog, QScrollArea
)
from PyQt5.QtCore import QSize, QDate, Qt
from PyQt5.QtGui import QIcon, QFont
import datetime
import sqlite3
import os
from PyQt5.QtWidgets import ( 
    QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit, QTextEdit,
    QGridLayout, QComboBox, QMessageBox, QDialog
    )



def open_handle_expenses_window(self):
    self.handle_window_exp = QDialog(self)
    self.handle_window_exp.setWindowTitle("Handle Expenses")
    self.handle_window_exp.setFixedSize(300, 200)
    
    # 2) Keep it on top of the main window
    # self.handle_window_exp.setWindowFlags(self.handle_window_exp.windowFlags() | Qt.WindowStaysOnTopHint)

    
    layout = QVBoxLayout()

    see_expense_button = QPushButton("See Expenses")
    def _show_and_wire_expenses():
        # 1) populate the table
        self.show_table("expenses")
        # 2) remove any old handler
        try:
            self.table.cellDoubleClicked.disconnect()
        except TypeError:
            pass
        # 3) wire the new handler
        self.table.cellDoubleClicked.connect(self._on_expense_doubleclick)

    see_expense_button.clicked.connect(_show_and_wire_expenses)
    layout.addWidget(see_expense_button)

    add_expense_button = QPushButton("Add New Expense")
    add_expense_button.clicked.connect(self.open_add_expense_window)
    layout.addWidget(add_expense_button)

    modify_expense_button = QPushButton("Modify Expense")
    modify_expense_button.clicked.connect(self.open_modify_expense_window)
    layout.addWidget(modify_expense_button)

    remove_expense_button = QPushButton("Remove Expense")
    remove_expense_button.clicked.connect(self.open_remove_expense_window)
    layout.addWidget(remove_expense_button)

    self.handle_window_exp.setLayout(layout)
    self.handle_window_exp.show()

def _on_expense_doubleclick(self, row, col):
    # 1) grab the CustomerID from column 0
    expe_id = self.table.item(row, 0).text()
    if not expe_id:
        return

    # 2) open the Modify Customer window (this creates self.modify_customer_id_entry)
    self.open_modify_expense_window()

    # 3) now fill that dialog’s ID-entry with your selected ID
    self.modify_expenseid_entry.setText(expe_id)
    # now immediately fetch & populate all other fields
    self.fetch_expense_to_modify()

def fetch_expense_to_modify(self):
        # Fetch and fill in the fields for the expense to modify
        expense_id = self.modify_expenseid_entry.text().strip()
        self.expense_id = expense_id
        
        # check suppliers exist
        self.cursor.execute("SELECT SupplierID FROM suppliers")
        suppliers = self.cursor.fetchall()
        supplier_list = [x[0] for x in suppliers]
    
        if expense_id:
            try:
                self.cursor.execute("SELECT * FROM expenses WHERE OCnumber = ?", (expense_id,))
                expense = self.cursor.fetchone()
    
                if expense:
                    # Fill the entries with current expense details
                    for i, (key, entry) in enumerate(self.expense_entries.items(), start=1):
                        value = expense[i]

                        if key == 'tax_return_applicable':
                            # skip if no value
                            if not value:
                                continue
                        
                            val_str = str(value).strip()
                            parts = val_str.split()
                            if len(parts) == 2:
                                quarter, year = parts
                        
                                # — Quarter (unchanged) —
                                if quarter in [entry[0].itemText(j) for j in range(entry[0].count())]:
                                    entry[0].setCurrentText(quarter)
                        
                                # — Year: add if missing, then set —
                                year_items = [entry[1].itemText(j) for j in range(entry[1].count())]
                                if year not in year_items:
                                    entry[1].addItem(year)
                                entry[1].setCurrentText(year)
                        
                            else:
                                incorrect_info_flag = True
                            
                                continue

    
                        elif isinstance(entry, QLineEdit):
                            if key == 'supplierid':
                                if value in supplier_list:
                                    entry.setText(str(value))
                                    incorrect_info_flag = True
                                else:
                                    entry.setText("")
                            elif key in ["cost_shipping", "btw", "tax_to_be_returned"] and value!= "":
                                try: # check its a number, otherwise remove
                                    entry.setText(str(float(value)))
                                except ValueError:
                                    incorrect_info_flag = True
                            else:
                                entry.setText(str(value))
    
                        elif isinstance(entry, QComboBox):
                            if value in [entry.itemText(j) for j in range(entry.count())]:
                                entry.setCurrentText(value)
                            else:
                                incorrect_info_flag = True
    
                        elif isinstance(entry, QTextEdit):
                            entry.setPlainText(str(value))
                            
                        elif isinstance(entry, QDateEdit):
                            # 1) skip if no value (None or empty)
                            if not value:
                                continue
                        
                            # 2) strip off any trailing time ("2020-02-10 00:00:00" → "2020-02-10")
                            if isinstance(value, str) and " " in value:
                                value = value.split(" ", 1)[0]
                        
                            # 3) try ISO first, then day-first
                            d = QDate.fromString(value, "yyyy-MM-dd")
                            if not d.isValid():
                                d = QDate.fromString(value, "dd-MM-yyyy")
                        
                            # 4) if valid, set it; otherwise fall back
                            if d.isValid():
                                entry.setDate(d)
                            else:
                                incorrect_info_flag = True

                                
                        # Update image label instead of replacing it
                        if expense[-1]:  # Assuming the last column is 'Picture'
                            self.image_label.setText("Image exists in database. If you attach a new picture, the old one will be lost.")
                            self.image_label.setStyleSheet("font-style: italic; color: gray;")
                        else:
                            self.image_label.setText("No image on database for this ID.")
                            self.image_label.setStyleSheet("font-style: italic; color: gray;")
    
                else:
                    QMessageBox.warning(None, "Expense Not Found", "No expense found with the given OCnumber.")
            except sqlite3.Error as e:
                QMessageBox.critical(None, "Error", f"Failed to fetch expense data: {e}")
        
        # If data inputted were not ok, say it here with a warning message
        if incorrect_info_flag:
            QMessageBox.warning(None, "Data format/content warning", "Some values fetched in the database for this ID are incorrect. They are automatically removed and set to default in this form.")
  
#%% WIDGET CREATION
def expense_widget(self, window, modify_expense_flag=False):
    ## Main layout
    dialog_layout = QVBoxLayout(window)
    
    # Scroll Area
    scroll_area = QScrollArea(window)
    scroll_area.setWidgetResizable(True)
    
    # Content inside scroll
    scroll_content = QWidget()
    layout = QVBoxLayout(scroll_content)
        # ── COPY EXISTING EXPENSE SECTION (Add only, not in modify) ──
    if not modify_expense_flag:
        copy_layout = QHBoxLayout()
        copy_layout.addWidget(QLabel("Copy From Expense ID:"))

        # plain text entry instead of dropdown
        self.copy_expense_entry = QLineEdit()
        self.copy_expense_entry.setPlaceholderText("Enter OCnumber…")
        self.copy_expense_entry.setFixedWidth(100)
        copy_layout.addWidget(self.copy_expense_entry)

        copy_btn = QPushButton("Copy Expense")
        copy_btn.clicked.connect(self.copy_expense_to_add)
        copy_layout.addWidget(copy_btn)

        layout.addLayout(copy_layout)
        
        

    expense_entries = {}   
    
    
    ## MODIFY EXPENSE - ID SELECTION
    if modify_expense_flag:
        modify_layout = QHBoxLayout()
        label = QLabel("OC Number to Modify:")
        self.modify_expenseid_entry = QLineEdit()  # Fixed incorrect reference
        self.modify_expenseid_entry.setReadOnly(True)
        search_button = QPushButton("Search Table")
        search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("expenses", self.modify_expenseid_entry))  # Fixed table reference
        fetch_button = QPushButton("Fetch Expense")
        fetch_button.clicked.connect(self.fetch_expense_to_modify)  # Fixed function reference

        modify_layout.addWidget(label)
        modify_layout.addWidget(self.modify_expenseid_entry)
        modify_layout.addWidget(search_button)
        modify_layout.addWidget(fetch_button)
        layout.addLayout(modify_layout) 
    
    
    ## --- SECTION 1: GENERAL INFORMATION ---
    general_group = QGroupBox("General Information")
    general_layout = QGridLayout()
    
    supplier_label = QLabel("Supplier ID (*)")
    self.supplier_id_search_exp = QLineEdit()
    self.supplier_id_search_exp.setFixedWidth(200)
    self.supplier_id_search_exp.setReadOnly(True)

    search_supplier_button = QPushButton("Search Supplier")
    search_supplier_button.setIcon(QIcon( self.resource_path("images/search_supplier.png") ))  # Optional: icon
    # search_supplier_button.setIconSize(QSize(20, 20))
    search_supplier_button.clicked.connect( lambda: (self.open_modifyfromtable_selection("suppliers", self.supplier_id_search_exp)) )

    # "New Supplier" Button
    icon_path = self.resource_path("images/add_supplier.png") #self.icons_path + r"\add_supplier.png" # Load the icon
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    add_supplier_button = QPushButton("New Supplier")
    add_supplier_button.setIcon(icon)  # Assign the icon
    # add_supplier_button.setIconSize(QSize(20, 20))  # Adjust icon size
    add_supplier_button.clicked.connect(self.open_add_supplier_window)
    
    general_layout.addWidget(supplier_label, 0, 0)
    general_layout.addWidget(self.supplier_id_search_exp, 0, 1)
    general_layout.addWidget(search_supplier_button, 0, 2)
    general_layout.addWidget(add_supplier_button, 0, 3)  
    
    expense_entries["supplierid"] = self.supplier_id_search_exp

    fields = [
        ("Component", QLineEdit), 
        ("Description", QLineEdit),
        ("Link", QLineEdit),
        ("Purpose", QComboBox)]
    
    row = 1
    for field, widget_type in fields:
        # Label
        label_text = field + " (*)" if field in ["SupplierID", "Component"] else field
        label = QLabel(label_text)
        general_layout.addWidget(label, row, 0)

        # Regular widgets
        widget = widget_type() if widget_type else None

        if field == "Purpose":
                widget.addItems(["Shipping", "Materials", "OfficeSupplies", "Filament", "Printer", "Printer parts", "Marketing", "Electricity", "Phone", "Tax return", "MonthlyCosts", "Travel cost", "DigitalTools", "Other"])
                
        widget.setFixedWidth(200)

        if widget:
            general_layout.addWidget(widget, row, 1)
            expense_entries[field.lower().replace(" ", "_")] = widget
            general_layout.addWidget(QLabel(""), row, 2)  # placeholder
            
        row += 1
        
    general_group.setLayout(general_layout)
    layout.addWidget(general_group)
    
    
    ## --- SECTION 2: ORDER INFORMATION ---
    fields = [
        ("Date Ordered", QDateEdit),
        ("Date Delivery", QDateEdit),
        ("Cost Inc BTW", QLineEdit),
        ("Cost Shipping", QLineEdit), 
        ("BTW", QLineEdit),
        ("Order Status", QComboBox),
        ("Responsible", QComboBox)]
    
    order_group = QGroupBox("Order Information")
    order_layout = QGridLayout()
    
    def calculate_BTW():
        try:
            BTW = float( expense_entries["cost_inc_btw"].text() ) * (1-1/(1+self.BTW))
            expense_entries["btw"].setText(str(BTW))
        except:
            pass
    
    row = 0
    for field, widget_type in fields:
        # Label
        label_text = field + " (*)" if field in ["Date Ordered", "Cost Inc BTW", "Order Status", "Responsible"] else field
        label = QLabel(label_text)
        order_layout.addWidget(label, row, 0)
        
        # Regular widgets
        widget = widget_type() if widget_type else None

        if isinstance(widget, QComboBox):
            # Populate comboboxes based on field
            if field == "Order Status":
                widget.addItems(["Approved", "Paid", "Shipped", "Delivered", "Cancelled"])
            elif field == "Responsible":
                try:
                    self.cursor.execute("SELECT FirstName || ' ' || LastName FROM employees")
                    employees = [row[0] for row in self.cursor.fetchall()]
                    widget.addItems(["NA"] + employees)
                except sqlite3.Error:
                    widget.addItems(["NA"])

        elif isinstance(widget, QDateEdit):
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setDate(QDate.currentDate())
            if field == "Date Ordered":
                date_ordered_edit = widget  # <-- Store this for signal

        elif isinstance(widget, QLineEdit):
            widget.setFixedWidth(200)
            
        if widget:
            order_layout.addWidget(widget, row, 1)
            expense_entries[field.lower().replace(" ", "_")] = widget

        # Add Euro unit label for cost fields
        if field in ["Cost Inc BTW", "Cost Shipping", "BTW"]:
            unit_label = QLabel("€")
            order_layout.addWidget(unit_label, row, 2)

        row += 1
        
    expense_entries["cost_inc_btw"].textChanged.connect(calculate_BTW)
    
    order_group.setLayout(order_layout)
    layout.addWidget(order_group)
    
    ## --- SECTION 3: ORDER INFORMATION ---
    fields = [
        ("Tax Return Applicable", None),
        ("Invoice Uploaded", QComboBox),
        ("Tax To Be Returned", QLineEdit),
        ("Paid From", QComboBox),
        ("Refund To", QComboBox),
        ("Status Refund", QComboBox) ]
    
    payment_group = QGroupBox("Payment Information")
    payment_layout = QGridLayout()

    row = 0
    for field, widget_type in fields:
        # Label
        label_text = field + " (*)" if field == "PaidFrom" else field
        label = QLabel(label_text)
        payment_layout.addWidget(label, row, 0)

        if field == "Tax Return Applicable":
            # Composite field with two QComboBoxes
            quarter_combo = QComboBox()
            quarter_combo.addItems(["Q1", "Q2", "Q3", "Q4"])
            quarter_combo.setFixedWidth(60)

            year_combo = QComboBox()
            current_year = datetime.datetime.now().year
            year_combo.addItems([str(year) for year in range(current_year-1, current_year + 6)])
            year_combo.setFixedWidth(80)
            year_combo.setCurrentText("2025")

            hbox = QHBoxLayout()
            hbox.addWidget(quarter_combo)
            hbox.addWidget(year_combo)

            wrapper = QWidget()
            wrapper.setLayout(hbox)

            payment_layout.addWidget(wrapper, row, 1)
            expense_entries[field.lower().replace(" ", "_")] = (quarter_combo, year_combo)

        else:
            # Regular widgets
            widget = widget_type() if widget_type else None

            if isinstance(widget, QComboBox):
                # Populate comboboxes based on field
                if field == "Invoice Uploaded":
                    widget.addItems(["Yes", "No"])
                    widget.setCurrentText("No")                    
                elif field == "Paid From":
                    widget.addItems(["Personal account", "Business account"])
                    widget.setCurrentText("Business account")
                    paid_from_combo = widget
                elif field == "Refund To":
                    try:
                        self.cursor.execute("SELECT FirstName || ' ' || LastName FROM employees")
                        employees = [row[0] for row in self.cursor.fetchall()]
                        employees.append("NA")
                        widget.addItems(employees)
                        refund_to_combo = widget
                    except sqlite3.Error:
                        widget.addItems(["NA"])
                    widget.setCurrentText("NA")
                elif field == "Status Refund":
                    widget.addItems(["NA", "Approved", "Refunded", "Not Refunded"])
                    status_refund_combo = widget

            elif isinstance(widget, QLineEdit):
                widget.setFixedWidth(200)

            if widget:
                payment_layout.addWidget(widget, row, 1)
                expense_entries[field.lower().replace(" ", "_")] = widget

            # Add Euro unit label for cost fields
            if field == "Tax To Be Returned":
                unit_label = QLabel("€")
                payment_layout.addWidget(unit_label, row, 2)
            elif field == "Invoice Uploaded":
                # INVOICE BUTTON 
                invoice_upl_button = QPushButton("Upload Invoice")
                invoice_upl_button.setIcon(QIcon( self.resource_path("images/add_folder.png") ))
                invoice_upl_button.clicked.connect( self.fun_invoice_upload )
                payment_layout.addWidget(invoice_upl_button, row, 2)

        row += 1

    # Correlated fields
    def toggle_refund_fields():
        is_business = paid_from_combo.currentText() == "Business account"
        refund_to_combo.setDisabled(is_business)
        status_refund_combo.setDisabled(is_business)
        if is_business:
            refund_to_combo.setCurrentText("NA")
            status_refund_combo.setCurrentText("NA")

    paid_from_combo.currentTextChanged.connect(toggle_refund_fields)
    toggle_refund_fields()  # Ensure initial state matches default
    
    # Sync Tax Return Applicable with Date Ordered
    def update_tax_return_applicable(date):
        month = date.month()
        year = date.year()
    
        # Determine quarter
        if month in [1, 2, 3]:
            quarter_combo.setCurrentText("Q1")
        elif month in [4, 5, 6]:
            quarter_combo.setCurrentText("Q2")
        elif month in [7, 8, 9]:
            quarter_combo.setCurrentText("Q3")
        else:
            quarter_combo.setCurrentText("Q4")
    
        # Set year (if present in the combo box)
        if str(year) in [year_combo.itemText(i) for i in range(year_combo.count())]:
            year_combo.setCurrentText(str(year))
    
    date_ordered_edit.dateChanged.connect(update_tax_return_applicable)
    update_tax_return_applicable(date_ordered_edit.date())

    payment_group.setLayout(payment_layout)
    layout.addWidget(payment_group)
    
    ## --- SECTION 4: OTHERS (NOTES) ---
    others_group = QGroupBox("Others")
    others_layout = QGridLayout()
    
    notes_label = QLabel("Notes")
    notes_entry = QTextEdit()
    notes_entry.setFixedHeight(40)
    image_label = QLabel("Image")
    self.image_label = QLabel("No image selected")
    self.image_label.setStyleSheet("font-style: italic; color: gray;")

    others_layout.addWidget(notes_label, 0, 0)
    others_layout.addWidget(notes_entry, 0, 1,1,3)
    
    others_layout.addWidget(image_label, 1, 0)
    others_layout.addWidget(self.image_label, 1, 1,1,3)

    others_group.setLayout(others_layout)
    layout.addWidget(others_group)

    expense_entries["notes"] = notes_entry
    
    self.expense_entries = expense_entries
    
    # === ATTACH PICTURE BUTTON ===
    icon_path = self.resource_path("images/add_picture.png") #self.icons_path + r"\add_picture.png" # Load the icon
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    attach_picture_button = QPushButton("Attach Picture")
    attach_picture_button.setIcon(icon) 
    attach_picture_button.clicked.connect(self.attach_picture)  # Call attach picture function
    layout.addWidget(attach_picture_button)  # Add it above Save/Modify button

    icon_path = self.resource_path("images/save_button.png") # self.icons_path + r"\save_button.png" # Load the icon
    icon = QIcon(icon_path)  # PyQt5 loads icons with QIcon
    ## SAVE / MODIFY BUTTONS
    if modify_expense_flag:
        modify_button = QPushButton("Modify Expense")
        modify_button.setIcon(icon) 
        modify_button.clicked.connect(lambda: self.save_expense(modify_expense_flag=True))
        layout.addWidget(modify_button)
    else:
        save_button = QPushButton("Save New Expense")
        save_button.setIcon(icon) 
        save_button.clicked.connect(self.save_expense)
        layout.addWidget(save_button)

    scroll_area.setWidget(scroll_content)

    # Add scroll area to dialog layout
    dialog_layout.addWidget(scroll_area)
    
    # self.add_expense_window.exec_()
    # window.setLayout(layout)
    
    window.closeEvent = lambda event: self.close_event(event, window)  
    window.show()

#%% ADDING NEW EXPENSE
def open_add_expense_window(self):
    # Create a new window for adding a new expense
    self.add_expense_window = QDialog(None)
    self.add_expense_window.setWindowTitle("Add New Expense")
    self.add_expense_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.add_expense_window.resize(600, 800)
    
    # 2) Keep it on top of the main window
    # self.add_expense_window.setWindowFlags(self.add_expense_window.windowFlags() | Qt.WindowStaysOnTopHint)

    
    # Generate a new OCnumber
    start_OCnumber = 600
    self.cursor.execute("SELECT MAX(OCnumber) FROM expenses;")
    max_expense_id = self.cursor.fetchone()[0]
    self.expense_id = (max_expense_id or start_OCnumber) + 1  
        
    # Get the entry fields 
    self.expense_widget(self.add_expense_window)
    
#%% SAVE
def save_expense(self, modify_expense_flag=False):
    try:
        entries = self.expense_entries
        values = [self.expense_id]

        for key, widget in entries.items():
            if key == "supplierid":
                # Get SupplierID from display string
                supplier_id = widget.text().strip()
                if not supplier_id:
                    QMessageBox.critical(None, "Validation Error", "Invalid SupplierID selected.")
                    return
                values.append(supplier_id)

            elif key in ["cost_inc_btw"]:
                try:
                    cost = float(widget.text())
                except ValueError:
                    QMessageBox.critical(None, "Validation Error", f"{key} must be a number.")
                    return
                values.append(cost)
            elif key in ["cost_shipping", "btw", "tax_to_be_returned"] and widget.text()!= "":
                try:
                    cost = float(widget.text())
                except ValueError:
                    QMessageBox.critical(None, "Validation Error", f"{key} must be a number.")
                    return
                values.append(cost)

            elif key == "tax_return_applicable":
                value1 = widget[0].currentText()
                value2 = widget[1].currentText()
                values.append(f"{value1} {value2}")

            elif isinstance(widget, QComboBox):
                values.append(widget.currentText())

            elif isinstance(widget, QLineEdit):
                values.append(widget.text())

            elif isinstance(widget, QTextEdit):
                values.append(widget.toPlainText())
            elif isinstance(widget, QDateEdit):
                values.append(widget.date().toString("yyyy-MM-dd"))

            else:
                values.append("")  # fallback if unknown
                print("Unknown widget type")

        # Validate required combo selections
        for key in ['order_status', 'responsible']:
            widget = entries.get(key)
            if widget and widget.currentText() not in [widget.itemText(i) for i in range(widget.count())]:
                QMessageBox.critical(None, "Validation Error", f"Invalid selection in {key.replace('_', ' ').title()}.")
                return

        for key in ['invoice_uploaded', 'paid_from', 'refund_to', 'status_refund', 'purpose']:
            widget = entries.get(key)
            if widget and widget.currentText() not in [widget.itemText(i) for i in range(widget.count())] and widget.currentText() != "":
                QMessageBox.critical(None, "Validation Error", f"Invalid selection in {key.replace('_', ' ').title()}.")
                return

        # Validate required text fields
        if not entries["component"].text() or not entries["date_ordered"].date():
            raise ValueError("Missing mandatory fields.")

        if not modify_expense_flag:
            self.cursor.execute('''INSERT INTO expenses (SupplierID, Component, Description, Link, Purpose,
                                                          DateOrdered, DateDelivery, CostIncBTW, CostShipping, BTW, OrderStatus, 
                                                          Responsible, TaxReturnApplicable, InvoiceUploaded, TaxToBeReturned,
                                                          PaidFrom, RefundTo, StatusRefund, Notes)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                  tuple(values[1:]))
            self.connection.commit()
            QMessageBox.information(None, "Success", "New expense added successfully!")
            self.add_expense_window.destroy()
        else:
            self.cursor.execute("""UPDATE expenses
                                   SET SupplierID = ?, Component = ?, Description = ?, Link = ?, Purpose = ?, 
                                       DateOrdered = ?, DateDelivery = ?, CostIncBTW = ?, CostShipping = ?, BTW = ?, OrderStatus = ?, 
                                       Responsible = ?, TaxReturnApplicable = ?, InvoiceUploaded = ?, TaxToBeReturned = ?, PaidFrom = ?, 
                                       RefundTo = ?, StatusRefund = ?, Notes = ?
                                   WHERE OCnumber = ?""",
                                tuple(values[1:] + [values[0]]))
            self.connection.commit()
            QMessageBox.information(None, "Success", "Expense modified successfully")
            self.modify_window_exp.destroy()

        # Handle picture attachment
        if hasattr(self, 'selected_image_path') and os.path.exists(self.selected_image_path):
            try:
                self.cursor.execute("""UPDATE expenses SET Picture = ? WHERE OCnumber = ?""", (self.empPhoto, self.expense_id))
                self.connection.commit()
                del self.empPhoto
                del self.selected_image_path
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to read picture: {e}")
                return
        elif hasattr(self, 'selected_image_path'):
            QMessageBox.critical(None, "Error", "Selected picture path does not exist.")
            return

        self.show_table("expenses")
        # Close other windows if any
        try:
            self.handle_window_exp.close()
        except AttributeError:
            pass  # or log the error if needed

    except ValueError as e:
        QMessageBox.critical(None, "Input Error", str(e))
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to add/update expense: {e}")

def copy_expense_to_add(self):
    # 1) read the OCnumber the user typed
    oc = self.copy_expense_entry.text().strip()
    if not oc:
        QMessageBox.warning(None, "Input Error", "Please enter an expense OCnumber to copy from.")
        return

    # 2) load that row
    try:
        self.cursor.execute("SELECT * FROM expenses WHERE OCnumber = ?", (oc,))
        row = self.cursor.fetchone()
    except Exception as e:
        QMessageBox.critical(None, "Database Error", f"Failed to query expense {oc}:\n{e}")
        return

    if not row:
        QMessageBox.warning(None, "Not Found", f"No expense found with OCnumber {oc}.")
        return

    # 3) map the columns (drop OCnumber and Picture)
    cols = [
      "supplierid","component","description","link","purpose",
      "date_ordered","date_delivery","cost_inc_btw","cost_shipping",
      "btw","order_status","responsible","tax_return_applicable",
      "invoice_uploaded","tax_to_be_returned","paid_from",
      "refund_to","status_refund","notes"
    ]
    values = dict(zip(cols, row[1:-1]))

    # 4) fill in each widget
    for key, widget in self.expense_entries.items():
        val = values.get(key)
        if val is None:
            continue

        if isinstance(widget, QLineEdit):
            widget.setText(str(val))

        elif isinstance(widget, QComboBox):
            if key == "tax_return_applicable":
                q, y = str(val).split()[:2]
                widget[0].setCurrentText(q)
                widget[1].setCurrentText(y)
            else:
                idx = widget.findText(str(val))
                if idx >= 0:
                    widget.setCurrentIndex(idx)

        elif isinstance(widget, QDateEdit):
            s = str(val).split(" ")[0]
            d = QDate.fromString(s, "yyyy-MM-dd")
            if not d.isValid():
                d = QDate.fromString(s, "dd-MM-yyyy")
            if d.isValid():
                widget.setDate(d)

        elif isinstance(widget, QTextEdit):
            widget.setPlainText(str(val))



#%% MODIFYING EXPENSE
def open_modify_expense_window(self):
    # Ask for employee ID to modify
    self.modify_window_exp = QDialog(None)
    self.modify_window_exp.setWindowTitle("Modify Expense")
    self.modify_window_exp.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.modify_window_exp.resize(600, 800)
    
    # 2) Keep it on top of the main window
    # self.modify_window_exp.setWindowFlags(self.modify_window_exp.windowFlags() | Qt.WindowStaysOnTopHint)

    
    # Get the entry fields 
    self.expense_widget(self.modify_window_exp, modify_expense_flag = True)

#%% REMOVING EXPENSES
def open_remove_expense_window(self):
    self.remove_window_exp = QDialog(None)
    self.remove_window_exp.setWindowTitle("Remove Expense")
    self.remove_window_exp.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
    self.remove_window_exp.resize(300, 200)
    
    # 2) Keep it on top of the main window
    # self.remove_window_exp.setWindowFlags(self.remove_window_exp.windowFlags() | Qt.WindowStaysOnTopHint)

    
    layout = QVBoxLayout()
    
    def remove_expense(ocnumber):
        try:
            self.cursor.execute("DELETE FROM expenses WHERE OCnumber = ?", (ocnumber,))
            self.connection.commit()
            QMessageBox.information(self, "Success", "Expense removed successfully")
            self.show_table("expenses")  # Refresh the table view
            self.remove_window_exp.destroy()
            self.handle_window_exp.destroy()
        except sqlite3.Error as e:
            QMessageBox.critical(self,"Error", f"Failed to remove expense: {e}")
            
    def fetch_expense_to_remove():
        # Fetch the expense to be removed and show confirmation
        ocnumber = self.remove_ocnumber_entry.text()
        if ocnumber:
            try:
                self.cursor.execute("SELECT Description FROM expenses WHERE OCnumber = ?", (ocnumber,))
                expense = self.cursor.fetchone()
    
                if expense:
                    confirmation = QMessageBox.question(
                        self, "Confirm Deletion",
                        f"Are you sure you want to delete expense {expense[0]} with OCnumber {ocnumber}?")
                    if confirmation == QMessageBox.Yes:
                        remove_expense(ocnumber)
                else:
                    QMessageBox.warning(self, "Expense Not Found", "No expense found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch expense data: {e}")
    
    # Specify ID, fetch it and remove it
    label = QLabel("OCnumber to Remove:")
    self.remove_ocnumber_entry = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(self.remove_ocnumber_entry)
    
    # Button to open selection table
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("expenses", self.remove_ocnumber_entry))
    layout.addWidget(search_button)
    
    fetch_button = QPushButton("Remove Expense")
    fetch_button.clicked.connect(fetch_expense_to_remove)
    layout.addWidget(fetch_button)
    
    self.remove_window_exp.setLayout(layout)
    self.remove_window_exp.show()
    
   

    

