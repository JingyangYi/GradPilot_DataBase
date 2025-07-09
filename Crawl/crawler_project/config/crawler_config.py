#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫配置文件
包含爬虫运行的所有配置参数
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class CrawlerConfig:
    """爬虫主要配置"""
    
    # 基础配置
    max_depth: int = 2  # 最大递归深度
    timeout: int = 30  # 页面加载超时时间（秒）
    delay_between_requests: float = 1.0  # 请求间隔（秒）
    max_retries: int = 3  # 最大重试次数
    
    # 浏览器配置
    headless: bool = True  # 是否无头模式
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    # 网络稳定性配置
    wait_for_load_state: str = "networkidle"  # 等待网络空闲
    wait_for_timeout: int = 10000  # 等待超时（毫秒）
    navigation_timeout: int = 30000  # 导航超时（毫秒）
    
    # 输出配置
    output_dir: str = "output"
    save_html: bool = False  # 是否保存原始HTML
    enable_snapshots: bool = True  # 是否启用页面快照


@dataclass
class StabilityConfig:
    """稳定性配置"""
    enable_request_interception: bool = True
    block_resources: List[str] = None
    
    def __post_init__(self):
        if self.block_resources is None:
            self.block_resources = ['image', 'stylesheet', 'font', 'media']


@dataclass
class InteractionConfig:
    """交互配置"""
    max_interactions_per_page: int = 10
    click_timeout: int = 5000
    after_click_wait: int = 2000
    
    clickable_selectors: List[str] = None
    tab_selectors: List[str] = None
    
    def __post_init__(self):
        if self.clickable_selectors is None:
            self.clickable_selectors = [
                'button:not([disabled])',
                '[data-toggle]',
                '.btn:not(.disabled)',
                '[role="button"]:not(.disabled)',
                'a[href="#"]'
            ]
        
        if self.tab_selectors is None:
            self.tab_selectors = [
                '[role="tab"]',
                '.tab',
                '.nav-tab'
            ]


# 默认配置实例
DEFAULT_CRAWLER_CONFIG = CrawlerConfig()
DEFAULT_STABILITY_CONFIG = StabilityConfig()
DEFAULT_INTERACTION_CONFIG = InteractionConfig() 