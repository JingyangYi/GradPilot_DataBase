#!/usr/bin/env python3
"""
爬虫启动脚本

支持两种模式：
1. 测试模式：python run_crawler.py --test 
2. 完整模式：python run_crawler.py 
"""

import os
import sys
import argparse
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='大学项目网页爬虫')
    parser.add_argument('csv_file', type=str,
                       help='指定CSV文件路径')
    
    args = parser.parse_args()
    
    # 使用指定的CSV文件
    csv_file = args.csv_file
    print(f"使用CSV文件: {csv_file}")
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_file):
        print(f"错误：找不到文件 {csv_file}")
        return
    
    # 切换到脚本目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.getcwd())
    
    # 配置日志输出
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # 从CSV文件路径中提取文件名（不含扩展名）
    csv_basename = os.path.splitext(os.path.basename(csv_file))[0]
    
    # 提取学科名称（去掉可能的数字后缀，如"计算机_1" -> "计算机"）
    subject_name = csv_basename.split('_')[0] if '_' in csv_basename else csv_basename
    
    log_filename = f'{csv_basename}_{timestamp}.log'
    subject_log_dir = os.path.join('log', subject_name)
    log_filepath = os.path.join(subject_log_dir, log_filename)
    
    # 确保学科日志目录存在
    if not os.path.exists(subject_log_dir):
        os.makedirs(subject_log_dir)
    
    # 初始化Scrapy设置
    settings = get_project_settings()
    settings.setmodule('program_crawler.settings')
    
    # 设置日志配置
    settings.set('LOG_FILE', log_filepath)
    settings.set('LOG_LEVEL', 'INFO')
    settings.set('LOG_ENCODING', 'utf-8')
    
    # 创建爬虫进程
    process = CrawlerProcess(settings)
    
    # 启动爬虫，传递CSV文件参数
    process.crawl('program_spider', csv_file=csv_file)
    
    try:
        print(f"开始爬取，使用文件: {csv_file}")
        print("按 Ctrl+C 可随时中断爬取")
        print("-" * 50)
        
        process.start()
        
    except KeyboardInterrupt:
        print(f"\n爬虫被用户中断")
        print(f"日志已保存在: {log_filepath}")
    except Exception as e:
        print(f"爬虫运行出错: {e}")
        print(f"日志已保存在: {log_filepath}")
    finally:
        print(f"\n完整日志记录已保存在: {log_filepath}")

if __name__ == '__main__':
    main()