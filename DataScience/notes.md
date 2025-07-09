1. excel先生成所属院系（英文）和链接，从而提高后续prompt回答正确率


不准确（瞎猜）、中等准确（有时出现假阳性或假阴性）、非常准确（几乎总是正确）

Data Science

- 申请费减免：使用gemini 2.5 flash，结合谷歌搜索返回结果，分类为applicable/not applicable/not mentioned，生成3次，只要有一次出现了applicable即记为可减免。分类为中等正确。但由于大部分学校都提供有条件的fee waiver，目前的分类结果也确实是大部分为applicable（325/350），因此正确率中等影响不大。

- 同申互斥：使用gemini 2.5 pro。谷歌搜索（program frequently asked question）+ 项目url。正确率仅为中等。api的web search仅仅返回一个snippet，而非整个html，因此对于同申互斥这种比较难以直接搜索的问题（prompt中要求搜索frequently asked questions），其准确率并不高。无论是gemini pro还是flash

- 推荐信：使用gemini 2.5 flash，结合谷歌搜索返回结果。推荐信数量的返回准确性较高，几乎总是正确

- ETS code: 使用gemini 2.5 flash，结合谷歌搜索返回结果  。ETS code的返回准确性较高，几乎总是正确

- 网申地址：非常不准确；一部分原因是在申请季还没开启时，部分学校的网申地址是关闭的；考虑手动添加

- 项目标签： 非常准确；通过项目网站直接总结即可

- 学费： 不准确。使用gemini 2.5 pro也时常出现3个不同的数字；建议不要该字段

- 雅思送分：不需要该字段；学生可以直接在雅思送分界面查看可送的学校，不接受电子版的院系需要额外邮寄，也通过雅思官网

- 职业项目：是否为professional program；根据官网来总结是否，非常准

- Capstone或Thesis：非常准确；并且可以给出其他毕业要求（如有）

- 面试：非常准确；需手动确认no explicit demand是否为真

- STEM-OPT：不准确。官网时长不会列出是否为STEM-OPT，即使该项目几乎肯定是STEM。建议不添加该字段

- 更多项目信息：非常准确。对官网文本的总结
