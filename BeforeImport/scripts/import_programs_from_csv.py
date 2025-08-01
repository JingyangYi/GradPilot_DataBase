#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os
import json
from datetime import datetime
import re

def clean_decimal_value(value):
    """Clean and convert string values to valid decimal format"""
    if pd.isna(value) or value == '' or value == 'N/A':
        return None
    
    # Convert to string and remove non-numeric characters except decimal point
    value_str = str(value).replace(',', '').replace('$', '').replace('美元', '').strip()
    
    # Extract numeric value using regex
    match = re.search(r'(\d+(?:\.\d+)?)', value_str)
    if match:
        return float(match.group(1))
    return None

def clean_date_value(value):
    """Clean and convert date values to ISO format"""
    if pd.isna(value) or value == '' or value == 'N/A':
        return None
    
    value_str = str(value).strip()
    
    # Handle various date formats
    try:
        # Try parsing common formats first
        if '/' in value_str:
            # MM/DD/YYYY or DD/MM/YYYY format
            parts = value_str.split('/')
            if len(parts) == 3:
                # Assume MM/DD/YYYY for US universities
                month, day, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        elif '-' in value_str and len(value_str) == 10:
            # Already in YYYY-MM-DD format
            return value_str
        elif len(value_str) == 8 and value_str.isdigit():
            # YYYYMMDD format
            return f"{value_str[:4]}-{value_str[4:6]}-{value_str[6:8]}"
        
        # Handle Chinese date formats
        import re
        
        # Extract all dates from complex strings (e.g., "秋季（11 月 1 日 – 12月 1 日）")
        # For now, we'll extract the first date found and assume it's the primary deadline
        chinese_date_pattern = r'(\d{1,2})\s*月\s*(\d{1,2})\s*日'
        matches = re.findall(chinese_date_pattern, value_str)
        
        if matches:
            # Use the first date found
            month, day = matches[0]
            # Assume current or next year - this might need refinement based on context
            year = "2025"  # Default year, could be made configurable
            return f"{year}-{int(month):02d}-{int(day):02d}"
            
        # Handle formats like "1月15日" or "12月1日"
        simple_chinese_pattern = r'^(\d{1,2})月(\d{1,2})日$'
        match = re.match(simple_chinese_pattern, value_str)
        if match:
            month, day = match.groups()
            year = "2025"  # Default year
            return f"{year}-{int(month):02d}-{int(day):02d}"
            
        # Handle English month formats like "January 15", "Dec 1", etc.
        english_date_pattern = r'(\w+)\s+(\d{1,2})'
        match = re.search(english_date_pattern, value_str)
        if match:
            month_name, day = match.groups()
            month_mapping = {
                'january': '01', 'jan': '01',
                'february': '02', 'feb': '02',
                'march': '03', 'mar': '03',
                'april': '04', 'apr': '04',
                'may': '05',
                'june': '06', 'jun': '06',
                'july': '07', 'jul': '07',
                'august': '08', 'aug': '08',
                'september': '09', 'sep': '09',
                'october': '10', 'oct': '10',
                'november': '11', 'nov': '11',
                'december': '12', 'dec': '12'
            }
            month_num = month_mapping.get(month_name.lower())
            if month_num:
                year = "2025"  # Default year
                return f"{year}-{month_num}-{int(day):02d}"
    
    except Exception as e:
        # If any error occurs during parsing, just return the original value as a string
        # This preserves the original deadline information even if we can't parse it
        return value_str
    
    # If no pattern matches, return the original string to preserve information
    return value_str

def process_csv_data(csv_file_path, output_file_path=None):
    """
    Process CSV data and convert it according to program table field mapping
    
    Args:
        csv_file_path (str): Path to the CSV file
        output_file_path (str): Path for the output JSON file (optional)
    """
    try:
        print(f"Processing CSV file: {csv_file_path}")
        
        # Read the CSV file
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        
        print(f"Loaded {len(df)} records")
        print("CSV columns:", list(df.columns))
        
        # Define the field mapping based on our analysis
        field_mapping = {
            '排名': 'university_ranking',  # US News university ranking
            '大学名称': 'university_name_zh',  # For lookup only
            '大学英文名称': 'university_name_en',  # For lookup only  
            '所在城市': 'university_city',  # University location city
            '专业中文名称': 'nameZh',
            '专业英文名称': 'nameEn',
            '所属院系': 'department',
            '学位': 'degree',
            '专业领域': 'programDetail',
            '课程长度': 'duration',
            '申请费（美元)': 'applicationFeeUsd',
            '开学期': 'intakeSeason',
            '截止日期': 'deadline',
            'GPA': 'gpaRequirement',
            '托福': 'toeflRequirement',
            '雅思': 'ieltsRequirement',
            'GRE': 'greRequirement',
            'GMAT': 'gmatRequirement',
            '学术背景': 'academicBackground',
            '材料要求': 'materialRequirements',
            '招生网址': 'admissionUrl',
            '专业网址': 'programUrl'
        }
        
        processed_data = []
        universities_needed = []
        
        # Extract the part after the last underscore of the file name (without extension)
        base_name = os.path.splitext(os.path.basename(csv_file_path))[0]
        major_category = base_name.split('_')[-1].strip()
        
        for index, row in df.iterrows():
            try:
                # Create a record for each program
                program_record = {
                    'source_row_index': index,
                    'majorCategory': major_category,
                }
                
                # Store university info for lookup
                university_info = {}
                
                # Map each CSV field to program table field
                for csv_field, db_field in field_mapping.items():
                    if csv_field not in df.columns:
                        print(f"Warning: CSV field '{csv_field}' not found in data")
                        continue
                        
                    value = row[csv_field]
                    
                    # Handle special cases for university-related fields
                    if db_field in ['university_name_zh', 'university_name_en', 'university_ranking', 'university_city']:
                        if db_field == 'university_ranking':
                            # Convert ranking to integer
                            try:
                                university_info[db_field] = int(value) if pd.notna(value) and str(value).isdigit() else None
                            except:
                                university_info[db_field] = None
                        else:
                            university_info[db_field] = value if pd.notna(value) else None
                        continue
                    elif db_field is None:
                        continue  # Skip unmapped fields
                    
                    # Process the value based on field type
                    if db_field == 'applicationFeeUsd':
                        program_record[db_field] = clean_decimal_value(value)
                    elif db_field == 'deadline':
                        program_record[db_field] = clean_date_value(value)
                    else:
                        # For string fields, convert NaN to None and clean whitespace
                        if pd.isna(value) or value == '':
                            program_record[db_field] = None
                        else:
                            program_record[db_field] = str(value).strip()
                
                # Add university lookup info
                program_record['university_lookup'] = university_info
                
                # Add university info to the list for processing
                if university_info:
                    university_key = (
                        university_info.get('university_name_zh'),
                        university_info.get('university_name_en'),
                        university_info.get('university_city'),
                        university_info.get('university_ranking')
                    )
                    if university_key not in [u['key'] for u in universities_needed]:
                        universities_needed.append({
                            'key': university_key,
                            'university_name_zh': university_info.get('university_name_zh'),
                            'university_name_en': university_info.get('university_name_en'),
                            'university_city': university_info.get('university_city'),
                            'university_ranking': university_info.get('university_ranking')
                        })
                
                processed_data.append(program_record)
                
            except Exception as e:
                print(f"Error processing row {index}: {str(e)}")
                continue
        
        # Create output summary
        result = {
            'source_file': csv_file_path,
            'processed_at': datetime.now().isoformat(),
            'total_records': len(processed_data),
            'major_category': major_category,
            'universities_needed': list(universities_needed),
            'field_mapping': field_mapping,
            'sample_record': processed_data[0] if processed_data else None,
            'records': processed_data
        }
        
        # Save to JSON file
        if output_file_path is None:
            base_name = os.path.splitext(csv_file_path)[0]
            output_file_path = f"{base_name}_processed.json"
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Processing completed successfully!")
        print(f"📁 Output file: {output_file_path}")
        print(f"📊 Total records processed: {len(processed_data)}")
        print(f"🏫 Unique universities found: {len(universities_needed)}")
        print(f"📚 Major category: {major_category}")
        
        # Show university info
        print(f"\nSample universities found:")
        for i, uni in enumerate(universities_needed[:3]):
            print(f"  {i+1}. {uni['university_name_zh']} ({uni['university_name_en']}) - {uni['university_city']} - Ranking: {uni['university_ranking']}")
        
        # Show some statistics
        print(f"\nField completion statistics:")
        for field in ['nameEn', 'degree', 'department', 'applicationFeeUsd', 'deadline']:
            non_null_count = sum(1 for record in processed_data if record.get(field) is not None)
            percentage = (non_null_count / len(processed_data)) * 100 if processed_data else 0
            print(f"  {field}: {non_null_count}/{len(processed_data)} ({percentage:.1f}%)")
        
        return output_file_path
        
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return None

if __name__ == "__main__":
    # Process both CSV files
    csv_files = [
        "Data/02 24-25美研数据科学与应用数据科学专业查校表_数据科学.csv",
        "Data/02 24-25美研数据科学与应用数据科学专业查校表_应用数据科学.csv"
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"\n{'='*60}")
            result = process_csv_data(csv_file)
            if not result:
                print(f"❌ Failed to process {csv_file}")
        else:
            print(f"❌ File not found: {csv_file}") 