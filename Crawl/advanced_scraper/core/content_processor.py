"""内容处理模块 - 复制Scrapy的内容提取逻辑"""

import sys
import os
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

# 添加路径以导入过滤模块
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from program_crawler.url_filter import filter_url


class ContentProcessor:
    """复制Scrapy spider的内容处理逻辑"""
    
    def __init__(self, logger=None):
        """初始化内容处理器"""
        if logger is None:
            import logging
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger
    
    def process_page(self, html_content: str, url: str, depth: int = 0) -> Dict[str, Any]:
        """处理页面内容，完全复制Scrapy的完整逻辑"""
        # 🎯 一次解析HTML，多次复用 - 性能优化核心 (复制program_spider.py:244)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 先提取链接，使用完整的soup (复制program_spider.py:248-252)
        links = []
        if depth < 1:  # 只有根页面或深度<1的页面才提取链接
            links = self.extract_links_from_soup(soup, url, depth)
        
        # 再提取其他内容（会删除导航元素）
        title = self.extract_title_from_soup(soup)
        content = self.extract_structured_content_from_soup(soup)
        
        return {
            'title': title,
            'content': content,
            'links': links,
            'is_meaningful': self.is_content_meaningful(title, content, links)
        }
    
    def extract_title_from_soup(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        try:
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.get_text().strip()
            
            # 备选：查找h1标签
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.get_text().strip()
                
            return ""
        except Exception:
            return ""
    
    def extract_structured_content_from_soup(self, soup: BeautifulSoup) -> str:
        """提取保留HTML结构的内容用于RAG系统"""
        try:
            if soup is None:
                return ""
            
            # 移除不需要的元素
            for script in soup(["script", "style", "header", "footer", "aside"]):
                script.decompose()
            
            content_parts = []
            
            # 提取并保留标题结构
            content_parts.extend(self.extract_structured_headings(soup))
            
            # 提取并保留表格结构
            content_parts.extend(self.extract_structured_tables(soup))
            
            # 提取段落和列表内容
            content_parts.extend(self.extract_structured_text_elements(soup))
            
            return '\n'.join(filter(None, content_parts))
            
        except Exception:
            return ""
    
    def extract_structured_headings(self, soup: BeautifulSoup) -> List[str]:
        """提取保留层级的标题结构"""
        content_parts = []
        
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if text:
                tag_name = tag.name.upper()
                content_parts.append(f"<{tag_name}>{text}</{tag_name}>")
        
        return content_parts
    
    def extract_structured_tables(self, soup: BeautifulSoup) -> List[str]:
        """提取保留结构的表格内容"""
        content_parts = []
        
        for table in soup.find_all('table'):
            table_html = self.extract_clean_table_html(table)
            if table_html:
                content_parts.append(table_html)
        
        return content_parts
    
    def extract_clean_table_html(self, table) -> str:
        """提取清理后的表格HTML结构"""
        try:
            table_content = ["<table>"]
            
            for tr in table.find_all('tr'):
                row_content = ["<tr>"]
                
                for cell in tr.find_all(['td', 'th']):
                    cell_text = cell.get_text().strip()
                    tag_name = cell.name
                    if cell_text:
                        row_content.append(f"<{tag_name}>{cell_text}</{tag_name}>")
                    else:
                        row_content.append(f"<{tag_name}></{tag_name}>")
                
                if len(row_content) > 1:
                    row_content.append("</tr>")
                    table_content.append("".join(row_content))
            
            table_content.append("</table>")
            
            if len(table_content) > 2:
                return "\n".join(table_content)
            
            return ""
            
        except Exception:
            return ""
    
    def extract_structured_text_elements(self, soup: BeautifulSoup) -> List[str]:
        """提取其他文本元素，保持基本结构"""
        content_parts = []
        
        # 提取段落
        for tag in soup.find_all('p'):
            text = tag.get_text().strip()
            if text and len(text) > 10:
                content_parts.append(f"<p>{text}</p>")
        
        # 提取列表
        for tag in soup.find_all(['ul', 'ol']):
            list_items = []
            for li in tag.find_all('li'):
                li_text = li.get_text().strip()
                if li_text:
                    list_items.append(f"<li>{li_text}</li>")
            
            if list_items:
                list_tag = tag.name
                content_parts.append(f"<{list_tag}>{''.join(list_items)}</{list_tag}>")
        
        return content_parts
    
    def extract_links_from_soup(self, soup: BeautifulSoup, base_url: str, depth: int = 0) -> List[Dict[str, str]]:
        """从 soup 对象提取页面链接并进行过滤；仅获取锥文本匹配的 links"""
        try:
            if soup is None:
                return []
            
            # 模拟project_id用于日志输出
            project_id = "advanced_scraper"
            
            # 统计所有链接 (复制program_spider.py:698-700)
            all_links = soup.find_all('a', href=True)
            self.logger.debug(f"[{project_id}] 页面总链接数: {len(all_links)}")
            
            # 删除导航元素 - 减少误删，只删除明确的导航和页脚 (复制program_spider.py:709-717)
            nav_selectors = ['footer', 'header']  # 移除了'nav'避免误删页面主要内容
            removed_nav_count = 0
            for selector in nav_selectors:
                nav_elements = soup.select(selector)
                for nav_elem in nav_elements:
                    removed_nav_count += len(nav_elem.find_all('a', href=True))
                    nav_elem.decompose()
            
            remaining_links = soup.find_all('a', href=True)
            self.logger.debug(f"[{project_id}] 移除导航后链接数: {len(remaining_links)} (移除了 {removed_nav_count} 个导航链接)")
            
            links = []
            returned_urls = set()  # 页面内URL去重
            valid_count = 0
            keyword_matched_count = 0
            
            for a_tag in remaining_links:
                href = a_tag['href']
                anchor_text = a_tag.get_text().strip()
                
                # 转换为绝对URL (复制program_spider.py:739-741)
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                    
                # 移除fragment (复制program_spider.py:743-744)
                href = href.split('#')[0]
                
                # 跳过指向当前页面的链接（避免自循环）(复制program_spider.py:746-748)
                if href == base_url:
                    continue
                    
                if self.is_valid_link(href, base_url):
                    valid_count += 1
                    matched_keyword = self.get_matched_keyword(href, anchor_text) # 仅匹配锚文本
                    if matched_keyword:
                        keyword_matched_count += 1
                        # 页面内URL唯一性去重 (复制program_spider.py:756-759)
                        if href in returned_urls:
                            continue  # 跳过重复 URL
                        returned_urls.add(href)
                        
                        # 🎯 完全复制Scrapy的过滤逻辑: if not filter_url(link_url, anchor_text=anchor_text)
                        if not filter_url(href, anchor_text=anchor_text):
                            link_info = {
                                "url": href,                    # 链接地址
                                "anchor_text": anchor_text,     # 锚文本（链接显示的文字）
                                "matched_keyword": matched_keyword  # 匹配的白名单关键词
                            }
                            links.append(link_info)
                            self.logger.debug(f"[{project_id}] 匹配链接: {href} (锚文本: '{anchor_text}', 关键词: '{matched_keyword}')")
                        else:
                            self.logger.debug(f"[{project_id}] 链接被filter_url过滤: {href} (锚文本: '{anchor_text}')")

                    else:
                        self.logger.debug(f"[{project_id}] 链接不匹配关键词: {href} (锚文本: '{anchor_text}')")
                else:
                    self.logger.debug(f"[{project_id}] 无效链接: {href} (锚文本: '{anchor_text}')")
            
            self.logger.info(f"[{project_id}] 有效链接数: {valid_count}, 关键词匹配数: {keyword_matched_count}, 最终提取数: {len(links)}")
            return links
            
        except Exception as e:
            self.logger.error(f"[advanced_scraper] 链接提取失败: {e}")
            return []
    
    def get_matched_keyword(self, url: str, anchor_text: str) -> Optional[str]:
        """复制program_spider.py:796-809的匹配逻辑"""
        from program_crawler.url_filter import URL_WHITELIST_KEYWORDS
        
        if not anchor_text:
            return None
            
        text_to_check = anchor_text.lower()
        
        for keyword in URL_WHITELIST_KEYWORDS:
            if keyword in text_to_check:
                return keyword
                
        return None
    
    def is_valid_link(self, url: str, base_url: str) -> bool:
        """检查链接是否有效 (复制program_spider.py:782-794)"""
        try:
            parsed_url = urlparse(url)
            base_parsed = urlparse(base_url)
            
            if not parsed_url.netloc:
                return False
                
            return True
            
        except:
            return False
    
    def is_content_meaningful(self, title: str, content: str, links: List[Dict[str, str]]) -> bool:
        """验证页面内容是否有意义"""
        try:
            # 简单检测：标题、内容、链接全部为空才认为失败
            if not title.strip() and not content.strip() and not links:
                return False
            return True
        except Exception:
            return True


if __name__ == "__main__":
    # 测试
    processor = ContentProcessor()
    test_html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Main Title</h1>
            <p>This is a test paragraph.</p>
            <table>
                <tr><th>Header</th></tr>
                <tr><td>Data</td></tr>
            </table>
            <a href="/test">Test Link</a>
        </body>
    </html>
    """
    
    result = processor.process_page(test_html, "https://example.com")
    print(f"Title: {result['title']}")
    print(f"Content length: {len(result['content'])}")
    print(f"Links count: {len(result['links'])}")
    print(f"Is meaningful: {result['is_meaningful']}")