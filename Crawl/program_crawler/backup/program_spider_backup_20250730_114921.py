"""
项目爬虫 - Program Spider

这是一个专门用于爬取多个大学项目页面信息的Scrapy爬虫。

=== 核心架构 ===

1. **顺序单项目管理**
   - 从CSV文件读取多个项目信息
   - 按顺序逐个处理每个项目（确保日志清晰）
   - 每个项目完成后自动启动下一个项目

2. **生命周期管理**
   - 初始化：加载所有项目信息到队列
   - 启动：仅启动第一个项目的根页面请求
   - 执行：当前项目爬取根页面→子页面→完成后启动下一项目
   - 完成：所有项目完成后生成统计报告

3. **页面处理流程**
   - 根页面 → 提取子链接 → 爬取子页面
   - 深度控制：根页面(depth=0) → 子页面(depth=1)
   - 内容提取：标题、正文、表格、链接等

4. **关键特性**
   - 顺序执行确保日志清晰易读
   - 每个项目独立完成统计
   - 项目间状态隔离
   - 自动项目切换机制

=== 数据流 ===
CSV文件 → 项目队列 → 顺序启动 → 页面解析 → 内容提取 → JSON输出 → 下一项目
"""

import scrapy
import csv
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from ..url_filter import filter_url
from ..items import ProgramPageItem


class ProgramSpider(scrapy.Spider):
    """
    单项目顺序爬虫类
    
    按顺序逐个处理大学项目，确保日志清晰可读，便于监控每个项目的进展。
    """
    name = 'program_spider'
    allowed_domains = []  # 动态设置，基于项目URL的域名
    
    def __init__(self, csv_file='program_urls.csv', *args, **kwargs):
        """
        初始化爬虫
        
        Args:
            csv_file: 包含项目信息的CSV文件名
            
        实例变量说明：
            - project_queue: 待处理的项目队列（FIFO）
            - current_project: 当前正在处理的项目
            - request_counters: 当前项目的剩余请求计数器
            - project_data: 当前项目收集的数据
            - total_projects/completed_projects/failed_projects: 统计信息
        """
        super(ProgramSpider, self).__init__(*args, **kwargs)
        
        # 文件配置
        self.csv_file = csv_file
        
        # 项目管理（顺序执行）
        self.project_queue = []           # 项目队列：[{id, name, url, source_file}, ...]
        self.current_project = None       # 当前正在处理的项目
        
        # 当前项目的请求和数据管理
        self.current_project_id = None    # 当前项目ID
        self.request_counter = 0          # 当前项目的剩余请求数
        self.current_project_data = {}    # 当前项目的数据存储
        
        # 全局统计信息
        self.total_projects = 0
        self.completed_projects = 0
        self.failed_projects = 0
        
        # 加载项目配置
        self.load_projects()
        
    def load_projects(self):
        """
        从CSV文件加载所有项目信息到队列
        
        CSV格式要求：
        - id: 项目唯一标识符
        - program_name: 项目名称
        - program_url: 项目根页面URL  
        - source_file: 数据来源文件名
        
        功能：
        1. 解析CSV文件
        2. 逐行构建项目队列（确保顺序）
        3. 提取并设置allowed_domains
        4. 初始化统计信息
        """
        # 计算CSV文件的绝对路径：向上两级目录到crawl文件夹
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.csv_file)
        
        self.logger.info(f"尝试加载CSV文件: {csv_path}")
        self.logger.info(f"文件是否存在: {os.path.exists(csv_path)}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 构建项目数据结构（每行作为独立项目）
                    project = {
                        'id': row['id'],
                        'name': row['program_name'],
                        'url': row['program_url'],
                        'source_file': row['source_file']
                    }
                    self.project_queue.append(project)
                    
                    # 提取域名并添加到allowed_domains
                    domain = urlparse(project['url']).netloc
                    if domain not in self.allowed_domains:
                        self.allowed_domains.append(domain)
                        
            # 更新统计信息
            self.total_projects = len(self.project_queue)
            self.logger.info(f"=== 项目加载完成 ===")
            self.logger.info(f"总项目数: {self.total_projects}")
            self.logger.info(f"允许的域名: {self.allowed_domains}")
            self.logger.info(f"项目列表: {[p['name'] for p in self.project_queue]}")
            
        except Exception as e:
            self.logger.error(f"加载CSV文件失败: {e}")
            
    def start_requests(self):
        """
        启动第一个项目的爬取
        
        *** 顺序执行模式 ***
        - 只启动第一个项目的根页面请求
        - 项目完成后会自动启动下一个项目
        - 确保日志清晰，便于监控单个项目进展
        
        Returns:
            list: 第一个项目的根页面请求列表
        """
        if self.project_queue:
            self.logger.info("=== 开始顺序执行项目爬取 ===")
            return self.start_next_project()
        else:
            self.logger.warning("没有找到任何项目，爬虫将退出")
            return []
            
    def start_next_project(self):
        """
        启动下一个项目的爬取
        
        功能：
        1. 从队列中取出下一个项目
        2. 初始化当前项目的数据结构和计数器
        3. 创建根页面的Scrapy请求
        4. 清理上一个项目的状态
        
        Returns:
            list: 包含单个根页面请求的列表，或空列表（无更多项目）
        """
        if not self.project_queue:
            self.logger.info("=== 所有项目已完成 ===")
            return []
            
        # === 启动新项目 ===
        self.current_project = self.project_queue.pop(0)  # FIFO队列
        self.current_project_id = self.current_project['id']
        
        # 重置当前项目状态
        self.request_counter = 1  # 从1开始（根页面请求）
        
        # 初始化当前项目数据结构
        self.current_project_data = {
            'project_id': self.current_project_id,
            'program_name': self.current_project['name'],
            'source_file': self.current_project['source_file'],
            'root_url': self.current_project['url'],
            'crawl_time': datetime.now().isoformat(),
            'pages': [],                  # 存储所有页面数据
            'total_pages': 0,
            'successful_pages': 0,
            'failed_pages': 0,
            'status': 'crawling'
        }
        
        # === 项目启动日志 ===
        self.logger.info(f"")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"启动项目 [{self.completed_projects + 1}/{self.total_projects}]")
        self.logger.info(f"项目名称: {self.current_project['name']}")
        self.logger.info(f"项目ID: {self.current_project_id}")
        self.logger.info(f"根URL: {self.current_project['url']}")
        self.logger.info(f"剩余项目数: {len(self.project_queue)}")
        self.logger.info(f"{'='*60}")
        
        # 创建根页面请求
        request = scrapy.Request(
            url=self.current_project['url'],
            callback=self.parse_page,           # 页面解析回调
            errback=self.handle_error,          # 错误处理回调
            meta={
                'depth': 0,                     # 根页面深度为0
                'is_root': True                 # 标记为根页面
            }
        )
        # 确保深度为0（避免Scrapy自动设置导致的深度限制问题）
        request.meta['depth'] = 0
        return [request]
        
    def parse_page(self, response):
        """
        页面解析主函数
        
        处理流程：
        1. 检查响应类型（HTML/非HTML）
        2. 提取页面内容（标题、正文、链接等）
        3. 对于根页面和depth<1的页面，提取子链接
        4. 创建子页面请求
        5. 更新请求计数器
        6. 检查项目完成状态
        
        Args:
            response: Scrapy响应对象
            
        Yields:
            scrapy.Request: 子页面请求
            或 项目完成时的数据项和下一项目的请求
        """
        depth = response.meta.get('depth', 0)
        
        self.logger.info(f"[{self.current_project['name']}] 处理页面: {response.url} (depth={depth})")
        
        # === 1. 处理非HTML内容 ===
        if not self.is_html_content(response):
            self.logger.info(f"[{self.current_project['name']}] 跳过非HTML内容: {response.url}")
            
            # 为非HTML内容创建基本记录
            page_data = {
                'url': response.url,
                'depth': depth,
                'title': '',
                'content': f"非HTML内容 - Content-Type: {response.headers.get('Content-Type', b'').decode('utf-8')}",
                'links': [],
                'crawl_status': 'skipped_non_html'
            }
            self.current_project_data['pages'].append(page_data)
            self.current_project_data['failed_pages'] += 1
            
            # 更新计数器并检查完成状态
            self.request_counter -= 1
            self.logger.info(f"[{self.current_project['name']}] 剩余请求数: {self.request_counter}")
            
            if self.request_counter <= 0:
                yield from self.complete_current_project()
            return
            
        # === 2. 处理HTML内容 ===
        try:
            # 创建页面数据结构
            page_data = {
                'url': response.url,
                'depth': depth,
                'title': self.extract_title(response),      # 提取标题
                'content': self.extract_content(response),  # 提取正文内容
                'links': [],
                'crawl_status': 'success'
            }
            
            # 添加到当前项目数据中
            self.current_project_data['pages'].append(page_data)
            self.current_project_data['successful_pages'] += 1
            
            self.logger.info(f"[{self.current_project['name']}] 成功解析: {response.url}")
            self.logger.info(f"[{self.current_project['name']}] 页面标题: {page_data['title'][:100]}...")
            
            # === 3. 链接提取和子请求创建 ===
            # 只有根页面(is_root=True)或深度小于1的页面才提取链接
            is_root = response.meta.get('is_root', False)
            if depth < 1 or is_root:
                # 提取页面中的所有有效链接
                links = self.extract_links(response)
                page_data['links'] = links
                
                # 调试信息
                if not links:
                    self.logger.warning(f"[{self.current_project['name']}] 页面 {response.url} (depth={depth}, is_root={is_root}) 没有提取到任何符合条件的链接")
                else:
                    self.logger.info(f"[{self.current_project['name']}] 页面 {response.url} (depth={depth}, is_root={is_root}) 提取到 {len(links)} 个链接")
                
                # === 4. 创建子页面请求 ===
                new_requests = []
                for link_url, anchor_text, matched_keyword in links:
                    # 通过URL过滤器检查链接是否应该爬取
                    if not filter_url(link_url, anchor_text=anchor_text):
                        self.logger.info(f"[{self.current_project['name']}] 添加子链接: {link_url}")
                        self.logger.debug(f"[{self.current_project['name']}] 锚文本: '{anchor_text}', 匹配关键词: '{matched_keyword}'")
                        
                        # 计算子页面深度：根页面的子链接深度为1，其他页面递增
                        child_depth = 1 if is_root else depth + 1
                        
                        # 创建子页面请求
                        request = scrapy.Request(
                            url=link_url,
                            callback=self.parse_page,      # 递归调用自身
                            errback=self.handle_error,
                            meta={
                                'depth': child_depth,
                                'is_root': False           # 子页面不是根页面
                            }
                        )
                        new_requests.append(request)
                
                # === 5. 批量更新请求计数器 ===
                if new_requests:
                    self.request_counter += len(new_requests)
                    self.logger.info(f"[{self.current_project['name']}] 添加 {len(new_requests)} 个新请求，当前剩余: {self.request_counter - 1}")
                
                # === 6. 发出所有子请求 ===
                for request in new_requests:
                    yield request
                        
        except Exception as e:
            self.logger.error(f"[{self.current_project['name']}] 解析页面失败 {response.url}: {e}")
            self.current_project_data['failed_pages'] += 1
            
        # === 7. 更新当前页面的请求计数并检查项目完成 ===
        self.request_counter -= 1  # 当前页面处理完成，计数减1
        self.logger.info(f"[{self.current_project['name']}] 剩余请求数: {self.request_counter}")
        
        # 如果当前项目没有剩余请求，则完成项目
        if self.request_counter <= 0:
            yield from self.complete_current_project()
        
    def handle_error(self, failure):
        """
        处理请求错误
        
        当页面请求失败时调用此函数。
        
        Args:
            failure: Scrapy失败对象，包含错误信息和原始请求
        """
        self.logger.error(f"[{self.current_project['name']}] 请求失败 {failure.request.url}: {failure.value}")
        self.current_project_data['failed_pages'] += 1
        
        # 更新请求计数器
        self.request_counter -= 1
        self.logger.info(f"[{self.current_project['name']}] 剩余请求数: {self.request_counter}")
        
        # 注意：handle_error不是生成器函数，无法yield
        # 如果项目完成，会在下次parse_page调用时检测到
            
    def complete_current_project(self):
        """
        完成当前项目处理
        
        功能：
        1. 汇总当前项目统计信息
        2. 创建输出数据项
        3. 更新全局完成计数
        4. 启动下一个项目（如果有）
        
        Yields:
            ProgramPageItem: 包含项目所有数据的输出项
            scrapy.Request: 下一个项目的根页面请求（如果有）
        """
        # === 汇总项目数据 ===
        self.current_project_data['status'] = 'completed'
        self.current_project_data['total_pages'] = len(self.current_project_data['pages'])
        
        # 计算成功率
        total_attempts = self.current_project_data['successful_pages'] + self.current_project_data['failed_pages']
        success_rate = (self.current_project_data['successful_pages'] / max(1, total_attempts)) * 100
        
        # === 输出项目完成统计 ===
        self.logger.info(f"")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"项目完成: {self.current_project_data['program_name']}")
        self.logger.info(f"  - 总页数: {self.current_project_data['total_pages']}")
        self.logger.info(f"  - 成功页数: {self.current_project_data['successful_pages']}")
        self.logger.info(f"  - 失败页数: {self.current_project_data['failed_pages']}")
        self.logger.info(f"  - 成功率: {success_rate:.1f}%")
        self.logger.info(f"{'='*60}")
        
        # === 创建输出数据项 ===
        item = ProgramPageItem()
        item['project_id'] = self.current_project_data['project_id']
        item['program_name'] = self.current_project_data['program_name']
        item['source_file'] = self.current_project_data['source_file']
        item['root_url'] = self.current_project_data['root_url']
        item['crawl_time'] = self.current_project_data['crawl_time']
        item['pages'] = self.current_project_data['pages']
        item['total_pages'] = self.current_project_data['total_pages']
        item['status'] = self.current_project_data['status']
        
        yield item  # 输出到Pipeline进行后续处理（如保存为JSON）
        
        # === 更新全局统计 ===
        self.completed_projects += 1
        
        # === 启动下一个项目 ===
        if self.project_queue:
            self.logger.info(f"启动下一个项目，队列中还有 {len(self.project_queue)} 个项目")
            for request in self.start_next_project():
                yield request
        else:
            self.logger.info("=== 所有项目爬取完成 ===")
            
    # ========================================
    # 内容提取相关函数
    # ========================================
    
    def is_html_content(self, response):
        """
        检查响应是否为HTML内容
        
        Args:
            response: Scrapy响应对象
            
        Returns:
            bool: 是否为HTML内容
        """
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
        return 'text/html' in content_type
        
    def extract_title(self, response):
        """
        提取页面标题
        
        Args:
            response: Scrapy响应对象
            
        Returns:
            str: 页面标题，提取失败返回空字符串
        """
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            return title_tag.get_text().strip() if title_tag else ""
        except:
            return ""
            
    def extract_content(self, response):
        """
        提取页面主要内容
        
        使用BeautifulSoup解析HTML，提取结构化内容包括：
        - 文本元素（标题、段落、列表）
        - 表格数据（HTML表格、CSS网格、定义列表、卡片）
        
        Args:
            response: Scrapy响应对象
            
        Returns:
            str: 提取的页面内容，各部分用换行符分隔
        """
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除不需要的元素（脚本、样式、导航等）
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
                
            content_parts = []
            
            # 提取常规文本元素
            content_parts.extend(self.extract_text_elements(soup))
            # 提取表格化数据
            content_parts.extend(self.extract_tables(soup))
            
            return '\n'.join(filter(None, content_parts))
            
        except Exception as e:
            self.logger.error(f"内容提取失败: {e}")
            return ""
            
    def extract_text_elements(self, soup):
        """
        提取常规文本元素
        
        包括标题(h1-h6)、段落(p)、列表(ul/ol)等
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            list: 文本内容列表
        """
        content_parts = []
        
        # 提取标题
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if text:
                content_parts.append(f"[HEADING] {text}")
                
        # 提取段落
        for tag in soup.find_all('p'):
            text = tag.get_text().strip()
            if text and len(text) > 10:  # 过滤太短的段落
                content_parts.append(text)
                
        # 提取列表
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
        """
        提取各种表格形式的内容
        
        包括：
        - HTML表格 (<table>)
        - CSS网格布局 (grid/row/col类)
        - 定义列表 (<dl>)
        - 卡片布局 (card/panel/box类)
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            list: 表格内容列表，每个元素带有类型标记
        """
        content_parts = []
        
        # HTML表格
        for table in soup.find_all('table'):
            table_content = self.extract_html_table(table)
            if table_content:
                content_parts.append(f"[HTML_TABLE]\n{table_content}")
                
        # CSS网格布局
        for grid in soup.find_all(class_=re.compile(r'grid|row|col')):
            grid_content = self.extract_grid_layout(grid)
            if grid_content:
                content_parts.append(f"[GRID_TABLE]\n{grid_content}")
                
        # 定义列表
        for dl in soup.find_all('dl'):
            dl_content = self.extract_definition_list(dl)
            if dl_content:
                content_parts.append(f"[DEFINITION_LIST]\n{dl_content}")
                
        # 卡片布局
        for card in soup.find_all(class_=re.compile(r'card|panel|box')):
            card_content = self.extract_card_content(card)
            if card_content:
                content_parts.append(f"[CARD]\n{card_content}")
                
        return content_parts
        
    def extract_html_table(self, table):
        """
        提取HTML表格内容
        
        Args:
            table: BeautifulSoup表格元素
            
        Returns:
            str: 表格内容，行用换行符分隔，列用 | 分隔
        """
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
        """
        提取CSS Grid/Flexbox布局内容
        
        Args:
            grid: BeautifulSoup网格元素
            
        Returns:
            str: 网格内容，项目用换行符分隔
        """
        items = []
        for item in grid.find_all(class_=re.compile(r'col|item|cell')):
            text = item.get_text().strip()
            if text and len(text) > 5:  # 过滤太短的内容
                items.append(text)
        return '\n'.join(items) if len(items) > 1 else ""
        
    def extract_definition_list(self, dl):
        """
        提取定义列表内容
        
        Args:
            dl: BeautifulSoup定义列表元素
            
        Returns:
            str: 定义列表内容，格式为"术语: 定义"
        """
        items = []
        current_term = ""
        
        for child in dl.children:
            if hasattr(child, 'name'):
                if child.name == 'dt':  # 定义术语
                    current_term = child.get_text().strip()
                elif child.name == 'dd' and current_term:  # 定义描述
                    definition = child.get_text().strip()
                    items.append(f"{current_term}: {definition}")
                    current_term = ""
                    
        return '\n'.join(items)
        
    def extract_card_content(self, card):
        """
        提取卡片式布局内容
        
        Args:
            card: BeautifulSoup卡片元素
            
        Returns:
            str: 卡片内容，标题和内容用换行符分隔
        """
        title = ""
        content = ""
        
        # 尝试找到标题元素
        title_elem = card.find(class_=re.compile(r'title|header|heading'))
        if title_elem:
            title = title_elem.get_text().strip()
            
        # 尝试找到内容元素
        content_elem = card.find(class_=re.compile(r'content|body|text'))
        if content_elem:
            content = content_elem.get_text().strip()
        else:
            content = card.get_text().strip()
            
        if title and content:
            return f"{title}\n{content}"
        return content if content else ""
        
    # ========================================
    # 链接提取和过滤相关函数
    # ========================================
    
    def extract_links(self, response):
        """
        提取页面链接并进行过滤
        
        链接提取流程：
        1. 解析页面HTML，统计所有链接
        2. 移除导航区域的链接（减少噪音）
        3. 链接预处理（相对路径转绝对路径、移除fragment）
        4. 有效性检查（域名、深度限制）
        5. 白名单关键词匹配
        
        Args:
            response: Scrapy响应对象
            
        Returns:
            list: 符合条件的链接列表，格式为[(url, anchor_text, matched_keyword), ...]
        """
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # === 1. 统计所有链接 ===
            all_links = soup.find_all('a', href=True)
            self.logger.info(f"[{self.current_project['name']}] 页面总链接数: {len(all_links)}")
            
            # === 2. 移除导航区域的链接 ===
            nav_selectors = ['nav', 'header', 'footer', '.navigation', '.menu', '.navbar']
            removed_nav_count = 0
            for selector in nav_selectors:
                nav_elements = soup.select(selector)
                for nav_elem in nav_elements:
                    nav_elem.decompose()  # 从DOM中删除
                    removed_nav_count += len(nav_elem.find_all('a', href=True))
            
            remaining_links = soup.find_all('a', href=True)
            self.logger.info(f"[{self.current_project['name']}] 移除导航后链接数: {len(remaining_links)} (移除了 {removed_nav_count} 个导航链接)")
                    
            # === 3. 链接处理和过滤 ===
            links = []
            valid_count = 0
            keyword_matched_count = 0
            
            for a_tag in remaining_links:
                href = a_tag['href']
                anchor_text = a_tag.get_text().strip()
                
                # 转换为绝对URL
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(response.url, href)
                    
                # 移除URL fragment（#后面的部分）
                href = href.split('#')[0]
                
                # 跳过指向当前页面的链接（避免自循环）
                if href == response.url:
                    continue
                    
                # === 4. 有效性检查 ===
                if self.is_valid_link(href, response.url):
                    valid_count += 1
                    
                    # === 5. 白名单关键词匹配 ===
                    matched_keyword = self.get_matched_keyword(href, anchor_text)
                    if matched_keyword:
                        keyword_matched_count += 1
                        links.append((href, anchor_text, matched_keyword))
                        self.logger.debug(f"[{self.current_project['name']}] 匹配链接: {href} (锚文本: '{anchor_text}', 关键词: '{matched_keyword}')")
            
            self.logger.info(f"[{self.current_project['name']}] 有效链接数: {valid_count}, 关键词匹配数: {keyword_matched_count}, 最终提取数: {len(links)}")
            return links
            
        except Exception as e:
            self.logger.error(f"[{self.current_project['name']}] 链接提取失败: {e}")
            return []
            
    def is_valid_link(self, url, base_url):
        """
        检查链接是否有效
        
        有效性检查规则：
        1. URL必须有域名
        2. 必须与基础URL在同一域名下（防止跨站）
        3. 路径深度不能超过5级（避免过深的URL）
        
        Args:
            url: 要检查的URL
            base_url: 基础URL（当前页面URL）
            
        Returns:
            bool: 链接是否有效
        """
        try:
            parsed_url = urlparse(url)
            base_parsed = urlparse(base_url)
            
            # 检查是否有域名
            if not parsed_url.netloc:
                return False
                
            # 检查是否在同一域名下
            if parsed_url.netloc != base_parsed.netloc:
                return False
                
            # 检查路径深度限制
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) > 5:
                return False
                
            return True
            
        except:
            return False
            
    def get_matched_keyword(self, url, anchor_text):
        """
        获取匹配的白名单关键词
        
        检查URL和锚文本是否包含白名单关键词。
        白名单关键词在url_filter.py中定义，包括：
        - 学位相关：master, graduate, program等
        - 申请相关：apply, admission, requirements等
        - 费用相关：tuition, fee, funding等
        
        Args:
            url: 链接URL
            anchor_text: 链接锚文本
            
        Returns:
            str: 匹配的关键词，无匹配返回None
        """
        from ..url_filter import URL_WHITELIST_KEYWORDS
        
        # 将URL和锚文本合并后转为小写进行匹配
        text_to_check = (anchor_text + " " + url).lower()
        
        for keyword in URL_WHITELIST_KEYWORDS:
            if keyword in text_to_check:
                return keyword
                
        return None
        
    def closed(self, reason):
        """
        爬虫关闭时的统计信息
        
        在爬虫结束时输出详细的统计信息，包括：
        - 项目完成情况
        - 整体完成率
        - 关闭原因
        
        Args:
            reason: 爬虫关闭原因
        """
        self.logger.info("")
        self.logger.info("="*80)
        self.logger.info("=== 爬虫完成统计 ===")
        self.logger.info(f"总项目数: {self.total_projects}")
        self.logger.info(f"完成项目数: {self.completed_projects}")
        self.logger.info(f"失败项目数: {self.failed_projects}")
        self.logger.info(f"关闭原因: {reason}")
        
        # === 计算完成率 ===
        if self.total_projects > 0:
            completion_rate = (self.completed_projects / self.total_projects) * 100
            self.logger.info(f"完成率: {completion_rate:.1f}%")
            
        # === 检查未完成项目 ===
        remaining_projects = len(self.project_queue)
        if remaining_projects > 0:
            self.logger.warning(f"剩余未处理项目数: {remaining_projects}")
            self.logger.warning(f"未处理项目列表: {[p['name'] for p in self.project_queue]}")
            
        self.logger.info("="*80)