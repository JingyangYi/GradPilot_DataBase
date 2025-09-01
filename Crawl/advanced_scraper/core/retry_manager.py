"""重试管理模块 - 管理不同类型失败的重试策略"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_analyzer import FailedURL
from core.proxy_pool import ProxyPool, Proxy
from core.scraper import AdvancedScraper
from core.content_processor import ContentProcessor


@dataclass
class RetryResult:
    """增强的重试结果，包含详细的爬取信息"""
    # 基本信息
    project_id: str
    program_name: str
    source_file: str
    url: str
    
    # 重试结果
    success: bool
    attempts: int = 0
    error: Optional[str] = None
    final_status_code: Optional[int] = None
    
    # 页面信息
    title: Optional[str] = None
    content_length: int = 0
    links_found: int = 0
    
    # 技术细节
    proxy_used: Optional[str] = None
    response_headers: Optional[Dict[str, str]] = None
    cloudflare_detected: bool = False
    
    # 时间信息
    retry_timestamp: str = None
    total_retry_time: float = 0.0
    
    # 内容数据（成功时）
    extracted_content: Optional[str] = None
    extracted_links: Optional[List[Dict[str, str]]] = None


class RetryManager:
    def __init__(self, proxy_pool: Optional[ProxyPool] = None, max_attempts: int = 3, log_file: Optional[str] = None, config=None):
        self.proxy_pool = proxy_pool
        self.max_attempts = max_attempts
        self.scraper = AdvancedScraper()
        self.config = config  # 添加配置引用
        
        # 设置日志记录器
        self.logger = logging.getLogger('advanced_scraper')
        self.logger.setLevel(logging.INFO)
        
        # 传递logger给ContentProcessor
        self.processor = ContentProcessor(logger=self.logger)
        
        if log_file and not self.logger.handlers:
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # 同时输出到控制台
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
    async def start(self):
        """启动管理器"""
        await self.scraper.start()
        
    async def stop(self):
        """停止管理器"""
        await self.scraper.stop()
        
    async def retry_failed_urls(self, failed_urls: List[FailedURL]) -> List[RetryResult]:
        """重试失败的URL列表"""
        results = []
        self.logger.info(f"开始重试 {len(failed_urls)} 个失败URL")
        
        for i, failed_url in enumerate(failed_urls, 1):
            self.logger.info(f"[{i}/{len(failed_urls)}] 重试 {failed_url.error_type}: {failed_url.url}")
            
            result = await self._retry_single_url(failed_url)
            results.append(result)
            
            if result.success:
                self.logger.info(f"✓ 重试成功，尝试次数: {result.attempts}")
            else:
                self.logger.warning(f"✗ 重试失败: {result.error}")
            
            # 延迟避免过于频繁的请求
            await asyncio.sleep(2)
            
        self.logger.info(f"重试完成，成功: {len([r for r in results if r.success])}/{len(results)}")
        return results
    
    async def _retry_single_url(self, failed_url: FailedURL) -> RetryResult:
        """重试单个URL并收集详细信息"""
        import time
        start_time = time.time()
        proxy_used = None
        cloudflare_detected = False
        final_status_code = None
        response_headers = None
        last_error = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                # 根据错误类型选择策略
                proxy = None
                if failed_url.error_type == '403' and self.proxy_pool:
                    proxy = self.proxy_pool.get_proxy()
                    proxy_used = proxy.url if proxy else None
                    
                # 尝试获取页面
                page_data = await self.scraper.fetch_page(failed_url.url, proxy)
                
                if page_data:
                    final_status_code = page_data.get('status_code')
                    response_headers = page_data.get('headers', {})
                    
                    # 检测Cloudflare
                    if 'cloudflare' in str(response_headers).lower() or 'just a moment' in page_data.get('content', '').lower():
                        cloudflare_detected = True
                    
                    if 'content' in page_data and final_status_code == 200:
                        # 处理内容，传递正确的深度信息
                        processed = self.processor.process_page(page_data['content'], failed_url.url, depth=0)
                        
                        if processed['is_meaningful']:
                            # 成功
                            if proxy:
                                self.proxy_pool.mark_success(proxy)
                                
                            return RetryResult(
                                project_id=failed_url.project_id,
                                program_name=failed_url.program_name,
                                source_file=failed_url.source_file,
                                url=failed_url.url,
                                success=True,
                                attempts=attempt,
                                final_status_code=final_status_code,
                                title=processed['title'],
                                content_length=len(processed['content']),
                                links_found=len(processed['links']),
                                proxy_used=proxy_used,
                                response_headers=response_headers,
                                cloudflare_detected=cloudflare_detected,
                                retry_timestamp=datetime.now().isoformat(),
                                total_retry_time=time.time() - start_time,
                                extracted_content=processed['content'],
                                extracted_links=processed['links']
                            )
                        else:
                            last_error = "内容无意义"
                    else:
                        last_error = f"HTTP {final_status_code}"
                else:
                    last_error = "无响应数据"
                
                # 失败，继续重试
                if proxy:
                    self.proxy_pool.mark_failed(proxy)
                    
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"尝试 {attempt} 失败: {e}")
                if attempt < self.max_attempts:
                    await asyncio.sleep(attempt * 2)  # 指数退避
        
        # 所有重试都失败了
        return RetryResult(
            project_id=failed_url.project_id,
            program_name=failed_url.program_name,
            source_file=failed_url.source_file,
            url=failed_url.url,
            success=False,
            attempts=self.max_attempts,
            error=last_error or "达到最大重试次数",
            final_status_code=final_status_code,
            proxy_used=proxy_used,
            response_headers=response_headers,
            cloudflare_detected=cloudflare_detected,
            retry_timestamp=datetime.now().isoformat(),
            total_retry_time=time.time() - start_time
        )
    
    def save_results(self, results: List[RetryResult], output_file: str):
        """保存详细的重试结果，同时合并到原始Scrapy输出"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        # 技术统计
        cloudflare_count = len([r for r in results if r.cloudflare_detected])
        proxy_count = len([r for r in results if r.proxy_used])
        avg_retry_time = sum(r.total_retry_time for r in results) / len(results) if results else 0
        
        # 错误类型统计
        error_stats = {}
        for result in failed_results:
            error_key = f"HTTP_{result.final_status_code}" if result.final_status_code else result.error
            error_stats[error_key] = error_stats.get(error_key, 0) + 1
        
        # 主要结果数据
        output_data = {
            'crawl_time': datetime.now().isoformat(),
            'summary': {
                'total_retried': len(results),
                'successful': len(successful_results),
                'failed': len(failed_results),
                'success_rate': len(successful_results) / len(results) * 100 if results else 0,
                'avg_retry_time_seconds': round(avg_retry_time, 2),
                'cloudflare_detected_count': cloudflare_count,
                'proxy_used_count': proxy_count
            },
            'error_statistics': error_stats,
            'results': [asdict(result) for result in results]
        }
        
        # 1. 保存到log目录（原有逻辑）
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        # 创建成功页面的Scrapy格式输出
        if successful_results:
            success_output_file = output_file.replace('retry_results_', 'successful_pages_')
            self._save_successful_pages(successful_results, success_output_file)
            self.logger.info(f"成功页面数据已保存到: {success_output_file}")
            
            # 2. 合并成功结果到原始Scrapy输出目录
            self.merge_to_original_output(successful_results)
        
        # 3. 保存最终失败的URL（高级爬虫重试后仍然失败）
        if failed_results:
            final_failed_file = output_file.replace('retry_results_', 'final_failed_urls_')
            self._save_final_failed_urls(failed_results, final_failed_file)
            self.logger.info(f"最终失败URL已保存到: {final_failed_file}")
            print(f"⚠ 发现 {len(failed_results)} 个最终失败URL，已记录到: {final_failed_file}")
            
            # 4. 额外保存重试2次后失败的URL到advanced_scraper目录
            if hasattr(self, 'config') and self.config:
                subject_name = self._extract_subject_name(output_file)
                if subject_name:
                    self._save_failed_urls_to_advanced_scraper(failed_results, subject_name)
            
        self.logger.info(f"重试结果已保存到: {output_file}")
        self.logger.info(f"重试结果已保存到: {output_file}")
        self.logger.info(f"统计: 总计 {output_data['summary']['total_retried']}, 成功 {output_data['summary']['successful']}, 失败 {output_data['summary']['failed']}")
        self.logger.info(f"成功率: {output_data['summary']['success_rate']:.1f}%, 平均重试时间: {output_data['summary']['avg_retry_time_seconds']}秒")
    
    def _save_successful_pages(self, successful_results: List[RetryResult], output_file: str):
        """保存成功页面的详细数据，采用类似Scrapy output的格式"""
        pages_data = []
        
        for result in successful_results:
            if result.extracted_content and result.extracted_links:
                page_data = {
                    'project_id': result.project_id,
                    'program_name': result.program_name,
                    'source_file': result.source_file,
                    'url': result.url,
                    'crawl_status': 'success_via_advanced_scraper',
                    'retry_attempts': result.attempts,
                    'title': result.title,
                    'content': result.extracted_content,
                    'links': result.extracted_links,
                    'retry_details': {
                        'proxy_used': result.proxy_used,
                        'cloudflare_detected': result.cloudflare_detected,
                        'final_status_code': result.final_status_code,
                        'retry_time_seconds': result.total_retry_time,
                        'retry_timestamp': result.retry_timestamp
                    }
                }
                pages_data.append(page_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pages_data, f, ensure_ascii=False, indent=2)
    
    def _save_final_failed_urls(self, failed_results: List[RetryResult], output_file: str):
        """保存最终失败的URL，供后续分析或手动处理"""
        from datetime import datetime
        
        final_failed_data = {
            'crawl_time': datetime.now().isoformat(),
            'description': '高级爬虫重试后仍然失败的URL列表',
            'total_failed_urls': len(failed_results),
            'failed_urls': []
        }
        
        # 统计错误类型
        error_summary = {}
        
        for result in failed_results:
            # 分类错误类型
            error_category = 'Unknown'
            if result.final_status_code:
                if result.final_status_code == 403:
                    error_category = 'HTTP_403_Forbidden'
                elif result.final_status_code == 404:
                    error_category = 'HTTP_404_NotFound'
                elif result.final_status_code == 503:
                    error_category = 'HTTP_503_ServiceUnavailable'
                elif result.final_status_code == 429:
                    error_category = 'HTTP_429_RateLimit'
                else:
                    error_category = f'HTTP_{result.final_status_code}'
            elif 'timeout' in result.error.lower():
                error_category = 'Network_Timeout'
            elif 'cloudflare' in result.error.lower():
                error_category = 'Cloudflare_Block'
            elif 'content' in result.error.lower():
                error_category = 'Content_Quality'
            else:
                error_category = 'Other_Error'
            
            # 统计
            error_summary[error_category] = error_summary.get(error_category, 0) + 1
            
            # 详细失败信息
            failed_url_info = {
                'project_id': result.project_id,
                'program_name': result.program_name,
                'source_file': result.source_file,
                'url': result.url,
                'error_category': error_category,
                'final_error': result.error,
                'http_status_code': result.final_status_code,
                'attempts_made': result.attempts,
                'total_retry_time_seconds': round(result.total_retry_time, 2),
                'proxy_used': result.proxy_used,
                'cloudflare_detected': result.cloudflare_detected,
                'retry_timestamp': result.retry_timestamp,
                'response_headers': result.response_headers if hasattr(result, 'response_headers') else None
            }
            
            final_failed_data['failed_urls'].append(failed_url_info)
        
        # 添加错误统计摘要
        final_failed_data['error_summary'] = error_summary
        
        # 保存文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_failed_data, f, ensure_ascii=False, indent=2)
    
    def _save_failed_urls_to_advanced_scraper(self, failed_results: List[RetryResult], subject_name: str):
        """保存重试2次后依然失败的URL到advanced_scraper目录"""
        if not self.config:
            self.logger.warning("无配置信息，跳过保存到advanced_scraper目录")
            return
        
        # 筛选出重试次数达到最大值（通常是2次）的失败URL
        max_retry_failed = [r for r in failed_results if r.attempts >= 2 and not r.success]
        
        if not max_retry_failed:
            return
        
        from datetime import datetime
        
        # 获取保存到advanced_scraper目录的路径
        output_file = self.config.get_final_failed_urls_file(subject_name)
        
        failed_urls_data = {
            'crawl_time': datetime.now().isoformat(),
            'description': f'重试{self.max_attempts}次后依然失败的URL列表（保存到advanced_scraper目录）',
            'subject_name': subject_name,
            'max_attempts': self.max_attempts,
            'total_failed_after_max_retries': len(max_retry_failed),
            'failed_urls': []
        }
        
        # 错误统计
        error_stats = {}
        
        for result in max_retry_failed:
            # 分类错误
            error_type = 'Unknown'
            if result.final_status_code:
                error_type = f'HTTP_{result.final_status_code}'
            elif result.error:
                if 'timeout' in result.error.lower():
                    error_type = 'Timeout'
                elif 'cloudflare' in result.error.lower():
                    error_type = 'Cloudflare'
                elif 'content' in result.error.lower() or '内容' in result.error:
                    error_type = 'ContentQuality'
                else:
                    error_type = 'Other'
            
            error_stats[error_type] = error_stats.get(error_type, 0) + 1
            
            # URL信息
            failed_url_entry = {
                'project_id': result.project_id,
                'program_name': result.program_name,
                'source_file': result.source_file,
                'url': result.url,
                'error_type': error_type,
                'final_error_message': result.error,
                'http_status_code': result.final_status_code,
                'attempts_made': result.attempts,
                'total_retry_time_seconds': round(result.total_retry_time, 2),
                'proxy_used': result.proxy_used,
                'cloudflare_detected': result.cloudflare_detected,
                'timestamp': result.retry_timestamp
            }
            
            failed_urls_data['failed_urls'].append(failed_url_entry)
        
        # 添加错误统计
        failed_urls_data['error_statistics'] = error_stats
        
        # 保存到advanced_scraper目录
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(failed_urls_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"✓ 重试{self.max_attempts}次后失败的{len(max_retry_failed)}个URL已保存到: {output_file}")
            print(f"📝 重试{self.max_attempts}次后失败的URL记录: {output_file}")
            
        except Exception as e:
            self.logger.error(f"保存失败URL到advanced_scraper目录时出错: {e}")
    
    def _extract_subject_name(self, output_file: str) -> str:
        """从输出文件路径中提取科目名称"""
        import re
        
        # 从类似这样的路径中提取科目名称:
        # log/交通运输/advanced_scraper/retry_results_交通运输_20250901_123456.json
        match = re.search(r'retry_results_([^_]+)_\d+_\d+\.json', output_file)
        if match:
            return match.group(1)
        
        # 备选方案：从路径中提取
        parts = output_file.split('/')
        for part in parts:
            if part and part not in ['log', 'advanced_scraper', 'retry_results']:
                if not part.startswith('retry_') and not part.endswith('.json'):
                    return part
        
        return None
    
    async def merge_to_original_output(self, successful_results: List[RetryResult]):
        """将重试成功的结果合并到原始Scrapy输出目录"""
        import os
        
        # 根据项目分组
        projects_by_source = {}
        for result in successful_results:
            source_file = result.source_file
            project_id = result.project_id
            
            if source_file not in projects_by_source:
                projects_by_source[source_file] = {}
            
            if project_id not in projects_by_source[source_file]:
                projects_by_source[source_file][project_id] = []
            
            projects_by_source[source_file][project_id].append(result)
        
        for source_file, projects in projects_by_source.items():
            for project_id, results_for_project in projects.items():
                await self._merge_project_to_output(source_file, project_id, results_for_project)
    
    async def _merge_project_to_output(self, source_file: str, project_id: str, results: List[RetryResult]):
        """将单个项目的重试成功结果合并到output目录，使用Scrapy的文件命名格式"""
        import os
        import re
        
        # 构建output目录路径
        crawl_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        output_dir = os.path.join(crawl_dir, 'output', source_file)
        
        # 使用Scrapy的文件命名逻辑: {program_name}_{source_file}.json
        if results:
            program_name = results[0].program_name
            safe_program_name = self.sanitize_filename(program_name)
            filename = f"{safe_program_name}_{source_file}.json"
            original_file = os.path.join(output_dir, filename)
        else:
            self.logger.warning(f"无法确定文件名，结果为空")
            return
            
        try:
            if os.path.exists(original_file):
                # 读取原始数据
                with open(original_file, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                
                # 添加重试成功的页面数据，包括根页面和子链接页面
                for result in results:
                    if result.extracted_content and result.extracted_links is not None:
                        # 根页面数据
                        root_page_data = {
                            'url': result.url,
                            'depth': 0,  # 重试的都是根URL
                            'title': result.title or '',
                            'content': result.extracted_content,
                            'links': result.extracted_links,
                            'crawl_status': 'success_via_advanced_scraper',
                            'retry_details': {
                                'attempts': result.attempts,
                                'retry_timestamp': result.retry_timestamp,
                                'proxy_used': result.proxy_used,
                                'cloudflare_detected': result.cloudflare_detected
                            }
                        }
                        
                        # 更新统计信息
                        original_data['pages'].append(root_page_data)
                        # Scrapy没有successful_pages字段，只有total_pages
                        original_data['total_pages'] += 1
                        
                        # 添加重试标记
                        if 'retry_info' not in original_data:
                            original_data['retry_info'] = {
                                'has_retry_data': True,
                                'retry_timestamp': result.retry_timestamp,
                                'retry_successful_pages': 0,
                                'retry_child_pages': 0
                            }
                        original_data['retry_info']['retry_successful_pages'] += 1
                        
                        # 添加子链接页面（模拟Scrapy的子页面爬取）
                        if result.extracted_links:
                            child_pages_added = await self._add_child_pages_to_output(original_data, result)
                            original_data['retry_info']['retry_child_pages'] += child_pages_added
                
                # 保存更新后的数据
                with open(original_file, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, ensure_ascii=False, indent=2)
                    
                self.logger.info(f"已将重试成功结果合并到: {original_file}")
                self.logger.info(f"✓ 已将{len(results)}个重试成功页面合并到: {original_file}")
            else:
                # 原始文件不存在，创建新的输出文件
                self.logger.warning(f"原始输出文件不存在: {original_file}")
                self.logger.info(f"为重试成功的结果创建新的输出文件")
                
                # 确保目录存在
                os.makedirs(os.path.dirname(original_file), exist_ok=True)
                
                # 创建符合Scrapy格式的新文件
                if results:
                    first_result = results[0]
                    new_data = {
                        "crawl_time": datetime.now().isoformat(),
                        "pages": [],
                        "program_name": first_result.program_name,
                        "project_id": first_result.project_id,
                        "root_url": first_result.url, 
                        "source_file": first_result.source_file,
                        "status": "completed_via_advanced_scraper",
                        "total_pages": 0,
                        "retry_info": {
                            "has_retry_data": True,
                            "retry_timestamp": datetime.now().isoformat(),
                            "retry_successful_pages": 0,
                            "retry_child_pages": 0
                        }
                    }
                    
                    # 添加所有重试成功的页面
                    for result in results:
                        if result.extracted_content and result.extracted_links is not None:
                            # 根页面数据
                            root_page_data = {
                                'url': result.url,
                                'depth': 0,
                                'title': result.title or '',
                                'content': result.extracted_content,
                                'links': result.extracted_links,
                                'crawl_status': 'success_via_advanced_scraper_new',
                                'retry_details': {
                                    'attempts': result.attempts,
                                    'retry_timestamp': result.retry_timestamp,
                                    'proxy_used': result.proxy_used,
                                    'cloudflare_detected': result.cloudflare_detected
                                }
                            }
                            
                            new_data['pages'].append(root_page_data)
                            new_data['total_pages'] += 1
                            new_data['retry_info']['retry_successful_pages'] += 1
                            
                            # 添加子链接页面
                            if result.extracted_links:
                                child_pages_added = await self._add_child_pages_to_output(new_data, result)
                                new_data['retry_info']['retry_child_pages'] += child_pages_added
                    
                    # 保存新文件
                    with open(original_file, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=2)
                    
                    self.logger.info(f"已创建新的输出文件: {original_file}")
                    self.logger.info(f"✓ 已为{len(results)}个重试成功页面创建新文件: {original_file}")
                
        except Exception as e:
            self.logger.error(f"合并结果到output目录时出错: {e}")
    
    def validate_scrapy_compatibility(self, retry_result_data: Dict) -> bool:
        """验证重试结果与Scrapy输出格式的兼容性"""
        required_fields = [
            'url', 'depth', 'title', 'content', 'links', 'crawl_status'
        ]
        
        for field in required_fields:
            if field not in retry_result_data:
                self.logger.error(f"缺少必需字段: {field}")
                return False
        
        # 验证links格式
        for link in retry_result_data.get('links', []):
            if not all(k in link for k in ['url', 'anchor_text', 'matched_keyword']):
                self.logger.error(f"链接格式不正确: {link}")
                return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名，复制pipelines.py的逻辑"""
        import re
        
        if not filename:
            return "unknown"
        
        # 移除不安全的字符，保留中文、英文、数字、空格、连字符
        filename = re.sub(r'[^\w\s\-\u4e00-\u9fff]', '', filename)
        
        # 将多个空格或连字符替换为单个下划线
        filename = re.sub(r'[-\s]+', '_', filename)
        
        # 移除首尾的下划线
        filename = filename.strip('_')
        
        # 限制文件名长度为50个字符，避免路径过长
        return filename[:50] if len(filename) > 50 else filename
    
    async def _add_child_pages_to_output(self, original_data: dict, parent_result: RetryResult) -> int:
        """模拟Scrapy的子页面爬取逻辑，为根页面的子链接爬取内容"""
        if not parent_result.extracted_links:
            return 0
            
        child_pages_added = 0
        
        # 处理子链接，最多20个以防止过多请求
        max_child_pages = 20
        links_to_process = parent_result.extracted_links[:max_child_pages]
        total_links = len(parent_result.extracted_links)
        
        self.logger.info(f"开始爬取子页面: 发现 {total_links} 个子链接，将处理前 {len(links_to_process)} 个")
        
        for i, link_info in enumerate(links_to_process, 1):
            child_url = link_info.get('url')
            if not child_url:
                continue
                
            try:
                # 爬取子页面
                child_page_data = await self.scraper.fetch_page(child_url)
                if child_page_data and 'content' in child_page_data:
                    # 处理子页面内容（深度=1，不提取更多链接）
                    processed = self.processor.process_page(child_page_data['content'], child_url, depth=1)
                    
                    if processed['is_meaningful']:
                        child_page_entry = {
                            'url': child_url,
                            'depth': 1,  # 子页面深度为1
                            'title': processed['title'],
                            'content': processed['content'],
                            'links': [],  # 子页面不提取链接
                            'crawl_status': 'success_via_advanced_scraper_child',
                            'parent_url': parent_result.url,
                            'matched_keyword': link_info.get('matched_keyword', ''),
                            'retry_details': {
                                'retry_timestamp': parent_result.retry_timestamp,
                                'parent_attempts': parent_result.attempts
                            }
                        }
                        
                        original_data['pages'].append(child_page_entry)
                        # Scrapy没有successful_pages字段，只有total_pages
                        original_data['total_pages'] += 1
                        child_pages_added += 1
                        
                        self.logger.info(f"成功添加子页面 [{i}/{len(links_to_process)}]: {child_url}")
                        
                        # 添加小延迟避免过于频繁的请求
                        await asyncio.sleep(1)
                        
            except Exception as e:
                self.logger.warning(f"子页面爬取失败 [{i}/{len(links_to_process)}] {child_url}: {e}")
                continue
        
        self.logger.info(f"子页面爬取完成: 成功 {child_pages_added}/{len(links_to_process)} 个，跳过 {total_links - len(links_to_process)} 个")
        return child_pages_added


async def main():
    """测试函数"""
    from ..utils.log_analyzer import LogAnalyzer
    
    # 测试重试管理器
    analyzer = LogAnalyzer()
    failed_urls = analyzer.get_retryable_urls("交通运输")
    
    if failed_urls:
        manager = RetryManager()
        await manager.start()
        
        try:
            results = await manager.retry_failed_urls(failed_urls[:2])  # 只测试前2个
            manager.save_results(results, "test_retry_results.json")
        finally:
            await manager.stop()
    else:
        print("没有找到可重试的URL")  # 保留用户提示


if __name__ == "__main__":
    asyncio.run(main())