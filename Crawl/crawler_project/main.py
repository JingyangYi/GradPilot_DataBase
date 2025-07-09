#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫主入口文件
读取CSV数据，协调整个爬虫流程
"""

import asyncio
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 使用绝对导入
from crawler_project.config.crawler_config import (
    CrawlerConfig, StabilityConfig, InteractionConfig,
    DEFAULT_CRAWLER_CONFIG, DEFAULT_STABILITY_CONFIG, DEFAULT_INTERACTION_CONFIG
)
from crawler_project.config.url_filters import URLFilterProcessor, DEFAULT_URL_FILTERS
from crawler_project.utils.text_extractor import TextExtractor
from crawler_project.core.crawler import WebCrawler
from crawler_project.core.data_models import ProjectInfo, CrawlResult


class CrawlerOrchestrator:
    """爬虫协调器 - 管理整个爬虫流程"""
    
    def __init__(self, csv_path: str, output_dir: str = "output"):
        self.csv_path = csv_path
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化爬虫
        self.crawler = WebCrawler(
            crawler_config=self._create_optimized_config(),
            stability_config=DEFAULT_STABILITY_CONFIG,
            interaction_config=self._create_simple_interaction_config(),
            url_filter=URLFilterProcessor(DEFAULT_URL_FILTERS),
            text_extractor=TextExtractor()
        )
        
        # 统计信息
        self.total_projects = 0
        self.successful_projects = 0
        self.failed_projects = 0
    
    def _create_optimized_config(self) -> CrawlerConfig:
        """创建优化的爬虫配置"""
        config = CrawlerConfig(
            max_depth=1,  # 限制深度为1，只爬取主页面
            timeout=15,   # 缩短超时时间
            delay_between_requests=3.0,  # 增加延迟避免被封
            max_retries=1,  # 减少重试次数
            headless=True,  # 无头模式提高性能
            output_dir=self.output_dir,
            enable_snapshots=False  # 暂时禁用快照功能
        )
        return config
    
    def _create_stability_config(self) -> StabilityConfig:
        """创建稳定性配置"""
        config = StabilityConfig(
            enable_request_interception=True,
            block_resources=['stylesheet', 'font', 'image']
        )
        return config
    
    def _create_simple_interaction_config(self) -> InteractionConfig:
        """创建简化的交互配置"""
        config = InteractionConfig(
            max_interactions_per_page=0,  # 暂时禁用交互处理
            click_timeout=1000,  
            after_click_wait=500,  
            clickable_selectors=[],  # 暂时禁用所有交互
            tab_selectors=[]  # 暂时禁用Tab处理
        )
        return config
    
    def load_csv_data(self) -> pd.DataFrame:
        """加载CSV数据"""
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8')
            print(f"成功加载CSV数据: {len(df)} 条记录")
            return df
        except Exception as e:
            print(f"CSV加载失败: {e}")
            raise
    
    def extract_project_info(self, row: pd.Series) -> ProjectInfo:
        """
        从CSV行数据提取项目信息
        
        Args:
            row: DataFrame的一行数据
            
        Returns:
            ProjectInfo: 项目信息对象
        """
        # 根据CSV列名提取信息
        university_name = str(row.get('大学英文名称', '')).strip()
        degree = str(row.get('学位', '')).strip()
        program_name = str(row.get('专业英文名称', '')).strip()
        department = str(row.get('所属院系（英文）', '')).strip()
        
        return ProjectInfo(
            university_name=university_name,
            degree=degree,
            program_name=program_name,
            department=department
        )
    
    def get_start_url(self, row: pd.Series) -> str:
        """
        从CSV行数据获取起始URL
        
        Args:
            row: DataFrame的一行数据
            
        Returns:
            str: 起始URL
        """
        url = str(row.get('专业网址', '')).strip()
        
        # 基本URL验证
        if not url or url == 'nan':
            raise ValueError("专业网址为空")
        
        if not url.startswith(('http://', 'https://')):
            if url.startswith('www.'):
                url = 'https://' + url
            else:
                raise ValueError(f"无效的URL格式: {url}")
        
        return url
    
    async def crawl_single_project(self, row: pd.Series, index: int) -> Dict[str, Any]:
        """
        爬取单个项目
        
        Args:
            row: CSV行数据
            index: 行索引
            
        Returns:
            Dict: 爬取结果统计
        """
        # 为每个项目创建新的爬虫实例，确保浏览器状态隔离
        project_crawler = None
        
        try:
            # 提取项目信息
            project_info = self.extract_project_info(row)
            start_url = self.get_start_url(row)
            
            print(f"\n[{index + 1}/{self.total_projects}] 开始爬取:")
            print(f"  项目: {project_info.university_name} - {project_info.program_name}")
            print(f"  URL: {start_url}")
            
            # 为每个项目创建新的WebCrawler实例
            project_crawler = WebCrawler(
                crawler_config=self._create_optimized_config(),
                stability_config=self._create_stability_config(),
                interaction_config=self._create_simple_interaction_config(),
                url_filter=URLFilterProcessor(),
                text_extractor=TextExtractor()
            )
            
            # 执行爬虫
            result = await project_crawler.crawl_project(start_url, project_info)
            
            # 保存结果
            file_path = await project_crawler.save_result(result, self.output_dir)
            
            # 统计信息
            stats = result.get_statistics()
            failed_urls = result.get_all_failed_urls()
            
            project_result = {
                'success': True,
                'project_info': project_info,
                'file_path': file_path,
                'statistics': stats,
                'failed_urls': failed_urls,
                'error': None
            }
            
            print(f"  ✅ 爬取成功: {stats['successful_pages']}/{stats['total_pages']} 页面")
            self.successful_projects += 1
            
            return project_result
            
        except Exception as e:
            error_msg = f"项目爬取失败: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.failed_projects += 1
            
            return {
                'success': False,
                'project_info': None,
                'file_path': None,
                'statistics': None,
                'failed_urls': [],
                'error': error_msg
            }
    
    async def crawl_all_projects(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        爬取所有项目
        
        Args:
            limit: 限制爬取的项目数量（用于测试）
            
        Returns:
            List[Dict]: 所有项目的爬取结果
        """
        # 加载数据
        df = self.load_csv_data()
        
        # 限制数量（用于测试）
        if limit:
            df = df.head(limit)
            print(f"限制爬取前 {limit} 个项目")
        
        self.total_projects = len(df)
        print(f"总共需要爬取 {self.total_projects} 个项目")
        
        # 逐个爬取项目
        results = []
        
        for index, row in df.iterrows():
            try:
                result = await self.crawl_single_project(row, index)
                results.append(result)
                
                # 在项目之间添加延迟
                if index < len(df) - 1:  # 最后一个项目不需要延迟
                    print(f"等待 5 秒后继续下一个项目...")
                    await asyncio.sleep(5)
                    
            except KeyboardInterrupt:
                print("\n用户中断爬虫...")
                break
            except Exception as e:
                print(f"处理项目 {index} 时发生未预期错误: {e}")
                results.append({
                    'success': False,
                    'error': f"未预期错误: {str(e)}"
                })
                continue
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印爬取总结"""
        print("\n" + "="*60)
        print("爬虫执行总结")
        print("="*60)
        print(f"总项目数: {self.total_projects}")
        print(f"成功项目: {self.successful_projects}")
        print(f"失败项目: {self.failed_projects}")
        print(f"成功率: {self.successful_projects/self.total_projects*100:.1f}%")
        
        # 统计失败原因
        if self.failed_projects > 0:
            print("\n失败项目详情:")
            for i, result in enumerate(results):
                if not result['success']:
                    print(f"  {i+1}. {result['error']}")
        
        # 统计成功项目的页面信息
        successful_results = [r for r in results if r['success']]
        if successful_results:
            total_pages = sum(r['statistics']['total_pages'] for r in successful_results)
            successful_pages = sum(r['statistics']['successful_pages'] for r in successful_results)
            print(f"\n页面爬取统计:")
            print(f"总页面数: {total_pages}")
            print(f"成功页面: {successful_pages}")
            print(f"页面成功率: {successful_pages/total_pages*100:.1f}%")
    
    async def run(self, limit: int = None):
        """运行爬虫"""
        print("="*60)
        print("智能数据科学项目爬虫 v2.0")
        print("="*60)
        
        try:
            results = await self.crawl_all_projects(limit)
            self.print_summary(results)
            
        except Exception as e:
            print(f"爬虫执行失败: {e}")
        
        print("\n爬虫执行完成!")


async def main():
    """主函数"""
    # CSV文件路径
    csv_path = "../24-25美研数据科学与应用数据科学专业查校表.csv"
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_path):
        print(f"错误: CSV文件不存在: {csv_path}")
        return
    
    # 创建协调器
    orchestrator = CrawlerOrchestrator(csv_path, "output")
    
    # 运行爬虫（限制为前3个项目进行测试）
    await orchestrator.run(limit=3)


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main()) 