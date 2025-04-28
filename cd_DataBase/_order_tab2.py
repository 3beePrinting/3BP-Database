# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 14:32:20 2025

Code for order tab2

@author: feder
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, 
    QFileDialog, QMessageBox, QGridLayout, QScrollArea,
    QWidget,  QDialog, QSpacerItem,
    QFrame, QAction, QSizePolicy, QSpinBox, QLayout, QGroupBox )
from PyQt5.QtCore import Qt
import re


#%% Cost estimation calculation
def price_estimation(self, data, final_cost = False):
    try:
        # --- Extract numeric inputs from fields ---
        print_weight = float(data['print_weight'].text().strip())
        print_time = float(data['print_time'].text().strip())

        design_price = self.design_hourly_rate * float(data['design_time'].text().strip())
        labour_price = float(data['labour_time'].text().strip()) / 60 * self.labour_hourly_rate

        # --- Filament pricing ---
        f_id = re.findall(r'\d+(?= -)', data['filamentids'].text())
        filament_ids = [int(n) for n in f_id]
        if filament_ids:
            query = f"SELECT PricePerGram FROM filaments WHERE FilamentID IN ({','.join('?' for _ in filament_ids)})"
            self.cursor.execute(query, filament_ids)
            prices = self.cursor.fetchall()
            pricepergram_reference = float(max(p[0] for p in prices))
        else:
            pricepergram_reference = self.filament_price_reference
        material_price = pricepergram_reference * print_weight

        # --- Printer power ---
        p_id = re.findall(r'\d+(?= -)', data['printerids'].text())
        printer_ids = [int(n) for n in p_id]
        if printer_ids:
            query = f"SELECT Power FROM printers WHERE PrinterID IN ({','.join('?' for _ in printer_ids)})"
            self.cursor.execute(query, printer_ids)
            powers = self.cursor.fetchall()
            power_reference = float(max(p[0] for p in powers))
        else:
            power_reference = self.printer_power_reference
            
        electricity_price = 0.9 * power_reference / 1000 * print_time
        printertime_price = (1.0 if print_time > 24 else 0.5) * print_time

        # --- Shipping cost ---
        shipping_type = data['shipping_type'].currentText()
        shipping_quantity = int(data['shipping_quantity'].text().strip())
        if shipping_type == "Letterbox parcel":
            shipping_cost = self.postNLprices[0] * shipping_quantity
        elif shipping_type == "Small parcel":
            shipping_cost = self.postNLprices[1] * shipping_quantity
        elif shipping_type == "Medium parcel":
            shipping_cost = self.postNLprices[2] * shipping_quantity
        elif shipping_type == "Large parcel":
            shipping_cost = self.postNLprices[3] * shipping_quantity
        else:
            shipping_cost = 0

        # --- Extra Services ---
        extra_services_cost = float(data['extra_services_cost'].text().strip())

        # --- Total Cost Calculation ---
        if final_cost:
            # --- Display Results ---
            result = {
                "design_cost": design_price,
                "material_cost": material_price,
                "electricity_cost": electricity_price,
                "printer_time_cost": printertime_price,
                "labour_cost": labour_price,
                "shipping_cost": shipping_cost    }
            return [shipping_cost, material_price, electricity_price]
            
        else:
            price_exclBTW = design_price + material_price + electricity_price + printertime_price + labour_price + extra_services_cost
            price_inclBTW = price_exclBTW * (1 + self.BTW) + shipping_cost
            profit = price_exclBTW - material_price - electricity_price
    
            # --- Display Results ---
            result = {
                "design_cost": design_price,
                "material_cost": material_price,
                "electricity_cost": electricity_price,
                "printer_time_cost": printertime_price,
                "labour_cost": labour_price,
                "shipping_cost": shipping_cost,
                "priceexclbtw": price_exclBTW,
                "price_incl_btw_and_shipping": price_inclBTW,
                "profit": profit      }

        for key, value in result.items():
            if key in data:
                data[key].setText(f"{value:.2f}")

    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", "Inputs are insufficient or incorrect for cost estimation.\n\n" + str(e))

# This function only calculates the BTW and profit if the price estimated 
def update_BTW_and_profit(self):
    data = self.order_entries_tab2
    # first update all costs with price estimation
    [shipping_cost, material_price, electricity_price] = self.price_estimation(data, final_cost=True)
        
    # --- Total Cost Calculation ---
    price_exclBTW = float(data['priceexclbtw'].text().strip())
    price_inclBTW = price_exclBTW * (1 + self.BTW) + shipping_cost
    profit = price_exclBTW - material_price - electricity_price

    # --- Display Results ---
    result = {
        "price_incl_btw_and_shipping": price_inclBTW,
        "profit": profit }

    for key, value in result.items():
        if key in data:
            data[key].setText(f"{value:.2f}")

#%% Select printers function and update their status
def open_printer_selection(self):
    # Fetch printers from the database
    self.cursor.execute("SELECT PrinterID, PrinterName, Status FROM printers WHERE Status != 'NA'")
    printers = self.cursor.fetchall()

    # Create popup dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Select Printers")
    dialog.resize(400, 500)
    layout = QVBoxLayout(dialog)

    # Checkbox list
    checkbox_widgets = []
    
    # Check if printers were already selected
    selected_printers = self.order_entries_tab2["printerids"].text().strip()
    selected_ids = [int(p.strip()) for p in selected_printers.split(",") if p.strip().isdigit()]

    for pid, name, status in printers:
        # Frame for each printer block
        printer_block = QVBoxLayout()

        # Checkbox with printer label
        checkbox = QCheckBox(f"{name} (ID{pid})")
        if pid in selected_ids:
            checkbox.setChecked(True)
        
        printer_block.addWidget(checkbox)

        if self.order_entries_tab1["stage"].currentText() == "Order":
            # Status dropdown
            status_box = QComboBox()
            status_box.addItems(["Busy", "Planned print", "Free"])
            if status in ["Busy", "Planned print", "Free"]:
                status_box.setCurrentText(status)
            printer_block.addWidget(status_box)
    
            # Add to layout
            layout.addLayout(printer_block)
            checkbox_widgets.append((pid, checkbox, status_box))
        else:
            # Add to layout
            layout.addLayout(printer_block)
            checkbox_widgets.append((pid, checkbox))

    # OK button
    def confirm_selection():
        selected_ids = []
        updates_to_apply = []
    
        if self.order_entries_tab1["stage"].currentText() == "Order":
            for pid, checkbox, status_box in checkbox_widgets:
                if checkbox.isChecked():
                    selected_ids.append(str(pid))
                    updates_to_apply.append((status_box.currentText(), pid))
            
            # Ask if user wants to update status
            if updates_to_apply:
                reply = QMessageBox.question(
                    self,
                    "Update Printer Status?",
                    "Do you want to update the printer statuses in the database as well? The original statuses will be lost after confirmation.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No   )
        
                if reply == QMessageBox.Yes:
                    for new_status, pid in updates_to_apply:
                        self.cursor.execute("UPDATE printers SET Status = ? WHERE PrinterID = ?", (new_status, pid))
                    self.connection.commit()
        else:
            for pid, checkbox in checkbox_widgets:
                if checkbox.isChecked():
                    selected_ids.append(str(pid))
    
        # Update display regardless
        self.order_entries_tab2["printerids"].setText(", ".join(selected_ids))
        dialog.accept()


    ok_button = QPushButton("OK")
    layout.addWidget(ok_button)
    ok_button.clicked.connect(confirm_selection)

    dialog.exec_()
 
#%% Select filaments
def open_filament_selection(self):
    # Fetch printers from the database
    self.cursor.execute("SELECT FilamentID, FilamentName, Material, Color, QuantityInStock, GramsPerRoll FROM filaments")
    filaments = self.cursor.fetchall()

    # Create popup dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("Select Filaments")
    dialog.resize(500, 600)
    layout = QVBoxLayout(dialog)

    # Checkbox list
    checkbox_widgets = []
    # Check if filaments were already selected
    selected_filaments = self.order_entries_tab2["filamentids"].text().strip()
    selected_ids = [int(p.strip()) for p in selected_filaments.split(",") if p.strip().isdigit()]


    for fid, name, material, color, qtystock, grams in filaments:
        filament_layout = QVBoxLayout()

        # Checkbox for selecting the filament
        checkbox = QCheckBox(f"{name} (ID{fid} - {material} {color})")
        if fid in selected_ids:
            checkbox.setChecked(True)
        filament_layout.addWidget(checkbox)

        # Sub-layout for additional info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"In stock: {qtystock} rolls ({grams}g/roll)"))
        
        if self.order_entries_tab1["stage"].currentText() == "Order":
            # If Printing, you can remove rolls of materials from stock
            # Input: how many rolls to use
            rolls_input = QSpinBox()
            rolls_input.setRange(0, 100)
            rolls_input.setValue(0)
            info_layout.addWidget(QLabel("Expected use:"))
            info_layout.addWidget(rolls_input)
    
            filament_layout.addLayout(info_layout)
            layout.addLayout(filament_layout)
            checkbox_widgets.append((fid, checkbox, rolls_input))
        else:
            layout.addLayout(filament_layout)
            checkbox_widgets.append((fid, checkbox))

    # OK button logic
    def confirm_selection():
        selected_ids = []
        selected_quantities = {}  # {fid: rolls_used}
        updates_to_apply = []     # [(fid, rolls_used, original_qty)]
    
        if self.order_entries_tab1["stage"].currentText() == "Order":
            for fid, checkbox, spinbox in checkbox_widgets:
                if checkbox.isChecked():
                    selected_ids.append(str(fid))
                    rolls_used = spinbox.value()
                    selected_quantities[fid] = rolls_used
        
                    # Fetch current stock for this filament
                    self.cursor.execute("SELECT QuantityInStock FROM filaments WHERE FilamentID = ?", (fid,))
                    result = self.cursor.fetchone()
                    if result:
                        current_stock = result[0]
                        updates_to_apply.append((fid, rolls_used, current_stock))
        else:
            for fid, checkbox in checkbox_widgets:
                if checkbox.isChecked():
                    selected_ids.append(str(fid))
    
        # Set the selected IDs to the display
        self.order_entries_tab2["filamentids"].setText(", ".join(selected_ids))
        
        if self.order_entries_tab1["stage"].currentText() == "Order":
            self.selected_filament_rolls = selected_quantities
        
            # Ask if user wants to update stock
            if updates_to_apply:
                reply = QMessageBox.question(
                    self,
                    "Update Stock?",
                    "Do you want to update the filament stock quantities based on usage?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No     )
        
                if reply == QMessageBox.Yes:
                    for fid, used, current_stock in updates_to_apply:
                        new_stock = max(0, current_stock - used)  # Prevent negative stock
                        self.cursor.execute(
                            "UPDATE filaments SET QuantityInStock = ? WHERE FilamentID = ?",
                            (new_stock, fid)            )
                    self.connection.commit()
    
        dialog.accept()


    ok_button = QPushButton("OK")
    layout.addWidget(ok_button)
    ok_button.clicked.connect(confirm_selection)

    dialog.setLayout(layout)
    dialog.exec_()

#%% TAB 2 - Price estimation widgets
def tab2_widgets(self, tab2, modify_flag = False):
    self.order_entries_tab2 = {}  # here I save all variables

    # ---- Main layout for tab2 ----
    # === NEW: Outer fixed-size wrapper frame ===
    wrapper_frame = QFrame()
    wrapper_frame.setFrameShape(QFrame.NoFrame)
    # wrapper_frame.setFixedSize(1200, 700)  # You can adjust size here
    
    # Inner layout inside the fixed-size box
    tab2_layout = QGridLayout()
    tab2_layout.setSpacing(20)
    tab2_layout.setContentsMargins(10, 10, 10, 10)
    wrapper_frame.setLayout(tab2_layout)
    
    # Add wrapper_frame to tab2 (centering optional)
    container_layout = QHBoxLayout()
    container_layout.addStretch()
    container_layout.addWidget(wrapper_frame)
    container_layout.addStretch()
    tab2.setLayout(container_layout)
    
    # ---- Print Inputs Frame (Top Left) ----
    print_inputs_frame = QGroupBox("Print Inputs")
    print_inputs_layout = QGridLayout()
    print_inputs_frame.setLayout(print_inputs_layout)
    tab2_layout.addWidget(print_inputs_frame, 0, 0)#, alignment=Qt.AlignTop | Qt.AlignHCenter)
    
    # ---- Populate dropdowns from DB ----
    row_nr = 1
    print_inputs_layout.addWidget(QLabel("Printers"), row_nr, 0)
    
    # Display area (read-only)
    printer_display = QLineEdit()
    printer_display.setReadOnly(True)
    printer_display.setFixedWidth(300)
    print_inputs_layout.addWidget(printer_display, row_nr, 1)
    
    # Button to open selection window
    add_printers_button = QPushButton("Select Printers")
    print_inputs_layout.addWidget(add_printers_button, row_nr, 2)
    add_printers_button.clicked.connect(self.open_printer_selection)
    
    # Store the field in the widget dictionary
    self.order_entries_tab2["printerids"] = printer_display

    # ---- Populate dropdowns from DB ----
    row_nr += 1
    print_inputs_layout.addWidget(QLabel("Filaments"), row_nr, 0)
    
    # Display area (read-only)
    filament_display = QLineEdit()
    filament_display.setReadOnly(True)
    filament_display.setFixedWidth(300)
    print_inputs_layout.addWidget(filament_display, row_nr, 1)
    
    # Button to open selection window
    add_filaments_button = QPushButton("Select Filaments")
    print_inputs_layout.addWidget(add_filaments_button, row_nr, 2)
    add_filaments_button.clicked.connect(self.open_filament_selection)
    
    # Store the field in the widget dictionary
    self.order_entries_tab2["filamentids"] = filament_display

    # ---- Entry fields (print weight, time, etc.) ----
    fields = [("Print Weight", "gram"),
              ("Print Time", "hour"),
              ("Design Time", "hour"),
              ("Labour Time", "min")]
    
    for label_text, unit in fields:
        row_nr += 1
        print_inputs_layout.addWidget(QLabel(label_text), row_nr, 0)
        entry = QLineEdit()
        entry.setText("0.00")
        entry.setFixedWidth(100)
        print_inputs_layout.addWidget(entry, row_nr, 1)
        self.order_entries_tab2[label_text.lower().replace(" ", "_")] = entry
        print_inputs_layout.addWidget(QLabel(unit), row_nr, 2)
    
    # ---- Additional Inputs Frame (Bottom Left) ----
    additional_inputs_frame = QGroupBox("Additional Inputs")
    additional_inputs_layout = QGridLayout()
    additional_inputs_frame.setLayout(additional_inputs_layout)
    
    tab2_layout.addWidget(additional_inputs_frame, 1, 0)#, alignment=Qt.AlignTop | Qt.AlignHCenter)
   
    # --- Shipping Combo ---
    additional_inputs_layout.addWidget(QLabel("Shipping"), 1, 0)
    
    shipping_combo = QComboBox()
    shipping_combo.addItems([
        "Letterbox parcel", "Small parcel", "Medium parcel",
        "Large parcel", "Order pickup" ])
    additional_inputs_layout.addWidget(shipping_combo, 1, 1)
    shipping_combo.setFixedWidth(150)
    self.order_entries_tab2["shipping_type"] = shipping_combo
    
    shipping_help_text = "PostNL Options (last updated: 02/03/2025):\n\n Small parcel max. 34x28x12cm max. 3kg (5.95€)\n Medium parcel max. 100x50x50cm max. 10kg (6.95€)\n Large parcel max. 176x78x58cm max. 23kg (14.50€)"
    self.create_label_with_help(shipping_help_text, additional_inputs_layout, row=1, col=4)
    
    # --- Shipping quantity ---
    additional_inputs_layout.addWidget(QLabel("Quantity"), 1, 2)
    
    shipping_quantity_entry = QSpinBox()
    shipping_quantity_entry.setRange(0, 100)
    shipping_quantity_entry.setValue(0)
    shipping_quantity_entry.setFixedWidth(100)
    additional_inputs_layout.addWidget(shipping_quantity_entry, 1, 3)
    self.order_entries_tab2["shipping_quantity"] = shipping_quantity_entry

    # --- Extra Services Section ---
    additional_inputs_layout.addWidget(QLabel("Other services"), 2, 0)
    
    # Container for checkboxes
    extraservice_checkboxes_frame = QVBoxLayout()
    additional_inputs_layout.addLayout(extraservice_checkboxes_frame, 2, 1, 1, 3)
    
    # Store checkboxes
    self.extraservice_vars = {
        "Sanding": QCheckBox("Sanding"),
        "Coating": QCheckBox("Coating"),
        "Painting": QCheckBox("Painting"),
        "Others": QCheckBox("Others") }
    
    # "Others" checkbox with dynamic entry
    others_checkbox_layout = QHBoxLayout()
    
    self.others_checkbox = self.extraservice_vars["Others"]
    others_checkbox_layout.addWidget(self.others_checkbox)
    
    self.others_entry = QLineEdit()
    self.others_entry.setPlaceholderText("Specify...")
    self.others_entry.setDisabled(True)
    self.others_entry.setFixedWidth(150)
    others_checkbox_layout.addWidget(self.others_entry)
    
    def toggle_others_entry(state):
        self.others_entry.setDisabled(not state)
        if not state:
            self.others_entry.clear()
    
    self.others_checkbox.toggled.connect(toggle_others_entry)

    # Add checkboxes to layout
    for key, checkbox in self.extraservice_vars.items():
        if key == "Others":
            extraservice_checkboxes_frame.addLayout(others_checkbox_layout)
        else:
            extraservice_checkboxes_frame.addWidget(checkbox)
            
    if modify_flag:
        selected_services = [s.strip() for s in self.order_data["extra_services"].split(",")]
    
        # Track unmatched values
        unmatched = []
    
        for service in selected_services:
            if service in self.extraservice_vars:
                self.extraservice_vars[service].setChecked(True)
            else:
                unmatched.append(service)
    
        # If there are unmatched services, check "Others" and fill the entry
        if unmatched:
            self.others_checkbox.setChecked(True)
            self.others_entry.setText(", ".join(unmatched))


    # ---- Cost Calculation Frame (right side) ----
    cost_calc_frame = QGroupBox("Cost Calculation")
    cost_calc_layout = QGridLayout()
    cost_calc_frame.setLayout(cost_calc_layout)
    tab2_layout.addWidget(cost_calc_frame, 0, 1, 2, 1)#, alignment=Qt.AlignTop | Qt.AlignHCenter)  # rowspan=2

    # Define the fields and their units
    cost_fields = [("Design Cost", "€"),
        ("Material Cost", "€"),
        ("Printer Time Cost", "€"),
        ("Electricity Cost", "€"),
        ("Labour Cost", "€"),
        ("Shipping Cost", "€"),
        ("Extra Services Cost", "€")]
    
    row_nr = 1
    for field_name, unit in cost_fields:
        cost_calc_layout.addWidget(QLabel(field_name), row_nr, 0)
        
        entry = QLineEdit()
        entry.setText("0.00")
        entry.setFixedWidth(100)
        if field_name not in ["Extra Services Cost"]:
            entry.setDisabled(True)
        cost_calc_layout.addWidget(entry, row_nr, 2)
        
        self.order_entries_tab2[field_name.lower().replace(" ", "_")] = entry
        cost_calc_layout.addWidget(QLabel(unit), row_nr, 3)
        
        row_nr += 1
        
    # --- Compute Button ---
    compute_button = QPushButton("Compute Price")
    compute_button.setFixedWidth(220)
    cost_calc_layout.addWidget(compute_button, row_nr, 1, 1, 2)
    compute_button.clicked.connect(lambda: self.price_estimation(data = self.order_entries_tab2))
    
    # Separator line before total cost
    row_nr += 1
    separator = QFrame()
    separator.setFrameShape(QFrame.HLine)
    separator.setFrameShadow(QFrame.Sunken)
    cost_calc_layout.addWidget(separator, row_nr, 0, 1, 4)
    
    row_nr += 1
    # Total costs etc
    total_fields = [("Price excl BTW", "€"),
        ("Price incl BTW and shipping", "€"),
        ("Profit", "€")]
    
    for field_name, unit in total_fields:
        cost_calc_layout.addWidget(QLabel(field_name), row_nr, 0)
        
        entry = QLineEdit()
        entry.setText("0.00")
        entry.setFixedWidth(100)
        if field_name == "Profit":
            entry.setDisabled(True)
        cost_calc_layout.addWidget(entry, row_nr, 2)
        
        if field_name == "Price excl BTW":
            self.order_entries_tab2['priceexclbtw'] = entry
        else:
            self.order_entries_tab2[field_name.lower().replace(" ", "_")] = entry
        cost_calc_layout.addWidget(QLabel(unit), row_nr, 3)
        
        row_nr += 1

    # --- Compute Button ---
    updatefinalcost_button = QPushButton("Update Final Cost")
    updatefinalcost_button.setFixedWidth(220)
    cost_calc_layout.addWidget(updatefinalcost_button, row_nr+1, 1, 1, 2)
    updatefinalcost_button.clicked.connect(self.update_BTW_and_profit)
    
    def go_to_tab3():
        if self.validate_fields_tab2():
            self.go_to_next_tab()
            
    # Tab buttons
    next_button = QPushButton("Next Tab")
    next_button.setFixedWidth(100)
    next_button.setStyleSheet("QPushButton { background-color: lightgray; }")
    tab2_layout.addWidget(next_button, 2, 0, 1, 2, alignment=Qt.AlignRight)
    next_button.clicked.connect(go_to_tab3)
    
    prev_button = QPushButton("Previous Tab")
    prev_button.setFixedWidth(100)
    prev_button.setStyleSheet("QPushButton { background-color: lightgray; }")
    tab2_layout.addWidget(prev_button, 2, 0, 1, 2, alignment=Qt.AlignLeft)
    prev_button.clicked.connect(self.go_to_previous_tab)
    
    if modify_flag:
        # Fill entries in tab2
        for key, widget in self.order_entries_tab2.items():
            value = self.order_data.get(key, "")

            if isinstance(widget, QLineEdit):
                if key in ["print_weight", "print_time", "design_time", "labour_time", "extra_services_cost"]:
                    try: # check its a number, otherwise remove
                        widget.setText(str(float(value)))
                    except ValueError:
                        self.incorrect_info_flag = True
                
                # Run the computations
                if key in ['price_incl_btw_and_shipping', 'profit']:
                    pass
                elif key == 'priceexclbtw':
                    # First check this is a number
                    try: # check its a number, otherwise remove
                        self.price_estimation(data = self.order_entries_tab2)
                        entry.setText(str(float(value)))
                        self.update_BTW_and_profit()   
                    except ValueError:
                        self.incorrect_info_flag = True
                        
                else:
                    widget.setText(str(value))
            elif isinstance(widget, QSpinBox): 
                widget.setValue(int(value))
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                widget.setCurrentIndex(index if index != -1 else 0)
    
#%% Check all fields are filled before moving on
def validate_fields_tab2(self):
    # Collect and trim values from widgets
    entries = self.order_entries_tab2
    for key, widget in entries.items():
        if key in ["print_weight", "print_time", "design_time", "labour_time", "extra_services_cost", "priceexclbtw"]:
            try:
                float(widget.text())
            except ValueError:
                QMessageBox.critical(None, "Validation Error", f"{key} must be a number.")
                return False
            
    return True
