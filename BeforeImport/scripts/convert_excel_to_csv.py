#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os

def convert_excel_to_csv(excel_file_path, csv_file_path=None):
    """
    Convert Excel file to CSV with proper Chinese character encoding
    
    Args:
        excel_file_path (str): Path to the Excel file
        csv_file_path (str): Path for the output CSV file (optional)
    """
    try:
        # Read the Excel file
        print(f"Reading Excel file: {excel_file_path}")
        
        # Try to read all sheets first to see the structure
        xl_file = pd.ExcelFile(excel_file_path)
        print(f"Found {len(xl_file.sheet_names)} sheet(s): {xl_file.sheet_names}")
        
        # If no output path specified, create one based on input file
        if csv_file_path is None:
            base_name = os.path.splitext(excel_file_path)[0]
            csv_file_path = f"{base_name}.csv"
        
        # Read the first sheet (or you can specify which sheet to read)
        df = pd.read_excel(excel_file_path, sheet_name=0)
        
        print(f"DataFrame shape: {df.shape}")
        print("Column names:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        print("\nFirst few rows:")
        print(df.head())
        
        # Save to CSV with UTF-8 encoding to preserve Chinese characters
        print(f"\nSaving to CSV: {csv_file_path}")
        df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        
        print(f"Successfully converted {excel_file_path} to {csv_file_path}")
        print(f"CSV file saved with UTF-8-BOM encoding to properly display Chinese characters")
        
        return csv_file_path
        
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return None

if __name__ == "__main__":
    # Set the file paths
    excel_file = "Data/02 24-25美研数据科学与应用数据科学专业查校表.xlsx"
    csv_file = "Data/02 24-25美研数据科学与应用数据科学专业查校表.csv"
    
    # Check if the Excel file exists
    if not os.path.exists(excel_file):
        print(f"Error: Excel file not found: {excel_file}")
        sys.exit(1)
    
    # Convert the file
    result = convert_excel_to_csv(excel_file, csv_file)
    
    if result:
        print(f"\n✅ Conversion completed successfully!")
        print(f"📁 Output file: {result}")
    else:
        print(f"\n❌ Conversion failed!")
        sys.exit(1) 