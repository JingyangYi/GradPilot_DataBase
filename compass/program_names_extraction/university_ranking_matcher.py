#!/usr/bin/env python3
"""
大学排名和专业排名匹配脚本
根据操作规划文档实现完整的排名匹配功能
"""

import json
import csv
import os
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd
from difflib import SequenceMatcher

class UniversityRankingMatcher:
    def __init__(self, data_dir, raw_data_subdir="raw_data"):
        self.data_dir = Path(data_dir)
        self.raw_data_dir = self.data_dir / raw_data_subdir
        self.processed_data_dir = self.data_dir / "processed_data"
        self.program_names_dir = self.data_dir / "program_names_extraction"
        
        # 确保输出目录存在
        self.processed_data_dir.mkdir(exist_ok=True)
        
        # 数据存储
        self.rankings_data = {}
        self.category_mapping = {}
        self.matching_stats = {
            'total_programs': 0,
            'university_matches': {'exact': 0, 'fuzzy': 0, 'failed': 0},
            'subject_matches': {'primary': 0, 'secondary': 0, 'failed': 0},
            'failed_universities': set(),
            'processing_errors': []
        }
        
    def load_rankings_data(self):
        """加载大学排名CSV数据"""
        rankings_file = self.data_dir / "univ_rankings_all_and_by_subject.csv"
        print(f"加载排名数据: {rankings_file}")
        
        try:
            # 读取CSV文件
            df = pd.read_csv(rankings_file, encoding='utf-8')
            
            # 清理列名（去除BOM和空格）
            df.columns = df.columns.str.strip().str.replace('\ufeff', '')
            
            print(f"排名数据行数: {len(df)}")
            print(f"排名数据列数: {len(df.columns)}")
            print(f"前5列: {list(df.columns[:5])}")
            
            # 转换为字典，使用英文名作为键
            for _, row in df.iterrows():
                uni_name_en = str(row.get('学校英文名', '')).strip()
                uni_name_cn = str(row.get('学校中文名', '')).strip()
                
                if uni_name_en and uni_name_en != 'nan':
                    self.rankings_data[uni_name_en] = {
                        'chinese_name': uni_name_cn,
                        'english_name': uni_name_en,
                        'country': str(row.get('国家/地区', '')).strip(),
                        'qs_2026': self._clean_rank_value(row.get('QS 2026')),
                        'usnews_2026': self._clean_rank_value(row.get('USNews 2026')),
                        'the_2025': self._clean_rank_value(row.get('THE 2025')),
                        'arwu_2024': self._clean_rank_value(row.get('ARWU 2024')),
                        'subjects': {}
                    }
                    
                    # 添加所有专业排名
                    for col in df.columns:
                        if col not in ['学校中文名', '学校英文名', '国家/地区', 'QS 2026', 'USNews 2026', 'THE 2025', 'ARWU 2024']:
                            subject_rank = self._clean_rank_value(row.get(col))
                            if subject_rank is not None:
                                self.rankings_data[uni_name_en]['subjects'][col] = subject_rank
            
            print(f"成功加载 {len(self.rankings_data)} 所大学的排名数据")
            
        except Exception as e:
            print(f"加载排名数据失败: {str(e)}")
            raise
    
    def _clean_rank_value(self, value):
        """清理排名数值"""
        if pd.isna(value) or value == '' or str(value).strip() == '' or str(value).strip() == '-':
            return None
        
        value_str = str(value).strip()
        
        # 处理等号开头的排名 (如 "=7")
        if value_str.startswith('='):
            try:
                return int(value_str[1:])
            except ValueError:
                return None
        
        # 处理范围排名 (如 "51-100")
        if '-' in value_str and not value_str.startswith('-'):
            try:
                parts = value_str.split('-')
                if len(parts) == 2:
                    start = int(parts[0])
                    end = int(parts[1])
                    return (start + end) / 2  # 返回中位数
            except ValueError:
                return None
        
        # 处理纯数字
        try:
            return int(float(value_str))
        except ValueError:
            return None
    
    def load_category_mapping(self):
        """加载专业类别映射表"""
        mapping_file = self.program_names_dir / "category_to_qs_mapping.json"
        print(f"加载类别映射表: {mapping_file}")
        
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self.category_mapping = json.load(f)
            print(f"成功加载 {len(self.category_mapping)} 个类别映射")
        except Exception as e:
            print(f"加载类别映射表失败: {str(e)}")
            raise
    
    def match_university_name(self, uni_name_en, uni_name_cn=None):
        """匹配大学名称，返回排名数据"""
        if not uni_name_en:
            return None
        
        # 第一层：英文名称精确匹配
        if uni_name_en in self.rankings_data:
            self.matching_stats['university_matches']['exact'] += 1
            return self.rankings_data[uni_name_en]
        
        # 第二层：英文名称模糊匹配
        best_match = None
        best_score = 0.0
        
        # 预处理查询名称
        query_name = self._normalize_university_name(uni_name_en)
        
        for ranked_uni_name, ranked_data in self.rankings_data.items():
            normalized_name = self._normalize_university_name(ranked_uni_name)
            
            # 计算相似度
            similarity = SequenceMatcher(None, query_name, normalized_name).ratio()
            
            if similarity > best_score and similarity > 0.85:  # 设置阈值
                best_score = similarity
                best_match = ranked_data
        
        if best_match:
            self.matching_stats['university_matches']['fuzzy'] += 1
            return best_match
        
        # 第三层：中文名称匹配（如果提供）
        if uni_name_cn:
            for ranked_data in self.rankings_data.values():
                if ranked_data['chinese_name'] == uni_name_cn:
                    self.matching_stats['university_matches']['fuzzy'] += 1
                    return ranked_data
        
        # 匹配失败
        self.matching_stats['university_matches']['failed'] += 1
        self.matching_stats['failed_universities'].add(uni_name_en)
        return None
    
    def _normalize_university_name(self, name):
        """标准化大学名称"""
        # 转换为小写
        name = name.lower()
        
        # 去除常见词汇
        common_words = ['university', 'college', 'institute', 'school', 'of', 'the', 'and', '&']
        words = name.split()
        filtered_words = [word for word in words if word not in common_words]
        
        # 处理常见缩写
        abbreviations = {
            'mit': 'massachusetts institute technology',
            'ucl': 'university college london',
            'nyu': 'new york university',
            'ucla': 'university california los angeles',
        }
        
        normalized = ' '.join(filtered_words)
        for abbr, full in abbreviations.items():
            if abbr in normalized:
                normalized = normalized.replace(abbr, full)
        
        return normalized
    
    def _create_subject_field_name(self, subject_name):
        """根据QS学科名称创建字段名"""
        # 清理学科名称，转换为适合字段名的格式
        field_name = subject_name.lower()
        
        # 替换特殊字符和空格
        replacements = {
            ' ': '_',
            '&': 'and', 
            '-': '_',
            '$': '',
            '/': '_',
            '.': '',
            ',': '',
            '(': '',
            ')': '',
            "'": '',
            '"': ''
        }
        
        for old, new in replacements.items():
            field_name = field_name.replace(old, new)
        
        # 去除多余的下划线
        while '__' in field_name:
            field_name = field_name.replace('__', '_')
        
        field_name = field_name.strip('_')
        
        # 添加前缀
        return f"qs_2026_{field_name}_rank"
    
    def get_subject_rankings(self, category, university_data):
        """根据类别获取专业排名"""
        if category not in self.category_mapping:
            return None, None, None, None
        
        mapping = self.category_mapping[category]
        primary_subject = mapping.get('primary')
        secondary_subject = mapping.get('secondary')
        
        primary_rank = None
        secondary_rank = None
        
        if primary_subject and university_data:
            primary_rank = university_data['subjects'].get(primary_subject)
            if primary_rank is not None:
                self.matching_stats['subject_matches']['primary'] += 1
        
        if secondary_subject and university_data:
            secondary_rank = university_data['subjects'].get(secondary_subject)
            if secondary_rank is not None:
                self.matching_stats['subject_matches']['secondary'] += 1
        
        if primary_rank is None and secondary_rank is None:
            self.matching_stats['subject_matches']['failed'] += 1
        
        return primary_rank, secondary_rank, primary_subject, secondary_subject
    
    def process_program(self, program, category):
        """处理单个项目，添加排名信息"""
        self.matching_stats['total_programs'] += 1
        
        # 获取大学信息
        uni_name_en = program.get('university_name_en', '')
        uni_name_cn = program.get('university_name', '')
        
        # 匹配大学排名
        university_data = self.match_university_name(uni_name_en, uni_name_cn)
        
        # 添加综合排名字段
        program['qs_2026_rank'] = university_data['qs_2026'] if university_data else None
        program['usnews_2026_rank'] = university_data['usnews_2026'] if university_data else None
        program['the_2025_rank'] = university_data['the_2025'] if university_data else None
        program['arwu_2024_rank'] = university_data['arwu_2024'] if university_data else None
        
        # 获取专业排名
        primary_rank, secondary_rank, primary_subject, secondary_subject = self.get_subject_rankings(category, university_data)
        
        # 添加专业排名字段（使用具体学科名称）
        if primary_subject:
            field_name = self._create_subject_field_name(primary_subject)
            program[field_name] = primary_rank
        
        # 只有当secondary_rank存在时才添加secondary字段
        if secondary_subject and secondary_rank is not None:
            field_name = self._create_subject_field_name(secondary_subject)
            program[field_name] = secondary_rank
        
        return program
    
    def process_json_file(self, json_file_path, category):
        """处理单个JSON文件"""
        print(f"处理文件: {json_file_path.name} (类别: {category})")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON文件格式错误：应为数组格式")
            
            processed_data = []
            
            for item in data:
                if isinstance(item, dict):
                    # 跳过completion_rate信息
                    if 'completion_rate' in item:
                        processed_data.append(item)
                        continue
                    
                    # 处理项目数据
                    processed_program = self.process_program(item, category)
                    processed_data.append(processed_program)
                else:
                    processed_data.append(item)
            
            # 保存处理后的数据
            output_file = self.processed_data_dir / json_file_path.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            print(f"已保存到: {output_file}")
            
        except Exception as e:
            error_msg = f"处理文件 {json_file_path.name} 时出错: {str(e)}"
            print(f"错误: {error_msg}")
            self.matching_stats['processing_errors'].append(error_msg)
    
    def process_all_files(self):
        """批量处理所有JSON文件"""
        print("开始批量处理所有JSON文件...")
        
        json_files = list(self.raw_data_dir.glob("*.json"))
        print(f"找到 {len(json_files)} 个JSON文件")
        
        for json_file in json_files:
            category = json_file.stem  # 使用文件名作为类别
            self.process_json_file(json_file, category)
        
        print("批量处理完成！")
    
    def generate_matching_report(self):
        """生成匹配统计报告"""
        report = {
            'processing_summary': {
                'total_programs_processed': self.matching_stats['total_programs'],
                'total_json_files': len(list(self.raw_data_dir.glob("*.json")))
            },
            'university_matching': {
                'exact_matches': self.matching_stats['university_matches']['exact'],
                'fuzzy_matches': self.matching_stats['university_matches']['fuzzy'],
                'failed_matches': self.matching_stats['university_matches']['failed'],
                'success_rate': round((self.matching_stats['university_matches']['exact'] + 
                                     self.matching_stats['university_matches']['fuzzy']) / 
                                    max(self.matching_stats['total_programs'], 1) * 100, 2)
            },
            'subject_ranking_matching': {
                'primary_matches': self.matching_stats['subject_matches']['primary'],
                'secondary_matches': self.matching_stats['subject_matches']['secondary'],
                'failed_matches': self.matching_stats['subject_matches']['failed']
            },
            'failed_universities': sorted(list(self.matching_stats['failed_universities'])),
            'processing_errors': self.matching_stats['processing_errors']
        }
        
        # 保存报告
        report_file = self.processed_data_dir / "matching_statistics_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成Markdown报告
        self._generate_markdown_report(report)
        
        return report
    
    def _generate_markdown_report(self, report):
        """生成Markdown格式的报告"""
        report_file = self.processed_data_dir / "matching_statistics_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 大学排名匹配统计报告\n\n")
            
            # 处理概要
            f.write("## 处理概要\n")
            f.write(f"- 总处理项目数: {report['processing_summary']['total_programs_processed']}\n")
            f.write(f"- 总JSON文件数: {report['processing_summary']['total_json_files']}\n\n")
            
            # 大学匹配统计
            f.write("## 大学名称匹配统计\n")
            uni_match = report['university_matching']
            f.write(f"- 精确匹配: {uni_match['exact_matches']}\n")
            f.write(f"- 模糊匹配: {uni_match['fuzzy_matches']}\n")
            f.write(f"- 匹配失败: {uni_match['failed_matches']}\n")
            f.write(f"- 匹配成功率: {uni_match['success_rate']}%\n\n")
            
            # 专业排名匹配统计
            f.write("## 专业排名匹配统计\n")
            subj_match = report['subject_ranking_matching']
            f.write(f"- 主要专业排名匹配: {subj_match['primary_matches']}\n")
            f.write(f"- 备选专业排名匹配: {subj_match['secondary_matches']}\n")
            f.write(f"- 专业排名匹配失败: {subj_match['failed_matches']}\n\n")
            
            # 失败的大学列表
            if report['failed_universities']:
                f.write("## 匹配失败的大学\n")
                for uni in report['failed_universities'][:50]:  # 只显示前50个
                    f.write(f"- {uni}\n")
                if len(report['failed_universities']) > 50:
                    f.write(f"\n... 还有 {len(report['failed_universities']) - 50} 个大学未列出\n")
                f.write("\n")
            
            # 处理错误
            if report['processing_errors']:
                f.write("## 处理错误\n")
                for error in report['processing_errors']:
                    f.write(f"- {error}\n")
        
        print(f"报告已保存到: {report_file}")

def main():
    """主函数"""
    # 设置数据目录
    data_dir = Path("/Users/yijingyang/Library/CloudStorage/OneDrive-个人/GradPilot/ProgramDB/compass")
    
    print("=== 大学排名匹配程序启动 ===")
    print(f"数据目录: {data_dir}")
    
    try:
        # 初始化匹配器，使用data 2作为数据源
        matcher = UniversityRankingMatcher(data_dir, "data")
        
        # 加载数据
        matcher.load_rankings_data()
        matcher.load_category_mapping()
        
        # 处理所有文件
        matcher.process_all_files()
        
        # 生成报告
        report = matcher.generate_matching_report()
        
        print("\n=== 处理完成 ===")
        print(f"总处理项目数: {report['processing_summary']['total_programs_processed']}")
        print(f"大学匹配成功率: {report['university_matching']['success_rate']}%")
        print(f"处理后的文件保存在: {matcher.processed_data_dir}")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())