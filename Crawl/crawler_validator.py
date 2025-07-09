#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫验证程序 - 根据爬虫方案文档实现
实现功能：
1. 按照方案定义的数据class结构
2. 递归爬虫（可设置深度）
3. 排除header/footer链接，只爬取body相关链接
4. 抓取交互内容（点击按钮等）
5. 保存页面快照
6. 错误处理与重试机制
7. 保存为JSON格式
8. 版本控制元数据
"""

import asyncio
import hashlib
import json
import os
import re
import uuid
import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup


# ================================
# 1. 数据结构定义（根据爬虫方案）
# ================================

@dataclass
class CrawlMetadata:
    """爬虫元数据，用于版本控制和追溯"""
    crawl_run_id: str
    crawl_time: str  # ISO 8601
    crawler_version: str
    max_depth: int
    success: bool
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class PageNode:
    """页面节点数据结构"""
    url: str
    parent_url: Optional[str]
    depth: int
    html: str
    text: str
    status_code: int
    content_type: str
    crawl_metadata: CrawlMetadata
    snapshot_path: Optional[str] = None  # 页面快照保存路径
    extracted_links: List[str] = field(default_factory=list)  # 从body提取的相关链接
    interactive_content: Dict[str, Any] = field(default_factory=dict)  # 交互内容（点击后显示）
    children: List["PageNode"] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于JSON序列化"""
        return {
            'url': self.url,
            'parent_url': self.parent_url,
            'depth': self.depth,
            'html': self.html,
            'text': self.text,
            'status_code': self.status_code,
            'content_type': self.content_type,
            'crawl_metadata': {
                'crawl_run_id': self.crawl_metadata.crawl_run_id,
                'crawl_time': self.crawl_metadata.crawl_time,
                'crawler_version': self.crawl_metadata.crawler_version,
                'max_depth': self.crawl_metadata.max_depth,
                'success': self.crawl_metadata.success,
                'error_message': self.crawl_metadata.error_message,
                'retry_count': self.crawl_metadata.retry_count
            },
            'snapshot_path': self.snapshot_path,
            'extracted_links': self.extracted_links,
            'interactive_content': self.interactive_content,
            'children': [child.to_dict() for child in self.children]
        }


# ================================
# 2. 爬虫约束配置
# ================================

class CrawlConstraints:
    """爬虫约束配置"""
    def __init__(self, max_depth: int = 2):
        self.max_depth = max_depth
        
        # 排除的URL模式（header/footer/导航栏等）
        self.excluded_patterns = [
            r'.*privacy.*',
            r'.*terms.*', 
            r'.*contact.*',
            r'.*about.*',
            r'.*facebook.*',
            r'.*twitter.*',
            r'.*linkedin.*',
            r'.*instagram.*',
            r'.*search.*',
            r'.*login.*',
            r'.*register.*',
            r'#.*',  # 锚点链接
            r'javascript:.*',
            r'mailto:.*',
            r'tel:.*',
            r'.*\.pdf$',  # PDF文件
            r'.*\.jpg$',  # 图片文件
            r'.*\.png$',
            r'.*\.gif$',
        ]
        
        # 只爬取body中的相关链接的CSS选择器
        self.body_selectors = [
            'main a[href]',
            'article a[href]', 
            '.content a[href]',
            '#main-content a[href]',
            '.program-details a[href]',
            '.admission-requirements a[href]',
            '.curriculum a[href]',
            '.course-list a[href]',
            'section a[href]',  # 通用section区域
            '.main a[href]',    # 主要内容区域
        ]


# ================================
# 3. 错误处理类
# ================================

class CrawlError:
    """爬虫错误分类"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error" 
    PERMISSION_ERROR = "permission_error"
    CONTENT_ERROR = "content_error"
    UNKNOWN_ERROR = "unknown_error"


# ================================
# 4. 爬虫核心类
# ================================

class WebCrawler:
    """网页爬虫主类"""
    
    def __init__(self, constraints: CrawlConstraints, output_dir: str = "crawl_output"):
        self.constraints = constraints
        self.output_dir = output_dir
        self.crawl_run_id = str(uuid.uuid4())
        self.crawler_version = "1.0.0"
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/snapshots", exist_ok=True)
        
        # 已访问的URL集合，避免重复爬取
        self.visited_urls = set()
        
    async def save_page_snapshot(self, page: Page, url: str) -> Optional[str]:
        """保存页面快照"""
        try:
            # 生成文件名（URL hash）
            url_hash = hashlib.md5(url.encode()).hexdigest()
            snapshot_path = f"{self.output_dir}/snapshots/{url_hash}.png"
            
            # 截取完整页面截图
            await page.screenshot(path=snapshot_path, full_page=True)
            print(f"✓ 快照已保存: {url} -> {snapshot_path}")
            
            return snapshot_path
        except Exception as e:
            print(f"✗ 快照保存失败 {url}: {e}")
            return None
    
    async def extract_interactive_content(self, page: Page) -> Dict[str, Any]:
        """抓取交互式内容"""
        interactive_data = {}
        
        try:
            # 1. 点击所有可点击元素获取隐藏内容
            clickable_selectors = [
                'button:not([disabled])',
                '.expandable', 
                '.collapsible', 
                '[data-toggle]', 
                '.tab:not(.active)',
                '.accordion-header',
                '.toggle-button',
                '[role="button"]'
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for i, element in enumerate(elements[:3]):  # 限制数量避免过度点击
                        try:
                            # 检查元素是否可见
                            is_visible = await element.is_visible()
                            if not is_visible:
                                continue
                                
                            # 点击元素
                            await element.click()
                            await page.wait_for_timeout(1000)  # 等待内容加载
                            
                            # 获取点击后的内容
                            content = await page.content()
                            key = f"clicked_{selector.replace(':', '_')}_{i}"
                            interactive_data[key] = content
                            
                        except Exception as e:
                            print(f"  点击元素失败 {selector}[{i}]: {e}")
                            continue
                            
                except Exception as e:
                    print(f"  查找元素失败 {selector}: {e}")
                    continue
            
            # 2. 处理Tab切换
            try:
                tabs = await page.query_selector_all('.tab, [role="tab"], .nav-tab')
                for i, tab in enumerate(tabs[:5]):  # 限制Tab数量
                    try:
                        is_visible = await tab.is_visible()
                        if not is_visible:
                            continue
                            
                        await tab.click()
                        await page.wait_for_timeout(500)
                        content = await page.content()
                        interactive_data[f"tab_{i}"] = content
                        
                    except Exception as e:
                        print(f"  Tab切换失败 [{i}]: {e}")
                        continue
                        
            except Exception as e:
                print(f"  Tab处理失败: {e}")
            
            print(f"✓ 交互内容抓取完成，获得 {len(interactive_data)} 个交互状态")
            
        except Exception as e:
            print(f"✗ 交互内容抓取失败: {e}")
            
        return interactive_data
    
    def should_exclude_url(self, url: str) -> bool:
        """检查URL是否应该被排除"""
        for pattern in self.constraints.excluded_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False
    
    async def extract_body_links(self, page: Page, base_url: str) -> List[str]:
        """提取body中的相关链接"""
        links = []
        
        try:
            # 使用多个选择器提取链接
            for selector in self.constraints.body_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        href = await element.get_attribute('href')
                        if href:
                            # 转换为绝对URL
                            absolute_url = urljoin(base_url, href)
                            
                            # 检查是否应该排除
                            if not self.should_exclude_url(absolute_url):
                                # 确保是同域名或相关域名
                                if self.is_relevant_domain(absolute_url, base_url):
                                    links.append(absolute_url)
                                    
                except Exception as e:
                    print(f"  提取链接失败 {selector}: {e}")
                    continue
                    
        except Exception as e:
            print(f"✗ 链接提取失败: {e}")
        
        # 去重并限制数量
        unique_links = list(set(links))[:10]  # 限制每页最多10个链接
        print(f"✓ 提取到 {len(unique_links)} 个相关链接")
        
        return unique_links
    
    def is_relevant_domain(self, url: str, base_url: str) -> bool:
        """检查URL是否为相关域名"""
        try:
            url_domain = urlparse(url).netloc.lower()
            base_domain = urlparse(base_url).netloc.lower()
            
            # 同域名或子域名
            return url_domain == base_domain or url_domain.endswith(f'.{base_domain}')
            
        except Exception:
            return False
    
    def create_failed_node(self, url: str, parent_url: Optional[str], depth: int, 
                          error_type: str, error_msg: str) -> PageNode:
        """创建失败节点"""
        metadata = CrawlMetadata(
            crawl_run_id=self.crawl_run_id,
            crawl_time=datetime.utcnow().isoformat(),
            crawler_version=self.crawler_version,
            max_depth=self.constraints.max_depth,
            success=False,
            error_message=f"{error_type}: {error_msg}"
        )
        
        return PageNode(
            url=url,
            parent_url=parent_url,
            depth=depth,
            html="",
            text=f"CRAWL_FAILED: {error_msg}",
            status_code=-1,
            content_type="error",
            crawl_metadata=metadata
        )
    
    async def crawl_page(self, page: Page, url: str, parent_url: Optional[str], depth: int) -> PageNode:
        """爬取单个页面"""
        print(f"{'  ' * depth}爬取页面 (深度 {depth}): {url}")
        
        # 检查是否已访问过
        if url in self.visited_urls:
            print(f"{'  ' * depth}跳过已访问的URL: {url}")
            return self.create_failed_node(url, parent_url, depth, CrawlError.CONTENT_ERROR, "URL already visited")
        
        self.visited_urls.add(url)
        
        try:
            # 访问页面
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            
            if not response:
                raise Exception("无法获取页面响应")
                
            status_code = response.status
            
            # 检查状态码
            if status_code >= 400:
                raise Exception(f"HTTP错误: {status_code}")
            
            # 等待页面加载完成
            await page.wait_for_load_state('networkidle')
            
            # 抓取基础内容
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text("\n", strip=True)
            
            print(f"{'  ' * depth}✓ 基础内容抓取完成 ({len(text)} 字符)")
            
            # 抓取交互内容
            print(f"{'  ' * depth}开始抓取交互内容...")
            interactive_content = await self.extract_interactive_content(page)
            
            # 保存快照
            print(f"{'  ' * depth}保存页面快照...")
            snapshot_path = await self.save_page_snapshot(page, url)
            
            # 提取body中的相关链接
            print(f"{'  ' * depth}提取相关链接...")
            extracted_links = await self.extract_body_links(page, url)
            
            # 创建元数据
            metadata = CrawlMetadata(
                crawl_run_id=self.crawl_run_id,
                crawl_time=datetime.utcnow().isoformat(),
                crawler_version=self.crawler_version,
                max_depth=self.constraints.max_depth,
                success=True
            )
            
            # 创建页面节点
            node = PageNode(
                url=url,
                parent_url=parent_url,
                depth=depth,
                html=html,
                text=text,
                status_code=status_code,
                content_type=response.headers.get('content-type', 'text/html'),
                crawl_metadata=metadata,
                snapshot_path=snapshot_path,
                extracted_links=extracted_links,
                interactive_content=interactive_content
            )
            
            # 递归抓取子页面
            if depth < self.constraints.max_depth and extracted_links:
                print(f"{'  ' * depth}开始递归抓取子页面...")
                for link in extracted_links[:3]:  # 限制子链接数量
                    try:
                        child_node = await self.crawl_page(page, link, url, depth + 1)
                        node.children.append(child_node)
                    except Exception as e:
                        print(f"{'  ' * depth}子页面爬取失败 {link}: {e}")
                        error_node = self.create_failed_node(link, url, depth + 1, CrawlError.UNKNOWN_ERROR, str(e))
                        node.children.append(error_node)
            
            print(f"{'  ' * depth}✓ 页面爬取完成: {url}")
            return node
            
        except Exception as e:
            print(f"{'  ' * depth}✗ 页面爬取失败 {url}: {e}")
            return self.create_failed_node(url, parent_url, depth, CrawlError.UNKNOWN_ERROR, str(e))
    
    async def crawl_project(self, start_url: str, project_id: str) -> Dict[str, Any]:
        """爬取单个项目"""
        print(f"\n开始爬取项目: {project_id}")
        print(f"起始URL: {start_url}")
        print(f"最大深度: {self.constraints.max_depth}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 设置用户代理
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            try:
                # 开始爬取
                root_node = await self.crawl_page(page, start_url, None, 0)
                
                # 转换为字典格式
                project_data = {
                    'project_id': project_id,
                    'crawl_run_id': self.crawl_run_id,
                    'start_url': start_url,
                    'crawl_time': datetime.utcnow().isoformat(),
                    'crawler_version': self.crawler_version,
                    'max_depth': self.constraints.max_depth,
                    'root_node': root_node.to_dict()
                }
                
                return project_data
                
            finally:
                await browser.close()
    
    def save_project_data(self, project_data: Dict[str, Any]) -> str:
        """保存项目数据为JSON"""
        project_id = project_data['project_id']
        crawl_run_id = project_data['crawl_run_id']
        
        # 保存主要数据
        json_file = f"{self.output_dir}/project_{project_id}_{crawl_run_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        # 保存元数据
        metadata = {
            'project_id': project_id,
            'crawl_run_id': crawl_run_id,
            'crawl_time': project_data['crawl_time'],
            'crawler_version': project_data['crawler_version'],
            'max_depth': project_data['max_depth'],
            'start_url': project_data['start_url']
        }
        
        metadata_file = f"{self.output_dir}/metadata_{crawl_run_id}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 项目数据已保存: {json_file}")
        print(f"✓ 元数据已保存: {metadata_file}")
        
        return json_file


# ================================
# 5. 失败URL重试功能
# ================================

def extract_failed_urls(json_data: Dict) -> List[str]:
    """从JSON数据中提取爬虫失败的URL"""
    failed_urls = []
    
    def traverse_node(node_data):
        crawl_metadata = node_data.get('crawl_metadata', {})
        if not crawl_metadata.get('success', True):
            failed_urls.append(node_data['url'])
        
        for child in node_data.get('children', []):
            traverse_node(child)
    
    if 'root_node' in json_data:
        traverse_node(json_data['root_node'])
    
    return failed_urls


async def retry_failed_urls(failed_urls: List[str], constraints: CrawlConstraints, max_retries: int = 2):
    """重新爬取失败的URL"""
    print(f"\n开始重试失败的URL ({len(failed_urls)} 个)...")
    
    crawler = WebCrawler(constraints)
    retry_results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            for url in failed_urls:
                print(f"\n重试URL: {url}")
                for attempt in range(max_retries):
                    try:
                        result = await crawler.crawl_page(page, url, None, 0)
                        if result.crawl_metadata.success:
                            retry_results[url] = result.to_dict()
                            print(f"✓ 重试成功: {url}")
                            break
                        else:
                            print(f"✗ 重试失败 (尝试 {attempt + 1}): {url}")
                    except Exception as e:
                        print(f"✗ 重试异常 (尝试 {attempt + 1}): {url} - {e}")
                        if attempt == max_retries - 1:
                            retry_results[url] = crawler.create_failed_node(
                                url, None, 0, CrawlError.UNKNOWN_ERROR, str(e)
                            ).to_dict()
        finally:
            await browser.close()
    
    return retry_results


# ================================
# 6. 主程序
# ================================

async def main():
    """主程序 - 验证爬虫功能"""
    print("=" * 60)
    print("爬虫验证程序启动")
    print("=" * 60)
    
    # 读取CSV文件
    try:
        df = pd.read_csv('24-25美研数据科学与应用数据科学专业查校表.csv')
        print(f"✓ 成功读取CSV文件，共 {len(df)} 行数据")
    except Exception as e:
        print(f"✗ 读取CSV文件失败: {e}")
        return
    
    # 获取前3个有效的专业网址进行测试
    test_urls = []
    for idx, row in df.head(10).iterrows():  # 检查前10行
        url = row.get('专业网址', '')
        if url and isinstance(url, str) and url.startswith('http'):
            test_urls.append({
                'project_id': f"{row.get('大学英文名称', 'Unknown')}_{idx}".replace(' ', '_'),
                'url': url,
                'university': row.get('大学名称', 'Unknown'),
                'program': row.get('专业中文名称', 'Unknown')
            })
            if len(test_urls) >= 3:  # 只测试3个项目
                break
    
    if not test_urls:
        print("✗ 未找到有效的专业网址")
        return
    
    print(f"✓ 找到 {len(test_urls)} 个测试URL")
    
    # 设置爬虫约束
    constraints = CrawlConstraints(max_depth=2)  # 设置最大深度为2
    crawler = WebCrawler(constraints)
    
    # 开始爬取测试
    for i, test_data in enumerate(test_urls):
        print(f"\n{'='*40}")
        print(f"测试 {i+1}/{len(test_urls)}")
        print(f"大学: {test_data['university']}")
        print(f"专业: {test_data['program']}")
        print(f"URL: {test_data['url']}")
        print(f"{'='*40}")
        
        try:
            # 爬取项目
            project_data = await crawler.crawl_project(
                test_data['url'], 
                test_data['project_id']
            )
            
            # 保存数据
            json_file = crawler.save_project_data(project_data)
            
            # 检查失败的URL并尝试重试
            failed_urls = extract_failed_urls(project_data)
            if failed_urls:
                print(f"\n发现 {len(failed_urls)} 个失败的URL，开始重试...")
                retry_results = await retry_failed_urls(failed_urls, constraints)
                
                # 保存重试结果
                retry_file = f"{crawler.output_dir}/retry_results_{project_data['crawl_run_id']}.json"
                with open(retry_file, 'w', encoding='utf-8') as f:
                    json.dump(retry_results, f, ensure_ascii=False, indent=2)
                print(f"✓ 重试结果已保存: {retry_file}")
            
            print(f"\n✓ 项目 {test_data['project_id']} 爬取完成")
            
        except Exception as e:
            print(f"\n✗ 项目 {test_data['project_id']} 爬取失败: {e}")
    
    print(f"\n{'='*60}")
    print("爬虫验证程序完成")
    print(f"结果保存在: {crawler.output_dir}/")
    print("- JSON数据文件: project_*.json")
    print("- 元数据文件: metadata_*.json") 
    print("- 页面快照: snapshots/*.png")
    print("- 重试结果: retry_results_*.json")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main()) 