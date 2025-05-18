# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 14:34:15 2025

Code for tab3 (Overview of teh order)

@author: feder
"""

from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout,QPushButton,
    QMessageBox, QTextEdit, QGroupBox, QComboBox, QScrollArea, QWidget )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import win32com.client as win32
import urllib.parse
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QMessageBox


#%% TAB 3 - Overview of the order widget
# In this tab, I want to show the order details to confirm everything before saving
def tab3_widgets(self, frame, modify_flag = False):
    container_widget = QWidget()
    
    layout = QVBoxLayout(container_widget)
    
    # Placeholder to hold the info box so we can update it
    self.info_box_tab3 = None
    
    def update_widget_tab3():
        # Remove old info box if it exists
        if self.info_box_tab3:
            layout.removeWidget(self.info_box_tab3)
            self.info_box_tab3.deleteLater()
            self.info_box_tab3 = None
            
        # --- Wrap in a titled box ---
        self.info_box_tab3 = QGroupBox("General Order Information")
        info_layout = QVBoxLayout(self.info_box_tab3)
        
        try: 
            services = self.separate_checkbox_values(self.service_vars)
            
            try:
                foldername = self.order_entries_tab1["folder_name"]
            except:
                foldername = "NA"
                
            entries = self.order_entries_tab1
            
            # Display order overview
            overview_text = f"""
Details for OrderID {self.orderid}:
• Customer ID{entries["customerid"].text()} {entries["customer_name"]}
• {services} of {entries["description"].text()} (in {len(self.parts)} part(s))
• Current order status: {entries["stage"].currentText()} > {entries["status"].currentText()}
• Request received on {entries["date_ordered"].date().toString("yyyy-MM-dd")} by {entries["responsible"].currentText()}
• Deadline: {entries["date_required"].date().toString("yyyy-MM-dd")}
• Files received saved in folder {foldername}    
            """
            
            try:
                # First organize all data to display
                first_partid = self.parts[0]["PartID"]
                last_partid = self.parts[-1]["PartID"]
                if last_partid==first_partid:
                    partid_text = f"PartID {first_partid}"
                else:
                    partid_text = f"Part IDs from {first_partid} to {last_partid}"
     
                printed_parts = 0
                total_parts = 0
                material_text = self.parts[0]["Materials"]
                color_text = self.parts[0]["Color"]
            
                for i in range(len(self.parts)):
                    part = self.parts[i]
                    printed_parts += int(part["QuantityPrinted"])
                    total_parts += int(part["QuantityOrdered"])
                    if part["Materials"] != material_text:
                        material_text = "multiple materials"
                    if part["Color"] != color_text:
                        color_text = "multiple"
                        
                overview_text = overview_text + f"""
• {partid_text} to print in material {material_text} and color {color_text}
• Printing status: total {printed_parts} printed parts over {total_parts} """
            except:
                    overview_text = overview_text + """
• No parts specified.   """
                       
            # Add information on cost
            price = float(self.order_entries_tab2["priceexclbtw"].text().strip())
            price_allincl = float(self.order_entries_tab2["price_incl_btw_and_shipping"].text().strip())
            overview_text = overview_text + f"""
• Price estimation {price} euros excl. BTW and shipping ({price_allincl} incl. BTW and shipping)
    """
            # Overview display (as QLabel with multiline text)
            info_label = QLabel(overview_text.strip())
            info_label.setStyleSheet("font-family: Arial; font-size: 10pt;")
            info_label.setWordWrap(True)
            info_layout.addWidget(info_label)
            
        except Exception:
            # Show placeholder message
            placeholder_label = QLabel("Overview information is not yet available. Please complete the required fields in the previous tabs.")
            placeholder_label.setWordWrap(True)
            placeholder_label.setStyleSheet("font-style: italic; color: gray; font-size: 10pt;")
            info_layout.addWidget(placeholder_label)
    
        layout.insertWidget(0, self.info_box_tab3)  # Always insert at the top
    
    update_widget_tab3()
    
    update_button = QPushButton("Update Overview")
    update_button.setFixedWidth(150)
    layout.addWidget(update_button, alignment=Qt.AlignCenter)
    update_button.clicked.connect(update_widget_tab3)
    
    # Notes entry
    notes_label = QLabel("Notes:")
    notes_edit = QTextEdit()
    self.ordernotes = notes_edit
    notes_edit.setPlaceholderText("Enter notes related to this order...")
    notes_edit.setFixedHeight(100)

    layout.addWidget(notes_label)
    layout.addWidget(notes_edit)
    
    if modify_flag:
       value = self.order_data.get("notes", "")
       notes_edit.setPlainText(str(value))
       update_widget_tab3()
       
       if self.incorrect_info_flag:# If data inputted were not ok, say it here with a warning message           
           QMessageBox.warning(None, "Data format/content warning", "Some values fetched in the database for this ID are incorrect. They are automatically removed and set to default in this form.")
     
    
    # Email buttons
    button_layout = QHBoxLayout()

    # === First button and combo (Employee selection) ===
    first_row = QHBoxLayout()
    orderreview_outlook = QPushButton("Ask Order Review to...")
    orderreview_outlook.setIcon(QIcon( self.resource_path("images/email.png") ))
    
    employee_combo = QComboBox()
    self.cursor.execute("SELECT FirstName || ' ' || LastName FROM employees")
    employee_names = [row[0] for row in self.cursor.fetchall()]
    employee_combo.addItems(employee_names)
    
    orderreview_outlook.clicked.connect(lambda: self.fun_ask_price_consultation_email(employee_combo))
    
    first_row.addWidget(orderreview_outlook)
    first_row.addWidget(employee_combo)
    
    button_layout.addLayout(first_row)
    
    # === Second button and combo (Language selection) ===
    second_row = QHBoxLayout()
    clientemail_outlook = QPushButton("Send Email to Client in...")
    clientemail_outlook.setIcon(QIcon( self.resource_path("images/email.png") ))
    
    language_combo = QComboBox()
    language_combo.addItems(["English", "Dutch"])
    language_combo.setCurrentText("English")
    
    clientemail_outlook.clicked.connect(lambda: self.fun_client_email(language_combo))
    
    second_row.addWidget(clientemail_outlook)
    second_row.addWidget(language_combo)
    
    button_layout.addLayout(second_row)
    
    # add buttons to main layout
    layout.addLayout(button_layout)
    
    ## --- SAVE / MODIFY BUTTONS ---
    icon_path = self.resource_path("images/save_button.png") 
    icon = QIcon(icon_path)  
    if modify_flag:
        modify_button = QPushButton("Modify Order")
        modify_button.setIcon(icon) 
        layout.addWidget(modify_button, alignment=Qt.AlignRight)
        modify_button.clicked.connect(lambda: self.save_order(modify_flag))
    else:
        save_button = QPushButton("Save Order")
        save_button.setFixedWidth(150)
        save_button.setIcon(icon) 
        layout.addWidget(save_button, alignment=Qt.AlignRight)
        save_button.clicked.connect(lambda: self.save_order())
        
    # Prev button
    prev_button = QPushButton("Previous Tab")
    prev_button.setFixedWidth(100)
    prev_button.setStyleSheet("QPushButton { background-color: lightgray; }")
    layout.addWidget(prev_button, alignment=Qt.AlignLeft)
    prev_button.clicked.connect(self.go_to_previous_tab)
        
    frame.setWidget(container_widget)
    
#%% EMAIL FUNCTIONS
 # Send request to colleague to check quotation
def fun_ask_price_consultation_email(self, employee):
    """
    Opens the default mail client with a prefilled message asking
    a colleague to review the cost estimation for the current order.
    """
    order_id   = self.orderid
    entries    = self.order_entries_tab1
    # get the excl. BTW price as float (fallback to 0.0 on error)
    try:
        total_cost = float(self.order_entries_tab2["priceexclbtw"].text().strip())
    except Exception:
        total_cost = 0.0

    # --- Lookup the consulting employee’s email ---
    try:
        consult_employee = employee.currentText()
        first_name, last_name = consult_employee.split(" ", 1)
        self.cursor.execute(
            "SELECT Email FROM employees WHERE FirstName = ? AND LastName = ?",
            (first_name, last_name)
        )
        row = self.cursor.fetchone()
        if not row or not row[0]:
            QMessageBox.warning(
                self,
                "Not Found",
                f"No email address found for {consult_employee}."
            )
            return
        recipient = row[0]
    except Exception as e:
        QMessageBox.critical(
            self,
            "Lookup Error",
            f"Failed to look up email for {consult_employee}:\n{e}"
        )
        return

    # --- Lookup the customer’s details ---
    try:
        customerid = entries["customerid"].text().strip()
        if not customerid:
            QMessageBox.warning(
                self,
                "Missing Data",
                "No Customer ID entered for this order."
            )
            return

        self.cursor.execute(
            "SELECT FirstName, LastName, Email FROM customers WHERE CustomerID = ?",
            (customerid,)
        )
        cust = self.cursor.fetchone()
        if not cust:
            QMessageBox.warning(
                self,
                "Not Found",
                f"No customer found with ID {customerid}."
            )
            return

        customer_firstname, customer_lastname, customer_email = cust
    except Exception as e:
        QMessageBox.critical(
            self,
            "Lookup Error",
            f"Failed to look up customer details:\n{e}"
        )
        return

    # --- Build the mail subject & body ---
    subject = f"Consult on Cost Estimation for Order #{order_id}"
    body = (
        f"Hi {consult_employee},\n\n"
        f"Could you please double-check my cost estimation for Order {order_id}?\n\n"
        f"• Customer: ID {customerid}, {customer_firstname} {customer_lastname}, {customer_email}\n"
        f"• Description: {entries['description'].text()}\n"
        f"• Date Ordered: {entries['date_ordered'].date().toString('yyyy-MM-dd')}\n"
        f"• Estimated Price (excl. BTW & shipping): €{total_cost:.2f}\n\n"
        "Thanks in advance!\n"
    )

    # --- Launch default mail client via mailto: URI ---
    params = {
        "subject": subject,
        "body":    body
    }
    mailto = QUrl(
        "mailto:" + urllib.parse.quote(recipient) + "?" +
        urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    )

    if not QDesktopServices.openUrl(mailto):
        QMessageBox.critical(
            self,
            "Mail Error",
            "Could not open your mail client. "
            "Please ensure you have a default mail application configured."
        )
    
    
    
 # Send email client draft
def fun_client_email(self, language_combo):
    """
    Opens the default mail client with a customer‐facing email
    about their cost estimate, in the selected language.
    """
    # --- Gather and validate inputs ---
    try:
        total_cost = float(self.order_entries_tab2["priceexclbtw"].text().strip())
        language   = language_combo.currentText()

        customerid = self.order_entries_tab1["customerid"].text().strip()
        if not customerid:
            raise ValueError("Missing Customer ID")

        # fetch the customer’s email
        self.cursor.execute(
            "SELECT Email FROM customers WHERE CustomerID = ?",
            (customerid,)
        )
        row = self.cursor.fetchone()
        if not row or not row[0]:
            raise ValueError(f"No email for customer {customerid}")
        recipient = row[0]

    except Exception as e:
        QMessageBox.critical(
            None,
            "Error",
            f"Cannot prepare email:\n{e}"
        )
        return

    # --- Build subject & body ---
    subject = "Your 3BeePrinting Cost Estimate"

    if language == 'English':
        body = (
            "Dear Sir/Madam,\n\n"
            "Thank you for your message and your interest in 3BeePrinting!\n\n"
            f"The cost for printing your design in PLA is €{total_cost:.2f}, excluding BTW and shipping.\n"
            "If you agree to the terms, please let us know:\n"
            "  1. Your full name and address.\n"
            "  2. Print color preferences.\n"
            "  3. Pickup in Delft/Rotterdam or shipping (€6.95)?\n\n"
            "We look forward to your reply.\n\n"
            "Kind regards,\n"
            "The 3BeePrinting Team"
        )
    else:
        body = (
            "Beste Meneer/Mevrouw,\n\n"
            "Bedankt voor uw bericht en interesse in 3BeePrinting!\n\n"
            f"De totale kosten om in PLA te printen zijn €{total_cost:.2f}, exclusief BTW en verzendkosten.\n"
            "Als u akkoord gaat, wilt u dan aangeven:\n"
            "  1. Uw naam en adresgegevens.\n"
            "  2. Kleurvoorkeuren.\n"
            "  3. Ophalen in Delft/Rotterdam of verzenden (€6,95)?\n\n"
            "Met vriendelijke groet,\n"
            "The 3BeePrinting Team"
        )

    # --- Launch default mail client via mailto: ---
    params = {
        "subject": subject,
        "body":    body
    }
    mailto = QUrl(
        "mailto:" + urllib.parse.quote(recipient)
        + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    )

    if not QDesktopServices.openUrl(mailto):
        QMessageBox.critical(
            None,
            "Mail Error",
            "Could not open your mail client.\n"
            "Please ensure you have a default mail application configured."
        )
