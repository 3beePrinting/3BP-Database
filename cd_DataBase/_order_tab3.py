# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 14:34:15 2025

Code for tab3 (Overview of teh order)

@author: feder
"""

from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout,QPushButton,
    QMessageBox, QTextEdit, QGroupBox, QComboBox )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import win32com.client as win32


#%% TAB 3 - Overview of the order widget
# In this tab, I want to show the order details to confirm everything before saving
def tab3_widgets(self, frame, modify_flag = False):
    layout = QVBoxLayout()
    frame.setLayout(layout)
    
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
                material_text = self.parts[0]["Material"]
                color_text = self.parts[0]["Color"]
            
                for i in range(len(self.parts)):
                    part = self.parts[i]
                    printed_parts += int(part["QuantityPrinted"])
                    total_parts += int(part["QuantityOrdered"])
                    if part["Material"] != material_text:
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
        save_button.clicked.connect(lambda: self.save_order(modify_flag))
        
    # Prev button
    prev_button = QPushButton("Previous Tab")
    prev_button.setFixedWidth(100)
    prev_button.setStyleSheet("QPushButton { background-color: lightgray; }")
    layout.addWidget(prev_button, alignment=Qt.AlignLeft)
    prev_button.clicked.connect(self.go_to_previous_tab)
        
    
#%% EMAIL FUNCTIONS
 # Send request to colleague to check quotation
def fun_ask_price_consultation_email(self, employee):
    order_id = self.orderid
    entries = self.order_entries_tab1
    total_cost = float(self.order_entries_tab2["priceexclbtw"].text().strip())
    
    # Check inputs
    try:
        consult_employee = employee.currentText()
        subject = f"Ask a consult to {consult_employee}"
        
        first_name, last_name = consult_employee.split(" ", 1)  # Split into two parts

        self.cursor.execute("SELECT Email FROM employees WHERE FirstName = ? AND LastName = ?", (first_name, last_name))
        recipient = self.cursor.fetchone()[0]
        
        customerid = entries["customerid"].text()
        self.cursor.execute("SELECT FirstName, LastName, Email FROM customers WHERE CustomerID = ?", (customerid))
        customer_firstname, customer_lastname, customer_email = self.cursor.fetchone()
        
        body = f""" Hi colleague!
Could you double-check my cost estimation for Order {order_id}.
More info on the order: 
    • Customer data: ID {customerid}, Name {customer_firstname} {customer_lastname}, email {customer_email},
    • Description: {entries["description"].text()}
    • Date Order: {entries["date_ordered"].date().toString("yyyy-MM-dd")}
    • My cost estimation: {total_cost}  euro excl. BTW & shipping 
For more information open the order on the database.
    
    """
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
        
        # Open the email for review (doesn't send it automatically)
        mail.Display()  # Opens the email window in Outlook for editing
        
        print("Email created successfully in Outlook.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    
    
 # Send email client draft
def fun_client_email(self, language_combo):
    try:
        total_cost = float(self.order_entries_tab2["priceexclbtw"].text().strip())
        language = language_combo.currentText()
        
        customerid = self.order_entries_tab1["customerid"].text()
        self.cursor.execute("SELECT Email FROM customers WHERE CustomerID = ?", (customerid))
        recipient = self.cursor.fetchone()
    except:
        QMessageBox.critical(None, "Error", "Insufficient data inputted.")
    
    subject = "New form submission"
    
    if language == 'English':
        body = f"""Dear Sir/Madam,


Thank you for your message and your interest in 3BeePrinting! 

The cost for printing your design in PLA is {total_cost} euro, excluding BTW and shipping costs.  
If you agree to the terms, then please provide the following information so that we may prepare the invoice and begin processing your order:
   1. Your full name and address.
   2. Print color preferences.
   3. Do you want to pick up the print in Delft/Rotterdam? Or do you want to have the print shipped to your address (6.95 euros)?

We are looking forward to hearing from you.


Kind regards,
The 3BeePrinting Team
    """
    else:
        body = f"""Beste Meneer/Mevrouw,


Bedankt voor uw bericht en interesse in 3BeePrinting!

De totale kosten om dit te printen in PLA zijn {total_cost} euro, exclusief BTW and verzendkosten.  
Als je hiermee akkoord gaat, zou je het volgende willen laten weten:
   1. Uw naam en adresgegevens.
   2. Heeft u kleurvoorkeuren?
   3. Wilt u het ophalen in Delft/Rotterdam? Of zullen we het verzenden (6.95 euros)?

In afwachting van uw reactie.


Met vriendelijke groet,
The 3BeePrinting Team
    """
    
    try:
        # Connect to Outlook
        outlook = win32.Dispatch('outlook.application')
        
        # Create a new email
        mail = outlook.CreateItem(0)  # 0 corresponds to a MailItem
        
        # Set recipient, subject, and body
        mail.To = recipient
        mail.Subject = subject
        mail.Body = body
        
        # Open the email for review (doesn't send it automatically)
        mail.Display()  # Opens the email window in Outlook for editing
        
        print("Email created successfully in Outlook.")
    except Exception as e:
        print(f"An error occurred: {e}")