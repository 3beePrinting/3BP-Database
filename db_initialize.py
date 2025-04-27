# -*- coding: utf-8 -*-
"""
Functions to import for 3BP database

@author: feder
"""

import sqlite3

def initialize_db(dbfile_name):
    conn = sqlite3.connect(dbfile_name)
    cursor = conn.cursor()

    # Create Employees table
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
                        EmployeeID INTEGER PRIMARY KEY,
                        FirstName TEXT,
                        LastName TEXT,
                        Email TEXT,
                        Phone TEXT,
                        Address TEXT,
                        ZIPCode TEXT,
                        City TEXT,
                        Country TEXT,
                        JobTitle TEXT,
                        Availability INTEGER,
                        CurrentStatus TEXT,
                        Notes TEXT,
                        Picture BLOB)''')
    
    # Create Customers table
    cursor.execute('''CREATE TABLE IF NOT EXISTS customers (
                        CustomerID INTEGER PRIMARY KEY,
                        FirstName TEXT,
                        LastName TEXT,
                        Company TEXT,
                        Email TEXT,
                        Phone TEXT,
                        Address TEXT,
                        ZIPCode TEXT,
                        City TEXT,
                        Country TEXT,
                        Notes TEXT,
                        Experience TEXT)''')

    
    # Create Suppliers table
    cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers (
                        SupplierID INTEGER PRIMARY KEY,
                        Company TEXT,
                        Website TEXT,
                        Description TEXT,
                        Products TEXT,
                        CompanyEmail TEXT,
                        CompanyPhone TEXT,
                        ContactName TEXT,
                        ContactEmail TEXT,
                        ContactPhone TEXT,
                        Address TEXT,
                        ZIPCode TEXT,
                        City TEXT,
                        Country TEXT,
                        Notes TEXT,
                        Experience TEXT)''')
    
    # Create Expenses table
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                        OCnumber INTEGER PRIMARY KEY,
                        SupplierID INTEGER,
                        Component TEXT,
                        Description TEXT,
                        Link TEXT,
                        Purpose TEXT,
                        DateOrdered TEXT,
                        DateDelivery TEXT,
                        CostIncBTW REAL,
                        CostShipping REAL,
                        BTW REAL,
                        OrderStatus TEXT,
                        Responsible TEXT,
                        TaxReturnApplicable TEXT,
                        InvoiceUploaded TEXT,
                        TaxToBeReturned REAL,
                        PaidFrom TEXT,
                        RefundTo TEXT,
                        StatusRefund TEXT,
                        Notes TEXT,
                        Picture BLOB,
                        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID))''')

    # Create printer inventory
    cursor.execute('''CREATE TABLE IF NOT EXISTS printers (
                        PrinterID INTEGER PRIMARY KEY,
                        OCnumber INTEGER,
                        SupplierID INTEGER,
                        PrinterName TEXT,
                        Power REAL,
                        PrintSizeX REAL,
                        PrintSizeY REAL,
                        PrintSizeZ REAL,
                        NozzleSizeOn REAL,
                        Status TEXT,
                        Condition TEXT, 
                        TotalHours INTEGER,
                        TotalHoursAfterLastMaintenance INTEGER,
                        DateLastMaintenance TEXT,
                        Notes TEXT,
                        Picture BLOB,
                        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID))''')
    
    # Create filament inventory
    cursor.execute('''CREATE TABLE IF NOT EXISTS filaments (
                        FilamentID INTEGER PRIMARY KEY,
                        OCnumber INTEGER,
                        SupplierID INTEGER,
                        FilamentName TEXT,
                        Material TEXT,
                        Color TEXT,
                        QuantityOrder INTEGER,
                        QuantityInStock INTEGER,
                        GramsPerRoll REAL,
                        PricePerGram REAL,
                        NozzleTemperature INTEGER,
                        BedTemperature INTEGER,
                        Properties TEXT,
                        Notes TEXT,
                        Picture BLOB,
                        FOREIGN KEY (SupplierID) REFERENCES suppliers (SupplierID))''')
    
    # Create Orders table
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        OrderID INTEGER PRIMARY KEY,
                        CustomerID INTEGER,
                        Services TEXT,
                        Description TEXT,
                        DateOrdered TEXT,
                        DateRequired TEXT,
                        Stage TEXT,
                        Status TEXT,
                        InvoiceNumber TEXT,
                        Responsible TEXT,
                        LastUpdated TEXT,
                        NumberParts REAL,
                        Progress TEXT,
                        PrinterIDs TEXT,
                        FilamentIDs TEXT,
                        PrintWeight REAL,
                        PrintTime REAL,
                        DesignTime REAL,
                        LabourTime REAL,
                        ShippingType TEXT,
                        ShippingQuantity REAL,
                        ExtraServices TEXT,
                        ExtraServicesCost REAL,
                        PriceExclBTW REAL,
                        Notes TEXT,
                        FOREIGN KEY (CustomerID) REFERENCES customers (CustomerID))''') # add pictures to folder automatically

    # Create part 
    cursor.execute('''CREATE TABLE IF NOT EXISTS orderparts (
                        PartID INTEGER PRIMARY KEY,
                        OrderID INTEGER,
                        PartNr INTEGER,
                        PartName TEXT,
                        Material TEXT,
                        Color TEXT,
                        QuantityOrdered INTEGER,
                        QuantityPrinted INTEGER,
                        PrintSettings TEXT,
                        FOREIGN KEY (OrderID) REFERENCES orders (OrderID))''') 
    
    # Create part and printer settings part
    cursor.execute('''CREATE TABLE IF NOT EXISTS printsettings (
                        PrintSettingID INTEGER PRIMARY KEY,
                        SettingName TEXT,
                        NozzleSize REAL,
                        Infill REAL,
                        LayerHeight REAL,
                        Speed REAL,
                        Support TEXT,
                        Brim TEXT,
                        Glue TEXT,
                        NozzleTemperature INTEGER,
                        BedTemperature INTEGER,
                        Notes TEXT)''')

    # Check if the table is empty
    cursor.execute("SELECT COUNT(*) FROM printsettings")
    row_count = cursor.fetchone()[0]
    
    # Insert default values if the table is empty
    if row_count == 0:
        default_values = [
            (1, "Default PLA", 0.4, 15.0, 0.2, 60.0, 'Yes', 'Yes', 'No', 215, 60, ""),
            (2, "Default ABS", 0.4, 15.0, 0.2, 60.0, 'Yes', 'Yes', 'Yes', 255, 100, ''),
            (3, "Default ASA", 0.4, 15.0, 0.2, 60.0, 'Yes', 'Yes', 'Yes', 260, 105, ''),
            (4, "Default PETG", 0.4, 15.0, 0.2, 60.0, 'Yes', 'Yes', 'Yes', 230, 85, ''),
            (5, "Default FLEXIBLE", 0.4, 15.0, 0.2, 60.0, 'Yes', 'Yes', 'Yes', 260, 85, '')]
    
        cursor.executemany('''INSERT INTO printsettings (PrintSettingID, SettingName, NozzleSize, Infill, LayerHeight, Speed, Support, Brim, 
                           Glue, NozzleTemperature, BedTemperature, Notes)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', default_values)
        print("Default print setting initialized.")


    
    conn.commit()
    conn.close()

