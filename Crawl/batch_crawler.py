#!/usr/bin/env python3
"""
分批爬虫总控制脚本

功能：
1. 按学科自动分批处理8000+条数据
2. 支持断点续传，从中断处继续
3. 三级日志：全局进度、学科级别、错误汇总
4. 失败项目追踪和重试机制

使用方法：
python batch_crawler.py --all      # 爬取所有学科
python batch_crawler.py --subjects "计算机,医学"  # 指定学科
python batch_crawler.py --resume   # 从断点继续
"""

import os
import sys
import json
import csv
import argparse
import logging
import time
from datetime import datetime
from collections import defaultdict
# Scrapy imports moved to function level to avoid import issues

class BatchCrawlManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.status_file = os.path.join(self.base_dir, 'crawl_status.json')
        self.csv_file = os.path.join(self.base_dir, 'top_200_urls.csv')
        self.log_dir = os.path.join(self.base_dir, 'logs')
        
        # 确保必要目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'output'), exist_ok=True)
        
        # 初始化日志
        self.setup_logging()
        
        # 加载状态
        self.status = self.load_status()
        
    def setup_logging(self):
        """设置三级日志系统"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. 全局进度日志
        self.global_logger = logging.getLogger('global')
        self.global_logger.setLevel(logging.INFO)
        global_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'global_progress_{timestamp}.log'),
            encoding='utf-8'
        )
        global_handler.setFormatter(logging.Formatter(
            '%(asctime)s [GLOBAL] %(levelname)s: %(message)s'
        ))
        self.global_logger.addHandler(global_handler)
        
        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(name)s] %(message)s'
        ))
        self.global_logger.addHandler(console_handler)
        
        # 2. 错误汇总日志
        self.error_logger = logging.getLogger('errors')
        self.error_logger.setLevel(logging.ERROR)
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'error_summary_{timestamp}.log'),
            encoding='utf-8'
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s [ERROR] %(message)s'
        ))
        self.error_logger.addHandler(error_handler)
        
    def load_status(self):
        """加载爬取状态"""
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "subjects": {},
            "failed_projects": [],
            "completed_subjects": [],
            "last_update": None
        }
    
    def save_status(self):
        """保存爬取状态"""
        self.status['last_update'] = datetime.now().isoformat()
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, ensure_ascii=False, indent=2)
    
    def get_subjects_data(self):
        """从CSV中获取按学科分组的数据"""
        subjects_data = defaultdict(list)
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8-sig') as f:  # 使用utf-8-sig自动处理BOM
                reader = csv.DictReader(f)
                for row in reader:
                    # 清理source_file字段
                    source_file = row['source_file'].replace('.json', '')
                    # 过滤掉异常数据
                    if source_file and not source_file.startswith(('http', '/', '-', '%')):
                        subjects_data[source_file].append(row)
                        
        except Exception as e:
            self.error_logger.error(f"读取CSV文件失败: {e}")
            raise
            
        return subjects_data
    
    def create_subject_csv(self, subject, data):
        """为特定学科创建CSV文件"""
        subject_csv = os.path.join(self.base_dir, f'temp_{subject}.csv')
        
        with open(subject_csv, 'w', encoding='utf-8', newline='') as f:  # 不使用BOM写入
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
                
        return subject_csv
    
    def get_subject_status(self, subject):
        """获取学科爬取状态"""
        return self.status['subjects'].get(subject, {
            'status': 'pending',
            'total': 0,
            'completed': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        })
    
    def update_subject_status(self, subject, **kwargs):
        """更新学科状态"""
        if subject not in self.status['subjects']:
            self.status['subjects'][subject] = self.get_subject_status(subject)
        
        self.status['subjects'][subject].update(kwargs)
        self.save_status()
    
    def crawl_subject(self, subject, data):
        """爬取单个学科（使用子进程避免reactor重启问题）"""
        subject_status = self.get_subject_status(subject)
        
        # 如果已完成，跳过
        if subject_status['status'] == 'completed':
            self.global_logger.info(f"学科 {subject} 已完成，跳过")
            return True
            
        self.global_logger.info(f"开始爬取学科: {subject} ({len(data)} 个项目)")
        
        # 更新状态
        self.update_subject_status(
            subject,
            status='running',
            total=len(data),
            start_time=datetime.now().isoformat()
        )
        
        # 创建临时CSV文件
        subject_csv = self.create_subject_csv(subject, data)
        
        try:
            # 使用子进程运行爬虫，避免reactor重启问题
            import subprocess
            import sys
            
            # 学科级别日志
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            subject_log = os.path.join(self.log_dir, f'subject_{subject}_{timestamp}.log')
            
            # 构建爬虫命令
            crawler_script = os.path.join(self.base_dir, 'run_crawler.py')
            cmd = [
                sys.executable, 
                crawler_script,
                '--csv-file', subject_csv
            ]
            
            self.global_logger.info(f"执行命令: {' '.join(cmd)}")
            
            # 运行子进程
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            if result.returncode == 0:
                # 标记完成
                self.update_subject_status(
                    subject,
                    status='completed',
                    end_time=datetime.now().isoformat()
                )
                
                if subject not in self.status['completed_subjects']:
                    self.status['completed_subjects'].append(subject)
                    self.save_status()
                
                self.global_logger.info(f"学科 {subject} 爬取完成")
                return True
            else:
                # 记录错误输出
                self.error_logger.error(f"学科 {subject} 爬取失败，返回码: {result.returncode}")
                if result.stderr:
                    self.error_logger.error(f"错误输出: {result.stderr}")
                if result.stdout:
                    self.global_logger.info(f"标准输出: {result.stdout}")
                
                self.update_subject_status(
                    subject,
                    status='failed',
                    end_time=datetime.now().isoformat()
                )
                return False
            
        except subprocess.TimeoutExpired:
            self.error_logger.error(f"学科 {subject} 爬取超时")
            self.update_subject_status(
                subject,
                status='failed',
                end_time=datetime.now().isoformat()
            )
            return False
            
        except Exception as e:
            self.error_logger.error(f"学科 {subject} 爬取失败: {e}")
            self.update_subject_status(
                subject,
                status='failed',
                end_time=datetime.now().isoformat()
            )
            return False
            
        finally:
            # 清理临时文件
            if os.path.exists(subject_csv):
                os.remove(subject_csv)
    
    def run_batch_crawl(self, target_subjects=None):
        """运行分批爬取"""
        subjects_data = self.get_subjects_data()
        
        if target_subjects:
            # 过滤指定学科
            subjects_data = {k: v for k, v in subjects_data.items() if k in target_subjects}
        
        total_subjects = len(subjects_data)
        completed_count = 0
        failed_count = 0
        
        self.global_logger.info(f"开始分批爬取，共 {total_subjects} 个学科")
        
        for subject, data in subjects_data.items():
            if self.crawl_subject(subject, data):
                completed_count += 1
            else:
                failed_count += 1
                
            # 短暂休息，避免系统压力
            time.sleep(2)
            
        # 总结
        self.global_logger.info(f"批量爬取完成: 成功 {completed_count}, 失败 {failed_count}")
        
        if failed_count > 0:
            self.error_logger.error(f"有 {failed_count} 个学科爬取失败，请查看详细日志")
    
    def resume_crawl(self):
        """从断点继续爬取"""
        subjects_data = self.get_subjects_data()
        
        # 过滤未完成的学科
        pending_subjects = {}
        for subject, data in subjects_data.items():
            status = self.get_subject_status(subject)
            if status['status'] != 'completed':
                pending_subjects[subject] = data
                
        if not pending_subjects:
            self.global_logger.info("所有学科已完成，无需继续")
            return
            
        self.global_logger.info(f"从断点继续，剩余 {len(pending_subjects)} 个学科")
        self.run_batch_crawl(list(pending_subjects.keys()))
    
    def show_status(self):
        """显示当前状态"""
        subjects_data = self.get_subjects_data()
        
        print("\n=== 爬取状态概览 ===")
        print(f"总学科数: {len(subjects_data)}")
        print(f"已完成: {len(self.status['completed_subjects'])}")
        print(f"失败项目数: {len(self.status['failed_projects'])}")
        
        if self.status['last_update']:
            print(f"最后更新: {self.status['last_update']}")
            
        # 失败项目统计
        if self.status['failed_projects']:
            print(f"\n=== 失败项目统计 ===")
            from collections import defaultdict
            failure_stats = defaultdict(int)
            subject_failures = defaultdict(int)
            
            for failed in self.status['failed_projects']:
                error_type = failed.get('error_type', 'Unknown')
                failure_stats[error_type] += 1
                subject_failures[failed.get('source_file', 'Unknown')] += 1
            
            print("按错误类型:")
            for error_type, count in sorted(failure_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error_type}: {count}")
                
            print("\n按学科:")
            for subject, count in sorted(subject_failures.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {subject}: {count}")
            
        print("\n各学科状态:")
        for subject, data in subjects_data.items():
            status = self.get_subject_status(subject)
            completed = status.get('completed', 0)
            failed = status.get('failed', 0)
            total = len(data)
            
            status_str = status['status']
            if completed > 0 or failed > 0:
                progress = f"({completed}成功/{failed}失败/{total}总计)"
            else:
                progress = f"({total} 项目)"
                
            print(f"  {subject}: {status_str} {progress}")
    
    def show_failures(self, limit=20):
        """显示失败项目详情"""
        if not self.status['failed_projects']:
            print("没有失败项目记录")
            return
            
        print(f"\n=== 失败项目详情 (最近{min(limit, len(self.status['failed_projects']))}条) ===")
        
        # 按时间倒序排列，显示最近的失败
        recent_failures = sorted(
            self.status['failed_projects'], 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )[:limit]
        
        for i, failed in enumerate(recent_failures, 1):
            print(f"\n{i}. {failed.get('program_name', 'Unknown')}")
            print(f"   学科: {failed.get('source_file', 'Unknown')}")
            print(f"   URL: {failed.get('url', 'Unknown')}")
            print(f"   错误: {failed.get('error', 'Unknown')}")
            print(f"   时间: {failed.get('timestamp', 'Unknown')}")

def main():
    parser = argparse.ArgumentParser(description='分批爬虫总控制脚本')
    parser.add_argument('--all', action='store_true', help='爬取所有学科')
    parser.add_argument('--subjects', type=str, help='指定学科，用逗号分隔')
    parser.add_argument('--resume', action='store_true', help='从断点继续')
    parser.add_argument('--status', action='store_true', help='显示当前状态')
    parser.add_argument('--failures', action='store_true', help='显示失败项目详情')
    
    args = parser.parse_args()
    
    manager = BatchCrawlManager()
    
    if args.status:
        manager.show_status()
    elif args.failures:
        manager.show_failures()
    elif args.resume:
        manager.resume_crawl()
    elif args.all:
        manager.run_batch_crawl()
    elif args.subjects:
        target_subjects = [s.strip() for s in args.subjects.split(',')]
        manager.run_batch_crawl(target_subjects)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()