# -*- coding: utf-8 -*-
"""
Requests / orders handling windows

@author: feder
"""

import sqlite3
from PyQt5.QtWidgets import ( QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMenu, QTabWidget, QDateEdit, QFileDialog,
    QMessageBox, QGridLayout, QFrame, QGroupBox, QTextEdit, QScrollArea,
    QDialog, QSpacerItem, QSizePolicy )
from PyQt5.QtCore import Qt
import re


#%% HANDLE TAB: see, modify, delete requests
def open_handle_order_window(self):
    # Open a new window for modifications
    self.handle_window_order = QDialog(self)
    self.handle_window_order.setWindowTitle("Handle Requests")
    self.handle_window_order.resize(300, 200)
    
    layout = QVBoxLayout()

    # See button
    see_requests_button = QPushButton("See All Requests")
    def _show_and_wire_orders(table, open_req=False, active_ord=False, print_parts = False):
        self.show_table(table, open_req=open_req, active_ord=active_ord, print_parts=print_parts)
        try:
            self.table.cellDoubleClicked.disconnect()
        except TypeError:
            pass
        self.table.cellDoubleClicked.connect(self._on_order_doubleclick)


    see_requests_button.clicked.connect(lambda:_show_and_wire_orders(table="orders"))
    layout.addWidget(see_requests_button)

    see_open_requests_button = QPushButton("See Open Requests")
    # see_open_requests_button.clicked.connect(lambda: self.show_table("orders", open_req = True))
    see_open_requests_button.clicked .connect(lambda:_show_and_wire_orders(table="orders", open_req=True))
    layout.addWidget(see_open_requests_button)
    
    see_active_orders_button = QPushButton("See Active Orders")
    # see_active_orders_button.clicked.connect(lambda: self.show_table("orders", active_ord = True))
    see_active_orders_button.clicked.connect(lambda:_show_and_wire_orders(table="orders", active_ord=True))
    layout.addWidget(see_active_orders_button)
    
    # See parts button
    see_parts_button = QPushButton("See All Request Parts")
    # see_parts_button.clicked.connect(lambda: self.show_table("orderparts"))
    see_parts_button.clicked.connect(lambda:_show_and_wire_orders(table="orderparts"))
    layout.addWidget(see_parts_button)
    
    see_printing_progress_button = QPushButton("See Parts Printing Progress")
    # see_printing_progress_button.clicked.connect(lambda: self.show_table("orderparts", print_parts = True))
    see_printing_progress_button.clicked.connect(lambda:_show_and_wire_orders(table="orderparts", print_parts = True))
    layout.addWidget(see_printing_progress_button)
    
    # Modify button
    modify_request_button = QPushButton("Modify Request")
    modify_request_button.clicked.connect(self.open_modify_order_window)
    layout.addWidget(modify_request_button)

    # Remove button
    remove_request_button = QPushButton("Remove Request")
    remove_request_button.clicked.connect(self.open_remove_order_window)
    layout.addWidget(remove_request_button)
    
    self.handle_window_order.setLayout(layout)
    self.handle_window_order.show()
    
def _on_order_doubleclick(self, row, col):
    # 1) grab the CustomerID from column 0
    ord_id = self.table.item(row, 0).text()
    if not ord_id:
        return

    # 2) open the Modify Customer window (this creates self.modify_customer_id_entry)
    self.open_modify_order_window()

    # 3) now fill that dialog’s ID-entry with your selected ID
    self.modify_order_id_entry.setText(ord_id)
    # now immediately fetch & populate all other fields
    self.fetch_order_to_modify()
    
def fetch_order_to_modify(self):
    self.orderid = self.modify_order_id_entry.text().strip()
    
    if not self.orderid:
        QMessageBox.warning(self, "Input Error", "Please enter an Order ID.")
        return

    try:
        self.cursor.execute("SELECT * FROM orders WHERE OrderID = ?", (self.orderid,))
        order = self.cursor.fetchone()
        
        if not order:
            QMessageBox.warning(self, "Order Not Found", "No order found with the given ID.")
            return

        # Get column names to map keys to order values
        column_names = [
            re.sub(r'(?<!^)(?=[A-Z])', '_', desc[0])
            .replace(" ", "_")
            .lower()
            if all(x not in desc[0] for x in ["ID", "BTW"])
            else desc[0].replace(" ", "_").lower()
            for desc in self.cursor.description ]

        order_data = dict(zip(column_names, order))
        self.order_data = order_data
        
        # Create a new window with the data filled in
        self.pick_order_to_modify_window.close()
        self.modify_window_order = QDialog(None)
        self.modify_window_order.setWindowTitle(f"Modify OrderID {self.orderid}")
        self.modify_window_order.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.modify_window_order.resize(1800, 800)  # Width, Height
        
        self.orders_setup_tabs(self.modify_window_order, modify_flag = True)

    except sqlite3.Error as e:
        QMessageBox.critical(self, "Error", f"Failed to fetch order data:\n{e}")

#%% SET UP ORDER WIDGET
def orders_setup_tabs(self, window, modify_flag = False):  
    self.parts = []  # List to keep track of parts
    
    # Create a Notebook (Tab widget)
    self.notebook = QTabWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(self.notebook)

    # Tab 1 - Order Tracking Tab
    ordertracking_tab = QScrollArea()
    ordertracking_tab.setWidgetResizable(True)
    self.notebook.addTab(ordertracking_tab, "Order Tracking")
    self.tab1_widgets(ordertracking_tab, modify_flag)

    # --- Tab 2 - Price Estimation ---
    priceestimation_tab = QScrollArea()
    priceestimation_tab.setWidgetResizable(True)
    self.notebook.addTab(priceestimation_tab, "Price Estimation")
    self.tab2_widgets(priceestimation_tab, modify_flag)
 
    # Tab 3 - Overview of the order
    overview_tab = QScrollArea()
    overview_tab.setWidgetResizable(True)
    self.notebook.addTab(overview_tab, "Order Overview")
    self.tab3_widgets(overview_tab, modify_flag)
    
    window.closeEvent = lambda event: self.close_event(event, window)
    window.show()
    
    
#%% ADD ORDER 
def open_add_order_window(self):
    # Create a new window for adding a new order
    self.add_order_window = QDialog(None)
    self.add_order_window.setWindowTitle("Add New Request")
    # self.add_order_window.showMaximized()
    self.add_order_window.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
    self.add_order_window.resize(1600, 700)  # Width, Height
    
        # 2) Keep it on top of the main window
    # self.add_order_window.setWindowFlags(self.add_order_window.windowFlags() | Qt.WindowStaysOnTopHint)

    
    # Generate a new OrderID
    try:
        self.cursor.execute("SELECT MAX(OrderID) FROM orders;")
        max_order_id = self.cursor.fetchone()[0]
        self.orderid = (max_order_id or 0) + 1  # Increment max OrderID or start at 1 if none exist
    except ValueError as e:
        QMessageBox.critical(None, "Error", f"Failed to generate OrderID: {e}")
        return
    
    self.orders_setup_tabs(self.add_order_window)
    

    
#%% MODIFY ORDER    
def open_modify_order_window(self):
    #  Create window to select order
    self.pick_order_to_modify_window = QDialog(None)
    self.pick_order_to_modify_window.setWindowTitle("Pick Request to Modify")
    
    # 2) Keep it on top of the main window
    # self.pick_order_to_modify_window.setWindowFlags(self.pick_order_to_modify_window.windowFlags() | Qt.WindowStaysOnTopHint)

    
    main_layout = QVBoxLayout(self.pick_order_to_modify_window)
    # --- Row: Label, Entry, and Search Button ---
    entry_layout = QHBoxLayout()
    label = QLabel("Select Order ID to Modify:")
    self.modify_order_id_entry = QLineEdit()
    self.modify_order_id_entry.setReadOnly(True)
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("orders", self.modify_order_id_entry))
    
    entry_layout.addWidget(label)
    entry_layout.addWidget(self.modify_order_id_entry)
    entry_layout.addWidget(search_button)
    
    # --- Fetch Button  ---
    fetch_button = QPushButton("Fetch Order")
    fetch_button.clicked.connect(self.fetch_order_to_modify)
    
    # --- Add everything to the main layout ---
    main_layout.addLayout(entry_layout)
    main_layout.addWidget(fetch_button)
    
    self.pick_order_to_modify_window.show()



#%% Function to get the selected services as a comma-separated string
def get_selected_services(self):
    selected_services = [service for service, var in self.service_vars.items() if var.get()]
    return ", ".join(selected_services)
 
#%% SAVE ORDER DETAILS IN TABLE DB
def save_order(self, modify_flag=False):
    orderid = self.orderid
    number_parts = (len(self.parts) or 0) #If its none, make it zero
    
    try:
        # old_parts = (self.order_data.get('number_parts') or 0) #If its none, make it zero
        # 1. SAVE ORDER PARTS
        # if modify flag, delete parts if number changes. 
        if modify_flag and ((number_parts > (self.order_data.get('number_parts') or 0)) or (number_parts < (self.order_data.get('number_parts') or 0))):    
                self.cursor.execute("DELETE FROM orderparts WHERE OrderID = ?", (orderid,))
                self.connection.commit()
            
        ordered_parts = 0
        printed_parts = 0
        for i in range(len(self.parts)):
            part_data = self.parts[i]    
            part_id = part_data['PartID']
            ordered_parts += int(part_data['QuantityOrdered'])
            printed_parts += int(part_data['QuantityPrinted'])
            # Insert the data into the orderparts table
            if modify_flag and (number_parts == self.order_data['number_parts']):
                self.cursor.execute('''UPDATE orderparts
                       SET PartName = ?, Materials = ?, Color = ?, QuantityOrdered = ?, QuantityPrinted = ?, 
                           PrintSettings = ? WHERE OrderID = ? AND PartNr = ?''',
                    (part_data['PartName'], part_data['Materials'], 
                     part_data['Color'],  part_data['QuantityOrdered'], part_data['QuantityPrinted'], 
                     part_data['PrintSettings'], orderid, part_id))

            else: #insert in db
                self.cursor.execute('''INSERT INTO orderparts (
                                        OrderID, PartNr, PartName, Materials, Color,
                                        QuantityOrdered, QuantityPrinted, PrintSettings) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                    (orderid, part_id, part_data['PartName'], part_data['Materials'], part_data['Color'], 
                                      part_data['QuantityOrdered'], part_data['QuantityPrinted'], part_data['PrintSettings']))
           
        
        # Validate fields
        self.validate_fields_tab1() 
        self.validate_fields_tab2()
        
        # --- Collect Tab 1 entries ---
        customer_id = self.order_entries_tab1["customerid"].text().strip()
        description = self.order_entries_tab1["description"].text().strip()
        date_ordered = self.order_entries_tab1["date_ordered"].date().toString("yyyy-MM-dd")
        date_required = self.order_entries_tab1["date_required"].date().toString("yyyy-MM-dd")
        stage = self.order_entries_tab1["stage"].currentText()
        status = self.order_entries_tab1["status"].currentText()
        responsible = self.order_entries_tab1["responsible"].currentText()
        last_updated = self.order_entries_tab1["last_updated"].date().toString("yyyy-MM-dd")
        invoice_nr = self.order_entries_tab1["invoice_number"].text().strip()

        # --- Services (checkboxes as list) ---
        services_str = self.separate_checkbox_values(self.service_vars)

        # --- Tab 2 entries ---
        printer_type = self.order_entries_tab2["printerids"].text().strip()
        filament_type = self.order_entries_tab2["filamentids"].text().strip()
        print_weight = float(self.order_entries_tab2["print_weight"].text().strip())
        print_time = float(self.order_entries_tab2["print_time"].text().strip())
        design_time = float(self.order_entries_tab2["design_time"].text().strip())
        labour_time = float(self.order_entries_tab2["labour_time"].text().strip())
        shipping_type = self.order_entries_tab2["shipping_type"].currentText()
        shipping_quantity = float(self.order_entries_tab2["shipping_quantity"].text().strip())
        extra_services_cost = float(self.order_entries_tab2["extra_services_cost"].text().strip())
        total_cost = float(self.order_entries_tab2["priceexclbtw"].text().strip())

        # --- Extra services (checkboxes + optional others entry) ---
        extraservices_str = self.separate_checkbox_values(self.extraservice_vars, self.others_entry)

        # Number parts, progress
        progress = f"{int(printed_parts)}/{int(ordered_parts)}"
        
        notes = self.ordernotes.toPlainText()
        
        # List all values
        values = (
            customer_id, services_str, description, date_ordered, date_required,
            stage, status, invoice_nr, responsible, last_updated, 
            number_parts, progress,
            printer_type, filament_type, print_weight, print_time, design_time,
            labour_time, shipping_type, shipping_quantity,
            extraservices_str, extra_services_cost, total_cost, notes  )
        
        if modify_flag:
            query = '''
                UPDATE orders SET
                    CustomerID = ?, Services = ?, Description = ?, DateOrdered = ?, DateRequired = ?,
                    Stage = ?, Status = ?, InvoiceNumber = ?, Responsible = ?, LastUpdated = ?,
                    NumberParts = ?, Progress = ?,
                    PrinterIDs = ?, FilamentIDs = ?, PrintWeight = ?, PrintTime = ?, DesignTime = ?,
                    LabourTime = ?, ShippingType = ?, ShippingQuantity = ?,
                    ExtraServices = ?, ExtraServicesCost = ?, PriceExclBTW = ?, Notes = ?
                WHERE OrderID = ?
            '''
            values = values + (orderid,)
            success_string = f"OrderID{orderid} updated successfully."
            window = self.modify_window_order
        else:
            query = '''
                INSERT INTO orders (
                    CustomerID, Services, Description, DateOrdered, DateRequired,
                    Stage, Status, InvoiceNumber, Responsible, LastUpdated,
                    NumberParts, Progress,
                    PrinterIDs, FilamentIDs, PrintWeight, PrintTime, DesignTime,
                    LabourTime, ShippingType, ShippingQuantity,
                    ExtraServices, ExtraServicesCost, PriceExclBTW, Notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            success_string = f"New Order ID {orderid} saved successfully."
            window = self.add_order_window

        self.cursor.execute(query, values)
        self.connection.commit()

        QMessageBox.information(self, "Success", success_string)
        
        window.close()
        
        self.show_table("orders")

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to save order:\n{e}")
    

#%% Invoice tab
# Invoice created and sent? Yes/No
# If yes fill in number (later should be made automatically)

#%% REMOVE ORDER
def open_remove_order_window(self):
    # Create the dialog window
    self.remove_window_ord = QDialog(None)  # or parent it to your main window
    self.remove_window_ord.setWindowTitle("Remove Request")
    self.remove_window_ord.setFixedSize(300, 200)
    
        # 2) Keep it on top of the main window
    # self.remove_window_ord.setWindowFlags(self.remove_window_ord.windowFlags() | Qt.WindowStaysOnTopHint)

    
    main_layout = QVBoxLayout(self.remove_window_ord)
    
    # --- Row: Label, Entry, and Search Button ---
    entry_layout = QHBoxLayout()
    label = QLabel("Select Order ID to Remove:")
    self.remove_order_id_entry = QLineEdit()
    self.remove_order_id_entry.setReadOnly(True)
    search_button = QPushButton("Search Table")
    search_button.clicked.connect(lambda: self.open_modifyfromtable_selection("orders", self.remove_order_id_entry))
    
    entry_layout.addWidget(label)
    entry_layout.addWidget(self.remove_order_id_entry)
    entry_layout.addWidget(search_button)
    
    def remove_order(order_id):
        try:
            # Remove from orders table
            self.cursor.execute("DELETE FROM orders WHERE OrderID = ?", (order_id,))
            self.connection.commit()

            # Remove from parts table
            self.cursor.execute("DELETE FROM orderparts WHERE OrderID = ?", (order_id,))
            self.connection.commit()

            QMessageBox.information(self.remove_window_ord, "Success", "Request removed successfully")
            self.show_table("orders")  # Refresh the table view

            if hasattr(self, 'handle_window_ord'):
                self.handle_window_ord.close()

            self.remove_window_ord.accept()
        except sqlite3.Error as e:
            QMessageBox.critical(self.remove_window_ord, "Error", f"Failed to remove request: {e}")

    def fetch_order_to_remove():
        order_id = self.remove_order_id_entry.text()
        if order_id:
            try:
                self.cursor.execute("SELECT Description, Services FROM orders WHERE OrderID = ?", (order_id,))
                order = self.cursor.fetchone()

                if order:
                    reply = QMessageBox.question(
                        self.remove_window_ord,
                        "Confirm Deletion",
                        f"Are you sure you want to delete request {order[0]} ({order[1]}) with OrderID {order_id}?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        remove_order(order_id)
                else:
                    QMessageBox.warning(self.remove_window_ord, "Request Not Found", "No request found with the given ID.")
            except sqlite3.Error as e:
                QMessageBox.critical(self.remove_window_ord, "Error", f"Failed to fetch request data: {e}")
    
    # --- Delete Button (below the row) ---
    delete_button = QPushButton("Delete Order")
    delete_button.clicked.connect(fetch_order_to_remove)
    
    # --- Add everything to the main layout ---
    main_layout.addLayout(entry_layout)
    main_layout.addWidget(delete_button)
        
    self.remove_window_ord.show()
    
    