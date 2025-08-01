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
    parser.add_argument('--test', action='store_true', 
                       help='使用测试模式，默认为完整模式')
    parser.add_argument('--csv-file', type=str,
                       help='指定自定义CSV文件路径')
    
    args = parser.parse_args()
    
    # 确定使用的CSV文件
    if args.csv_file:
        csv_file = args.csv_file
        print(f"使用自定义CSV文件: {csv_file}")
    elif args.test:
        csv_file = 'test_urls.csv'
        print("测试模式：使用test_urls.csv")
        
        # 检查测试文件是否存在，不存在则生成
        if not os.path.exists(csv_file):
            print("测试文件不存在，正在生成...")
            try:
                from generate_test_urls import generate_test_urls
                generate_test_urls()
            except ImportError:
                print("无法导入生成测试URL的模块，请先运行: python generate_test_urls.py")
                return
    else:
        csv_file = 'program_urls.csv'
        print("完整模式：使用program_urls.csv（12,486个项目）")
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_file):
        print(f"错误：找不到文件 {csv_file}")
        return
    
    # 切换到脚本目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.getcwd())
    
    # 配置日志输出
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    mode = 'test' if args.test else 'full'
    log_filename = f'crawl_{mode}_{timestamp}.log'
    log_filepath = os.path.join('log', log_filename)
    
    # 确保 log 目录存在
    if not os.path.exists('log'):
        os.makedirs('log')
    
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