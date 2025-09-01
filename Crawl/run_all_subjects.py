#!/usr/bin/env python3
import subprocess
import sys
import argparse

# 重新分配到8个组，每组约15-16个文件 (受SLURM QOS限制，最多8个并发任务)

# 第1组 (1-16)
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
    "urls_subject/其他社科/其他社科_3.csv"
]

# 第2组 (17-32)
group2 = [
    "urls_subject/创业与创新/创业与创新_urls.csv",
    "urls_subject/化学/化学_urls.csv",
    "urls_subject/化工/化工_urls.csv",
    "urls_subject/医学/医学_1.csv",
    "urls_subject/医学/医学_2.csv",
    "urls_subject/医学/医学_3.csv",
    "urls_subject/医学/医学_4.csv",
    "urls_subject/医学/医学_5.csv",
    "urls_subject/历史/历史_1.csv",
    "urls_subject/历史/历史_2.csv",
    "urls_subject/历史/历史_3.csv",
    "urls_subject/哲学/哲学_urls.csv",
    "urls_subject/商业分析/商业分析_urls.csv",
    "urls_subject/国际关系/国际关系_1.csv",
    "urls_subject/国际关系/国际关系_2.csv",
    "urls_subject/国际关系/国际关系_3.csv"
]

# 第3组 (33-48)
group3 = [
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
    "urls_subject/市场营销/市场营销_1.csv",
    "urls_subject/市场营销/市场营销_2.csv",
    "urls_subject/建筑/建筑_1.csv"
]

# 第4组 (49-64)
group4 = [
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
    "urls_subject/数据科学/数据科学_2.csv"
]

# 第5组 (65-80)
group5 = [
    "urls_subject/数据科学/数据科学_3.csv",
    "urls_subject/文化/文化_1.csv",
    "urls_subject/文化/文化_2.csv",
    "urls_subject/文化/文化_3.csv",
    "urls_subject/新媒体/新媒体_urls.csv",
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
    "urls_subject/海洋技术/海洋技术_urls.csv"
]

# 第6组 (81-96)
group6 = [
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
    "urls_subject/电气电子/电气电子_1.csv",
    "urls_subject/电气电子/电气电子_2.csv",
    "urls_subject/电气电子/电气电子_3.csv",
    "urls_subject/社会学与社工/社会学与社工_1.csv",
    "urls_subject/社会学与社工/社会学与社工_2.csv"
]

# 第7组 (97-112)
group7 = [
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
    "urls_subject/计算机/计算机_2.csv"
]

# 第8组 (113-126)
group8 = [
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

def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='运行指定组的爬虫')
    parser.add_argument('group', type=int, choices=[1, 2, 3, 4, 5, 6, 7, 8], 
                       help='选择要运行的组号 (1-8)')
    
    args = parser.parse_args()
    
    # 根据参数选择对应的组
    groups = {
        1: group1,
        2: group2,
        3: group3,
        4: group4,
        5: group5,
        6: group6,
        7: group7,
        8: group8
    }
    
    selected_group = groups[args.group]
    
    print(f"开始爬取第{args.group}组，共 {len(selected_group)} 个CSV文件")
    
    # 统计变量
    total_projects = len(selected_group)
    scrapy_success = 0
    advanced_first_success = 0
    advanced_second_success = 0
    total_failures = 0
    
    for i, csv_file in enumerate(selected_group, 1):
        print(f"\n[{i}/{len(selected_group)}] 爬取: {csv_file}")
        
        # 提取科目名称
        subject_name = csv_file.split('/')[-2] if '/' in csv_file else csv_file.split('_')[0]
        
        try:
            # 第一阶段：常规Scrapy爬取
            subprocess.run([sys.executable, "run_crawler.py", csv_file], check=True)
            print(f"✓ Scrapy爬取完成")
            scrapy_success += 1
            
            # 第二阶段：高级爬虫双重尝试机制
            max_advanced_attempts = 2
            advanced_success = False
            
            for attempt in range(1, max_advanced_attempts + 1):
                print(f"开始高级爬虫重试 (第{attempt}/{max_advanced_attempts}次): {subject_name}")
                
                try:
                    result = subprocess.run([sys.executable, "advanced_scraper/main.py", subject_name], 
                                          check=True, capture_output=True, text=True)
                    print(f"✓ 高级爬虫第{attempt}次尝试成功")
                    advanced_success = True
                    # 统计成功次数
                    if attempt == 1:
                        advanced_first_success += 1
                    else:
                        advanced_second_success += 1
                    break
                    
                except subprocess.CalledProcessError as e:
                    print(f"⚠ 高级爬虫第{attempt}次尝试失败 (返回码: {e.returncode})")
                    
                    if attempt < max_advanced_attempts:
                        print(f"准备进行第{attempt + 1}次尝试...")
                        # 在重试间添加短暂延迟，避免过于频繁的请求
                        import time
                        time.sleep(10)  # 等待10秒再进行第二次尝试
                    else:
                        print(f"✗ 高级爬虫在{max_advanced_attempts}次尝试后仍然失败")
                        # 不中断整个流程，继续处理下一个CSV文件
                        advanced_success = False
            
            if advanced_success:
                print(f"✅ 高级爬虫最终成功: {subject_name}")
            else:
                print(f"❌ 高级爬虫最终失败: {subject_name} (将继续处理下一个项目)")
                total_failures += 1
            
        except subprocess.CalledProcessError as e:
            print(f"✗ 失败: {e}")
            break
        except KeyboardInterrupt:
            print("\n用户中断")
            break
    
    # 打印详细统计报告
    print(f"\n{'='*60}")
    print(f"🏁 第{args.group}组爬取完成统计报告")
    print(f"{'='*60}")
    print(f"📊 总体统计:")
    print(f"   总学科数: {total_projects}")
    print(f"   Scrapy成功: {scrapy_success}/{total_projects} ({scrapy_success/total_projects*100:.1f}%)")
    
    total_advanced_success = advanced_first_success + advanced_second_success
    print(f"\n🚀 高级爬虫统计:")
    print(f"   第1次成功: {advanced_first_success}")
    print(f"   第2次成功: {advanced_second_success}")
    print(f"   高级爬虫总成功: {total_advanced_success}/{total_projects} ({total_advanced_success/total_projects*100:.1f}%)")
    print(f"   最终失败: {total_failures}")
    
    # 双重尝试效果分析
    if advanced_second_success > 0:
        improvement = advanced_second_success / (total_advanced_success) * 100 if total_advanced_success > 0 else 0
        print(f"\n📈 双重尝试效果:")
        print(f"   第2次尝试贡献: {advanced_second_success} 个成功项目")
        print(f"   成功率提升: {improvement:.1f}% (通过第2次尝试获得)")
    
    final_success_rate = (scrapy_success + total_advanced_success - total_failures) / total_projects * 100
    print(f"\n🎯 最终综合成功率: {final_success_rate:.1f}%")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()