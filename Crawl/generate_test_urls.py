#!/usr/bin/env python3
"""
生成测试用URL列表

从完整的top_200_urls.csv中随机选取项目用于测试
避免测试时爬取所有项目
"""

import pandas as pd
import random

def generate_test_urls(sample_size=50):
    """
    从完整URL列表中随机选取项目生成测试列表
    
    Args:
        sample_size (int): 测试项目数量
    """
    print("正在生成测试URL列表...")
    
    # 读取完整的URL列表
    df = pd.read_csv('top_200_urls.csv')
    print(f"完整列表包含 {len(df)} 个项目")
    
    # 随机采样
    test_df = df.sample(sample_size)
    
    # 保存测试列表
    test_df.to_csv('test_urls.csv', index=False)
    
    print(f"已生成测试列表: test_urls.csv ({sample_size}个项目)")
    print("\n测试项目预览:")
    print("-" * 80)
    
    for i, row in test_df.iterrows():
        print(f"{row['program_name'][:40]:<40} | {row['program_url']}")
    
    print("-" * 80)
    print(f"使用方法: python run_crawler.py --test")

if __name__ == "__main__":
    generate_test_urls()