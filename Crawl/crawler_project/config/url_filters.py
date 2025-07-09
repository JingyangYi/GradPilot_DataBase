#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL过滤配置
定义需要排除和包含的URL模式，确保只爬取body中的相关链接
"""

import re
from typing import List, Pattern
from dataclasses import dataclass


@dataclass
class URLFilters:
    """URL过滤规则配置"""
    
    # 需要排除的URL模式 (header/footer/导航栏等)
    excluded_patterns: List[str] = None
    
    # 需要排除的域名关键词
    excluded_domains: List[str] = None
    
    # 只包含body中的相关链接选择器
    body_link_selectors: List[str] = None
    
    # 必须包含的URL关键词（相关性判断）
    required_keywords: List[str] = None
    
    def __post_init__(self):
        if self.excluded_patterns is None:
            self.excluded_patterns = [
                # 隐私政策和法律页面
                r'.*privacy.*',
                r'.*terms.*',
                r'.*legal.*',
                r'.*disclaimer.*',
                r'.*cookie.*',
                
                # 联系和关于页面
                r'.*contact.*',
                r'.*about.*',
                r'.*help.*',
                r'.*support.*',
                r'.*faq.*',
                
                # 社交媒体
                r'.*facebook.*',
                r'.*twitter.*',
                r'.*linkedin.*',
                r'.*instagram.*',
                r'.*youtube.*',
                r'.*github.*',
                
                # 登录注册
                r'.*login.*',
                r'.*register.*',
                r'.*signup.*',
                r'.*signin.*',
                r'.*logout.*',
                
                # 搜索和工具
                r'.*search.*',
                r'.*sitemap.*',
                r'.*rss.*',
                r'.*feed.*',
                
                # 文件下载
                r'.*\.pdf$',
                r'.*\.doc$',
                r'.*\.docx$',
                r'.*\.ppt$',
                r'.*\.pptx$',
                r'.*\.zip$',
                
                # 锚点和JavaScript
                r'^#.*',
                r'^javascript:.*',
                r'^mailto:.*',
                r'^tel:.*',
                r'^sms:.*',
                
                # 无关页面
                r'.*news.*',
                r'.*events.*',
                r'.*calendar.*',
                r'.*directory.*',
                r'.*staff.*',
                r'.*faculty.*(?!.*admission).*',  # 排除faculty但保留admission相关
                r'.*employment.*',
                r'.*careers.*',
                r'.*jobs.*',
                
                # 技术页面
                r'.*accessibility.*',
                r'.*site-map.*',
                r'.*print.*',
                r'.*share.*',
                
                # 多媒体
                r'.*gallery.*',
                r'.*photos.*',
                r'.*videos.*'
            ]
        
        if self.excluded_domains is None:
            self.excluded_domains = [
                'facebook.com',
                'twitter.com', 
                'linkedin.com',
                'instagram.com',
                'youtube.com',
                'github.com',
                'google.com',
                'microsoft.com'
            ]
        
        if self.body_link_selectors is None:
            self.body_link_selectors = [
                # 主要内容区域的链接
                'main a[href]',
                'article a[href]',
                '.content a[href]',
                '.main-content a[href]',
                '#main-content a[href]',
                
                # 专业相关区域
                '.program-details a[href]',
                '.program-info a[href]',
                '.admission-requirements a[href]',
                '.curriculum a[href]',
                '.course-description a[href]',
                
                # 学术区域
                '.academic a[href]',
                '.degree a[href]',
                '.major a[href]',
                '.department a[href]',
                '.school a[href]',
                '.college a[href]',
                
                # 申请相关
                '.apply a[href]',
                '.application a[href]',
                '.admissions a[href]',
                '.requirements a[href]',
                
                # 排除明显的导航区域
                'main a[href]:not(header a):not(footer a):not(nav a):not(.nav a)',
                'article a[href]:not(.social a):not(.share a)'
            ]
        
        if self.required_keywords is None:
            self.required_keywords = [
                # 学位相关
                'program', 'degree', 'major', 'course', 'curriculum',
                'admission', 'apply', 'application', 'requirement',
                'graduate', 'master', 'phd', 'doctoral',
                
                # 专业相关
                'data science', 'statistics', 'analytics', 'machine learning',
                'computer science', 'engineering', 'mathematics',
                
                # 学校结构
                'department', 'school', 'college', 'faculty',
                'academic', 'study', 'education'
            ]


class URLFilterProcessor:
    """URL过滤处理器"""
    
    def __init__(self, filters: URLFilters = None):
        self.filters = filters or URLFilters()
        # 编译正则表达式以提高性能
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.filters.excluded_patterns
        ]
    
    def should_exclude_url(self, url: str) -> bool:
        """
        判断URL是否应该被排除
        
        Args:
            url: 要检查的URL
            
        Returns:
            bool: True表示应该排除，False表示可以爬取
        """
        url_lower = url.lower()
        
        # 检查排除的域名
        for domain in self.filters.excluded_domains:
            if domain in url_lower:
                return True
        
        # 检查排除的模式
        for pattern in self.compiled_patterns:
            if pattern.search(url):
                return True
        
        return False
    
    def is_relevant_url(self, url: str, text_content: str = "") -> bool:
        """
        判断URL是否与专业相关
        
        Args:
            url: 要检查的URL
            text_content: 链接的文本内容
            
        Returns:
            bool: True表示相关，False表示不相关
        """
        combined_text = f"{url} {text_content}".lower()
        
        # 检查是否包含相关关键词
        for keyword in self.filters.required_keywords:
            if keyword.lower() in combined_text:
                return True
                
        return False
    
    def filter_links(self, links: List[dict]) -> List[dict]:
        """
        过滤链接列表
        
        Args:
            links: 包含URL和文本的链接列表 [{'url': str, 'text': str}, ...]
            
        Returns:
            List[dict]: 过滤后的链接列表
        """
        filtered_links = []
        
        for link in links:
            url = link.get('url', '')
            text = link.get('text', '')
            
            # 跳过排除的URL
            if self.should_exclude_url(url):
                continue
            
            # 只保留相关的URL
            if self.is_relevant_url(url, text):
                filtered_links.append(link)
        
        return filtered_links


# 默认过滤器实例
DEFAULT_URL_FILTERS = URLFilters()
DEFAULT_FILTER_PROCESSOR = URLFilterProcessor(DEFAULT_URL_FILTERS) 