"""日志分析模块 - 提取最新批次失败URL"""

import json
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class FailedURL:
    """失败URL的详细信息，保留Scrapy原始数据"""
    # 基本标识信息
    project_id: str
    program_name: str
    source_file: str
    url: str
    
    # 错误信息
    error_type: str  # '403', '404', 'other'
    error_message: str
    timestamp: str
    
    # 可选的技术细节
    http_status: Optional[int] = None
    response_headers: Optional[Dict] = None
    response_preview: Optional[str] = None


class LogAnalyzer:
    def __init__(self, log_dir: str = "log"):
        self.log_dir = log_dir
        
    def get_latest_failed_urls(self, subject_name: str) -> Tuple[List[FailedURL], Dict[str, int]]:
        """获取最新批次失败URL"""
        log_dir = os.path.join(self.log_dir, subject_name)
        if not os.path.exists(log_dir):
            return [], {}
        
        all_failed = []
        
        # 读取所有 failed_urls*.json 文件
        for file in os.listdir(log_dir):
            if file.startswith('failed_urls_') and file.endswith('.json'):
                file_path = os.path.join(log_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            error_type = self._classify_error(item.get('http_status'), item.get('error', ''))
                            all_failed.append(FailedURL(
                                project_id=item.get('project_id', ''),
                                program_name=item.get('program_name', ''),
                                source_file=item.get('source_file', ''),
                                url=item['url'],
                                error_type=error_type,
                                error_message=item.get('error', ''),
                                http_status=item.get('http_status'),
                                timestamp=item['timestamp'],
                                response_headers=item.get('response_headers'),
                                response_preview=item.get('response_preview')
                            ))
                except Exception as e:
                    print(f"读取 {file_path} 失败: {e}")
        
        # 按日期分组，取最新
        groups = self._group_by_date(all_failed)
        if not groups:
            return [], {}
            
        latest_date = max(groups.keys())
        latest_urls = groups[latest_date]
        
        # 去重
        unique = {}
        for url in latest_urls:
            if url.url not in unique or url.timestamp > unique[url.url].timestamp:
                unique[url.url] = url
        
        final_urls = list(unique.values())
        stats = defaultdict(int)
        for url in final_urls:
            stats[url.error_type] += 1
        
        return final_urls, dict(stats)
    
    def get_retryable_urls(self, subject_name: str) -> List[FailedURL]:
        """获取可重试URL（排除404）"""
        failed_urls, _ = self.get_latest_failed_urls(subject_name)
        return [url for url in failed_urls if url.error_type != '404']
    
    def _classify_error(self, status_code, error_msg: str) -> str:
        if status_code == 403:
            return '403'
        elif status_code == 404:
            return '404'
        else:
            return 'other'
    
    def _group_by_date(self, failed_urls: List[FailedURL]) -> Dict[str, List[FailedURL]]:
        groups = defaultdict(list)
        for url in failed_urls:
            date = url.timestamp[:10]  # 取日期部分
            groups[date].append(url)
        return dict(groups)


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    failed_urls, stats = analyzer.get_latest_failed_urls("交通运输")
    print(f"失败URL数: {len(failed_urls)}")
    print(f"统计: {stats}")
    retryable = analyzer.get_retryable_urls("交通运输")
    print(f"可重试: {len(retryable)}")