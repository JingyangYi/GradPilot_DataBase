#!/usr/bin/env python3
"""
爬虫结果汇总分析器
================

功能：
- 统计所有subject的成功/失败情况
- 分析失败原因分布（HTTP状态码）
- 统计每个项目爬取的页面数量
- 生成清晰的汇总报告

使用：python analyze_crawl_results.py
"""

import os
import json
import glob
from collections import defaultdict
from datetime import datetime

class CrawlAnalyzer:
    def __init__(self, crawl_dir='.'):
        self.crawl_dir = crawl_dir
        self.output_dir = os.path.join(crawl_dir, 'output')
        self.log_dir = os.path.join(crawl_dir, 'log')
        self.status_dir = os.path.join(crawl_dir, 'status_log')
        
        self.results = {
            'summary': {},
            'subjects': {},
            'failed_analysis': {},
            'page_stats': {}
        }
    
    def analyze(self):
        """执行完整分析"""
        print("🔍 开始分析爬取结果...")
        print("=" * 60)
        
        # 分析成功的项目数据
        self.analyze_successful_data()
        
        # 分析失败的URL数据  
        self.analyze_failed_data()
        
        # 生成汇总统计
        self.generate_summary()
        
        # 输出报告
        self.print_report()
        
        # 保存详细结果到文件
        self.save_detailed_results()
    
    def analyze_successful_data(self):
        """分析成功爬取的数据"""
        print("📊 分析成功数据...")
        
        if not os.path.exists(self.output_dir):
            print(f"   ⚠️  输出目录不存在: {self.output_dir}")
            return
            
        total_projects = 0
        total_pages = 0
        subject_stats = defaultdict(lambda: {'projects': 0, 'pages': 0, 'avg_pages': 0})
        
        # 扫描所有subject目录
        for subject_dir in glob.glob(os.path.join(self.output_dir, '*')):
            if not os.path.isdir(subject_dir):
                continue
                
            subject_name = os.path.basename(subject_dir)
            
            # 扫描该subject下的所有JSON文件
            json_files = glob.glob(os.path.join(subject_dir, '*.json'))
            
            subject_projects = len(json_files)
            subject_pages = 0
            
            # 统计页面数量
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        pages_count = data.get('total_pages', 0)
                        subject_pages += pages_count
                except Exception as e:
                    print(f"   ⚠️  读取文件失败: {json_file} - {e}")
            
            # 更新统计
            subject_stats[subject_name]['projects'] = subject_projects
            subject_stats[subject_name]['pages'] = subject_pages
            subject_stats[subject_name]['avg_pages'] = subject_pages / max(1, subject_projects)
            
            total_projects += subject_projects
            total_pages += subject_pages
        
        self.results['subjects'] = dict(subject_stats)
        self.results['summary']['total_successful_projects'] = total_projects
        self.results['summary']['total_pages_crawled'] = total_pages
        self.results['summary']['avg_pages_per_project'] = total_pages / max(1, total_projects)
        
        print(f"   ✅ 成功项目: {total_projects}")
        print(f"   📄 总页面数: {total_pages}")
    
    def analyze_failed_data(self):
        """分析失败的URL数据"""
        print("❌ 分析失败数据...")
        
        if not os.path.exists(self.log_dir):
            print(f"   ⚠️  日志目录不存在: {self.log_dir}")
            return
        
        failed_stats = defaultdict(int)
        failed_by_subject = defaultdict(lambda: defaultdict(int))
        total_failed = 0
        
        # 扫描所有subject的失败日志
        for subject_dir in glob.glob(os.path.join(self.log_dir, '*')):
            if not os.path.isdir(subject_dir):
                continue
                
            subject_name = os.path.basename(subject_dir)
            
            # 扫描失败URL文件
            failed_files = glob.glob(os.path.join(subject_dir, 'failed_urls_*_HTTP*.json'))
            failed_files += glob.glob(os.path.join(subject_dir, 'failed_urls_*_OTHER.json'))
            
            for failed_file in failed_files:
                try:
                    # 从文件名提取状态码
                    filename = os.path.basename(failed_file)
                    if '_HTTP' in filename:
                        status_code = filename.split('_HTTP')[1].split('.json')[0]
                        status_key = f'HTTP_{status_code}'
                    else:
                        status_key = 'OTHER'
                    
                    # 读取失败记录
                    with open(failed_file, 'r', encoding='utf-8') as f:
                        failed_data = json.load(f)
                        count = len(failed_data)
                        
                        failed_stats[status_key] += count
                        failed_by_subject[subject_name][status_key] += count
                        total_failed += count
                        
                except Exception as e:
                    print(f"   ⚠️  读取失败文件错误: {failed_file} - {e}")
        
        self.results['failed_analysis']['by_status'] = dict(failed_stats)
        self.results['failed_analysis']['by_subject'] = dict(failed_by_subject)
        self.results['summary']['total_failed_projects'] = total_failed
        
        print(f"   ❌ 失败项目: {total_failed}")
        print(f"   🔢 失败类型: {len(failed_stats)}")
    
    def generate_summary(self):
        """生成总体汇总统计"""
        successful = self.results['summary'].get('total_successful_projects', 0)
        failed = self.results['summary'].get('total_failed_projects', 0)
        total = successful + failed
        
        if total > 0:
            success_rate = (successful / total) * 100
        else:
            success_rate = 0
        
        self.results['summary'].update({
            'total_projects': total,
            'success_rate': success_rate,
            'failure_rate': 100 - success_rate,
            'analysis_time': datetime.now().isoformat()
        })
    
    def print_report(self):
        """打印分析报告"""
        print("\n" + "=" * 60)
        print("📈 爬取结果汇总报告")
        print("=" * 60)
        
        # 总体统计
        summary = self.results['summary']
        print(f"🎯 总体统计:")
        print(f"   • 总项目数: {summary.get('total_projects', 0):,}")
        print(f"   • 成功项目: {summary.get('total_successful_projects', 0):,}")
        print(f"   • 失败项目: {summary.get('total_failed_projects', 0):,}")
        print(f"   • 成功率: {summary.get('success_rate', 0):.1f}%")
        print(f"   • 总爬取页面: {summary.get('total_pages_crawled', 0):,}")
        print(f"   • 平均页面/项目: {summary.get('avg_pages_per_project', 0):.1f}")
        
        # 失败分析
        print(f"\n❌ 失败分析:")
        failed_by_status = self.results['failed_analysis'].get('by_status', {})
        if failed_by_status:
            for status, count in sorted(failed_by_status.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / summary.get('total_failed_projects', 1)) * 100
                print(f"   • {status}: {count:,} ({percentage:.1f}%)")
        else:
            print("   • 无失败记录")
        
        # Top 10 学科统计
        print(f"\n🏆 Top 10 学科 (按成功项目数):")
        subjects = self.results['subjects']
        if subjects:
            top_subjects = sorted(subjects.items(), 
                                key=lambda x: x[1]['projects'], reverse=True)[:10]
            for i, (subject, stats) in enumerate(top_subjects, 1):
                print(f"   {i:2d}. {subject}: "
                      f"{stats['projects']} 项目, "
                      f"{stats['pages']} 页面 "
                      f"(avg: {stats['avg_pages']:.1f})")
        else:
            print("   • 无成功数据")
        
        print("\n" + "=" * 60)
        print(f"📅 分析完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def save_detailed_results(self):
        """保存详细结果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"crawl_analysis_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 详细分析结果已保存: {filename}")
        except Exception as e:
            print(f"\n⚠️  保存详细结果失败: {e}")

def main():
    """主函数"""
    print("🚀 爬虫结果分析器")
    print("Author: Claude Code Assistant")
    print("=" * 60)
    
    analyzer = CrawlAnalyzer()
    analyzer.analyze()
    
    print("\n✨ 分析完成！")

if __name__ == '__main__':
    main()