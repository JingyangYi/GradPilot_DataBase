#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
简化的数据结构，只保留文本信息，去除HTML、CSS、SVG等
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class CrawlMetadata:
    """爬虫元数据，用于版本控制和追溯"""
    crawl_run_id: str
    crawl_time: str  # ISO 8601格式
    crawler_version: str
    max_depth: int
    total_pages_crawled: int
    failed_pages: int
    success: bool
    
    def __post_init__(self):
        if not self.crawl_run_id:
            self.crawl_run_id = str(uuid.uuid4())
        if not self.crawl_time:
            self.crawl_time = datetime.now().isoformat()


@dataclass 
class ProjectInfo:
    """项目基本信息，用于JSON文件命名"""
    university_name: str  # 大学英文名称
    degree: str  # 学位
    program_name: str  # 专业英文名称  
    department: str  # 所属院系（英文）
    
    def get_filename(self) -> str:
        """生成JSON文件名"""
        # 清理文件名中的特殊字符
        clean_university = self._clean_filename(self.university_name)
        clean_degree = self._clean_filename(self.degree) 
        clean_program = self._clean_filename(self.program_name)
        clean_department = self._clean_filename(self.department)
        
        return f"{clean_university}-{clean_degree}-{clean_program}-{clean_department}.json"
    
    def _clean_filename(self, text: str) -> str:
        """清理文件名中的特殊字符"""
        import re
        # 替换空格为下划线，移除特殊字符
        cleaned = re.sub(r'[^\w\s-]', '', text)
        cleaned = re.sub(r'[\s-]+', '_', cleaned)
        return cleaned.strip('_')


@dataclass
class PageContent:
    """页面内容 - 仅包含文本信息"""
    url: str
    title: str  # 页面标题
    text_content: str  # 清理后的纯文本内容
    status_code: int
    crawl_timestamp: str
    error_message: Optional[str] = None
    
    # 交互内容 - 只保留文本
    interactive_text: Dict[str, str] = field(default_factory=dict)  # {action: text_content}
    
    # 提取的链接信息
    extracted_links: List[Dict[str, str]] = field(default_factory=list)  # [{'url': str, 'text': str}]
    
    def __post_init__(self):
        if not self.crawl_timestamp:
            self.crawl_timestamp = datetime.now().isoformat()


@dataclass
class CrawlNode:
    """爬虫节点 - 递归树状结构"""
    depth: int
    parent_url: Optional[str]
    content: PageContent
    children: List['CrawlNode'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于JSON序列化"""
        return {
            'depth': self.depth,
            'parent_url': self.parent_url,
            'url': self.content.url,
            'title': self.content.title,
            'text_content': self.content.text_content,
            'status_code': self.content.status_code,
            'crawl_timestamp': self.content.crawl_timestamp,
            'error_message': self.content.error_message,
            'interactive_text': self.content.interactive_text,
            'extracted_links': self.content.extracted_links,
            'children': [child.to_dict() for child in self.children]
        }


@dataclass
class CrawlResult:
    """完整的爬虫结果"""
    project_info: ProjectInfo
    metadata: CrawlMetadata
    root_node: CrawlNode
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为完整的JSON结构"""
        return {
            'project_info': {
                'university_name': self.project_info.university_name,
                'degree': self.project_info.degree,
                'program_name': self.project_info.program_name,
                'department': self.project_info.department,
                'filename': self.project_info.get_filename()
            },
            'metadata': {
                'crawl_run_id': self.metadata.crawl_run_id,
                'crawl_time': self.metadata.crawl_time,
                'crawler_version': self.metadata.crawler_version,
                'max_depth': self.metadata.max_depth,
                'total_pages_crawled': self.metadata.total_pages_crawled,
                'failed_pages': self.metadata.failed_pages,
                'success': self.metadata.success
            },
            'crawl_data': self.root_node.to_dict()
        }
    
    def get_all_failed_urls(self) -> List[str]:
        """递归提取所有失败的URL"""
        failed_urls = []
        
        def extract_failed(node: CrawlNode):
            if node.content.error_message:
                failed_urls.append(node.content.url)
            for child in node.children:
                extract_failed(child)
        
        extract_failed(self.root_node)
        return failed_urls
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取爬虫统计信息"""
        total_pages = 0
        failed_pages = 0
        successful_pages = 0
        
        def count_pages(node: CrawlNode):
            nonlocal total_pages, failed_pages, successful_pages
            total_pages += 1
            
            if node.content.error_message:
                failed_pages += 1
            else:
                successful_pages += 1
            
            for child in node.children:
                count_pages(child)
        
        count_pages(self.root_node)
        
        return {
            'total_pages': total_pages,
            'successful_pages': successful_pages,
            'failed_pages': failed_pages,
            'success_rate': successful_pages / total_pages if total_pages > 0 else 0
        }


@dataclass  
class RetryInfo:
    """重试信息"""
    url: str
    attempts: int
    last_error: str
    next_retry_time: Optional[str] = None
    
    def increment_attempts(self):
        """增加重试次数"""
        self.attempts += 1
    
    def set_next_retry(self, delay_seconds: float):
        """设置下次重试时间"""
        from datetime import datetime, timedelta
        next_time = datetime.now() + timedelta(seconds=delay_seconds)
        self.next_retry_time = next_time.isoformat()


def create_failed_page_content(url: str, error_message: str, status_code: int = -1) -> PageContent:
    """创建失败页面的内容对象"""
    return PageContent(
        url=url,
        title="",
        text_content="",
        status_code=status_code,
        crawl_timestamp=datetime.now().isoformat(),
        error_message=error_message
    ) 