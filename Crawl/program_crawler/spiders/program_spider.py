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
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """自定义构造函数，用于注册 spider_idle 信号处理器"""
        # 从crawler设置中获取URLs文件路径
        urls_file = crawler.settings.get('URLS_FILE')
        if urls_file:
            kwargs['csv_file'] = urls_file
            
        spider = super(ProgramSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider
    
    def __init__(self, csv_file='program_urls.csv', start_index=0, *args, **kwargs):
        super(ProgramSpider, self).__init__(*args, **kwargs)
        
        self.csv_file = csv_file
        self.start_index = int(start_index)  # 支持从指定索引开始
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
        # 如果是绝对路径，直接使用；否则拼接相对路径
        if os.path.isabs(str(self.csv_file)):
            csv_path = str(self.csv_file)
        else:
            # 向上两级目录到crawl文件夹，然后加上csv文件名
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.csv_file)
        
        self.logger.info(f"尝试加载CSV文件: {csv_path}")
        self.logger.info(f"文件是否存在: {os.path.exists(csv_path)}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:  # 处理BOM字符
                reader = csv.DictReader(f)
                all_projects = []
                for row in reader:
                    project = {
                        'id': row['id'],
                        'name': row['program_name'],
                        'url': row['program_url'],
                        'source_file': row['source_file']
                    }
                    all_projects.append(project)
                    
                    domain = urlparse(project['url']).netloc
                    if domain not in self.allowed_domains:
                        self.allowed_domains.append(domain)
                
                # 从指定索引开始加载项目
                original_total = len(all_projects)
                self.project_queue = all_projects[self.start_index:]
                self.total_projects = len(self.project_queue)
                self.completed_projects = self.start_index  # 已跳过的项目算作已完成
                        
            self.logger.info("\n" + "="*80)
            self.logger.info(f"原始总项目数: {original_total}")
            if self.start_index > 0:
                self.logger.info(f"从索引 {self.start_index} 开始，跳过了 {self.start_index} 个项目")
            self.logger.info(f"将要爬取 {self.total_projects} 个项目")
            self.logger.info(f"允许的域名: {self.allowed_domains}")
            self.logger.info("将按顺序逐个项目进行爬取")
            self.logger.info("="*80)
            
        except Exception as e:
            self.logger.error(f"加载CSV文件失败: {e}")
            # 输出更详细的错误信息帮助调试
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            # 不要继续运行，确保问题被发现
            raise RuntimeError(f"CSV文件加载失败，无法继续: {e}")
            
    def start_requests(self):
        """开始第一个项目的爬取，其他项目将在前一个完成后依次启动"""
        if self.project_queue:
            for request in self.start_next_project():
                yield request
        return
            
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
        
        old_count = self.request_counters[project_id]
        self.request_counters[project_id] += 1
        self.logger.info(f"[{project_id}] 计数器变更: {old_count} -> {self.request_counters[project_id]}, 操作: 启动根页面请求")
        
        # 验证URL有效性
        url = self.current_project['url']
        if not url or url.strip() in ['暂无', 'N/A', 'None', ''] or not url.startswith(('http://', 'https://')):
            self.logger.warning(f"[{project_id}] 跳过无效URL: {url}")
            # 先减少计数器，然后完成项目
            self.request_counters[project_id] -= 1
            self._complete_project_sync(project_id)  # 同步完成项目，不yield Item
            # 继续处理下一个项目
            if self.project_queue:
                yield from self.start_next_project()
            return
        
        request = scrapy.Request(
            url=url,
            callback=self.parse_page,
            errback=self.handle_error,
            meta={
                'project_id': project_id,
                'depth': 0,
                'is_root': True,
                'cookiejar': project_id,
            },
            dont_filter=True  # 避免全局去重影响计数
        )
        # 重置根页面的深度为0，避免深度限制问题
        request.meta['depth'] = 0
        yield request
        
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
            old_count = self.request_counters[project_id]
            self.request_counters[project_id] -= 1
            self.logger.info(f"[{project_id}] 计数器变更: {old_count} -> {self.request_counters[project_id]}, 操作: 完成非HTML页面处理")
            self.logger.info(f"[{project_id}] 剩余请求数: {self.request_counters[project_id]}")
            
            if self.request_counters[project_id] <= 0:
                yield from self.complete_project(project_id)
            return
            
        try:
            # 🎯 一次解析HTML，多次复用 - 性能优化核心
            soup = BeautifulSoup(response.text, 'html.parser')
            
            page_data = {
                'url': response.url,
                'depth': depth,
                'title': self.extract_title_from_soup(soup),
                'content': self.extract_content_from_soup(soup),
                'links': [],
                'crawl_status': 'success'
            }
            
            self.project_data[project_id]['pages'].append(page_data)
            self.project_data[project_id]['successful_pages'] += 1
            
            # 修改链接提取条件：允许根页面(is_root=True)或深度小于1的页面提取链接
            is_root = response.meta.get('is_root', False)
            if depth < 1 or is_root:
                links = self.extract_links_from_soup(soup, response) # 仅匹配锚文本
                page_data['links'] = links
                
                # 调试信息：如果没有提取到链接，记录详细信息
                if not links:
                    self.logger.warning(f"[{project_id}] 页面 {response.url} (depth={depth}, is_root={is_root}) 没有提取到任何符合条件的链接")
                else:
                    self.logger.info(f"[{project_id}] 页面 {response.url} (depth={depth}, is_root={is_root}) 提取到 {len(links)} 个链接")
                
                # 使用项目级全局集合进行去重，保证计数准确
                seen_urls_global = self.project_data[project_id].setdefault('seen_urls', set())
                new_requests = []
                num_duplication = 0
                # 处理新的字典格式links
                for link_info in links:
                    link_url = link_info["url"]
                    anchor_text = link_info["anchor_text"] 
                    matched_keyword = link_info["matched_keyword"]
                    
                    if link_url in seen_urls_global:
                        num_duplication += 1
                        continue
                    seen_urls_global.add(link_url)

                    if not filter_url(link_url, anchor_text=anchor_text): # 仅匹配锚文本
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
                                'is_root': False,
                                'cookiejar': project_id,
                            },
                            dont_filter=True  # 避免 Scrapy 去重导致计数器失配
                        )
                        new_requests.append(request)

                # 记录去重后的新请求数
                self.logger.info(f"[{project_id}] 提取链接完成，去重前 {len(links)} 个链接，去重后 {len(new_requests)} 个新请求（去重了 {num_duplication} 个重复链接）")
                
                # 一次性更新计数器（仅统计真正会被调度的请求）
                if new_requests:
                    old_count = self.request_counters[project_id]
                    self.request_counters[project_id] += len(new_requests)
                    self.logger.info(f"[{project_id}] 计数器变更: {old_count} -> {self.request_counters[project_id]}, 操作: 添加{len(new_requests)}个子页面请求")
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
        old_count = self.request_counters[project_id]
        self.request_counters[project_id] -= 1
        self.logger.info(f"[{project_id}] 计数器变更: {old_count} -> {self.request_counters[project_id]}, 操作: 完成页面解析")
        processed_pages_after = current_project_data['successful_pages'] + current_project_data['failed_pages']
        self.logger.debug(f"[{project_id}] 已处理页面: {processed_pages_after}, 剩余请求数: {self.request_counters[project_id]}")
        
        if self.request_counters[project_id] <= 0:
            yield from self.complete_project(project_id)
        
    def handle_error(self, failure):
        """处理请求错误（作为生成器，可 yield item/request）"""
        project_id = failure.request.meta.get('project_id')
        if not project_id:
            return

        # 增强错误信息显示
        error_info = []
        error_info.append(f"URL: {failure.request.url}")
        error_info.append(f"错误类型: {failure.type.__name__}")
        error_info.append(f"错误描述: {failure.value}")
        
        # 如果是HTTP错误，显示状态码和响应头
        if hasattr(failure.value, 'response') and failure.value.response is not None:
            response = failure.value.response
            error_info.append(f"HTTP状态码: {response.status}")
            
            # 显示关键响应头
            important_headers = ['server', 'content-type', 'set-cookie', 'cf-ray', 'user-agent']
            response_headers = []
            for header in important_headers:
                if header.encode() in response.headers:
                    value = response.headers.get(header).decode('utf-8', errors='ignore')[:200]
                    response_headers.append(f"{header}: {value}")
            
            if response_headers:
                error_info.append(f"响应头: {'; '.join(response_headers)}")
                
            # 显示响应体前200字符（如果有）
            if hasattr(response, 'text') and len(response.text) > 0:
                response_preview = response.text[:200].replace('\n', ' ').replace('\r', ' ')
                error_info.append(f"响应预览: {response_preview}...")
        
        # 显示请求头信息
        request_headers = []
        important_req_headers = ['user-agent', 'accept', 'accept-language', 'accept-encoding']
        for header in important_req_headers:
            if header.encode() in failure.request.headers:
                value = failure.request.headers.get(header).decode('utf-8', errors='ignore')[:100]
                request_headers.append(f"{header}: {value}")
        
        if request_headers:
            error_info.append(f"请求头: {'; '.join(request_headers)}")
        
        # 输出详细错误信息
        self.logger.error(f"[{project_id}] 请求失败详情:")
        for info in error_info:
            self.logger.error(f"[{project_id}]   {info}")
            
        self.project_data[project_id]['failed_pages'] += 1

        # 更新计数器
        old_count = self.request_counters[project_id]
        self.request_counters[project_id] -= 1
        self.logger.info(f"[{project_id}] 计数器变更: {old_count} -> {self.request_counters[project_id]}, 操作: 处理请求错误")
        current_project_data = self.project_data[project_id]
        processed_pages = current_project_data['successful_pages'] + current_project_data['failed_pages']
        self.logger.info(f"[{project_id}] 已处理页面: {processed_pages}, 剩余请求数: {self.request_counters[project_id]}")

        # 记录失败到状态文件
        self.record_failed_request(project_id, failure)

        # 如果当前项目所有请求都已回收，立即完成项目
        if self.request_counters[project_id] <= 0:
            self.logger.info(f"[{project_id}] 项目在错误处理中完成，立即收尾 …")
            yield from self.complete_project(project_id)
    
    def record_failed_request(self, project_id, failure):
        """记录失败的请求到学科专门的失败日志文件"""
        try:
            import json
            import os
            from datetime import datetime
            
            # 获取项目信息
            project_data = self.project_data.get(project_id, {})
            program_name = project_data.get('program_name', 'Unknown')
            source_file_raw = project_data.get('source_file', 'unknown.csv')
            
            # 统一处理source_file，移除所有可能的扩展名
            source_file = source_file_raw.replace('.csv', '').replace('.json', '')
            
            # 提取学科名称（去掉可能的数字后缀，如"计算机_1" -> "计算机"）
            subject_name = source_file.split('_')[0] if '_' in source_file else source_file
            
            # 构建失败日志文件路径
            # __file__ = .../crawl/program_crawler/spiders/program_spider.py
            # 需要4个dirname到达crawl目录：spiders -> program_crawler -> crawl
            crawl_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            log_dir = os.path.join(crawl_dir, 'log', subject_name)
            
            # 确保学科日志目录存在
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            failed_log_file = os.path.join(log_dir, f'failed_urls_{source_file}.json')
            
            # 构建详细错误信息
            error_msg = f"{failure.type.__name__}: {failure.value}"
            http_status = None
            response_headers = {}
            response_preview = ""
            
            if hasattr(failure.value, 'response') and failure.value.response is not None:
                response = failure.value.response
                http_status = response.status
                error_msg += f" (HTTP {response.status})"
                
                # 提取响应头
                important_headers = ['server', 'content-type', 'set-cookie', 'cf-ray']
                for header in important_headers:
                    if header.encode() in response.headers:
                        value = response.headers.get(header).decode('utf-8', errors='ignore')[:200]
                        response_headers[header] = value
                
                # 提取响应体预览
                if hasattr(response, 'text') and len(response.text) > 0:
                    response_preview = response.text[:200].replace('\n', ' ').replace('\r', ' ')
            
            # 创建失败记录（去掉timestamp字段）
            failed_record = {
                'project_id': project_id,
                'program_name': program_name,
                'source_file': source_file,
                'url': failure.request.url,
                'error': error_msg,
                'error_type': failure.type.__name__,
                'http_status': http_status,
                'response_headers': response_headers,
                'response_preview': response_preview
            }
            
            # 读取现有失败记录
            failed_records = []
            if os.path.exists(failed_log_file):
                with open(failed_log_file, 'r', encoding='utf-8') as f:
                    failed_records = json.load(f)
            
            # 🎯 URL去重：检查是否已存在相同URL的失败记录
            existing_urls = {record['url'] for record in failed_records}
            if failure.request.url not in existing_urls:
                failed_records.append(failed_record)
                self.logger.info(f"[{project_id}] 新增失败URL记录: {failure.request.url}")
            else:
                self.logger.debug(f"[{project_id}] 失败URL已存在，跳过重复记录: {failure.request.url}")
            
            # 保存失败记录（仅在有新记录时写入）
            if failure.request.url not in existing_urls:
                with open(failed_log_file, 'w', encoding='utf-8') as f:
                    json.dump(failed_records, f, ensure_ascii=False, indent=2)
                self.logger.info(f"[{project_id}] 失败记录已保存到: {failed_log_file}")
            else:
                self.logger.debug(f"[{project_id}] 未保存重复失败记录")
            
        except Exception as e:
            # 状态记录失败不应影响主流程
            self.logger.warning(f"[{project_id}] 记录失败状态时出错: {e}")
            
    def _complete_project_sync(self, project_id):
        """同步完成项目，直接处理Item而不yield（用于Request生成器中）"""
        import time
        time.sleep(1)  # 给并发请求1秒缓冲时间，确保所有请求都已处理完毕
        
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
        
        # 直接通过pipeline处理item，不通过yield
        item = ProgramPageItem()
        item['project_id'] = project_data['project_id']
        item['program_name'] = project_data['program_name']
        item['source_file'] = project_data['source_file']
        item['root_url'] = project_data['root_url']
        item['crawl_time'] = project_data['crawl_time']
        item['pages'] = project_data['pages']
        item['total_pages'] = project_data['total_pages']
        item['status'] = project_data['status']
        
        # 直接调用pipeline处理item
        self.crawler.engine.scraper.itemproc.process_item(item, self)
        
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
    
    def complete_project(self, project_id):
        """完成当前项目，输出统计信息并开始下一个项目（生成器版本，用于正常流程）"""
        import time
        time.sleep(1)  # 给并发请求1秒缓冲时间，确保所有请求都已处理完毕
        
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
        """提取页面标题（兼容性方法，建议使用extract_title_from_soup）"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.extract_title_from_soup(soup)
        except:
            return ""
            
    def extract_title_from_soup(self, soup):
        """从soup对象提取页面标题"""
        try:
            if soup is None:
                return ""
            title_tag = soup.find('title')
            return title_tag.get_text().strip() if title_tag else ""
        except:
            return ""
            
    def extract_content(self, response):
        """提取页面内容（兼容性方法，建议使用extract_content_from_soup）"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.extract_content_from_soup(soup)
        except Exception as e:
            self.logger.error(f"内容提取失败: {e}")
            return ""
            
    def extract_content_from_soup(self, soup):
        """从soup对象提取页面内容（带文本去重）"""
        try:
            if soup is None:
                return ""
                
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
                
            content_parts = []
            
            content_parts.extend(self.extract_text_elements(soup))
            content_parts.extend(self.extract_tables(soup))
            
            # 应用文本去重：过滤掉重复的大段文本，避免响应式设计、SEO重复等导致的冗余
            deduplicated_parts = self.deduplicate_text_content(content_parts)
            
            return '\n'.join(filter(None, deduplicated_parts))
            
        except Exception as e:
            self.logger.error(f"内容提取失败: {e}")
            return ""
    
    def deduplicate_text_content(self, content_parts):
        """
        文本去重：行级去重 + 统一规范化 (改进版)

        改进点：
        1. 先按换行拆分为行级片段，粒度更细；
        2. 统一去掉前缀标记（如 [HTML_TABLE] 等）和行首符号（•、-、数字序号等）；
        3. 长度 <10 的行视为噪声直接过滤；
        4. 使用规范化文本（去空白、转小写）做去重判断。
        """
        if not content_parts:
            return content_parts

        deduplicated_parts = []
        seen = set()

        for part in content_parts:
            if not part or not isinstance(part, str):
                continue

            # 拆分行，避免整块文本去重失败
            for line in part.split('\n'):
                text = line.strip()
                if not text:
                    continue

                # 去掉像 [HTML_TABLE]、[GRID_TABLE] 等前缀标记
                text_no_prefix = re.sub(r'^\[[A-Z_]+\]\s*', '', text)
                # 去掉行首 bullet / 破折号 / 序号等
                text_no_prefix = re.sub(r'^[•●\-\u2022\s\d\.\)\(]+', '', text_no_prefix)

                # 规范化：去多余空白、转小写
                normalized = ' '.join(text_no_prefix.lower().split())
                if len(normalized) < 10:
                    # 信息量过低，跳过
                    continue

                if normalized in seen:
                    continue
                seen.add(normalized)

                # 保留原始行文本（含符号，保持可读性）
                deduplicated_parts.append(text)

        return deduplicated_parts
            
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
            for li in tag.find_all('li'):
                item_text = li.get_text().strip()
                if item_text:
                    content_parts.append(f"• {item_text}")
                
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
        """提取页面链接并进行过滤（兼容性方法，建议使用extract_links_from_soup）"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.extract_links_from_soup(soup, response)
        except Exception as e:
            self.logger.error(f"链接提取失败: {e}")
            return []
            
    def extract_links_from_soup(self, soup, response):
        """从soup对象提取页面链接并进行过滤；仅获取锚文本匹配的links"""
        try:
            if soup is None:
                return []
                
            # 从 response 中获取 project_id
            project_id = response.meta.get('project_id', 'unknown')
            
            # 统计所有链接
            all_links = soup.find_all('a', href=True)
            self.logger.info(f"[{project_id}] 页面总链接数: {len(all_links)}")
            
            # # 临时调试：打印所有原始链接的锚文本
            # self.logger.info(f"[{project_id}] === 原始链接锚文本列表 ===")
            # for i, link in enumerate(all_links):  # 只显示前20个避免日志过长
            #     anchor_text = link.get_text().strip()
            #     href = link.get('href', 'N/A')
            #     self.logger.info(f"[{project_id}] 原始链接{i+1}: '{anchor_text}' -> {href}")
            
            # 删除导航元素 - 减少误删，只删除明确的导航和页脚
            nav_selectors = ['footer', '.menu', "header"]  # 移除了'nav'避免误删页面主要内容
            removed_nav_count = 0
            for selector in nav_selectors:
                nav_elements = soup.select(selector)
                for nav_elem in nav_elements:
                    nav_elem.decompose()
                    removed_nav_count += len(nav_elem.find_all('a', href=True))
            
            remaining_links = soup.find_all('a', href=True)
            self.logger.info(f"[{project_id}] 移除导航后链接数: {len(remaining_links)} (移除了 {removed_nav_count} 个导航链接)")
            
            # # 临时调试：打印移除导航后的链接锚文本
            # self.logger.info(f"[{project_id}] === 移除导航后链接锚文本列表 ===")
            # for i, link in enumerate(remaining_links[:20]):  # 只显示前20个
            #     anchor_text = link.get_text().strip()
            #     href = link.get('href', 'N/A')
            #     self.logger.info(f"[{project_id}] 剩余链接{i+1}: '{anchor_text}' -> {href}")
            # if len(remaining_links) > 20:
            #     self.logger.info(f"[{project_id}] ... 还有 {len(remaining_links)-20} 个链接未显示")
                    
            links = []
            returned_urls = set()  # 页面内URL去重
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
                    matched_keyword = self.get_matched_keyword(href, anchor_text) # 仅匹配锚文本
                    if matched_keyword:
                        keyword_matched_count += 1
                        # 保存为结构化字典，便于JSON中查看和理解
                        # 页面内URL唯一性去重
                        if href in returned_urls:
                            continue  # 跳过重复 URL
                        returned_urls.add(href)

                        link_info = {
                            "url": href,                    # 链接地址
                            "anchor_text": anchor_text,     # 锚文本（链接显示的文字）
                            "matched_keyword": matched_keyword  # 匹配的白名单关键词
                        }
                        links.append(link_info)
                        self.logger.debug(f"[{project_id}] 匹配链接: {href} (锚文本: '{anchor_text}', 关键词: '{matched_keyword}')")

                    else:
                        self.logger.debug(f"[{project_id}] 链接不匹配关键词: {href} (锚文本: '{anchor_text}')")
                else:
                    self.logger.debug(f"[{project_id}] 无效链接: {href} (锚文本: '{anchor_text}')")
            
            self.logger.info(f"[{project_id}] 有效链接数: {valid_count}, 关键词匹配数: {keyword_matched_count}, 最终提取数: {len(links)}")
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
                
            return True
            
        except:
            return False
            
    def get_matched_keyword(self, url, anchor_text):
        """获取匹配的白名单关键词；检查anchor_text中是否包含白名单关键词"""
        from ..url_filter import URL_WHITELIST_KEYWORDS
        
        if not anchor_text:
            return None
            
        text_to_check = anchor_text.lower()
        
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
            responses = list(self.start_next_project())
            requests = []
            
            # 分离Request和Item对象
            for obj in responses:
                if hasattr(obj, 'url') and hasattr(obj, 'callback'):
                    # 这是一个Request对象
                    requests.append(obj)
                else:
                    # 这是一个Item对象，直接通过pipeline处理
                    self.crawler.engine.scraper.itemproc.process_item(obj, self)
            
            if requests:
                for req in requests:
                    # 直接通过 engine 调度，避免深度叠加（Scrapy ≥2.9 的 crawl 只接受 request 参数）
                    self.crawler.engine.crawl(req)
                raise DontCloseSpider  # 告诉 Scrapy 暂时不要关闭