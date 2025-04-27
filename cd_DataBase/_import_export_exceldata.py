# -*- coding: utf-8 -*-
"""
Import Export database functions

@author: feder
"""

import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (QFileDialog, QMessageBox)
import warnings


def fun_import_database(self):
    # Open file dialog
    file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
    if not file_path:
        return  # User cancelled

    try:
        # Define table names and their specific ID columns
        table_id_columns = {
            "employees": "EmployeeID",
            "customers": "CustomerID",
            "suppliers": "SupplierID",
            "expenses": "OCnumber",
            "printers": "PrinterID",
            "filaments": "FilamentID",
            "orders": "OrderID",
            "orderparts": "PartID",
            "printsettings": "PrintSettingID"  }
        
        cursor = self.connection.cursor()
        
        for table_name, id_column in table_id_columns.items():
            print(f"Trying to import into {table_name}")
            try:
                # === Read Excel sheets into DataFrames ===
                df_import = pd.read_excel(file_path, sheet_name=table_name)
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                print(f"DataFrame columns: {df_import.columns.tolist()}")
                print(f"Checking conflicts in {table_name} on {id_column}...")
                print(df_import)
            except ValueError:
                continue  # Sheet doesn't exist, skip
            if df_import.empty:
                continue  # Skip empty sheets
            
            # === Check if IDs were imported. ===
            if id_column not in df_import.columns:
                continue  # No ID column, skip conflict checking
            imported_ids = df_import[id_column].dropna().tolist()

            if not imported_ids:
                continue
            
            placeholders = ",".join(["?"] * len(imported_ids))
            query = f"SELECT {id_column} FROM {table_name} WHERE {id_column} IN ({placeholders})"
            cursor.execute(query, imported_ids)
            existing_ids = [row[0] for row in cursor.fetchall()]

            if existing_ids:
                # === Ask user what to do ===
                reply = QMessageBox.question(
                    self,
                    "ID Conflict Detected",
                    f"Some {id_column}s already exist in the '{table_name}' table.\n\nExisting IDs: {existing_ids}\n\nDo you want to overwrite them?",
                    QMessageBox.Yes | QMessageBox.No )

                if reply == QMessageBox.Yes:
                    print(f"Deleting existing IDs: {existing_ids}")
                    # Delete the conflicting rows
                    placeholder_new = ",".join(["?"] * len(existing_ids))
                    del_query = f"DELETE FROM {table_name} WHERE {id_column} IN ({placeholder_new})"
                    cursor.execute(del_query, existing_ids)
                    print(f"Running delete query: {del_query}")
                    self.connection.commit()
                    if table_name == 'orders':
                        try: # Remove from parts table, if any
                            self.cursor.execute(f"DELETE FROM orderparts WHERE OrderID = ? IN ({placeholder_new}")
                            print(f"Running delete order parts query: {del_query}")
                            self.connection.commit()
                        except:
                            pass
                    # Insert all imported rows
                    df_import.to_sql(table_name, self.connection, if_exists="append", index=False)
                else:
                    # Insert only non-conflicting rows
                    df_import = df_import[~df_import[id_column].isin(existing_ids)]
                    if not df_import.empty:
                        df_import.to_sql(table_name, self.connection, if_exists="append", index=False)
            else:
                # If no conflicts, insert all rows
                df_import.to_sql(table_name, self.connection, if_exists="append", index=False)

        QMessageBox.information(self, "Success", "Data imported successfully!")

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to import data:\n{str(e)}")
    
    
def fun_export_database(self):
    # === Step 1: Timestamp ===
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    excel_file = f"3BP_database_{timestamp}.xlsx"
    
    try:
        all_table_names = ["employees", "customers", "suppliers", "expenses", "printers", "filaments",
                       "orders", "orderparts", "printsettings"]
        # === Open Excel writer ONCE ===
        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            for table_name in all_table_names:
                # === Read each table into a DataFrame ===
                df_export = pd.read_sql_query(f"SELECT * FROM {table_name}", self.connection)
                
                # === Write to a sheet ===
                df_export.to_excel(writer, sheet_name=table_name[:31], index=False)
                # Note: Excel sheet names must be <= 31 characters
        QMessageBox.information(self, "Success", f"Data exported successfully as {excel_file}!")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to export data:\n{str(e)}")
        
        
# Simplified version of import
# def fun_import_database(self):
#     # Open file dialog
#     file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
#     if not file_path:
#         return  # User cancelled

#     try:
#         all_table_names = ["employees", "customers", "suppliers", "expenses", "printers", "filaments",
#                        "orders", "orderparts", "printsettings"]
#         for table_name in all_table_names:
#             # === Read Excel sheets into DataFrames ===
#             df_import = pd.read_excel(file_path, sheet_name=table_name)
#             if df_import.empty:
#                 continue  # Skip empty sheet
            
#             # === Insert data into SQLite tables ===
#             df_import.to_sql(table_name, self.connection, if_exists="append", index=False)

#         QMessageBox.information(self, "Success", "Data imported successfully!")

#     except Exception as e:
#         QMessageBox.critical(self, "Error", f"Failed to import data:\n{str(e)}")
    