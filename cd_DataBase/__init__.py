#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Class definition for the 3BP Database application using PyQt5.
Here the following is defined:
    - App main page with buttons and table visualization
    - All database (self) functions
    - Base functions and repetitive functions (used in many parts of the database)

@author: feder
"""

import sqlite3
import re
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QSizePolicy, QMessageBox, QFileDialog, QMenu)
from PyQt5.QtWidgets import QAction, QDialog, QMessageBox,QApplication
from settings_dialog import SettingsDialog, load_settings, save_settings
from .analytics import (
    RevenuePerPeriodDialog,
    CostOfGoodsSoldDialog,
    ExpensesByCategoryDialog,
    MonthlyBurnRateDialog,
    FixedVariableExpensesDialog,
    ExpenseTrendByCategoryDialog,
    TopExpensesDialog,
    ExpenseToRevenueRatioDialog,
    RequestsConversionDialog,
    OrderStatusDialog,
    ServiceMixDialog,
    AverageOrderCostDialog,
    ExpensesByPeriodDialog,
)


from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt
from functools import partial
import os
import subprocess
import shutil
import sys

import json


from PyQt5.QtCore   import QTimer




class DatabaseApp(QMainWindow):
    #%% Import methods from sub-modules (assumed adapted for PyQt5)
    from ._showtable import show_table, insert_rows_to_table, search_table, reset_table, open_image
    from ._handle_customers import open_handle_customers_window, open_add_customer_window, open_modify_customer_window, open_remove_customer_window, save_customer, customer_widget, _on_customer_doubleclick, fetch_customer_to_modify
    from ._handle_suppliers import open_handle_suppliers_window, open_add_supplier_window, open_modify_supplier_window, open_remove_supplier_window, save_supplier, supplier_widget, _on_supplier_doubleclick, fetch_supplier_to_modify
    from ._handle_printsettings import open_handle_printsetting_window, widget_printsettings, open_add_printsetting_window, open_modify_printsetting_window, save_printsettings, open_remove_printsettings_window, open_print_settings_window, assign_printsetting, confirm_assign
    from ._handle_inventory import open_handle_printers_window, open_add_printer_window, open_modify_printer_window, open_remove_printer_window, printer_widgets, save_printer, open_handle_filaments_window, open_add_filament_window, open_modify_filament_window, open_remove_filament_window, filament_widgets, update_price, save_filament, get_selected_properties, restock_filament, _on_printer_doubleclick, fetch_printer_to_modify, _on_filament_doubleclick, fetch_filament_to_modify
    from ._handle_employees import open_handle_employees_window, open_add_employee_window, open_modify_employee_window, open_remove_employee_window, save_employee, employee_widget, _on_employee_doubleclick, fetch_employee_to_modify
    from ._handle_expenses import open_handle_expenses_window, open_add_expense_window, open_modify_expense_window, open_remove_expense_window, expense_widget, save_expense, _on_expense_doubleclick, fetch_expense_to_modify,copy_expense_to_add

    from ._handle_orders import open_add_order_window, open_handle_order_window, open_modify_order_window, open_remove_order_window, save_order, get_selected_services, orders_setup_tabs, fetch_order_to_modify, _on_order_doubleclick
    # Import tab widgets from separate files
    from ._order_tab1 import tab1_widgets, validate_fields_tab1, fun_task_assignment, fun_folder_upload, create_parts_table_tab1, _open_invoice_window
    from ._order_tab2 import tab2_widgets, open_printer_selection, open_filament_selection, price_estimation, update_BTW_and_profit, validate_fields_tab2
    from ._order_tab3 import tab3_widgets, fun_ask_price_consultation_email, fun_client_email
    from ._import_export_exceldata import fun_import_database, fun_export_database
    
    
    def __init__(self, database_path, settings):        
        #%% Initialize database connection
        super(DatabaseApp, self).__init__()
        self.settings = load_settings()
        self._create_menus()
        self.database_path = database_path
        self.connection = sqlite3.connect(self.database_path)
        self.cursor = self.connection.cursor()
        
        #%% --- INPUTS ---
        # Define global data used all over database
        
        one_drive_root = os.path.abspath(
            os.path.join(self.database_path, os.pardir, os.pardir, os.pardir)
            )
        self.one_drive_local_path = one_drive_root
        # Cost estimation inputs
        self.BTW = 0.21  # 21%
        self.postNLprices = [4.25, 5.95, 6.95, 14.50]
        
        # Cost rates - inputs for cost calc
        self.design_hourly_rate = settings['design_hourly_rate'] #e/h
        self.labour_hourly_rate = settings['labour_hourly_rate'] #e/h
        self.printer_power_reference = 400 #W
        self.filament_price_reference = 0.03 #e/g
        
        # Define design parameters for main page
        style_group = "QGroupBox { font-weight: bold; font-size: 12pt; font-family: 'Segoe UI'; }"
        button_font = QFont("Segoe UI", 10)  # Define font once
        button_width = 250  # Set desired width
        button_height = 30
        button_style = "QPushButton { color: #4A4A4A; }"  # Dark Gray Text
        
        #%% --- MAIN WINDOW DEFINITION ---
        # Define paths
        self.upload_folder_path = os.path.join(self.one_drive_local_path, "01 File upload")
        self.upload_order_invoice_path = os.path.join(self.one_drive_local_path, "02 Financial", "Orders Invoices") 
        self.upload_expense_invoice_path = os.path.join(self.one_drive_local_path, "02 Financial", "Invoices") 
        # self.icons_path = os.path.join(os.getcwd(), "images")
        
        # Organize layout main page
        self.setWindowTitle("3Bee Printing Database")
        self.setWindowIcon(QIcon(self.resource_path("images/3bp_logo.png")))


        # Set up a central widget with a horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        #%% LEFT PANEL: divided into 3 groups w/ logo
        self.action_frame = QWidget()
        action_layout = QVBoxLayout(self.action_frame)
        action_layout.setAlignment(Qt.AlignTop)

        # Logo
        self.logo_label = QLabel()
        pixmap = QPixmap( self.resource_path("images/3bp_logo.png") )
        if not pixmap.isNull():
            pixmap = pixmap.scaled(260, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        action_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)

        # Group: Inventories
        self.inventory_group = QGroupBox("Tables")
        inventory_layout = QVBoxLayout()

        self.handle_employees_button = QPushButton("Employees")
        self.handle_employees_button.clicked.connect(self.open_handle_employees_window)
        inventory_layout.addWidget(self.handle_employees_button)
        
        self.handle_customer_button = QPushButton("Customers")
        self.handle_customer_button.clicked.connect(self.open_handle_customers_window)
        inventory_layout.addWidget(self.handle_customer_button)
        
        self.handle_supplier_button = QPushButton("Suppliers")
        self.handle_supplier_button.clicked.connect(self.open_handle_suppliers_window)
        inventory_layout.addWidget(self.handle_supplier_button)
        
        self.handle_expense_button = QPushButton("Expenses")
        self.handle_expense_button.clicked.connect(self.open_handle_expenses_window)
        inventory_layout.addWidget(self.handle_expense_button)
        
        self.handle_printers_button = QPushButton("Printers")
        self.handle_printers_button.clicked.connect(self.open_handle_printers_window)
        inventory_layout.addWidget(self.handle_printers_button)
        
        self.handle_filaments_button = QPushButton("Filaments")
        self.handle_filaments_button.clicked.connect(self.open_handle_filaments_window)
        inventory_layout.addWidget(self.handle_filaments_button)
        
        self.handle_printset_button = QPushButton("Print Settings")
        self.handle_printset_button.clicked.connect(self.open_handle_printsetting_window)
        inventory_layout.addWidget(self.handle_printset_button)
        

        
        self.inventory_group.setLayout(inventory_layout)
        action_layout.addWidget(self.inventory_group)

        # Group: Requests & Orders
        self.request_group = QGroupBox("Requests handling")
        request_layout = QVBoxLayout()
        
        self.handle_orders_button = QPushButton("See Requests")
        self.handle_orders_button.clicked.connect(self.open_handle_order_window)
        request_layout.addWidget(self.handle_orders_button)
        
        self.add_order_button = QPushButton("Add a New Request")
        self.add_order_button.clicked.connect(self.open_add_order_window)
        request_layout.addWidget(self.add_order_button)



        self.request_group.setLayout(request_layout)
        action_layout.addWidget(self.request_group)

        # Group: Analytics
        self.analytics_group = QGroupBox("Analytics")
        analytics_layout = QVBoxLayout()
        analytics_layout.addWidget(QLabel("Analytics Features (To be implemented)"))
        self.analytics_group.setLayout(analytics_layout)
        action_layout.addWidget(self.analytics_group)
        
        # # Group: Datasets
        # self.datasets_group = QGroupBox("Datasets")
        # datasets_layout = QVBoxLayout()
        # self.import_excel_button = QPushButton("Import Excel Data")
        # self.import_excel_button.clicked.connect(self.fun_import_database)
        # datasets_layout.addWidget(self.import_excel_button)
        
        # self.export_excel_button = QPushButton("Export to Excel")
        # self.export_excel_button.clicked.connect(self.fun_export_database)
        # datasets_layout.addWidget(self.export_excel_button)
        
        # self.datasets_group.setLayout(datasets_layout)
        # action_layout.addWidget(self.datasets_group)
        
              
        # DESIGN OF LEFT PANEL: Specify fonts and sizes
        self.inventory_group.setStyleSheet(style_group)
        self.request_group.setStyleSheet(style_group)
        self.analytics_group.setStyleSheet(style_group)
        # self.datasets_group.setStyleSheet(style_group)

        for button in [self.handle_printers_button, self.handle_filaments_button, self.handle_employees_button,
            self.handle_customer_button, self.handle_supplier_button, self.handle_expense_button, self.handle_printset_button,
            self.add_order_button, self.handle_orders_button]:
            button.setFont(button_font)
            button.setFixedSize(button_width, button_height)  # Fixed width and height
            button.setStyleSheet(button_style)  # Apply text color


        main_layout.addWidget(self.action_frame)
        
        #%% RIGHT PANEL: Table Display
        self.table_frame = QWidget()
        self.table_frame.setLayout(QVBoxLayout())  # Ensure it has a layout
        self.table_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table_frame.setMinimumSize(1000, 600)  # Ensures the panel is large enough

        main_layout.addWidget(self.table_frame, stretch=2)
        
        # Call the function to populate the table
        self.show_table("printsettings")
    
#%% APP or COMMON FUNCTIONS are defined here
    def _create_menus(self):
        menubar = self.menuBar()
    
        # --- File Menu ---
        file_menu = menubar.addMenu("&File")
        imp = QAction("Import Database…", self)
        imp.triggered.connect(self.fun_import_database)
        file_menu.addAction(imp)
        exp = QAction("Export Database…", self)
        exp.triggered.connect(self.fun_export_database)
        file_menu.addAction(exp)
    
        # --- Settings Menu ---
        settings_menu = menubar.addMenu("&Settings")
        settings_act = QAction("Settings…", self)
        settings_act.triggered.connect(self._open_settings)
        settings_menu.addAction(settings_act)
    
        # --- View Menu ---
        view_menu = menubar.addMenu("&View")
        upd = QAction("Check for updates…", self)
        upd.triggered.connect(self._check_for_updates)
        view_menu.addAction(upd)
    
        # --- Analytics Menu ---
        analytics_menu = menubar.addMenu("&Analytics")
    
        # Financial Metrics
        fm = QMenu("Financial Metrics", self)
        # 1.1 Revenue & Profit
        rev = QMenu("Revenue & Profit", self)
        rev.addAction("Revenue per Period…", 
                      lambda: RevenuePerPeriodDialog(self, self.connection).exec_())
        rev.addAction("Cost of Goods Sold (COGS)…", 
                      lambda: CostOfGoodsSoldDialog(self, self.connection).exec_())
        rev.addAction("Gross Profit & Margin…")  # placeholder
        fm.addMenu(rev)
        # 1.2 Expense Breakdown
        eb = QMenu("Expense Breakdown", self)
        eb.addAction("Expenses by Category…", 
                     lambda: ExpensesByCategoryDialog(self, self.connection).exec_())
        eb.addAction("Expenses by Period…", 
             lambda: ExpensesByPeriodDialog(self, self.connection).exec_())
        eb.addAction("Monthly Burn Rate…", 
                     lambda: MonthlyBurnRateDialog(self, self.connection).exec_())
        eb.addAction("Fixed vs Variable Expenses…", 
                     lambda: FixedVariableExpensesDialog(self, self.connection).exec_())
        eb.addAction("Expense Trend by Category…", 
                     lambda: ExpenseTrendByCategoryDialog(self, self.connection).exec_())
        eb.addAction("Top 10 Expenses…", 
                     lambda: TopExpensesDialog(self, self.connection).exec_())
        eb.addAction("Expense-to-Revenue Ratio…", 
                     lambda: ExpenseToRevenueRatioDialog(self, self.connection).exec_())
        fm.addMenu(eb)
        # 1.3 Cash Flow (placeholders)
        cf = QMenu("Cash Flow", self)
        cf.addAction("Invoices Issued vs Paid…")
        cf.addAction("Outstanding Receivables…")
        fm.addMenu(cf)
    
        analytics_menu.addMenu(fm)
    
        # Operational Metrics
        op = QMenu("Operational Metrics", self)
        # 2.1 Orders & Requests
        ordr = QMenu("Orders & Requests", self)
        ordr.addAction("Requests vs Converted Orders…", 
                       lambda: RequestsConversionDialog(self, self.connection).exec_())
        ordr.addAction("Order Acceptance Rates…", 
                       lambda: OrderStatusDialog(self, self.connection).exec_())
        op.addMenu(ordr)
        # 2.2 Service Mix
        svc = QMenu("Service Mix", self)
        svc.addAction("Service Mix Breakdown…", 
                      lambda: ServiceMixDialog(self, self.connection).exec_())
        svc.addAction("Average Order Cost…", 
                      lambda: AverageOrderCostDialog(self, self.connection).exec_())
        op.addMenu(svc)
        # 2.3 Task & Resource Utilization (placeholders)
        tr = QMenu("Task & Resource Utilization", self)
        tr.addAction("Printer Utilization…")
        tr.addAction("Employee Workload…")
        op.addMenu(tr)
    
        analytics_menu.addMenu(op)
    
        # Inventory Metrics
        inv = QMenu("Inventory Metrics", self)
        # 3.1 Filament Stock
        fs = QMenu("Filament Stock", self)
        fs.addAction("Stock Levels vs Usage…")
        fs.addAction("Days of Stock on Hand…")
        inv.addMenu(fs)
        # 3.2 Printers & Print Settings
        ps = QMenu("Printers & Print Settings", self)
        ps.addAction("Print Setting Performance…")
        ps.addAction("Cost per Material…")
        inv.addMenu(ps)
    
        analytics_menu.addMenu(inv)
    
        # Customer & Supplier Metrics
        cs = QMenu("Customer & Supplier Metrics", self)
        cu = QMenu("Customers", self)
        cu.addAction("Top Customers by Revenue…")
        cu.addAction("New vs Returning…")
        cu.addAction("Customer Lifetime Value…")
        cs.addMenu(cu)
        su = QMenu("Suppliers", self)
        su.addAction("Spend by Supplier…")
        su.addAction("Lead Times…")
        cs.addMenu(su)
    
        analytics_menu.addMenu(cs)
    
        # --- Help Menu ---
        help_menu = menubar.addMenu("&Help")
        about = QAction("About…", self)
        # about.triggered.connect(self._show_about)
        help_menu.addAction(about)




    def _check_for_updates(self):
        """
        Look in a “dist” subfolder next to the database file for version.json,
        compare versions, prompt the user, copy the new .exe over the running one,
        and restart.
        """
        # 1) Determine the folder containing your .db and locate dist/
        db_dir   = os.path.dirname(self.database_path)
        dist_dir = os.path.join(db_dir, "dist")
        ver_file = os.path.join(dist_dir, "version.json")

        # 2) Read version.json
        try:
            with open(ver_file, "r") as f:
                info    = json.load(f)
                new_ver = info["version"]
                new_exe = info["exe"]
        except Exception as e:
            QMessageBox.warning(
                self,
                "Update check failed",
                f"Could not read update info:\n{ver_file}\n{e}"
            )
            return

        # 3) Compare to current version stored in settings (default 0.0.0)
        current_ver = self.settings.get("version", "0.0.0")
        if new_ver <= current_ver:
            QMessageBox.information(
                self,
                "No update available",
                "You already have the latest version."
            )
            return

        # 4) Ask the user if they want to install
        if QMessageBox.question(
                self,
                "Update available",
                f"A new version ({new_ver}) is available.\nInstall and restart now?",
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
            return

        # 5) Copy the new executable over the running one
        src = os.path.join(dist_dir, new_exe)
        tgt = sys.executable
        try:
            shutil.copy2(src, tgt)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Update failed",
                f"Could not replace executable:\n{e}"
            )
            return

        # 6) Record the new version and restart
        self.settings["version"] = new_ver
        save_settings(self.settings)

        QMessageBox.information(
            self,
            "Update installed",
            "Update complete. The application will now restart."
        )
        QTimer.singleShot(100, self._restart)

    def _restart(self):
        """Quit and re-launch the current executable."""
        QApplication.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)



    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.settings = load_settings()
            # TODO: propagate any changed settings into your UI

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.connection:
                self.connection.close()
            event.accept()
        else:
            event.ignore()
         
    # Handle images paths for both exe and py
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    
    # Check formats (validation)
    def is_float(self, value):
        try:
            float(value.replace(",", "."))
            return True
        except ValueError:
            return False
    
    def is_valid_email(self, email):
        email_regex = (r"^(?!\.)[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]+"
                        r"(?<!\.)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        return re.match(email_regex, email) is not None
    
    ## Prevent accidental closing of windows 
    def close_event(self, event, window):
        if event.spontaneous():
            reply = QMessageBox.question(window, "Confirm Exit", "Are you sure you want to close?\nIf you close now, the progress won't be saved.", 
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()   
    
    # Help windows with ? mark
    def create_label_with_help(self, help_text, layout, row, col):
        """Creates a '?' button that shows/hides a floating help popup."""
        help_button = QPushButton("?")
        help_button.setFixedWidth(30)
        layout.addWidget(help_button, row, col)
    
        # Store the popup reference per button
        help_popup = None
    
        def toggle_help():
            nonlocal help_popup
    
            if help_popup and help_popup.isVisible():
                help_popup.close()
                help_popup = None
                return
    
            # Create new popup
            help_popup = QWidget(help_button, Qt.ToolTip)
            help_popup.setWindowFlags(Qt.ToolTip)
            help_popup.setAttribute(Qt.WA_DeleteOnClose)
    
            label = QLabel(help_text, help_popup)
            label.setWordWrap(True)
            label.setStyleSheet("background-color: lightyellow; border: 1px solid gray; padding: 5px;")
            label.adjustSize()
    
            help_popup.resize(label.size())
    
            # Position help window near button
            pos = help_button.mapToGlobal(help_button.rect().bottomRight())
            help_popup.move(pos.x() + 10, pos.y() - label.height() // 2)
    
            help_popup.show()
    
            # Optional: auto-clear reference when closed
            def clear_popup():
                nonlocal help_popup
                help_popup = None
            help_popup.destroyed.connect(clear_popup)
    
        help_button.clicked.connect(toggle_help)

    # Open a file dialog to select an image and read its binary data.
    def attach_picture(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a Picture", "", 
                                                   "Image Files (*.jpeg *.jpg *.png);;All Files (*)", options=options)
    
        if file_path:  # Check if a file was selected
            try:
                with open(file_path, 'rb') as file:
                    self.empPhoto = file.read()  # Store image binary data
                self.selected_image_path = file_path  # Store image path
                
                # Extract and display only the filename (not full path)
                image_name = file_path.split("/")[-1]
                self.image_label.setText(image_name)  # Update label with image name
                self.image_label.setStyleSheet("color: black; font-weight: bold;")  # Make it more visible
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read image file: {e}")

    ### SELECTION OF ID FROM TABLE  
    # First the table is open on the main app window
    def open_modifyfromtable_selection(self, table_name, id_entry, fillin_supplier=False, fillin_customer=False):
        """Opens the table for selection."""
        self.show_table(table_name)
        
        # Disconnect any previous connections to avoid duplicate calls
        try:
            self.table.cellDoubleClicked.disconnect()
        except TypeError:
            pass  # If there's no connection, ignore the error
    
        # Connect with partial to pass id_entry correctly
        self.table.cellDoubleClicked.connect(partial(self.select_modifyfromtable, id_entry=id_entry, fillin_supplier=fillin_supplier, fillin_customer=fillin_customer))
    # Then the ID is chosen
    def select_modifyfromtable(self, row, col, id_entry, fillin_supplier=False, fillin_customer=False):
        """Handles selecting an ID from the table."""
        if row == -1:
            return
        
        selected_item = self.table.item(row, 0).text()  # Ensure we get the first column value
        if selected_item:
            id_entry.setText(selected_item)
            
        if fillin_supplier:
            self.cursor.execute("SELECT SupplierID FROM expenses WHERE OCnumber = ?", (selected_item,))
            result = self.cursor.fetchone()
            if result:
                self.supplier_id_search.setText(str(result[0]))
        elif fillin_customer:
            self.cursor.execute("SELECT FirstName, LastName FROM customers WHERE CustomerID = ?", (selected_item,))
            row = self.cursor.fetchone()
            if row:
                self.first_last_name_label.setText(f"Check customer's name: {row[0]} {row[1]}")
                self.order_entries_tab1["customer_name"] = f"{row[0]} {row[1]}"
           
    # Move between tabs (orders)
    def go_to_next_tab(self):
        current_index = self.notebook.currentIndex()
        total_tabs = self.notebook.count()
        next_index = (current_index + 1) % total_tabs  # Loop around
        self.notebook.setCurrentIndex(next_index)
    def go_to_previous_tab(self):
        current_index = self.notebook.currentIndex()
        total_tabs = self.notebook.count()
        prev_index = (current_index - 1 + total_tabs) % total_tabs
        self.notebook.setCurrentIndex(prev_index)
    
    # From db string to checks on checkbox values
    def separate_checkbox_values(self, checkbox_dict, others_entry=None):
        selected = []
    
        for name, checkbox in checkbox_dict.items():
            if checkbox.isChecked():
                if name == "Others" and others_entry:
                    custom_value = others_entry.text().strip()
                    if custom_value:
                        selected.append(custom_value)
                else:
                    selected.append(name)
    
        return ", ".join(selected)

    # Function to upload invoices
    def fun_invoice_upload(self, order_flag = False):          
        # Build the folder name using PyQt widgets
        if order_flag:
            date_str = self.order_entries_tab1["date_ordered"].date().toString("yyyy-MM-dd")
            path = self.upload_order_invoice_path
            year = date_str[:4]
            month = int(date_str[5:7])
            if month in [1, 2, 3]:
                quarter= "Q1"
            elif month in [4, 5, 6]:
                quarter= "Q2"
            elif month in [7, 8, 9]:
                quarter= "Q3"
            else:
                quarter= "Q4"
        else:
            date_str = self.expense_entries["tax_return_applicable"]
            path= self.upload_expense_invoice_path
            quarter = date_str[0].currentText()
            year = date_str[1].currentText()
        
        folder_path = os.path.join(path, str(year), str(quarter))
        os.makedirs(folder_path, exist_ok=True)
        
        # Open file dialog to select files
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select files to upload")
     
        if not file_paths:
            QMessageBox.information(self, "No Files Selected", "No files were selected for upload.")
            return
        
        # Move selected files to the appropriate folder
        for file_path in file_paths:
            try:
                shutil.copy(file_path, folder_path)
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
    def _show_revenue_per_period(self):
        """Open the Revenue per Period analytics dialog."""
        dlg = RevenuePerPeriodDialog(parent=self, connection=self.connection)
        dlg.exec_()
    def _show_expenses_by_category(self):
        dlg = ExpensesByCategoryDialog(parent=self, connection=self.connection)
        dlg.exec_()
    def _show_expenses_per_period(self):
        dlg = ExpensesByPeriodDialog(parent=self, connection=self.connection)
        dlg.exec_()
