# -*- coding: utf-8 -*-
"""
Method: show tables with search query

@author: feder
"""
import pandas as pd
from PyQt5.QtWidgets import ( QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, 
    QComboBox, QLineEdit, QPushButton, QLabel, QMessageBox, QSizePolicy, QAbstractItemView )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import re

def show_table(self, table_name, open_req=False, active_ord=False, print_parts=False):
    # STEP1 : Clear the current TableWidget and associated widgets
    self.current_table = table_name
    for i in reversed(range(self.table_frame.layout().count())):
        widget = self.table_frame.layout().itemAt(i).widget()
        if widget is not None:
            widget.deleteLater()
    
    # STEP2: Fetch data using pandas
    try:
        if open_req:
            query = f"SELECT * FROM {table_name} WHERE stage = 'Request' AND NOT status = 'Not accepted';"
        elif active_ord:
            query = f"SELECT * FROM {table_name} WHERE stage = 'Order';"
        elif print_parts:
            query = f"""
                    SELECT {table_name}.*
                    FROM {table_name}
                    JOIN orders ON {table_name}.OrderID = orders.OrderID
                    WHERE orders.status = 'Printing'
                """
        else:
            query = f"SELECT * FROM {table_name};"
        self.current_df = pd.read_sql_query(query, self.connection)
        
        if self.current_df.empty:
            QMessageBox.information(self, "Info", f"No data available in the {table_name} table.")
            return
        
        if table_name == 'expenses':
            custom_headers = [
                "OC Number\n", "SupplierID\n", 
                "Component\n", "Description\n", "Link\n", "Purpose\n", "Date Ordered\n", 
                "Date Delivery\n", "Cost Incl. BTW\n(€)", "Cost Shipping\n(€)", "BTW\n(€)",
                "Order Status\n", "Responsible\n", "Tax Return Applicable\n", "Invoice Uploaded\n",
                "Tax To Be Returned\n(€)", "Paid From\n", "Refund To\n", "Status Refund\n", "Notes\n", "Picture\n" ]
                
        elif table_name == 'printers':
            custom_headers = [
                "PrinterID\n", "OC Number\n", "SupplierID\n", 
                "Printer Name\n", "Power\n(W)", "Print Size X\n(mm)", "Print Size Y\n(mm)", "Print Size Z\n(mm)", 
                "Nozzle Size On\n(mm)", "Status\n", "Condition\n", "Total Hours\n(h)", "Total Hours After Last Maintenance\n(h)", 
                "Date Last Maintenance\n", "Notes\n", "Picture\n" ]
            
        elif table_name == 'filaments':
              custom_headers = [
                  "FilamentID\n", "OC Number\n", "SupplierID\n",
                  "Filament Name\n", "Material\n", "Color\n", "Quantity Order\n(rolls)", "Quantity In Stock\n(rolls)",
                  "Grams Per Roll\n(g)", "Price Per Gram\n(€/g)", "Nozzle Temperature\n(°C)", "Bed Temperature\n(°C)",
                  "Properties\n", "Notes\n", "Picture\n" ]
        elif table_name == 'orders':
            custom_headers = [
                "OrderID\n", "CustomerID\n", "Services\n", "Description\n", "Date Ordered\n", "Date Required\n",
                "Stage\n", "Status\n", "Invoice Number\n", "Responsible\n", "Last Updated\n", "Number of Parts\n", "Progress\n(printed/ordered)", "Printer IDs\n", "Filament IDs\n",
                "Print Weight\n(g)", "Print Time\n(h)", "Design Time\n(h)", "Labour Time\n(min)", "Shipping Type\n", "Shipping Quantity\n",
                "Extra Services\n", "Extra Services Cost\n(€)", "Total Cost\n(€)", "Notes\n"]
        elif table_name == 'printsettings':
            custom_headers = [
                "PrintSettingID\n", "Setting's Name\n", "Nozzle Size\n(mm)", "Infill\n(%)",
                "Layer Height\n(mm)", "Speed \n(mm/s)", "Support\n", "Brim\n", "Glue\n",
                "Nozzle Temperature\n(°C)", "BedTemperature\n(°C)", "Notes\n"]
        else:
            custom_headers = [s if "ID" in s or "ZIP" in s else re.sub(r'(?<!^)(?=[A-Z])', ' ', s) for s in self.current_df.columns ]

        
        # STEP3: Create TableWidget
        self.table = QTableWidget()
        self.table.setRowCount(len(self.current_df))
        self.table.setColumnCount(len(custom_headers))
        self.table.setHorizontalHeaderLabels(custom_headers)
        # Make horizontal header wrap text by using word-wrap inside a QWidget
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow resizing
        header.setStretchLastSection(True)  # Stretch last column
        # header.setDefaultAlignment(Qt.AlignCenter)
        
        # Loop through headers and use custom widget to wrap text
        for col in range(self.table.columnCount()):
            label = QLabel(self.current_df.columns[col])
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("margin: 2px;")
            self.table.setCellWidget(-1, col, label)  # doesn't set headers this way, but we’ll fix it below
        
        # Trick to increase header height
        font_metrics = self.table.fontMetrics()
        max_height = max(font_metrics.boundingRect(header_text).height() for header_text in self.current_df.columns)
        header.setFixedHeight(max(50, max_height * 2))  # adjust multiplier if needed
        
        # Let user expand columns manually
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        self.table_frame.layout().addWidget(self.table)
        
        # Populate table
        self.insert_rows_to_table(self.current_df, table_name = table_name)
        
        for row_idx, row in self.current_df.iterrows():
            for col_idx, column_name in enumerate(self.current_df.columns):
                value = row[column_name]
                
                if column_name.lower() == "picture":  # If column is "Picture", show filename instead
                    value = "Image" if isinstance(value, bytes) and value else "NA"
                
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Make table read-only
                self.table.setItem(row_idx, col_idx, item)
                
        # STEP4: search and reset buttons
        # Remove old search buttons before adding new ones
        for i in reversed(range(self.table_frame.layout().count())):
            item = self.table_frame.layout().itemAt(i)
            if isinstance(item, QHBoxLayout):
                while item.count():
                    sub_item = item.takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
                self.table_frame.layout().removeItem(item)
                
        # Search and Reset Buttons
        button_layout = QHBoxLayout()
        self.search_column_var = QComboBox()
        self.search_column_var.addItems(self.current_df.columns)
        self.search_query_var = QLineEdit()
        search_button = QPushButton("Search")
        reset_button = QPushButton("Reset")
        
        button_layout.addWidget(QLabel("Search Column:"))
        button_layout.addWidget(self.search_column_var)
        button_layout.addWidget(QLabel("Search Query:"))
        button_layout.addWidget(self.search_query_var)
        button_layout.addWidget(search_button)
        button_layout.addWidget(reset_button)
        self.table_frame.layout().addLayout(button_layout)
        
        search_button.clicked.connect(lambda: self.search_table(table_name=table_name))
        reset_button.clicked.connect(lambda: self.reset_table(table_name=table_name))
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load table data: {e}")

def open_image(self, row, col):
    if col != self.picture_column_index:  # Ensure only Picture column triggers
        return

    selected_row = row  # Get the row number
    id_value = self.table.item(selected_row, 0).text()  # Get ID from first column

    if self.current_table == "expenses":
        self.cursor.execute(f"SELECT Picture FROM {self.current_table} WHERE OCnumber = ?", (id_value,))
    else:
        self.cursor.execute(f"SELECT Picture FROM {self.current_table} WHERE {self.current_table[:-1]}ID = ?", (id_value,))
    result = self.cursor.fetchone()

    if result and result[0]:  # Ensure image data exists
        image_data = result[0]
        image = QImage.fromData(image_data)
        pixmap = QPixmap.fromImage(image)

        # Create Image Display Window
        self.image_window = QWidget()
        self.image_window.setWindowTitle(f"{self.current_table} {id_value} - Picture")

        image_label = QLabel()
        image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        image_layout = QVBoxLayout()
        image_layout.addWidget(image_label)
        self.image_window.setLayout(image_layout)
        self.image_window.show()
    else:
        QMessageBox.information(self, "No Image", "No image available for this record.")

def insert_rows_to_table(self, df, table_name):
    self.current_table = table_name
    if table_name in ['customers', 'orders', 'suppliers', 'printsettings']:
        self.table.setRowCount(len(df))  # Set the number of rows   
        df = df.reset_index(drop=True)  # Reset index to avoid mismatches
        
        for row_idx, row in df.iterrows():
            for col_idx, column_name in enumerate(df.columns):  # Get column name
                value = row[column_name]  # Get value using column name
        
                if column_name.lower() == "picture":  # If column is "Picture", show filename instead of binary
                    value = "Image" if isinstance(value, bytes) and value else "NA"
        
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Ensure cells remain read-only
                self.table.setItem(row_idx, col_idx, item)

    else:
        self.table.setRowCount(len(df))  # Set the number of rows   
        df = df.reset_index(drop=True)  # Reset index to avoid mismatches
        
        for row_idx, row in df.iterrows():
            for col_idx, column_name in enumerate(df.columns):  # Get column name
                value = row[column_name]  # Get value using column name
        
                if column_name.lower() == "picture":  # If column is "Picture", show filename instead of binary
                    value = "Image" if isinstance(value, bytes) and value else "NA"
        
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Ensure cells remain read-only
                self.table.setItem(row_idx, col_idx, item)
                
        # Find Picture column index dynamically
        if "Picture" in df.columns:
            self.picture_column_index = df.columns.get_loc("Picture")

        # Connect double-click event
        self.table.cellDoubleClicked.connect(lambda row, col: self.open_image(row, col))

def search_table(self, table_name):
    search_column = self.search_column_var.currentText()
    search_query = self.search_query_var.text()
    if not search_query:
        QMessageBox.warning(self, "Warning", "Search query cannot be empty.")
        return
    try:
        filtered_df = self.current_df[self.current_df[search_column].astype(str).str.contains(search_query, case=False, na=False)]
        self.insert_rows_to_table(filtered_df, table_name)
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to perform search: {e}")

def reset_table(self, table_name):
    self.insert_rows_to_table(self.current_df, table_name)
    
# def show_context_menu(self, pos: QPoint):
#         index = self.table.indexAt(pos)
#         if not index.isValid():
#             return

#         row = index.row()
#         menu = QMenu()
#         see_action = menu.addAction("See as filled-in form")
#         action = menu.exec_(self.table.viewport().mapToGlobal(pos))
            
#         window = QDialog(self)
        
#         if action == see_action:
#             if table_name == "printsettings":
#                 self.widget_printsettings(window, modify_flag_printsettings = True)
              
            
            
#             self.show_row_info(row)