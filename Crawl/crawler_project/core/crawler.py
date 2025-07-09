#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主爬虫引擎
实现稳定的递归爬虫，集成所有配置和工具模块
"""

import asyncio
import os
import hashlib
import json
from urllib.parse import urljoin, urlparse
from typing import List, Optional, Dict, Any
from datetime import datetime

# Playwright imports
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# 本地模块导入
from crawler_project.config.crawler_config import CrawlerConfig, StabilityConfig, InteractionConfig
from crawler_project.config.url_filters import URLFilterProcessor
from crawler_project.utils.text_extractor import TextExtractor
from crawler_project.utils.retry_utils import RetryManager, retry_on_network_error
from crawler_project.core.data_models import (
    ProjectInfo, CrawlMetadata, PageContent, CrawlNode, 
    CrawlResult, create_failed_page_content
)


class WebCrawler:
    """主爬虫类 - 集成所有功能模块"""
    
    def __init__(
        self,
        crawler_config: CrawlerConfig = None,
        stability_config: StabilityConfig = None,
        interaction_config: InteractionConfig = None,
        url_filter: URLFilterProcessor = None,
        text_extractor: TextExtractor = None
    ):
        # 配置初始化
        self.crawler_config = crawler_config or CrawlerConfig()
        self.stability_config = stability_config or StabilityConfig()
        self.interaction_config = interaction_config or InteractionConfig()
        
        # 工具初始化
        self.url_filter = url_filter or URLFilterProcessor()
        self.text_extractor = text_extractor or TextExtractor()
        self.retry_manager = RetryManager()
        
        # 状态追踪
        self.visited_urls = set()
        self.failed_urls = []
        self.total_pages_crawled = 0
        
        # Playwright实例
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def crawl_project(
        self,
        start_url: str,
        project_info: ProjectInfo,
        max_depth: Optional[int] = None
    ) -> CrawlResult:
        """
        爬取整个项目
        
        Args:
            start_url: 起始URL
            project_info: 项目信息
            max_depth: 最大深度（覆盖配置）
            
        Returns:
            CrawlResult: 完整的爬虫结果
        """
        print(f"开始爬取项目: {project_info.university_name} - {project_info.program_name}")
        print(f"起始URL: {start_url}")
        
        # 重置状态
        self.visited_urls.clear()
        self.failed_urls.clear()
        self.total_pages_crawled = 0
        
        # 确定最大深度
        actual_max_depth = max_depth or self.crawler_config.max_depth
        
        try:
            # 初始化浏览器
            await self._init_browser()
            
            # 创建根节点
            root_content = await self._crawl_page(start_url, 0)
            root_node = CrawlNode(
                depth=0,
                parent_url=None,
                content=root_content
            )
            
            # 递归爬取子页面
            if root_content.error_message is None:
                await self._crawl_children(root_node, actual_max_depth)
            
            # 创建元数据
            metadata = CrawlMetadata(
                crawl_run_id="",  # 将在__post_init__中生成
                crawl_time="",    # 将在__post_init__中生成
                crawler_version="2.0.0",
                max_depth=actual_max_depth,
                total_pages_crawled=self.total_pages_crawled,
                failed_pages=len(self.failed_urls),
                success=len(self.failed_urls) == 0
            )
            
            # 创建完整结果
            result = CrawlResult(
                project_info=project_info,
                metadata=metadata,
                root_node=root_node
            )
            
            print(f"爬取完成: 总页面 {self.total_pages_crawled}, 失败 {len(self.failed_urls)}")
            return result
            
        finally:
            await self._cleanup_browser()
    
    async def _init_browser(self):
        """初始化浏览器和上下文"""
        self.playwright = await async_playwright().start()
        
        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=self.crawler_config.headless,
            timeout=self.crawler_config.navigation_timeout
        )
        
        # 创建上下文
        self.context = await self.browser.new_context(
            viewport={
                'width': self.crawler_config.viewport_width,
                'height': self.crawler_config.viewport_height
            },
            user_agent=self.crawler_config.user_agent
        )
        
        # 设置请求拦截（提高性能）
        if self.stability_config.enable_request_interception:
            await self.context.route("**/*", self._intercept_request)
    
    async def _intercept_request(self, route, request):
        """拦截请求，阻止不必要的资源加载"""
        resource_type = request.resource_type
        
        if resource_type in self.stability_config.block_resources:
            await route.abort()
        else:
            await route.continue_()
    
    async def _cleanup_browser(self):
        """清理浏览器资源"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def _crawl_page(self, url: str, depth: int) -> PageContent:
        """
        爬取单个页面
        
        Args:
            url: 页面URL
            depth: 当前深度
            
        Returns:
            PageContent: 页面内容
        """
        if url in self.visited_urls:
            return create_failed_page_content(url, "URL已访问过")
        
        self.visited_urls.add(url)
        self.total_pages_crawled += 1
        
        print(f"[深度{depth}] 爬取: {url}")
        
        try:
            # 使用重试机制爬取页面
            return await retry_on_network_error(
                self._fetch_page_content, url, max_retries=self.crawler_config.max_retries
            )
            
        except Exception as e:
            error_msg = f"页面爬取失败: {str(e)}"
            self.failed_urls.append(url)
            return create_failed_page_content(url, error_msg)
    
    async def _fetch_page_content(self, url: str) -> PageContent:
        """
        获取页面内容 - 具体的爬取逻辑
        
        Args:
            url: 页面URL
            
        Returns:
            PageContent: 页面内容
        """
        page = await self.context.new_page()
        
        try:
            # 设置超时
            page.set_default_timeout(self.crawler_config.timeout * 1000)
            
            # 导航到页面
            response = await page.goto(
                url,
                wait_until=self.crawler_config.wait_for_load_state,
                timeout=self.crawler_config.navigation_timeout
            )
            
            # 检查响应状态
            if response and response.status >= 400:
                raise Exception(f"HTTP错误: {response.status}")
            
            # 等待页面完全加载
            await page.wait_for_load_state('networkidle')
            
            # 获取HTML内容
            html_content = await page.content()
            
            # 提取页面标题
            title = self.text_extractor.extract_title(html_content)
            
            # 提取文本内容
            text_content = self.text_extractor.extract_clean_text(html_content)
            
            # 处理交互元素
            interactive_text = await self._handle_interactive_elements(page)
            
            # 提取相关链接
            extracted_links = self._extract_relevant_links(html_content, url)
            
            # 创建页面内容对象
            page_content = PageContent(
                url=url,
                title=title,
                text_content=text_content,
                status_code=response.status if response else 200,
                crawl_timestamp=datetime.now().isoformat(),
                interactive_text=interactive_text,
                extracted_links=extracted_links
            )
            
            return page_content
            
        except Exception as e:
            # 确保页面关闭
            if not page.is_closed():
                await page.close()
            raise e
        else:
            # 正常完成时关闭页面
            if not page.is_closed():
                await page.close()
    
    async def _handle_interactive_elements(self, page: Page) -> Dict[str, str]:
        """
        处理页面中的交互元素
        
        Args:
            page: Playwright页面对象
            
        Returns:
            Dict[str, str]: 交互内容 {action: text_content}
        """
        interactive_content = {}
        interaction_count = 0
        max_interactions = self.interaction_config.max_interactions_per_page
        
        try:
            # 检查页面是否仍然有效
            if page.is_closed():
                return interactive_content
            
            # 检查上下文是否仍然有效
            if self.context is None:
                return interactive_content
                
            # 处理可点击元素
            for selector in self.interaction_config.clickable_selectors:
                if interaction_count >= max_interactions:
                    break
                
                try:
                    elements = await page.query_selector_all(selector)
                    
                    for i, element in enumerate(elements):
                        if interaction_count >= max_interactions:
                            break
                        
                        try:
                            # 检查页面是否仍然有效
                            if page.is_closed():
                                return interactive_content
                                
                            # 检查元素是否可见和可点击
                            if await element.is_visible() and await element.is_enabled():
                                # 获取点击前的内容
                                before_content = await page.content()
                                
                                # 点击元素
                                await element.click(timeout=self.interaction_config.click_timeout)
                                
                                # 等待内容变化
                                await page.wait_for_timeout(self.interaction_config.after_click_wait)
                                
                                # 获取点击后的内容
                                after_content = await page.content()
                                
                                # 提取新增的文本内容
                                if after_content != before_content:
                                    new_text = self.text_extractor.extract_clean_text(after_content)
                                    action_key = f"click_{selector}_{i}"
                                    interactive_content[action_key] = new_text
                                    interaction_count += 1
                                
                        except Exception as e:
                            # 忽略页面关闭的错误
                            if "closed" not in str(e).lower():
                                print(f"交互元素处理失败 {selector}[{i}]: {e}")
                            continue
                
                except Exception as e:
                    # 忽略页面关闭的错误
                    if "closed" not in str(e).lower():
                        print(f"选择器处理失败 {selector}: {e}")
                    continue
            
            # 处理Tab元素
            for selector in self.interaction_config.tab_selectors:
                if interaction_count >= max_interactions:
                    break
                
                try:
                    # 检查页面是否仍然有效
                    if page.is_closed():
                        return interactive_content
                        
                    tabs = await page.query_selector_all(selector)
                    for i, tab in enumerate(tabs):
                        if interaction_count >= max_interactions:
                            break
                        
                        try:
                            # 检查页面是否仍然有效
                            if page.is_closed():
                                return interactive_content
                                
                            if await tab.is_visible():
                                await tab.click()
                                await page.wait_for_timeout(self.interaction_config.after_click_wait)
                                
                                content = await page.content()
                                text = self.text_extractor.extract_clean_text(content)
                                action_key = f"tab_{selector}_{i}"
                                interactive_content[action_key] = text
                                interaction_count += 1
                                
                        except Exception as e:
                            # 忽略页面关闭的错误
                            if "closed" not in str(e).lower():
                                print(f"Tab处理失败 {selector}[{i}]: {e}")
                            continue
                
                except Exception as e:
                    # 忽略页面关闭的错误
                    if "closed" not in str(e).lower():
                        print(f"Tab选择器处理失败 {selector}: {e}")
                    continue
        
        except Exception as e:
            print(f"交互元素处理总体失败: {e}")
        
        return interactive_content
    
    def _extract_relevant_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """
        提取相关链接
        
        Args:
            html: HTML内容
            base_url: 基准URL
            
        Returns:
            List[Dict[str, str]]: 链接列表
        """
        # 提取所有链接
        raw_links = self.text_extractor.extract_links_with_text(
            html, self.url_filter.filters.body_link_selectors
        )
        
        # 转换为绝对URL并过滤
        processed_links = []
        for link in raw_links:
            try:
                absolute_url = urljoin(base_url, link['url'])
                
                # 使用URL过滤器过滤
                if not self.url_filter.should_exclude_url(absolute_url):
                    if self.url_filter.is_relevant_url(absolute_url, link['text']):
                        processed_links.append({
                            'url': absolute_url,
                            'text': link['text']
                        })
            
            except Exception as e:
                print(f"链接处理失败 {link['url']}: {e}")
                continue
        
        return processed_links
    
    async def _crawl_children(self, parent_node: CrawlNode, max_depth: int):
        """
        递归爬取子页面
        
        Args:
            parent_node: 父节点
            max_depth: 最大深度
        """
        if parent_node.depth >= max_depth:
            return
        
        child_depth = parent_node.depth + 1
        
        # 限制每层的子页面数量
        max_children_per_level = 5
        child_links = parent_node.content.extracted_links[:max_children_per_level]
        
        for link in child_links:
            child_url = link['url']
            
            if child_url in self.visited_urls:
                continue
            
            # 添加延迟避免过于频繁的请求
            await asyncio.sleep(self.crawler_config.delay_between_requests)
            
            # 爬取子页面
            child_content = await self._crawl_page(child_url, child_depth)
            child_node = CrawlNode(
                depth=child_depth,
                parent_url=parent_node.content.url,
                content=child_content
            )
            
            parent_node.children.append(child_node)
            
            # 递归爬取子页面的子页面
            if child_content.error_message is None:
                await self._crawl_children(child_node, max_depth)
    
    async def save_result(self, result: CrawlResult, output_dir: str = None) -> str:
        """
        保存爬虫结果到JSON文件
        
        Args:
            result: 爬虫结果
            output_dir: 输出目录
            
        Returns:
            str: 保存的文件路径
        """
        output_dir = output_dir or self.crawler_config.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        filename = result.project_info.get_filename()
        file_path = os.path.join(output_dir, filename)
        
        # 保存JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {file_path}")
        return file_path
    
    def extract_failed_urls(self, result: CrawlResult) -> List[str]:
        """提取失败的URL列表"""
        return result.get_all_failed_urls()
    
    async def retry_failed_urls(self, failed_urls: List[str]) -> Dict[str, PageContent]:
        """
        重试失败的URL
        
        Args:
            failed_urls: 失败的URL列表
            
        Returns:
            Dict[str, PageContent]: 重试结果
        """
        retry_results = {}
        
        if not failed_urls:
            return retry_results
        
        print(f"开始重试 {len(failed_urls)} 个失败的URL...")
        
        try:
            await self._init_browser()
            
            for url in failed_urls:
                print(f"重试: {url}")
                try:
                    content = await self._fetch_page_content(url)
                    retry_results[url] = content
                    
                    # 添加延迟
                    await asyncio.sleep(self.crawler_config.delay_between_requests)
                    
                except Exception as e:
                    print(f"重试失败 {url}: {e}")
                    retry_results[url] = create_failed_page_content(url, f"重试失败: {str(e)}")
        
        finally:
            await self._cleanup_browser()
        
        return retry_results 