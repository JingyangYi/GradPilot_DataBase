#!/usr/bin/env python3
import subprocess
import sys

# 第1组 (1-23)
group1 = [
    "urls_subject/交通运输/交通运输_urls.csv",
    "urls_subject/人力资源管理/人力资源管理_urls.csv",
    "urls_subject/会计/会计_urls.csv",
    "urls_subject/体育/体育_urls.csv",
    "urls_subject/供应链管理/供应链管理_urls.csv",
    "urls_subject/信息系统/信息系统_urls.csv",
    "urls_subject/公共卫生/公共卫生_1.csv",
    "urls_subject/公共卫生/公共卫生_2.csv",
    "urls_subject/公共政策与事务/公共政策与事务_1.csv",
    "urls_subject/公共政策与事务/公共政策与事务_2.csv",
    "urls_subject/公共政策与事务/公共政策与事务_3.csv",
    "urls_subject/其他商科/其他商科_urls.csv",
    "urls_subject/其他工科/其他工科_urls.csv",
    "urls_subject/其他社科/其他社科_1.csv",
    "urls_subject/其他社科/其他社科_2.csv",
    "urls_subject/其他社科/其他社科_3.csv",
    "urls_subject/创业与创新/创业与创新_urls.csv",
    "urls_subject/化学/化学_urls.csv",
    "urls_subject/化工/化工_urls.csv",
    "urls_subject/医学/医学_1.csv",
    "urls_subject/医学/医学_2.csv",
    "urls_subject/医学/医学_3.csv",
    "urls_subject/医学/医学_4.csv"
]

# 第2组 (24-46)
group2 = [
    "urls_subject/医学/医学_5.csv",
    "urls_subject/历史/历史_1.csv",
    "urls_subject/历史/历史_2.csv",
    "urls_subject/历史/历史_3.csv",
    "urls_subject/哲学/哲学_urls.csv",
    "urls_subject/商业分析/商业分析_urls.csv",
    "urls_subject/国际关系/国际关系_1.csv",
    "urls_subject/国际关系/国际关系_2.csv",
    "urls_subject/国际关系/国际关系_3.csv",
    "urls_subject/国际关系/国际关系_4.csv",
    "urls_subject/土木工程/土木工程_1.csv",
    "urls_subject/土木工程/土木工程_2.csv",
    "urls_subject/地球科学/地球科学_1.csv",
    "urls_subject/地球科学/地球科学_2.csv",
    "urls_subject/媒介与社会/媒介与社会_urls.csv",
    "urls_subject/媒体与传播/媒体与传播_urls.csv",
    "urls_subject/媒体产业/媒体产业_urls.csv",
    "urls_subject/工业工程/工业工程_urls.csv",
    "urls_subject/工商管理/工商管理_1.csv",
    "urls_subject/工商管理/工商管理_2.csv",
    "urls_subject/工程管理/工程管理_1.csv",
    "urls_subject/工程管理/工程管理_2.csv",
    "urls_subject/市场营销/市场营销_1.csv"
]

# 第3组 (47-69)
group3 = [
    "urls_subject/市场营销/市场营销_2.csv",
    "urls_subject/建筑/建筑_1.csv",
    "urls_subject/建筑/建筑_2.csv",
    "urls_subject/建筑/建筑_3.csv",
    "urls_subject/影视/影视_urls.csv",
    "urls_subject/心理学/心理学_1.csv",
    "urls_subject/心理学/心理学_2.csv",
    "urls_subject/心理学/心理学_3.csv",
    "urls_subject/房地产/房地产_urls.csv",
    "urls_subject/教育/教育_1.csv",
    "urls_subject/教育/教育_2.csv",
    "urls_subject/教育/教育_3.csv",
    "urls_subject/教育/教育_4.csv",
    "urls_subject/数学/数学_1.csv",
    "urls_subject/数学/数学_2.csv",
    "urls_subject/数学/数学_3.csv",
    "urls_subject/数据科学/数据科学_1.csv",
    "urls_subject/数据科学/数据科学_2.csv",
    "urls_subject/数据科学/数据科学_3.csv",
    "urls_subject/文化/文化_1.csv",
    "urls_subject/文化/文化_2.csv",
    "urls_subject/文化/文化_3.csv",
    "urls_subject/新媒体/新媒体_urls.csv"
]

# 第4组 (70-92)
group4 = [
    "urls_subject/新闻/新闻_urls.csv",
    "urls_subject/旅游酒店管理/旅游酒店管理_urls.csv",
    "urls_subject/机械工程/机械工程_1.csv",
    "urls_subject/机械工程/机械工程_2.csv",
    "urls_subject/材料/材料_urls.csv",
    "urls_subject/法律/法律_1.csv",
    "urls_subject/法律/法律_2.csv",
    "urls_subject/法律/法律_3.csv",
    "urls_subject/法律/法律_4.csv",
    "urls_subject/法律/法律_5.csv",
    "urls_subject/海洋技术/海洋技术_urls.csv",
    "urls_subject/物理/物理_1.csv",
    "urls_subject/物理/物理_2.csv",
    "urls_subject/环境工程/环境工程_1.csv",
    "urls_subject/环境工程/环境工程_2.csv",
    "urls_subject/环境工程/环境工程_3.csv",
    "urls_subject/生物/生物_1.csv",
    "urls_subject/生物/生物_2.csv",
    "urls_subject/生物/生物_3.csv",
    "urls_subject/生物/生物_4.csv",
    "urls_subject/生物工程/生物工程_1.csv",
    "urls_subject/生物工程/生物工程_2.csv",
    "urls_subject/电气电子/电气电子_1.csv"
]

# 第5组 (93-115)
group5 = [
    "urls_subject/电气电子/电气电子_2.csv",
    "urls_subject/电气电子/电气电子_3.csv",
    "urls_subject/社会学与社工/社会学与社工_1.csv",
    "urls_subject/社会学与社工/社会学与社工_2.csv",
    "urls_subject/社会学与社工/社会学与社工_3.csv",
    "urls_subject/科学传播/科学传播_urls.csv",
    "urls_subject/策略传播/策略传播_urls.csv",
    "urls_subject/管理/管理_1.csv",
    "urls_subject/管理/管理_2.csv",
    "urls_subject/管理/管理_3.csv",
    "urls_subject/经济/经济_1.csv",
    "urls_subject/经济/经济_2.csv",
    "urls_subject/经济/经济_3.csv",
    "urls_subject/能源/能源_urls.csv",
    "urls_subject/航空工程/航空工程_urls.csv",
    "urls_subject/艺术/艺术_1.csv",
    "urls_subject/艺术/艺术_2.csv",
    "urls_subject/药学/药学_urls.csv",
    "urls_subject/计算机/计算机_1.csv",
    "urls_subject/计算机/计算机_2.csv",
    "urls_subject/计算机/计算机_3.csv",
    "urls_subject/计算机/计算机_4.csv",
    "urls_subject/计算机/计算机_5.csv",
    "urls_subject/语言/语言_1.csv",
    "urls_subject/语言/语言_2.csv",
    "urls_subject/语言/语言_3.csv",
    "urls_subject/金工金数/金工金数_1.csv",
    "urls_subject/金工金数/金工金数_2.csv",
    "urls_subject/金融/金融_1.csv",
    "urls_subject/金融/金融_2.csv",
    "urls_subject/金融/金融_3.csv",
    "urls_subject/食品科学/食品科学_urls.csv"
]

# 选择要运行的组 (修改这里选择组号)
selected_group = group5  # 改为 group1, group2, group3, group4, group5

print(f"开始爬取选定组，共 {len(selected_group)} 个CSV文件")

for i, csv_file in enumerate(selected_group, 1):
    print(f"\n[{i}/{len(selected_group)}] 爬取: {csv_file}")
    try:
        subprocess.run([sys.executable, "run_crawler.py", csv_file], check=True)
        print(f"✓ 完成")
    except subprocess.CalledProcessError:
        print(f"✗ 失败")
        break
    except KeyboardInterrupt:
        print("\n用户中断")
        break

print("\n该组爬取结束")