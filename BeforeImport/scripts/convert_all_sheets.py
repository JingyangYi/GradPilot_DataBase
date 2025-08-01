#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os

def convert_all_sheets_to_csv(excel_file_path):
    """
    Convert all sheets in Excel file to separate CSV files with proper Chinese character encoding
    
    Args:
        excel_file_path (str): Path to the Excel file
    """
    try:
        # Read the Excel file
        print(f"Reading Excel file: {excel_file_path}")
        
        # Get all sheets
        xl_file = pd.ExcelFile(excel_file_path)
        print(f"Found {len(xl_file.sheet_names)} sheet(s): {xl_file.sheet_names}")
        
        base_name = os.path.splitext(excel_file_path)[0]
        output_files = []
        
        # Convert each sheet
        for sheet_name in xl_file.sheet_names:
            print(f"\n--- Processing sheet: {sheet_name} ---")
            
            # Read the sheet
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            
            print(f"DataFrame shape: {df.shape}")
            print("Column names:")
            for i, col in enumerate(df.columns):
                print(f"  {i+1}. {col}")
            
            print(f"First few rows:")
            print(df.head())
            
            # Create output filename
            csv_file_path = f"{base_name}_{sheet_name}.csv"
            
            # Save to CSV with UTF-8 encoding to preserve Chinese characters
            print(f"\nSaving to CSV: {csv_file_path}")
            df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
            
            print(f"Successfully saved sheet '{sheet_name}' to {csv_file_path}")
            output_files.append(csv_file_path)
        
        print(f"\n✅ All sheets converted successfully!")
        for file in output_files:
            print(f"📁 Output file: {file}")
        
        return output_files
        
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return None

if __name__ == "__main__":
    # Set the file path
    excel_file = "Data/02 24-25美研数据科学与应用数据科学专业查校表.xlsx"
    
    # Check if the Excel file exists
    if not os.path.exists(excel_file):
        print(f"Error: Excel file not found: {excel_file}")
        sys.exit(1)
    
    # Convert all sheets
    result = convert_all_sheets_to_csv(excel_file)
    
    if not result:
        print(f"\n❌ Conversion failed!")
        sys.exit(1) 