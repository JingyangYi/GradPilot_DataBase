#!/usr/bin/env python3
"""
提取所有JSON文件中的program_name_en字段的脚本
用于后续的专业排名匹配分析
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import csv

def extract_program_names(raw_data_dir):
    """
    从raw_data目录下的所有JSON文件中提取program_name_en字段
    
    Args:
        raw_data_dir (str): raw_data目录路径
    
    Returns:
        dict: 包含提取结果的字典
    """
    results = {
        'program_names': [],  # 所有program_name_en的列表
        'unique_names': set(),  # 去重后的program_name_en
        'file_stats': {},  # 每个文件的统计信息
        'category_stats': defaultdict(list),  # 按类别分组的统计
        'extraction_errors': []  # 提取过程中的错误
    }
    
    raw_data_path = Path(raw_data_dir)
    
    if not raw_data_path.exists():
        raise FileNotFoundError(f"目录不存在: {raw_data_dir}")
    
    # 遍历所有JSON文件
    json_files = list(raw_data_path.glob("*.json"))
    print(f"找到 {len(json_files)} 个JSON文件")
    
    for json_file in json_files:
        file_name = json_file.stem
        print(f"处理文件: {file_name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 初始化文件统计
            file_stats = {
                'total_programs': 0,
                'programs_with_name_en': 0,
                'programs_without_name_en': 0,
                'empty_name_en': 0,
                'program_names': []
            }
            
            # 跳过第一个元素（通常是completion_rate）
            if isinstance(data, list) and len(data) > 0:
                programs = data[1:] if 'completion_rate' in str(data[0]) else data
            else:
                programs = data
            
            # 提取每个项目的program_name_en
            for program in programs:
                if isinstance(program, dict):
                    file_stats['total_programs'] += 1
                    
                    program_name_en = program.get('program_name_en', '')
                    
                    if program_name_en:
                        if program_name_en.strip():  # 非空字符串
                            file_stats['programs_with_name_en'] += 1
                            file_stats['program_names'].append(program_name_en.strip())
                            
                            # 添加到总结果中
                            results['program_names'].append({
                                'name': program_name_en.strip(),
                                'category': file_name,
                                'program_id': program.get('id', 'unknown'),
                                'university': program.get('university_name_en', program.get('university_name', 'unknown'))
                            })
                            results['unique_names'].add(program_name_en.strip())
                            results['category_stats'][file_name].append(program_name_en.strip())
                        else:
                            file_stats['empty_name_en'] += 1
                    else:
                        file_stats['programs_without_name_en'] += 1
            
            results['file_stats'][file_name] = file_stats
            
        except Exception as e:
            error_msg = f"处理文件 {file_name} 时出错: {str(e)}"
            print(f"错误: {error_msg}")
            results['extraction_errors'].append(error_msg)
    
    # 转换set为list便于序列化
    results['unique_names'] = sorted(list(results['unique_names']))
    
    return results

def save_results(results, output_dir):
    """
    保存提取结果到多个文件
    
    Args:
        results (dict): 提取结果
        output_dir (str): 输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 1. 保存完整结果为JSON
    with open(output_path / 'program_names_extraction_results.json', 'w', encoding='utf-8') as f:
        # 需要处理set类型
        json_results = results.copy()
        json_results['unique_names'] = sorted(list(results['unique_names']))
        json.dump(json_results, f, ensure_ascii=False, indent=2)
    
    # 2. 保存所有program_name_en列表为CSV
    with open(output_path / 'all_program_names.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['program_name_en', 'category', 'program_id', 'university'])
        for item in results['program_names']:
            writer.writerow([item['name'], item['category'], item['program_id'], item['university']])
    
    # 3. 保存去重后的program_name_en列表
    with open(output_path / 'unique_program_names.txt', 'w', encoding='utf-8') as f:
        for name in results['unique_names']:
            f.write(f"{name}\\n")
    
    # 4. 保存统计报告
    with open(output_path / 'extraction_statistics.md', 'w', encoding='utf-8') as f:
        f.write("# Program Name 提取统计报告\\n\\n")
        
        # 总体统计
        f.write("## 总体统计\\n")
        f.write(f"- 总文件数: {len(results['file_stats'])}\\n")
        f.write(f"- 总项目数: {sum(stats['total_programs'] for stats in results['file_stats'].values())}\\n")
        f.write(f"- 有program_name_en的项目数: {sum(stats['programs_with_name_en'] for stats in results['file_stats'].values())}\\n")
        f.write(f"- 无program_name_en的项目数: {sum(stats['programs_without_name_en'] for stats in results['file_stats'].values())}\\n")
        f.write(f"- program_name_en为空的项目数: {sum(stats['empty_name_en'] for stats in results['file_stats'].values())}\\n")
        f.write(f"- 去重后的program_name_en数量: {len(results['unique_names'])}\\n\\n")
        
        # 按文件统计
        f.write("## 按文件统计\\n")
        f.write("| 文件名 | 总项目数 | 有name_en | 无name_en | 空name_en |\\n")
        f.write("|--------|----------|-----------|-----------|-----------|\\n")
        for file_name, stats in results['file_stats'].items():
            f.write(f"| {file_name} | {stats['total_programs']} | {stats['programs_with_name_en']} | {stats['programs_without_name_en']} | {stats['empty_name_en']} |\\n")
        
        # 错误报告
        if results['extraction_errors']:
            f.write("\\n## 提取错误\\n")
            for error in results['extraction_errors']:
                f.write(f"- {error}\\n")
    
    # 5. 保存按类别分组的program_name_en
    with open(output_path / 'program_names_by_category.json', 'w', encoding='utf-8') as f:
        json.dump(dict(results['category_stats']), f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    # 设置路径
    current_dir = Path(__file__).parent
    raw_data_dir = current_dir / "raw_data"
    output_dir = current_dir / "program__extraction"
    
    print("开始提取program_name_en字段...")
    print(f"数据目录: {raw_data_dir}")
    print(f"输出目录: {output_dir}")
    
    try:
        # 提取数据
        results = extract_program_names(raw_data_dir)
        
        # 保存结果
        save_results(results, output_dir)
        
        # 打印总结
        print("\\n=== 提取完成 ===")
        print(f"总项目数: {len(results['program_names'])}")
        print(f"去重后数量: {len(results['unique_names'])}")
        print(f"处理文件数: {len(results['file_stats'])}")
        if results['extraction_errors']:
            print(f"错误数量: {len(results['extraction_errors'])}")
        
        print(f"\\n结果已保存到: {output_dir}")
        print("\\n生成的文件:")
        print("- program_names_extraction_results.json (完整结果)")
        print("- all_program_names.csv (所有项目名称)")
        print("- unique_program_names.txt (去重后的项目名称)")
        print("- extraction_statistics.md (统计报告)")
        print("- program_names_by_category.json (按类别分组)")
        
    except Exception as e:
        print(f"提取过程中发生错误: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())