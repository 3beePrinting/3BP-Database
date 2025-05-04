# invoice_pyqt.py

import sys
import os
import threading
import qrcode
import io
from PyQt5 import QtCore, QtGui, QtWidgets
from .payment_system import PaymentSystem
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

class InvoiceWindow(QtWidgets.QMainWindow):
    def __init__(self, customers=None):
        super().__init__()
        self.setWindowTitle("Invoice Creator")
        self.resize(1000, 950)

        # ——— Payment system setup ———
        self.payment_system = PaymentSystem()
        self.payment_system.set_invoice_status_callback(self.update_invoice_status)
        threading.Thread(target=self.payment_system.start_webhook_server, daemon=True).start()

        # ——— Customer data ———
        default_customers = {
            "John Doe": {
                "email": "johndoe@example.com",
                "billing_address": "123 Main St, Amsterdam, Netherlands",
                "shipping_address": "123 Main St, Amsterdam, Netherlands"
            }
        }
        # Use provided customers dict if given, otherwise fallback
        self.customers = customers if customers is not None else default_customers

        # ——— Build scrollable central widget ———
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        outer_layout = QtWidgets.QVBoxLayout(central)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)
        container = QtWidgets.QWidget()
        scroll.setWidget(container)
        self.main_layout = QtWidgets.QVBoxLayout(container)

        # Fonts
        self.default_font = QtGui.QFont("Helvetica", 9)
        self.bold_font = QtGui.QFont("Helvetica", 12, QtGui.QFont.Bold)

        # Totals
        self.subtotal = 0.0
        self.total_tax = 0.0

        # ——— Build all sections ———
        self.build_header()
        self.build_customer_info()
        self.build_invoice_title()
        self.build_items_section()
        self.build_totals_section()
        self.build_notes_section()
        self.build_terms_section()
        self.build_export_button()

    def build_header(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        grid = QtWidgets.QGridLayout(frame)

        # Logo and company info
        logo = QtGui.QPixmap('company_logo.png').scaled(100, 100, QtCore.Qt.KeepAspectRatio)
        lbl_logo = QtWidgets.QLabel()
        lbl_logo.setPixmap(logo)
        grid.addWidget(lbl_logo, 0, 0, 3, 1)

        info = [
            "3Bee Printing",
            "Address: Your Company Address",
            "Email: info@company.com",
            "Phone: +123456789",
            "TaxID: NL861821087B01",
            "KVK: 80840647"
        ]
        for i, text in enumerate(info):
            lbl = QtWidgets.QLabel(text)
            lbl.setFont(self.default_font if i > 0 else self.bold_font)
            grid.addWidget(lbl, i, 1)

        labels = ["Invoice Number:", "Issue Date:", "Due Date:", "PO Number:"]
        widgets = [
            QtWidgets.QLineEdit(),
            QtWidgets.QDateEdit(QtCore.QDate.currentDate()),
            QtWidgets.QDateEdit(QtCore.QDate.currentDate()),
            QtWidgets.QLineEdit()
        ]
        widgets[1].setDisplayFormat('dd-MM-yyyy')
        widgets[2].setDisplayFormat('dd-MM-yyyy')

        for i, widget in enumerate(widgets):
            grid.addWidget(QtWidgets.QLabel(labels[i]), i, 2)
            grid.addWidget(widget, i, 3)
        self.invoice_number, self.issue_date, self.due_date, self.po_number = widgets

        self.main_layout.addWidget(frame)

    def build_customer_info(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        form = QtWidgets.QFormLayout(frame)

        # Customer dropdown
        self.cmb_customer = QtWidgets.QComboBox()
        self.cmb_customer.addItems(self.customers.keys())
        self.cmb_customer.currentTextChanged.connect(self.populate_customer_info)

        # Labels for displaying details
        self.lbl_email = QtWidgets.QLabel()
        self.lbl_billing = QtWidgets.QLabel()
        self.lbl_shipping = QtWidgets.QLabel()

        form.addRow("Customer:", self.cmb_customer)
        form.addRow("Email:", self.lbl_email)
        form.addRow("Billing Address:", self.lbl_billing)
        form.addRow("Shipping Address:", self.lbl_shipping)

        # Populate initial info
        if self.customers:
            self.populate_customer_info()

        self.main_layout.addWidget(frame)

    def populate_customer_info(self):
        info = self.customers.get(self.cmb_customer.currentText(), {})
        self.lbl_email.setText(info.get('email', ''))
        self.lbl_billing.setText(info.get('billing_address', ''))
        self.lbl_shipping.setText(info.get('shipping_address', ''))

    def build_invoice_title(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        h = QtWidgets.QHBoxLayout(frame)
        h.addWidget(QtWidgets.QLabel("Invoice Title:"))
        self.invoice_title = QtWidgets.QLineEdit()
        h.addWidget(self.invoice_title)
        self.main_layout.addWidget(frame)

    def build_items_section(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        v = QtWidgets.QVBoxLayout(frame)

        self.tbl_items = QtWidgets.QTableWidget(0, 6)
        self.tbl_items.setHorizontalHeaderLabels([
            "Description", "Qty", "Price", "Tax", "Total", "Remove"
        ])
        self.tbl_items.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tbl_items.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tbl_items.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        v.addWidget(self.tbl_items)

        btn_add = QtWidgets.QPushButton("Add Item")
        btn_add.clicked.connect(self.add_item_row)
        v.addWidget(btn_add)

        self.main_layout.addWidget(frame, stretch=1)
        self._resize_items_table()

    def add_item_row(self):
        r = self.tbl_items.rowCount()
        self.tbl_items.insertRow(r)
        desc = QtWidgets.QLineEdit()
        qty = QtWidgets.QSpinBox(); qty.setRange(1, 100)
        price = QtWidgets.QLineEdit()

        tax_input = QtWidgets.QLineEdit(); tax_input.setReadOnly(True)
        btw_btn = QtWidgets.QPushButton("BTW"); btw_btn.setCheckable(True)
        btw_btn.toggled.connect(lambda checked, row=r: self.toggle_vat(row, checked))

        tax_container = QtWidgets.QWidget()
        tax_layout = QtWidgets.QHBoxLayout(tax_container); tax_layout.setContentsMargins(0,0,0,0)
        tax_layout.addWidget(tax_input); tax_layout.addWidget(btw_btn)
        tax_container.vat_enabled = False

        total_lbl = QtWidgets.QLabel("€ 0.00")
        remove_btn = QtWidgets.QPushButton("Remove"); remove_btn.clicked.connect(self.remove_item)

        widgets = [desc, qty, price, tax_container, total_lbl, remove_btn]
        for i, w in enumerate(widgets):
            self.tbl_items.setCellWidget(r, i, w)
            if i in (1, 2):
                w.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        qty.valueChanged.connect(self.update_line_total)
        price.textChanged.connect(self.update_line_total)
        self._resize_items_table()

    def toggle_vat(self, row, enabled):
        container = self.tbl_items.cellWidget(row, 3)
        container.vat_enabled = enabled
        self.update_line_total()

    def remove_item(self):
        btn = self.sender()
        for r in range(self.tbl_items.rowCount()):
            if self.tbl_items.cellWidget(r, 5) is btn:
                self.tbl_items.removeRow(r)
                break
        self.update_line_total()
        self._resize_items_table()

    def _resize_items_table(self):
        rows = self.tbl_items.rowCount()
        hdr_h = self.tbl_items.horizontalHeader().height()
        row_h = self.tbl_items.verticalHeader().defaultSectionSize()
        h = hdr_h + row_h * max(rows, 1)
        self.tbl_items.setMinimumHeight(h)
        self.tbl_items.setMaximumHeight(h)

    def update_line_total(self):
        sub = 0.0
        total_tax = 0.0
        for r in range(self.tbl_items.rowCount()):
            qty = self.tbl_items.cellWidget(r, 1).value()
            price = float(self.tbl_items.cellWidget(r, 2).text() or 0)
            container = self.tbl_items.cellWidget(r, 3)
            tax_amt = qty * price * 0.21 if container.vat_enabled else 0.0
            tax_input = container.findChild(QtWidgets.QLineEdit)
            tax_input.setText(f"{tax_amt:.2f}" if container.vat_enabled else "")
            total = qty * price + tax_amt
            self.tbl_items.cellWidget(r, 4).setText(f"€ {total:.2f}")
            sub += qty * price
            total_tax += tax_amt
        self.subtotal, self.total_tax = sub, total_tax
        self.calculate_totals()

    def build_totals_section(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        grid = QtWidgets.QGridLayout(frame)
        grid.setColumnStretch(2, 1)
        labels = [
            "Subtotal:", "Tax Total:", "Invoice Total:",
            "Discount (%):", "Deposit (%):", "Balance Due:"
        ]
        for i, text in enumerate(labels):
            grid.addWidget(QtWidgets.QLabel(text), i, 0)
        self.lbl_subtotal = QtWidgets.QLabel("€ 0.00"); grid.addWidget(self.lbl_subtotal, 0, 1)
        self.lbl_tax_total = QtWidgets.QLabel("€ 0.00"); grid.addWidget(self.lbl_tax_total, 1, 1)
        self.lbl_invoice_total = QtWidgets.QLabel("€ 0.00"); grid.addWidget(self.lbl_invoice_total, 2, 1)
        self.spin_discount = QtWidgets.QSpinBox(); self.spin_discount.setRange(0,100)
        self.spin_discount.valueChanged.connect(self.calculate_totals); grid.addWidget(self.spin_discount, 3, 1)
        self.spin_deposit = QtWidgets.QSpinBox(); self.spin_deposit.setRange(0,100)
        self.spin_deposit.valueChanged.connect(self.calculate_totals); grid.addWidget(self.spin_deposit, 4, 1)
        self.lbl_balance = QtWidgets.QLabel("€ 0.00"); grid.addWidget(self.lbl_balance, 5, 1)
        self.lbl_qr = QtWidgets.QLabel(); self.lbl_qr.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        grid.addWidget(self.lbl_qr, 0, 2, 6, 1)
        self.btn_qr = QtWidgets.QPushButton("Generate QR"); self.btn_qr.clicked.connect(self.handle_generate_qr)
        grid.addWidget(self.btn_qr, 6, 0, 1, 2)
        self.main_layout.addWidget(frame)

    def calculate_totals(self):
        inv = self.subtotal + self.total_tax - (self.subtotal * self.spin_discount.value() / 100)
        bal = inv - (inv * self.spin_deposit.value() / 100)
        self.lbl_subtotal.setText(f"€ {self.subtotal:.2f}")
        self.lbl_tax_total.setText(f"€ {self.total_tax:.2f}")
        self.lbl_invoice_total.setText(f"€ {inv:.2f}")
        self.lbl_balance.setText(f"€ {bal:.2f}")

    def handle_generate_qr(self):
        try:
            amt = float(self.lbl_balance.text().lstrip('€ '))
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid balance amount")
            return
        url = self.payment_system.create_payment(
            amt,
            self.invoice_number.text(),
            "http://example.org",
            "https://your.webhook.url/webhook"
        )
        if url:
            self.generate_qr_code(url)

    def generate_qr_code(self, url):
        img = qrcode.make(url).resize((200, 200))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        pix = QtGui.QPixmap()
        pix.loadFromData(buf.getvalue())
        self.lbl_qr.setPixmap(pix)
        path = os.path.join(os.getcwd(), 'qr_code_temp.png')
        img.save(path)
        self.qr_path = path

    def build_notes_section(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        v = QtWidgets.QVBoxLayout(frame)
        v.addWidget(QtWidgets.QLabel("Notes:"))
        self.txt_notes = QtWidgets.QTextEdit()
        self.txt_notes.setPlainText("Bedankt voor je bestelling! Groet, Team 3Bee")
        v.addWidget(self.txt_notes)
        self.main_layout.addWidget(frame)

    def build_terms_section(self):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        v = QtWidgets.QVBoxLayout(frame)
        v.addWidget(QtWidgets.QLabel("Terms and Conditions:"))
        self.txt_terms = QtWidgets.QTextEdit()
        self.txt_terms.setPlainText(
            "Payment terms: Payment within 14 days of the invoice date. "
            "Processing of the order will start after payment is processed.\n\n"
            "Payment Details: Directly, by clicking on the link in this invoice, "
            "via webshop payment or bank transfer to the following account\n\n"
            "Account name: 2AIM2    BIC/Swift Code: INGBNL2A\n"
            "IBAN: NL56INGB0007254515\n\n"
            "By placing an order the user agrees to the complete terms and conditions "
            "laid out by the company."
        )
        v.addWidget(self.txt_terms)
        self.main_layout.addWidget(frame)

    def build_export_button(self):
        btn = QtWidgets.QPushButton("Export to PDF")
        btn.clicked.connect(self.export_to_pdf)
        self.main_layout.addWidget(btn)

    def update_invoice_status(self, status):
        color = QtGui.QColor(
            'green' if status == 'paid' else
            'red'   if status == 'failed' else
            'orange'
        )
        self.lbl_balance.setText(status.capitalize())
        self.lbl_balance.setStyleSheet(f"color: {color.name()}")

    def export_to_pdf(self):
        fn = f"Invoice_{self.invoice_number.text()}.pdf"
        c = canvas.Canvas(fn, pagesize=letter)
        c.save()
        QtWidgets.QMessageBox.information(self, "Export Successful", f"{fn} created.")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = InvoiceWindow()
    window.show()
    sys.exit(app.exec_())
