Step 1: Clean the table; deal with deadline and multiple terms; remove duplicate Chinese columns.
    Input: raw data: Data/美研-数据科学 - Sheet1 (1).csv
    Output: cleaned data: Data/美研-数据科学 - Sheet1 (1)_cleaned.csv
    Method: Data/task_program_data_clean.md
    Code: Data/scripts/clean_program_data.py
    Run: python Data/scripts/clean_program_data.py (Adjust path if needed)


Step 2: Translate the cleaned data to English and format the data if needed (like fee, deadline, etc)
    Input: cleaned data: Data/美研-数据科学 - Sheet1 (1)_cleaned.csv
    Output: translated data: Data/美研-数据科学 - Sheet1 (1)_translated.csv, Data/美研-数据科学 - Sheet1 (1)_cleaned_translated.cache.json (for debug)
    Method: Data/task_program_data_translate.md
    Code: Data/scripts/translate_program_data.py
    Run: python Data/scripts/translate_program_data.py (Adjust path if needed)


Step 3: Form related data like universities, cities, states, countries, majors, etc.
    Input: cleaned data: Data/美研-数据科学 - Sheet1 (1)_cleaned.csv
    Output: Data/import_cities.csv, Data/import_universities.csv, Data/import_country_regions.csv, Data/import_degrees.csv, Data/import_majors.csv, Data/import_state_provinces.csv, Data/import_tags.csv
    Method: Data/task_form_related_data.md
    Code: Data/scripts/complete_import_csvs.py, Data/scripts/generate_import_csvs.py
    Run: (order is important)
        1. python Data/scripts/generate_import_csvs.py (Adjust path if needed)
        2. python Data/scripts/complete_import_csvs.py (Adjust path if needed)
    
Step 4: import all data to database
    Input: Data/import_cities.csv, Data/import_universities.csv, Data/import_country_regions.csv, Data/import_degrees.csv, Data/import_majors.csv, Data/import_state_provinces.csv, Data/import_tags.csv, Data/美研-数据科学 - Sheet1 (1)_cleaned_translated.csv
    Output: database's corresponding tables are updated
    Method: Data/task_import_data.md
    Code: gradpilot-backend/script/import_from_csvs.ts,gradpilot-backend/script/import_programs.ts
    Run: (order is important)
        1. cd gradpilot-backend & pnpm exec tsx script/import_from_csvs.ts
        2. cd gradpilot-backend & pnpm exec tsx script/import_programs.ts
    Problem:
        判断一个program是否exist需要加入term的区别。
        


    

