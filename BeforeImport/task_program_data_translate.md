now you need to use translate api ( for now deepseek) to translate each field in Data/美研-数据科学 - Sheet1 (1)_cleaned.csv to **English (from Chinese)**. 
You need to provide a little context to the api. Meanwhile, the api need to do some data cleaning.

univ_rank,univ_name,city,degree_detail,program_name,program_detail,program_length,application_fee_usd,terms_start,deadline,gpa_req,toefl_req,ielts_req,gre_req,gmat_req,academic_background,material_requirements,admission_url,program_url,more_info,course_url,interview,application_fee_waiver,department,department_url,recommendation_letters,ets_code,tags,professional_program,grad_requirement

Here're some instructions for each column.

1. univ_rank no need
2. univ_name  no need
3. city no need
4. degree_detail no need
5. program_name no need
6. program_detail: need. it is describe details about the graduate program.
7. program_length: need. it is how long the program is.
8. application_fee_usd: no need. but make sure each field is a number. alert for wrong format.
9. terms_start: need. it is when the program starts. should be either Fall, Spring, Summer, or Winter.
10. deadline: need. it is when the application deadline is. **should be only a date or "rolling"** if the raw data is not, attach the translation version of it to more_info, set empty for deadline field.
11. gpa_req: need. it is the gpa requirement. should be a number showing the minimum requirement (not average). if it is not, set it to empty. if it says average gpa, add this info to more_info. 
12. toefl_req: need. it is the toefl requirement. just translate
13. ielts_req: need. it is the ielts requirement. just translate
14. gre_req: need. it is the gre requirement. just translate
15. gmat_req: need. it is the gmat requirement. just translate
16. academic_background: need. it is the academic background. just translate
17. material_requirements: no need.
18. admission_url: no need.
19. program_url: no need.
20. more_info: no need.
21. course_url: no need.
22. interview: translate to one of the three options: "Required", "Optional", "Not needed". for Phd programs, (look at degree_detail to determine), it is "Optional".
23. application_fee_waiver: translate to one of the three options: "Applicable", "Not Applicable", "Unknown". 
24. department: no need.
25. department_url: no need.
26. recommendation_letters: should be a number or "no explicit demand"
27. ets_code: no need.
28. tags: no need. clean the "需要额外确认" to empty
29. professional_program: translate to one of the three options: "Professional", "Non-Professional", "Unknown".
30. grad_requirement: no need.


I encourage you to write a function for each column for this step. and please test 20 first row first.