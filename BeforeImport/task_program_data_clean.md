now I have raw data about grad programs (Data/美研-应用数据科学 - Sheet1.csv, Data/美研-数据科学 - Sheet1 (1).csv). I need to do some cleaning.

1. only retain English Info. Columns of Chinese should either be translated to English (via standard translate API's) or discard (if English counterpart is already there). I'd like to use Microsoft Translator Text API and Deepseek API.


2. for 开学期, if multiple terms, it should be split as separate records

3. if multiple 截止日期 are there, only retain the first one; add others to the Column name "更多项目信息" (append these info as a new linew)

4. for 托福送分ETS code， if it is not a code, clear the entry (user need to search by themselves)




after you clean the data like this, we're ready to import the program data into the database. I need you to generate a csv for the program data after cleaning.