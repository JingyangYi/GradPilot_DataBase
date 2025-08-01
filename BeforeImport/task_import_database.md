now we have the data.

2. university data: Data/import_universities.csv; it should be import to university table and university_translation table with Language_code = En.

3. city data: Data/import_cities.csv; it should be import to city table and city_translation table with Language_code = En. Note that additional field like region_code and zip_code, city type and is capital should be added by llm's search api. You should complete the data in csv first.

4. state_province data: Data/import_state_provinces.csv; it should be import to state_province table and state_province_translation table with Language_code = En. Note that additional field like region_code and abbreviation should be added by llm's search api. You should complete the data in csv first.

5. country_region data: Data/import_country_regions.csv; it should be import to country_region table and country_region_translation table with Language_code = En. Note that additional field like region_code and telephone_code and iso2 should be added by llm's search api. You should complete the data in csv first.

6. major data: Data/import_majors.csv; it should be import to major table and major_translation table with Language_code = En.

7. degree data: form degree data consisting Bachelor, Master, Doctoral in Data/import_degrees.csv first; it should be import to degree table and degree_translation table with Language_code = En.

8. tag data:  Data/import_tags.csv; it should be import to tag table and tag_translation table with Language_code = En.

note there're orders of imporint the data. start from leave tables.
1. import country_region -> state_province-> city
2. import major, degree, tag
3. import university

always create the main table first, then create the translation table.

You should read the schema in gradpilot-backend/prisma/schema.prisma to understand the structure of the database and make sure you import the right data to right property.



//next step

1. program data: Data/美研-数据科学 - Sheet1 (1)_cleaned_translated.csv; it should be import to program table and program_translation table with Language_code = En.