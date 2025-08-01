import scrapy
import csv
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from ..url_filter import filter_url
from ..items import ProgramPageItem

# =============================================================================
# ProgramSpider — GradPilot 定制爬虫
# -----------------------------------------------------------------------------
# 功能概览
#   1. 逐个“项目(project)”顺序爬取：每个项目代表一条 CSV 记录（包含 UUID、项目
#      名称、根 URL 等）。根页面 + 同域名且锚文本/URL 包含白名单关键词的若干子
#      页面（深度≤1）会被抓取。
#   2. 手动请求计数(request_counters) + spider_idle 信号：避免同时调度成百上千个
#      请求导致 DEPTH_LIMIT 或并发压力；当前项目全部完成后再启动下一个项目。
#   3. 全局去重策略：使用 per-project 的 seen_urls 集合自行去重，并统一给所有新的
#      Request 加 `dont_filter=True`，从而保证 “计数器 == 实际排队请求数”。
#   4. 稳健的错误处理：errback → handle_error() 会即时递减计数并在计数归零时直接
#      调用 complete_project()，保证无论成功还是失败都能正确收尾并解锁下一个项目。
#
# 维护者须知
#   • 如果要修改链接白名单，请查看 crawl/program_crawler/url_filter.py
#   • 若需调节并发/深度等爬虫设置，可在 crawl/run_crawler.py 或 settings.py 修改。
#   • 计数器 / seen_urls / dont_filter 三者必须保持一致，否则爬虫会再次出现“剩余请求
#     != 实际请求”而提前关闭的问题。
# =============================================================================


class ProgramSpider(scrapy.Spider):
    name = 'program_spider'
    allowed_domains = []
    # ------------------------------------------------------------------
    # 处理非 200 状态码（如 403/429/503）
    # ------------------------------------------------------------------
    # Scrapy 默认对 400+ 状态码触发 HttpErrorMiddleware 并进入 errback。
    # 这些高校站点常因防爬或限流返回 403 / 429 / 503，但页面仍然包含可解析的
    # HTML 内容。将其加入允许列表后，相关响应会直接进入 `parse_page` 回调，
    # 不会被当作失败请求提前终止。

    # 告诉 HttpErrorMiddleware：这些状态码不算错误
    custom_settings = {
        'HTTPERROR_ALLOWED_CODES': [403, 429, 503],
    }

    # 同时在 spider 级别声明，确保所有请求继承
    handle_httpstatus_list = [403, 429, 503]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """自定义构造函数，用于注册 spider_idle 信号处理器"""
        spider = super(ProgramSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider
    
    def __init__(self, csv_file='program_urls.csv', *args, **kwargs):
        super(ProgramSpider, self).__init__(*args, **kwargs)
        
        self.csv_file = csv_file
        self.project_queue = []
        self.current_project = None
        self.current_project_id = None
        self.request_counters = {}
        self.project_data = {}
        
        self.total_projects = 0
        self.completed_projects = 0
        self.failed_projects = 0
        self.is_processing_project = False
        
        self.load_projects()
        
    def load_projects(self):
        """从CSV文件加载项目列表"""
        # 向上两级目录到crawl文件夹，然后加上csv文件名
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.csv_file)
        
        self.logger.info(f"尝试加载CSV文件: {csv_path}")
        self.logger.info(f"文件是否存在: {os.path.exists(csv_path)}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    project = {
                        'id': row['id'],
                        'name': row['program_name'],
                        'url': row['program_url'],
                        'source_file': row['source_file']
                    }
                    self.project_queue.append(project)
                    
                    domain = urlparse(project['url']).netloc
                    if domain not in self.allowed_domains:
                        self.allowed_domains.append(domain)
                        
            self.total_projects = len(self.project_queue)
            self.logger.info("\n" + "="*80)
            self.logger.info(f"成功加载 {self.total_projects} 个项目")
            self.logger.info(f"允许的域名: {self.allowed_domains}")
            self.logger.info("将按顺序逐个项目进行爬取")
            self.logger.info("="*80)
            
        except Exception as e:
            self.logger.error(f"加载CSV文件失败: {e}")
            
    def start_requests(self):
        """开始第一个项目的爬取，其他项目将在前一个完成后依次启动"""
        if self.project_queue:
            return self.start_next_project()
        return []
            
    def start_next_project(self):
        """启动下一个项目的爬取"""
        if not self.project_queue:
            self.logger.info("\n" + "="*50)
            self.logger.info("所有项目已完成")
            self.logger.info("="*50)
            return []
            
        if self.is_processing_project:
            self.logger.warning("当前正在处理项目，跳过启动新项目")
            return []
            
        self.current_project = self.project_queue.pop(0)
        project_id = self.current_project['id']
        self.current_project_id = project_id
        self.is_processing_project = True
        
        self.request_counters[project_id] = 0
        self.project_data[project_id] = {
            'project_id': project_id,
            'program_name': self.current_project['name'],
            'source_file': self.current_project['source_file'],
            'root_url': self.current_project['url'],
            'crawl_time': datetime.now().isoformat(),
            'pages': [],
            'total_pages': 0,
            'successful_pages': 0,
            'failed_pages': 0,
            'status': 'crawling',
            'seen_urls': set([self.current_project['url']])  # 记录已调度的 URL，避免重复
        }
        
        # 更清晰的项目开始日志
        self.logger.info("\n" + "="*80)
        self.logger.info(f"开始爬取项目 [{self.completed_projects + 1}/{self.total_projects}]")
        self.logger.info(f"项目名称: {self.current_project['name']}")
        self.logger.info(f"项目ID: {project_id}")
        self.logger.info(f"根URL: {self.current_project['url']}")
        self.logger.info(f"剩余项目数: {len(self.project_queue)}")
        self.logger.info("="*80)
        
        self.request_counters[project_id] += 1
        
        request = scrapy.Request(
            url=self.current_project['url'],
            callback=self.parse_page,
            errback=self.handle_error,
            meta={
                'project_id': project_id,
                'depth': 0,
                'is_root': True
            },
            dont_filter=True  # 避免全局去重影响计数
        )
        # 重置根页面的深度为0，避免深度限制问题
        request.meta['depth'] = 0
        return [request]
        
    def parse_page(self, response):
        """解析页面内容"""
        project_id = response.meta['project_id']
        depth = response.meta.get('depth', 0)
        is_root = response.meta.get('is_root', False)
        
        # 在解析每个页面时输出进度信息
        current_project_data = self.project_data[project_id]
        processed_pages = current_project_data['successful_pages'] + current_project_data['failed_pages']
        page_type = "根页面" if is_root else f"子页面(深度{depth})"
        
        self.logger.info(f"[{project_id}] 正在处理{page_type} (已处理{processed_pages}个页面): {response.url[:100]}{'...' if len(response.url) > 100 else ''}")
        
        if not self.is_html_content(response):
            self.logger.info(f"[{project_id}] 跳过非HTML内容: {response.url}")
            
            # 为非HTML内容创建一个基本的页面记录
            page_data = {
                'url': response.url,
                'depth': depth,
                'title': '',
                'content': f"非HTML内容 - Content-Type: {response.headers.get('Content-Type', b'').decode('utf-8')}",
                'links': [],
                'crawl_status': 'skipped_non_html'
            }
            self.project_data[project_id]['pages'].append(page_data)
            self.project_data[project_id]['failed_pages'] += 1
            
            # 检查项目是否完成  
            self.request_counters[project_id] -= 1
            self.logger.info(f"[{project_id}] 剩余请求数: {self.request_counters[project_id]}")
            
            if self.request_counters[project_id] <= 0:
                yield from self.complete_project(project_id)
            return
            
        try:
            page_data = {
                'url': response.url,
                'depth': depth,
                'title': self.extract_title(response),
                'content': self.extract_content(response),
                'links': [],
                'crawl_status': 'success'
            }
            
            self.project_data[project_id]['pages'].append(page_data)
            self.project_data[project_id]['successful_pages'] += 1
            
            # 修改链接提取条件：允许根页面(is_root=True)或深度小于1的页面提取链接
            is_root = response.meta.get('is_root', False)
            if depth < 1 or is_root:
                links = self.extract_links(response)
                page_data['links'] = links
                
                # 调试信息：如果没有提取到链接，记录详细信息
                if not links:
                    self.logger.warning(f"[{project_id}] 页面 {response.url} (depth={depth}, is_root={is_root}) 没有提取到任何符合条件的链接")
                else:
                    self.logger.info(f"[{project_id}] 页面 {response.url} (depth={depth}, is_root={is_root}) 提取到 {len(links)} 个链接")
                
                # 使用项目级全局集合进行去重，保证计数准确
                seen_urls_global = self.project_data[project_id].setdefault('seen_urls', set())
                new_requests = []
                for link_url, anchor_text, matched_keyword in links:
                    if link_url in seen_urls_global:
                        continue
                    seen_urls_global.add(link_url)

                    if not filter_url(link_url, anchor_text=anchor_text):
                        self.logger.info(
                            f"[{project_id}] 爬取子链接: {link_url} (锚文本: '{anchor_text}', 匹配关键词: '{matched_keyword}')")

                        # 为根页面的子链接使用深度1，避免深度限制问题
                        child_depth = 1 if is_root else depth + 1
                        request = scrapy.Request(
                            url=link_url,
                            callback=self.parse_page,
                            errback=self.handle_error,
                            meta={
                                'project_id': project_id,
                                'depth': child_depth,
                                'is_root': False
                            },
                            dont_filter=True  # 避免 Scrapy 去重导致计数器失配
                        )
                        new_requests.append(request)

                # 一次性更新计数器（仅统计真正会被调度的请求）
                if new_requests:
                    self.request_counters[project_id] += len(new_requests)
                    self.logger.info(
                        f"[{project_id}] 添加 {len(new_requests)} 个新请求，当前剩余: {self.request_counters[project_id] - 1}")

                # 发出所有请求
                for request in new_requests:
                    yield request
                        
        except Exception as e:
            self.logger.error(f"[{project_id}] 解析页面失败 {response.url}: {e}")
            self.project_data[project_id]['failed_pages'] += 1
            
        # 先检查并处理待完成的项目（来自错误处理）
        if hasattr(self, '_projects_to_complete'):
            for pending_project_id in list(self._projects_to_complete):
                if self.request_counters.get(pending_project_id, 0) <= 0:
                    self._projects_to_complete.remove(pending_project_id)
                    yield from self.complete_project(pending_project_id)
        
        # 最后检查当前项目是否完成（在所有yield操作完成后）
        self.request_counters[project_id] -= 1
        processed_pages_after = current_project_data['successful_pages'] + current_project_data['failed_pages']
        self.logger.info(f"[{project_id}] 已处理页面: {processed_pages_after}, 剩余请求数: {self.request_counters[project_id]}")
        
        if self.request_counters[project_id] <= 0:
            yield from self.complete_project(project_id)
        
    def handle_error(self, failure):
        """处理请求错误（作为生成器，可 yield item/request）"""
        project_id = failure.request.meta.get('project_id')
        if not project_id:
            return

        self.logger.error(f"[{project_id}] 请求失败 {failure.request.url}: {failure.value}")
        self.project_data[project_id]['failed_pages'] += 1

        # 更新计数器
        self.request_counters[project_id] -= 1
        current_project_data = self.project_data[project_id]
        processed_pages = current_project_data['successful_pages'] + current_project_data['failed_pages']
        self.logger.info(f"[{project_id}] 已处理页面: {processed_pages}, 剩余请求数: {self.request_counters[project_id]}")

        # 如果当前项目所有请求都已回收，立即完成项目
        if self.request_counters[project_id] <= 0:
            self.logger.info(f"[{project_id}] 项目在错误处理中完成，立即收尾 …")
            yield from self.complete_project(project_id)
            
    def complete_project(self, project_id):
        """完成当前项目，输出统计信息并开始下一个项目"""
        self.logger.info(f"[{project_id}] 正在完成项目")
        
        # 检查项目是否已经完成过，避免重复处理
        if not hasattr(self, '_completed_projects'):
            self._completed_projects = set()
        
        if project_id in self._completed_projects:
            self.logger.info(f"[{project_id}] 项目已经完成过，跳过")
            return
            
        self._completed_projects.add(project_id)
        
        project_data = self.project_data[project_id]
        project_data['status'] = 'completed'
        project_data['total_pages'] = len(project_data['pages'])
        
        total_attempts = project_data['successful_pages'] + project_data['failed_pages']
        success_rate = (project_data['successful_pages'] / max(1, total_attempts)) * 100
        
        # 更清晰的项目完成日志
        self.logger.info("\n" + "-"*60)
        self.logger.info(f"[{project_id}] 项目完成: {project_data['program_name']}")
        self.logger.info(f"[{project_id}]   - 总页数: {project_data['total_pages']}")
        self.logger.info(f"[{project_id}]   - 成功页数: {project_data['successful_pages']}")
        self.logger.info(f"[{project_id}]   - 失败页数: {project_data['failed_pages']}")
        self.logger.info(f"[{project_id}]   - 成功率: {success_rate:.1f}%")
        self.logger.info("-"*60)
        
        item = ProgramPageItem()
        item['project_id'] = project_data['project_id']
        item['program_name'] = project_data['program_name']
        item['source_file'] = project_data['source_file']
        item['root_url'] = project_data['root_url']
        item['crawl_time'] = project_data['crawl_time']
        item['pages'] = project_data['pages']
        item['total_pages'] = project_data['total_pages']
        item['status'] = project_data['status']
        
        yield item
        
        self.completed_projects += 1
        self.is_processing_project = False  # 释放当前项目状态
        
        # 不在此处直接启动下一个项目，而是留给 spider_idle 信号统一调度，
        # 以避免深度叠加导致的 DEPTH_LIMIT 丢包
        if self.project_queue:
            self.logger.info(f"[{project_id}] 仍有 {len(self.project_queue)} 个项目待爬，将在爬虫空闲时继续。")
        else:
            self.logger.info("\n" + "="*50)
            self.logger.info("所有项目已完成")
            self.logger.info(f"完成率: {self.completed_projects}/{self.total_projects} (100%)")
            self.logger.info("="*50)
        
    def is_html_content(self, response):
        """检查响应是否为HTML内容"""
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        return 'text/html' in content_type
        
    def extract_title(self, response):
        """提取页面标题"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            return title_tag.get_text().strip() if title_tag else ""
        except:
            return ""
            
    def extract_content(self, response):
        """提取页面内容"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
                
            content_parts = []
            
            content_parts.extend(self.extract_text_elements(soup))
            content_parts.extend(self.extract_tables(soup))
            
            return '\n'.join(filter(None, content_parts))
            
        except Exception as e:
            self.logger.error(f"内容提取失败: {e}")
            return ""
            
    def extract_text_elements(self, soup):
        """提取常规文本元素"""
        content_parts = []
        
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if text:
                content_parts.append(f"[HEADING] {text}")
                
        for tag in soup.find_all('p'):
            text = tag.get_text().strip()
            if text and len(text) > 10:
                content_parts.append(text)
                
        for tag in soup.find_all(['ul', 'ol']):
            items = []
            for li in tag.find_all('li'):
                item_text = li.get_text().strip()
                if item_text:
                    items.append(f"• {item_text}")
            if items:
                content_parts.append('\n'.join(items))
                
        return content_parts
        
    def extract_tables(self, soup):
        """提取各种表格形式的内容"""
        content_parts = []
        
        for table in soup.find_all('table'):
            table_content = self.extract_html_table(table)
            if table_content:
                content_parts.append(f"[HTML_TABLE]\n{table_content}")
                
        for grid in soup.find_all(class_=re.compile(r'grid|row|col')):
            grid_content = self.extract_grid_layout(grid)
            if grid_content:
                content_parts.append(f"[GRID_TABLE]\n{grid_content}")
                
        for dl in soup.find_all('dl'):
            dl_content = self.extract_definition_list(dl)
            if dl_content:
                content_parts.append(f"[DEFINITION_LIST]\n{dl_content}")
                
        for card in soup.find_all(class_=re.compile(r'card|panel|box')):
            card_content = self.extract_card_content(card)
            if card_content:
                content_parts.append(f"[CARD]\n{card_content}")
                
        return content_parts
        
    def extract_html_table(self, table):
        """提取HTML表格内容"""
        rows = []
        for tr in table.find_all('tr'):
            cells = []
            for cell in tr.find_all(['td', 'th']):
                cell_text = cell.get_text().strip()
                cells.append(cell_text)
            if cells:
                rows.append(' | '.join(cells))
        return '\n'.join(rows)
        
    def extract_grid_layout(self, grid):
        """提取CSS Grid/Flexbox布局内容"""
        items = []
        for item in grid.find_all(class_=re.compile(r'col|item|cell')):
            text = item.get_text().strip()
            if text and len(text) > 5:
                items.append(text)
        return '\n'.join(items) if len(items) > 1 else ""
        
    def extract_definition_list(self, dl):
        """提取定义列表内容"""
        items = []
        current_term = ""
        
        for child in dl.children:
            if hasattr(child, 'name'):
                if child.name == 'dt':
                    current_term = child.get_text().strip()
                elif child.name == 'dd' and current_term:
                    definition = child.get_text().strip()
                    items.append(f"{current_term}: {definition}")
                    current_term = ""
                    
        return '\n'.join(items)
        
    def extract_card_content(self, card):
        """提取卡片式布局内容"""
        title = ""
        content = ""
        
        title_elem = card.find(class_=re.compile(r'title|header|heading'))
        if title_elem:
            title = title_elem.get_text().strip()
            
        content_elem = card.find(class_=re.compile(r'content|body|text'))
        if content_elem:
            content = content_elem.get_text().strip()
        else:
            content = card.get_text().strip()
            
        if title and content:
            return f"{title}\n{content}"
        return content if content else ""
        
    def extract_links(self, response):
        """提取页面链接并进行过滤"""
        try:
            # 从 response 中获取 project_id
            project_id = response.meta.get('project_id', 'unknown')
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 统计所有链接
            all_links = soup.find_all('a', href=True)
            self.logger.debug(f"[{project_id}] 页面总链接数: {len(all_links)}")
            
            # 删除导航元素
            nav_selectors = ['nav', 'header', 'footer', '.navigation', '.menu', '.navbar']
            removed_nav_count = 0
            for selector in nav_selectors:
                nav_elements = soup.select(selector)
                for nav_elem in nav_elements:
                    nav_elem.decompose()
                    removed_nav_count += len(nav_elem.find_all('a', href=True))
            
            remaining_links = soup.find_all('a', href=True)
            self.logger.debug(f"[{project_id}] 移除导航后链接数: {len(remaining_links)} (移除了 {removed_nav_count} 个导航链接)")
                    
            links = []
            valid_count = 0
            keyword_matched_count = 0
            
            for a_tag in remaining_links:
                href = a_tag['href']
                anchor_text = a_tag.get_text().strip()
                
                # 转换为绝对URL
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(response.url, href)
                    
                # 移除fragment
                href = href.split('#')[0]
                
                # 跳过指向当前页面的链接（避免自循环）
                if href == response.url:
                    continue
                    
                if self.is_valid_link(href, response.url):
                    valid_count += 1
                    matched_keyword = self.get_matched_keyword(href, anchor_text)
                    if matched_keyword:
                        keyword_matched_count += 1
                        links.append((href, anchor_text, matched_keyword))
                        self.logger.debug(f"[{project_id}] 匹配链接: {href} (锚文本: '{anchor_text}', 关键词: '{matched_keyword}')")
            
            self.logger.debug(f"[{project_id}] 有效链接数: {valid_count}, 关键词匹配数: {keyword_matched_count}, 最终提取数: {len(links)}")
            return links
            
        except Exception as e:
            project_id = response.meta.get('project_id', 'unknown')
            self.logger.error(f"[{project_id}] 链接提取失败: {e}")
            return []
            
    def is_valid_link(self, url, base_url):
        """检查链接是否有效"""
        try:
            parsed_url = urlparse(url)
            base_parsed = urlparse(base_url)
            
            if not parsed_url.netloc:
                return False
                
            if parsed_url.netloc != base_parsed.netloc:
                return False
                
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) > 5:
                return False
                
            return True
            
        except:
            return False
            
    def get_matched_keyword(self, url, anchor_text):
        """获取匹配的白名单关键词"""
        from ..url_filter import URL_WHITELIST_KEYWORDS
        
        text_to_check = (anchor_text + " " + url).lower()
        
        for keyword in URL_WHITELIST_KEYWORDS:
            if keyword in text_to_check:
                return keyword
                
        return None
        
    def closed(self, reason):
        """爬虫关闭时的统计信息"""
        self.logger.info("=== 爬虫完成统计 ===")
        self.logger.info(f"总项目数: {self.total_projects}")
        self.logger.info(f"完成项目数: {self.completed_projects}")
        self.logger.info(f"失败项目数: {self.failed_projects}")
        self.logger.info(f"关闭原因: {reason}")
        
        # 检查是否有未完成的项目
        unfinished_projects = []
        for project_id, counter in self.request_counters.items():
            if counter > 0:
                project_name = self.project_data.get(project_id, {}).get('program_name', project_id)
                unfinished_projects.append(f"{project_name} (剩余: {counter})")
                
        if unfinished_projects:
            self.logger.warning(f"发现未完成的项目: {unfinished_projects}")
            
        # 尝试完成所有待完成的项目
        if hasattr(self, '_projects_to_complete') and self._projects_to_complete:
            self.logger.warning(f"发现待完成项目: {list(self._projects_to_complete)}")
        
        if self.total_projects > 0:
            completion_rate = (self.completed_projects / self.total_projects) * 100
            self.logger.info(f"完成率: {completion_rate:.1f}%")

    # ------------------------------------------------------------------
    # signal handlers
    # ------------------------------------------------------------------
    def spider_idle(self):
        """当爬虫即将 idle 时，如果队列中还有项目，则启动下一个项目"""
        if self.project_queue and not self.is_processing_project:
            self.logger.info("spider_idle 触发，调度下一个项目 …")
            for req in self.start_next_project():
                # 直接通过 engine 调度，避免深度叠加（Scrapy ≥2.9 的 crawl 只接受 request 参数）
                self.crawler.engine.crawl(req)
            raise DontCloseSpider  # 告诉 Scrapy 暂时不要关闭