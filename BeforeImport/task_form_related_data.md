we just completed translation of program data, now we need to get other related date ready for importing it to the database. Data/美研-数据科学 - Sheet1 (1)_cleaned_translated.csv

Here're are the task

5. extract all the tags separated by comma, they need to be inserted in table tag

6. for all universities mentioned in the table, extra their name first, then fill the university table. Create a csv for universities, you can get city and ranking from the program csv, and you need university website by deepseek api, ignore cs_ranking for now.

7. also form a csv table for all the cities encountered. be ready to insert those data to table city, state_province, country_region

8. for the major's it should be the name suffix of the csv, like 应用数据科学 and 数据科学, insert them into the major table (both English and Chinese)

I need you to form a csv for each the data first, and you need to insert them into the database.

please read the schema gradpilot-backend/prisma/schema.prisma:
table program
table university
table city
table state_province
table country_region
table tag
table major
table degree

and their translations
