# -*- coding: utf-8 -*-
"""
Analytics dialogs for 3BP Database
"""

import re
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QSizePolicy, QScrollArea, QPushButton, QToolButton, QMenu
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


class RevenuePerPeriodDialog(QDialog):
    """
    Dialog showing monthly Income, Profit, and Order counts for each year.
    Bars are grouped by month with different colors per year.
    Displays three stacked bar charts and a data table below, all inside a scrollable area.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.parent_app = parent
        self.conn = connection
        self.setWindowTitle("Monthly Financial Comparison")
        self.resize(1000, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(5,5,5,5)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)

        header = QLabel("Monthly Income, Profit & Orders by Year", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom:10px;")
        content_layout.addWidget(header)

        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        canvas.setMinimumHeight(600)
        content_layout.addWidget(canvas)
        content_layout.addSpacing(20)

        years, agg = self._aggregate_year_month()
        n = len(years)
        table = QTableWidget()
        table.setColumnCount(1 + n*3)
        headers = ["Month"] + [f"{y} Rev" for y in years] + [f"{y} Prof" for y in years] + [f"{y} #Orders" for y in years]
        table.setHorizontalHeaderLabels(headers)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        table.setMinimumHeight(400)

        months = [datetime(2000,m,1).strftime('%b') for m in range(1,13)]
        table.setRowCount(12)
        for r, mlabel in enumerate(months):
            table.setItem(r, 0, QTableWidgetItem(mlabel))
            for i, y in enumerate(years):
                rev = agg[y][r+1]['rev']
                prof = agg[y][r+1]['prof']
                cnt = agg[y][r+1]['count']
                table.setItem(r, 1 + i, QTableWidgetItem(f"{rev:.2f}"))
                table.setItem(r, 1 + n + i, QTableWidgetItem(f"{prof:.2f}"))
                table.setItem(r, 1 + 2*n + i, QTableWidgetItem(str(cnt)))
        table.resizeColumnsToContents()
        content_layout.addWidget(table)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
              substr(DateOrdered,1,4) as year,
              substr(DateOrdered,6,2) as month,
              PrintWeight, PrintTime, DesignTime, LabourTime,
              ShippingType, ShippingQuantity, ExtraServicesCost,
              FilamentIDs, PrinterIDs, PriceExclBTW
            FROM orders
            WHERE DateOrdered IS NOT NULL
              AND Status = 'Closed';
        """)
        return cur.fetchall()

    def _aggregate_year_month(self):
        data = self._fetch_data()
        app = self.parent_app
        dr, lr = app.design_hourly_rate, app.labour_hourly_rate
        fr, pr = app.filament_price_reference, app.printer_power_reference
        postNL = app.postNLprices

        years = sorted({row[0] for row in data if row[0] is not None})
        agg = {y: {m: {'rev':0.0, 'prof':0.0, 'count':0} for m in range(1,13)} for y in years}
        cur = self.conn.cursor()

        for year, mstr, pw, pt, dt, lt, st, sq, esc, fids, pids, price_excl in data:
            try:
                month = int(mstr)
                if not 1 <= month <= 12:
                    continue
            except:
                continue
            pw, pt, dt, lt = map(lambda x: float(x or 0), (pw, pt, dt, lt))
            esc = float(esc or 0)
            sq = int(sq or 0)
            cost_design = dr * dt
            cost_labour = (lt/60.0) * lr
            fids_list = [int(n) for n in re.findall(r"\d+", fids or "")] if fids else []
            if fids_list:
                ph = ",".join(['?']*len(fids_list))
                cur.execute(f"SELECT PricePerGram FROM filaments WHERE FilamentID IN ({ph})", fids_list)
                prices = [r[0] for r in cur.fetchall()]
                mat_ref = max(prices) if prices else fr
            else:
                mat_ref = fr
            cost_material = mat_ref * pw
            pids_list = [int(n) for n in re.findall(r"\d+", pids or "")] if pids else []
            if pids_list:
                ph = ",".join(['?']*len(pids_list))
                cur.execute(f"SELECT Power FROM printers WHERE PrinterID IN ({ph})", pids_list)
                powers = [r[0] for r in cur.fetchall()]
                pwr_ref = max(powers) if powers else pr
            else:
                pwr_ref = pr
            cost_elec = 0.9 * pwr_ref / 1000.0 * pt
            cost_ship = postNL.get(st, 0) * sq if isinstance(postNL, dict) else 0
            revenue = price_excl if price_excl is not None else (cost_design + cost_labour + cost_material + cost_elec + esc + cost_ship)
            profit = revenue - cost_material - cost_elec
            agg[year][month]['rev'] += revenue
            agg[year][month]['prof'] += profit
            agg[year][month]['count'] += 1

        return years, agg

    def _create_chart(self):
        years, agg = self._aggregate_year_month()
        months = list(range(1,13))
        labels = [datetime(2000,m,1).strftime('%b') for m in months]
        x = np.arange(len(months))
        width = 0.8 / max(len(years),1)

        fig, axes = plt.subplots(3,1, figsize=(12,10), tight_layout=True)
        for i,y in enumerate(years):
            axes[0].bar(x + i*width, [agg[y][m]['rev'] for m in months], width, label=str(y))
        axes[0].set_title('Income')
        axes[0].set_xticks(x + width*(len(years)-1)/2)
        axes[0].set_xticklabels(labels)
        axes[0].legend()

        for i,y in enumerate(years):
            axes[1].bar(x + i*width, [agg[y][m]['prof'] for m in months], width, label=str(y))
        axes[1].set_title('Profit')
        axes[1].set_xticks(x + width*(len(years)-1)/2)
        axes[1].set_xticklabels(labels)

        for i,y in enumerate(years):
            axes[2].bar(x + i*width, [agg[y][m]['count'] for m in months], width, label=str(y))
        axes[2].set_title('Orders')
        axes[2].set_xticks(x + width*(len(years)-1)/2)
        axes[2].set_xticklabels(labels)

        for ax in axes:
            ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        return FigureCanvas(fig)


class OrderStatusDialog(QDialog):
    """
    Dialog showing per-year counts of Closed vs Not accepted orders as a stacked bar chart.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Order Acceptance Rates")
        self.resize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        header = QLabel("Accepted vs Not Accepted Orders by Year", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom:10px;")
        layout.addWidget(header)

        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_status_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                substr(DateOrdered,1,4) AS year,
                SUM(CASE WHEN Status='Closed' THEN 1 ELSE 0 END) AS accepted,
                SUM(CASE WHEN Status='Not accepted' THEN 1 ELSE 0 END) AS rejected
            FROM orders
            WHERE DateOrdered IS NOT NULL
            GROUP BY year
            ORDER BY year;
        """)
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_status_data()
        years = [row[0] for row in data]
        acc = [row[1] for row in data]
        rej = [row[2] for row in data]
        x = np.arange(len(years))
        width = 0.6

        fig, ax = plt.subplots(figsize=(8,6), tight_layout=True)
        ax.bar(x, acc, width, label='Accepted')
        ax.bar(x, rej, width, bottom=acc, label='Not accepted')
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.set_ylabel('Number of Orders')
        ax.set_title('Order Acceptance by Year')
        ax.legend()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        return FigureCanvas(fig)


class CostOfGoodsSoldDialog(QDialog):
    """
    Dialog showing monthly COGS (material + electricity + labour + printer time).
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.parent_app = parent
        self.conn = connection
        self.setWindowTitle("Cost of Goods Sold (COGS) per Period")
        self.resize(800,600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        title = QLabel("Monthly COGS by Year", alignment=Qt.AlignCenter)
        title.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom:10px;")
        layout.addWidget(title)

        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_cogs_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
              substr(DateOrdered,1,4) AS year,
              substr(DateOrdered,6,2) AS month,
              PrintWeight, PrintTime, DesignTime, LabourTime,
              FilamentIDs, PrinterIDs
            FROM orders
            WHERE DateOrdered IS NOT NULL
              AND Status='Closed';
        """)
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_cogs_data()
        app = self.parent_app
        dr, lr = app.design_hourly_rate, app.labour_hourly_rate
        fr, pr = app.filament_price_reference, app.printer_power_reference
        years = sorted({row[0] for row in data if row[0]})
        agg = {y:{m:0.0 for m in range(1,13)} for y in years}
        cur = self.conn.cursor()
        for year, mstr, pw, pt, dt, lt, fids, pids in data:
            try:
                month = int(mstr)
            except:
                continue
            pw, pt, dt, lt = map(lambda x: float(x or 0),(pw,pt,dt,lt))
            ids = [int(n) for n in re.findall(r"\d+", fids or "")] if fids else []
            if ids:
                ph = ",".join(['?']*len(ids))
                cur.execute(f"SELECT PricePerGram FROM filaments WHERE FilamentID IN ({ph})", ids)
                prices=[r[0] for r in cur.fetchall()]
                mat_ref = max(prices) if prices else fr
            else:
                mat_ref=fr
            cost_mat = mat_ref * pw
            ids2=[int(n) for n in re.findall(r"\d+", pids or "")] if pids else []
            if ids2:
                ph2=",".join(['?']*len(ids2))
                cur.execute(f"SELECT Power FROM printers WHERE PrinterID IN ({ph2})", ids2)
                powers=[r[0] for r in cur.fetchall()]
                pwr_ref=max(powers) if powers else pr
            else:
                pwr_ref=pr
            cost_elec = 0.9 * pwr_ref/1000.0 * pt
            cost_lab = (lt/60.0)*lr
            cost_prt = (1.0 if pt>24 else 0.5)*pt
            cogs = cost_mat + cost_elec + cost_lab + cost_prt
            agg[year][month]+=cogs
        months=list(range(1,13))
        labels=[datetime(2000,m,1).strftime('%b') for m in months]
        x=np.arange(12)
        width=0.8/len(years)
        fig,ax=plt.subplots(figsize=(10,5),tight_layout=True)
        for i,y in enumerate(years):
            vals=[agg[y][m] for m in months]
            ax.bar(x+i*width,vals,width,label=str(y))
        ax.set_xticks(x+width*(len(years)-1)/2)
        ax.set_xticklabels(labels)
        ax.set_ylabel('COGS (€)')
        ax.set_title('Monthly COGS by Year')
        ax.legend()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        return FigureCanvas(fig)


class AnalyticsDialog(QDialog):
    """
    Main Analytics menu dialog with metric categories and sub-options.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.parent_app = parent
        self.setWindowTitle("Analytics")
        self.resize(500, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20,20,20,20)

        # --- Financial Metrics ---
        fm_button = QToolButton(self)
        fm_button.setText("Financial Metrics")
        fm_menu = QMenu(fm_button)
        # 1.1 Revenue & Profit
        rev_menu = QMenu("Revenue & Profit", fm_button)
        rev_menu.addAction("Revenue per Period", lambda: RevenuePerPeriodDialog(self.parent_app, self.conn).exec_())
        rev_menu.addAction("Cost of Goods Sold (COGS)", lambda: CostOfGoodsSoldDialog(self.parent_app, self.conn).exec_())
        rev_menu.addAction("Gross Profit & Margin")
        fm_menu.addMenu(rev_menu)
        # 1.2 Expense Breakdown
        exp_br_menu = QMenu("Expense Breakdown", fm_button)
        exp_br_menu.addAction("Expenses by Category", lambda: ExpensesByCategoryDialog(self.parent_app, self.conn).exec_())
        exp_br_menu.addAction("Monthly Burn Rate", lambda: MonthlyBurnRateDialog(self.parent_app, self.conn).exec_())
        exp_br_menu.addAction("Fixed vs Variable Expenses", lambda: FixedVariableExpensesDialog(self.parent_app, self.conn).exec_())
        exp_br_menu.addAction("Expense Trend by Category", lambda: ExpenseTrendByCategoryDialog(self.parent_app, self.conn).exec_())
        exp_br_menu.addAction("Top 10 Expenses", lambda: TopExpensesDialog(self.parent_app, self.conn).exec_())
        exp_br_menu.addAction("Expense-to-Revenue Ratio", lambda: ExpenseToRevenueRatioDialog(self.parent_app, self.conn).exec_())
        fm_menu.addMenu(exp_br_menu)
        # 1.3 Cash Flow
        cash_menu = QMenu("Cash Flow", fm_button)
        cash_menu.addAction("Invoices Issued vs Paid")
        cash_menu.addAction("Outstanding Receivables")
        fm_menu.addMenu(cash_menu)
        fm_button.setMenu(fm_menu)
        fm_button.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(fm_button)

        # --- Operational Metrics ---
        op_button = QToolButton(self)
        op_button.setText("Operational Metrics")
        op_menu = QMenu(op_button)
        # 2.1 Orders & Requests
        ord_menu = QMenu("Orders & Requests", op_button)
        ord_menu.addAction("Number of Requests vs Converted Orders", lambda: RequestsConversionDialog(self.parent_app, self.conn).exec_())
        # TODO: add Throughput and Lead Time metrics here
        ord_menu.addAction("Order Acceptance Rates", lambda: OrderStatusDialog(self.parent_app, self.conn).exec_())
        op_menu.addMenu(ord_menu)
        # 2.2 Service Mix
        svc_menu = QMenu("Service Mix", op_button)
        svc_menu.addAction("Services Breakdown", lambda: ServiceMixDialog(self.parent_app, self.conn).exec_())
        svc_menu.addAction("Average Order Size", lambda: AverageOrderCostDialog(self.parent_app, self.conn).exec_())
        op_menu.addMenu(svc_menu)
        # 2.3 Task & Resource Utilization
        util_menu = QMenu("Task & Resource Utilization", op_button)
        util_menu.addAction("Printer Utilization")
        util_menu.addAction("Employee Workload")
        op_menu.addMenu(util_menu)
        op_button.setMenu(op_menu)
        op_button.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(op_button)

        # --- Inventory Metrics ---
        inv_button = QToolButton(self)
        inv_button.setText("Inventory Metrics")
        inv_menu = QMenu(inv_button)
        # 3.1 Filament Stock
        fil_menu = QMenu("Filament Stock", inv_button)
        fil_menu.addAction("Stock Levels vs Usage")
        fil_menu.addAction("Days of Stock on Hand")
        inv_menu.addMenu(fil_menu)
        # 3.2 Printers & Print Settings
        ps_menu = QMenu("Printers & Print Settings", inv_button)
        ps_menu.addAction("Print Setting Performance")
        ps_menu.addAction("Cost per Material")
        inv_menu.addMenu(ps_menu)
        inv_button.setMenu(inv_menu)
        inv_button.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(inv_button)

        # --- Customer & Supplier Metrics ---
        cs_button = QToolButton(self)
        cs_button.setText("Customer & Supplier Metrics")
        cs_menu = QMenu(cs_button)
        # 4.1 Customers
        cust_menu = QMenu("Customers", cs_button)
        cust_menu.addAction("Top Customers by Revenue")
        cust_menu.addAction("New vs Returning")
        cust_menu.addAction("Customer Lifetime Value")
        cs_menu.addMenu(cust_menu)
        # 4.2 Suppliers
        sup_menu = QMenu("Suppliers", cs_button)
        sup_menu.addAction("Spend by Supplier")
        sup_menu.addAction("Lead Times")
        cs_menu.addMenu(sup_menu)
        cs_button.setMenu(cs_menu)
        cs_button.setPopupMode(QToolButton.InstantPopup)
        layout.addWidget(cs_button)

        layout.addStretch()
        

class RequestsConversionDialog(QDialog):
    """
    Dialog showing the number of requests vs converted (closed) orders per year.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Requests vs Converted Orders")
        self.resize(800,600)
        layout = QVBoxLayout(self)
        header = QLabel("Requests vs Converted Orders by Year", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
              substr(DateOrdered,1,4) AS year,
              SUM(CASE WHEN Status='Closed' OR Status='Not accepted' THEN 1 ELSE 0 END) AS requests,
              SUM(CASE WHEN Status='Closed' THEN 1 ELSE 0 END) AS converted
            FROM orders
            WHERE DateOrdered IS NOT NULL
            GROUP BY year
            ORDER BY year;
        """)
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_data()
        years = [row[0] for row in data]
        req = [row[1] for row in data]
        conv = [row[2] for row in data]
        x = np.arange(len(years))
        width = 0.35
        fig, ax = plt.subplots(figsize=(8,6), tight_layout=True)
        ax.bar(x - width/2, req, width, label='Requests')
        ax.bar(x + width/2, conv, width, label='Converted')
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.set_ylabel('Count')
        ax.set_title('Requests vs Converted Orders by Year')
        ax.legend()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        return FigureCanvas(fig)

class ServiceMixDialog(QDialog):
    """
    Dialog showing the breakdown of services requested vs executed per year.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Service Mix Breakdown")
        self.resize(800,600)
        layout = QVBoxLayout(self)
        header = QLabel("Service Mix by Year", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This chart shows the count of each service type (3D Printing, 3D Design, 3D Scanning) "
            "for each closed order, grouped by year.", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT substr(DateOrdered,1,4) AS year, Services
            FROM orders
            WHERE DateOrdered IS NOT NULL AND Status = 'Closed';
        """)
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_data()
        types = ["3D Printing", "3D Design", "3D Scanning"]
        years = sorted({row[0] for row in data if row[0]})
        counts = {t:{y:0 for y in years} for t in types}
        for year, svc in data:
            if svc:
                for s in svc.split(','):
                    s = s.strip()
                    if s in counts:
                        counts[s][year] += 1
        x = np.arange(len(years))
        width = 0.8 / len(types)
        fig, ax = plt.subplots(figsize=(8,6), tight_layout=True)
        for i, t in enumerate(types):
            vals = [counts[t][y] for y in years]
            ax.bar(x + i*width, vals, width, label=t)
        ax.set_xticks(x + width*(len(types)-1)/2)
        ax.set_xticklabels(years)
        ax.set_ylabel('Count')
        ax.set_title('Service Mix by Year')
        ax.legend()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        return FigureCanvas(fig)


class AverageOrderCostDialog(QDialog):
    """
    Dialog showing the average order cost (PriceExclBTW) per order per year.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Average Order Cost by Year")
        self.resize(800,600)
        layout = QVBoxLayout(self)
        header = QLabel("Average Order Cost by Year", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This chart displays the average cost per closed order for each year, "
            "calculated from the PriceExclBTW field.", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT substr(DateOrdered,1,4) AS year, PriceExclBTW
            FROM orders
            WHERE DateOrdered IS NOT NULL AND Status = 'Closed';
        """)
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_data()
        years = sorted({row[0] for row in data if row[0]})
        vals = {y: [] for y in years}
        for year, cost in data:
            try:
                vals[year].append(float(cost or 0))
            except:
                pass
        avgs = [(sum(vals[y]) / len(vals[y])) if vals[y] else 0 for y in years]
        x = np.arange(len(years))
        fig, ax = plt.subplots(figsize=(8,6), tight_layout=True)
        ax.bar(x, avgs, 0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.set_ylabel('Avg Cost (€)')
        ax.set_title('Average Order Cost by Year')
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        return FigureCanvas(fig)


class ExpensesByCategoryDialog(QDialog):
    """
    Dialog showing expense breakdown by category (pie chart).
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Expenses by Category")
        self.resize(700,500)
        layout = QVBoxLayout(self)
        header = QLabel("Expenses by Category", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This pie chart shows the proportion of total expenses by each category (Purpose).", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT Purpose, SUM(CostIncBTW) AS total
            FROM expenses
            GROUP BY Purpose;
        """)
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_data()
        labels = [row[0] for row in data]
        sizes  = [row[1] for row in data]
        fig, ax = plt.subplots(figsize=(8,6), tight_layout=True)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.set_title('Expense Breakdown by Category')
        return FigureCanvas(fig)


class MonthlyBurnRateDialog(QDialog):
    """
    Dialog showing monthly total expenses over time (burn rate line).
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Monthly Burn Rate")
        self.resize(900,500)
        layout = QVBoxLayout(self)
        header = QLabel("Monthly Burn Rate", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This line chart plots total monthly expenses to help visualize your burn rate over time.", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT substr(DateOrdered,1,7) AS period, SUM(CostIncBTW) AS total
            FROM expenses
            WHERE DateOrdered IS NOT NULL
            GROUP BY period
            ORDER BY period;
        """)
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_data()
        periods = [row[0] for row in data]
        totals  = [row[1] for row in data]
        x = np.arange(len(periods))
        fig, ax = plt.subplots(figsize=(10,5), tight_layout=True)
        ax.plot(x, totals, marker='o')
        ax.set_xticks(x)
        ax.set_xticklabels(periods, rotation=45)
        ax.set_ylabel('Total Expense (€)')
        ax.set_title('Monthly Burn Rate')
        return FigureCanvas(fig)


class FixedVariableExpensesDialog(QDialog):
    """
    Dialog showing fixed vs variable expenses proportions.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Fixed vs Variable Expenses")
        self.resize(700,500)
        layout = QVBoxLayout(self)
        header = QLabel("Fixed vs Variable Expenses", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This pie chart classifies expenses into fixed (e.g. rent, salaries) vs variable (e.g. materials, shipping) and shows their proportions.", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("SELECT Purpose, SUM(CostIncBTW) FROM expenses GROUP BY Purpose;")
        return cur.fetchall()

    def _create_chart(self):
        data = self._fetch_data()
        fixed_list = ["Monthly costs","Marketing","Tax return"]
        fixed = sum(val for purp,val in data if purp in fixed_list)
        variable = sum(val for purp,val in data if purp not in fixed_list)
        labels = ["Fixed","Variable"]
        sizes  = [fixed, variable]
        fig, ax = plt.subplots(figsize=(8,6), tight_layout=True)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title('Fixed vs Variable Expenses')
        return FigureCanvas(fig)


class ExpenseTrendByCategoryDialog(QDialog):
    """
    Dialog showing monthly expense trends per category (line chart).
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Expense Trend by Category")
        self.resize(900,500)
        layout = QVBoxLayout(self)
        header = QLabel("Expense Trends by Category", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This line chart shows monthly expense totals for each category (Purpose) over time. Use it to spot rising or falling costs by category.", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT substr(DateOrdered,1,7) AS period, Purpose, SUM(CostIncBTW)
            FROM expenses
            WHERE DateOrdered IS NOT NULL
            GROUP BY period, Purpose
            ORDER BY period;
        """)
        return cur.fetchall()

    def _create_chart(self):
        raw    = self._fetch_data()
        periods = sorted({r[0] for r in raw})
        cats    = sorted({r[1] for r in raw})
        data    = {c:{p:0 for p in periods} for c in cats}
        for p, c, v in raw:
            data[c][p] = v
        fig, ax = plt.subplots(figsize=(10,6), tight_layout=True)
        x = np.arange(len(periods))
        for c in cats:
            y = [data[c][p] for p in periods]
            ax.plot(x, y, marker='o', label=c)
        ax.set_xticks(x)
        ax.set_xticklabels(periods, rotation=45)
        ax.set_ylabel('Expense (€)')
        ax.set_title('Monthly Expense Trends by Category')
        ax.legend()
        return FigureCanvas(fig)
    
class ExpensesByPeriodDialog(QDialog):
    """
    Dialog showing monthly total expenses per year.
    Bars are grouped by month with different colors per year,
    plus a table below.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.parent_app = parent
        self.conn = connection
        self.setWindowTitle("Expenses per Period")
        self.resize(1000, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(5,5,5,5)
        outer.setSpacing(10)

        # Scroll area for entire content
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)

        # Header
        header = QLabel("Monthly Expenses by Year", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold;")
        layout.addWidget(header)

        # Chart
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        canvas.setMinimumHeight(400)
        layout.addWidget(canvas)

        # Table
        self.table = QTableWidget()
        self._populate_table()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.table.setMinimumHeight(300)
        layout.addWidget(self.table)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
              substr(DateOrdered,1,4) AS year,
              substr(DateOrdered,6,2) AS month,
              ROUND(SUM(CostIncBTW),2) AS total
            FROM expenses
            WHERE DateOrdered IS NOT NULL
            GROUP BY year, month
            ORDER BY year, month;
        """)
        return cur.fetchall()

    def _aggregate(self):
        raw = self._fetch_data()
        # collect unique years
        years = sorted({r[0] for r in raw if r[0]})
        # init agg[year][month] = 0
        agg = {y: {m:0.0 for m in range(1,13)} for y in years}

        for year, mstr, total in raw:
            try:
                m = int(mstr)
                if 1 <= m <= 12:
                    agg[year][m] = float(total or 0)
            except:
                continue
        return years, agg

    def _create_chart(self):
        years, agg = self._aggregate()
        months = list(range(1,13))
        labels = [datetime(2000,m,1).strftime('%b') for m in months]
        x = np.arange(len(months))
        width = 0.8 / max(len(years),1)

        fig, ax = plt.subplots(figsize=(12,5), tight_layout=True)
        for i, y in enumerate(years):
            vals = [agg[y][m] for m in months]
            ax.bar(x + i*width, vals, width, label=str(y))

        ax.set_xticks(x + width*(len(years)-1)/2)
        ax.set_xticklabels(labels)
        ax.set_ylabel("Expenses (€)")
        ax.set_title("Monthly Expenses by Year")
        ax.legend()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        return FigureCanvas(fig)

    def _populate_table(self):
        years, agg = self._aggregate()
        # columns: Month, one per year
        self.table.setColumnCount(1 + len(years))
        headers = ["Month"] + [str(y) for y in years]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(12)

        for row_idx, m in enumerate(range(1,13)):
            month_label = datetime(2000,m,1).strftime('%b')
            self.table.setItem(row_idx, 0, QTableWidgetItem(month_label))
            for col_idx, y in enumerate(years, start=1):
                val = agg[y][m]
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(f"{val:.2f}"))

        self.table.resizeColumnsToContents()

class TopExpensesDialog(QDialog):
    """
    Dialog showing top 10 largest individual expense entries.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Top 10 Largest Expenses")
        self.resize(800,500)
        layout = QVBoxLayout(self)
        header = QLabel("Top 10 Largest Expenses", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This bar chart lists the ten individual expenses with the highest CostIncBTW values.", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("SELECT Description, CostIncBTW FROM expenses ORDER BY CostIncBTW DESC LIMIT 10;")
        return cur.fetchall()

    def _create_chart(self):
        data  = self._fetch_data()
        labels= [r[0] for r in data]
        vals  = [r[1] for r in data]
        y_pos = np.arange(len(labels))
        fig, ax= plt.subplots(figsize=(8,6), tight_layout=True)
        ax.barh(y_pos, vals)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel('CostIncBTW (€)')
        ax.set_title('Top 10 Largest Expenses')
        return FigureCanvas(fig)


class ExpenseToRevenueRatioDialog(QDialog):
    """
    Dialog showing expense-to-revenue ratio per month.
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Expense-to-Revenue Ratio")
        self.resize(900,500)
        layout = QVBoxLayout(self)
        header = QLabel("Monthly Expense/Revenue Ratio", alignment=Qt.AlignCenter)
        header.setStyleSheet("font-size:16pt; font-weight:bold; margin-bottom:10px;")
        layout.addWidget(header)
        expl = QLabel(
            "This line chart shows the ratio of total expenses to revenue each month, highlighting cost efficiency.", alignment=Qt.AlignLeft)
        expl.setWordWrap(True)
        expl.setStyleSheet("font-size:10pt; margin-bottom:15px;")
        layout.addWidget(expl)
        canvas = self._create_chart()
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(canvas)

    def _fetch_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            WITH rev AS (
              SELECT substr(DateOrdered,1,7) AS period, SUM(PriceExclBTW) AS rev
              FROM orders WHERE Status='Closed' GROUP BY period
            ), exp AS (
              SELECT substr(DateOrdered,1,7) AS period, SUM(CostIncBTW) AS exp
              FROM expenses GROUP BY period
            )
            SELECT r.period, r.rev, e.exp FROM rev r LEFT JOIN exp e ON r.period=e.period ORDER BY r.period;
        """)
        return cur.fetchall()

    def _create_chart(self):
        data  = self._fetch_data()
        periods= [r[0] for r in data]
        ratios = [(r[2] or 0)/r[1] if r[1] else 0 for r in data]
        x = np.arange(len(periods))
        fig, ax= plt.subplots(figsize=(10,5), tight_layout=True)
        ax.plot(x, ratios, marker='o')
        ax.set_xticks(x)
        ax.set_xticklabels(periods, rotation=45)
        ax.set_ylabel('Expense/Revenue')
        ax.set_title('Monthly Expense-to-Revenue Ratio')
        return FigureCanvas(fig)


# --- Grouped dialogs for second-level menu selections ---

class RevenueProfitDialog(QDialog):
    """
    Grouped view for Revenue & Profit metrics:
      • Revenue per Period
      • Cost of Goods Sold (COGS)
      • Gross Profit & Margin
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Revenue & Profit Metrics")
        self.resize(900,800)
        layout = QVBoxLayout(self)
        title = QLabel("Revenue & Profit Metrics", alignment=Qt.AlignCenter)
        title.setStyleSheet("font-size:18pt; font-weight:bold; margin-bottom:15px;")
        layout.addWidget(title)
        # Section: Revenue per Period
        sec1 = QLabel("Revenue per Period: Displays monthly revenue grouped by period (PriceExclBTW).", alignment=Qt.AlignLeft)
        sec1.setWordWrap(True)
        sec1.setStyleSheet("font-size:10pt; margin-bottom:10px;")
        layout.addWidget(sec1)
        try:
            from .analytics import RevenuePerPeriodDialog
            rpt = RevenuePerPeriodDialog(parent, connection)
            inner = rpt._create_chart()
            layout.addWidget(inner)
        except:
            pass
        # Section: COGS
        sec2 = QLabel("Cost of Goods Sold (COGS): Calculates total cost of materials and services used to produce goods.", alignment=Qt.AlignLeft)
        sec2.setWordWrap(True)
        sec2.setStyleSheet("font-size:10pt; margin-bottom:10px;")
        layout.addWidget(sec2)
        # Placeholder if COGS dialog exists
        try:
            from .analytics import CostOfGoodsSoldDialog
            cogs = CostOfGoodsSoldDialog(parent, connection)
            layout.addWidget(cogs._create_chart())
        except:
            pass
        # Section: Gross Profit & Margin
        sec3 = QLabel("Gross Profit & Margin: Shows gross profit and margin percentages over time.", alignment=Qt.AlignLeft)
        sec3.setWordWrap(True)
        sec3.setStyleSheet("font-size:10pt; margin-bottom:10px;")
        layout.addWidget(sec3)
        try:
            from .analytics import GrossProfitMarginDialog
            gpm = GrossProfitMarginDialog(parent, connection)
            layout.addWidget(gpm._create_chart())
        except:
            pass

class ExpenseBreakdownDialog(QDialog):
    """
    Grouped view for Expense Breakdown metrics:
      • Expenses by Category
      • Monthly Burn Rate
      • Fixed vs Variable Expenses
      • Expense Trends by Category
    """
    def __init__(self, parent=None, connection=None):
        super().__init__(parent)
        self.conn = connection
        self.setWindowTitle("Expense Breakdown Metrics")
        self.resize(900,1000)
        layout = QVBoxLayout(self)
        title = QLabel("Expense Breakdown Metrics", alignment=Qt.AlignCenter)
        title.setStyleSheet("font-size:18pt; font-weight:bold; margin-bottom:15px;")
        layout.addWidget(title)
        # Expenses by Category
        sec1 = QLabel("Expenses by Category: Shows proportion of expenses grouped by category.", alignment=Qt.AlignLeft)
        sec1.setWordWrap(True)
        sec1.setStyleSheet("font-size:10pt; margin-bottom:10px;")
        layout.addWidget(sec1)
        try:
            ebc = ExpensesByCategoryDialog(parent, connection)
            layout.addWidget(ebc._create_chart())
        except:
            pass
        # Monthly Burn Rate
        sec2 = QLabel("Monthly Burn Rate: Plots total monthly expenses to visualize cash burn.", alignment=Qt.AlignLeft)
        sec2.setWordWrap(True)
        sec2.setStyleSheet("font-size:10pt; margin-bottom:10px;")
        layout.addWidget(sec2)
        try:
            mbr = MonthlyBurnRateDialog(parent, connection)
            layout.addWidget(mbr._create_chart())
        except:
            pass
        # Fixed vs Variable Expenses
        sec3 = QLabel("Fixed vs Variable Expenses: Compares fixed and variable components of expenses.", alignment=Qt.AlignLeft)
        sec3.setWordWrap(True)
        sec3.setStyleSheet("font-size:10pt; margin-bottom:10px;")
        layout.addWidget(sec3)
        try:
            fve = FixedVariableExpensesDialog(parent, connection)
            layout.addWidget(fve._create_chart())
        except:
            pass
        # Expense Trends by Category
        sec4 = QLabel("Expense Trends by Category: Tracks expense changes over time by category.", alignment=Qt.AlignLeft)
        sec4.setWordWrap(True)
        sec4.setStyleSheet("font-size:10pt; margin-bottom:10px;")
        layout.addWidget(sec4)
        try:
            etc = ExpenseTrendByCategoryDialog(parent, connection)
            layout.addWidget(etc._create_chart())
        except:
            pass





