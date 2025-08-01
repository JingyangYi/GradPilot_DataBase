工作流程：

0. (首先确认原始xlsx表格是否有多个sheet，一次处理一个sheet)在小库留学原始数据xlsx表上添加字段：

CS rankings	项目代号	网申地址	申请费减免	托福送分ETS code	雅思送分Account Name	面试	同申互斥	STEM-OPT	Capstone或Thesis	学费	项目标签	更多申请信息	更多项目信息	CV	SOP	Writing Sample	推荐信	职业项目	专业类别	课程网址	所属院系（英文）	所属院系网址

然后将原始xlsx另存为csv格式（会损失部分超链接），保存在ProgramDB/Major下
1. field_raw.ipynb 生成所有字段对应的csv
2. **首先**生成 所属院系（英文）	所属院系网址；为之后的字段AI检索提供更多有价值信息
3. 生成 所属院系（英文）	所属院系网址 后，打开ProgramDB/Major/Math/fields_records/所属院系（英文）/所属院系英文_处理结果.csv。将这两个字段的值复制到ProgramDB/Major下csv上的所属院系右边2个列。（注意删除原有最后的两个列，否则会出现重复）
4. field_raw.ipynb 再次生成所有字段对应的csv，此时将有所属院系的英文供搜索
5. 使用对应的 .ipynb去填充相应字段
6. 在项目标签中，注意要新增中英文版本。有一个tags.json记录了所有的中英文互译，对于一个新的专业方向，需要先用llm生成新的中英互译方向