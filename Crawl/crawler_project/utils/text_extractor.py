#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本提取工具
专门用于从HTML中提取干净的文本内容，排除SVG、CSS等无关元素
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Comment, Tag


class TextExtractor:
    """文本提取器 - 专注于提取有意义的文本内容"""
    
    def __init__(self):
        # 需要完全移除的标签
        self.excluded_tags = {
            'script', 'style', 'meta', 'link', 'noscript',
            'svg', 'path', 'g', 'rect', 'circle', 'line',  # SVG元素
            'head', 'title'  # 不需要在正文中的head元素
        }
        
        # 需要移除但保留内容的标签
        self.unwrap_tags = {
            'span', 'div', 'b', 'i', 'strong', 'em', 'u',
            'font', 'small', 'big', 'sub', 'sup'
        }
        
        # 段落和块级标签 - 添加换行
        self.block_tags = {
            'p', 'div', 'section', 'article', 'header', 'footer',
            'main', 'aside', 'nav', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'li', 'dt', 'dd', 'tr', 'th', 'td', 'blockquote', 'pre'
        }
    
    def extract_clean_text(self, html: str) -> str:
        """
        提取干净的文本内容
        
        Args:
            html: 原始HTML内容
            
        Returns:
            str: 清理后的纯文本
        """
        if not html:
            return ""
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 1. 移除不需要的元素
            self._remove_unwanted_elements(soup)
            
            # 2. 处理特殊元素
            self._process_special_elements(soup)
            
            # 3. 提取文本并清理
            text = self._extract_and_clean_text(soup)
            
            return text
            
        except Exception as e:
            print(f"文本提取失败: {e}")
            return ""
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """移除不需要的HTML元素"""
        
        # 移除注释
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # 移除不需要的标签
        for tag_name in self.excluded_tags:
            for tag in soup.find_all(tag_name):
                tag.extract()
        
        # 移除导航栏、页脚等
        navigation_selectors = [
            'nav', '.nav', '.navbar', '.navigation',
            'header', '.header', 'footer', '.footer',
            '.breadcrumb', '.sidebar', '.aside',
            '.social', '.share', '.advertisement', '.ads'
        ]
        
        for selector in navigation_selectors:
            for element in soup.select(selector):
                element.extract()
    
    def _process_special_elements(self, soup: BeautifulSoup):
        """处理特殊元素"""
        
        # 处理链接 - 保留文本，移除href
        for link in soup.find_all('a'):
            if link.string:
                link.replace_with(link.get_text())
        
        # 处理图片 - 用alt文本替换
        for img in soup.find_all('img'):
            alt_text = img.get('alt', '')
            if alt_text:
                img.replace_with(f"[图片: {alt_text}]")
            else:
                img.extract()
        
        # 处理表格 - 保持结构
        for table in soup.find_all('table'):
            self._process_table(table)
    
    def _process_table(self, table: Tag):
        """处理表格，保持基本结构"""
        for row in table.find_all('tr'):
            cells = []
            for cell in row.find_all(['td', 'th']):
                cell_text = cell.get_text().strip()
                if cell_text:
                    cells.append(cell_text)
            
            if cells:
                row_text = ' | '.join(cells)
                row.replace_with(row_text + '\n')
        
        # 如果表格为空，移除它
        if not table.get_text().strip():
            table.extract()
    
    def _extract_and_clean_text(self, soup: BeautifulSoup) -> str:
        """提取并清理文本"""
        
        # 为块级元素添加换行符
        for tag in soup.find_all(self.block_tags):
            tag.insert_after('\n')
        
        # 提取文本
        text = soup.get_text()
        
        # 清理文本
        text = self._clean_extracted_text(text)
        
        return text
    
    def _clean_extracted_text(self, text: str) -> str:
        """清理提取的文本"""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 标准化换行符
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 移除行首行尾空白
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
        
        text = '\n'.join(lines)
        
        # 移除重复的短语（可能来自模板）
        text = self._remove_duplicate_phrases(text)
        
        return text.strip()
    
    def _remove_duplicate_phrases(self, text: str) -> str:
        """移除重复的短语"""
        lines = text.split('\n')
        seen_lines = set()
        unique_lines = []
        
        for line in lines:
            # 跳过太短的行
            if len(line) < 10:
                unique_lines.append(line)
                continue
            
            # 检查是否重复
            line_lower = line.lower().strip()
            if line_lower not in seen_lines:
                seen_lines.add(line_lower)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def extract_title(self, html: str) -> str:
        """提取页面标题"""
        if not html:
            return ""
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 优先顺序：h1 > title > og:title
            title = ""
            
            # 1. 查找主要的h1标题
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
            
            # 2. 查找title标签
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
            
            # 3. 查找og:title
            if not title:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title = og_title.get('content', '').strip()
            
            return title or "无标题"
            
        except Exception:
            return "无标题"
    
    def extract_links_with_text(self, html: str, selectors: List[str]) -> List[Dict[str, str]]:
        """
        根据选择器提取链接及其文本
        
        Args:
            html: HTML内容
            selectors: CSS选择器列表
            
        Returns:
            List[Dict]: [{'url': str, 'text': str}, ...]
        """
        if not html:
            return []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            links = []
            seen_urls = set()
            
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get('href')
                        if not href or href.startswith('#'):
                            continue
                        
                        # 避免重复
                        if href in seen_urls:
                            continue
                        seen_urls.add(href)
                        
                        # 提取链接文本
                        link_text = element.get_text().strip()
                        if not link_text:
                            # 尝试从父元素获取上下文
                            parent = element.parent
                            if parent:
                                link_text = parent.get_text().strip()[:100]
                        
                        if href and link_text:
                            links.append({
                                'url': href,
                                'text': link_text
                            })
                
                except Exception as e:
                    print(f"选择器 {selector} 处理失败: {e}")
                    continue
            
            return links
            
        except Exception as e:
            print(f"链接提取失败: {e}")
            return []


# 默认文本提取器实例
DEFAULT_TEXT_EXTRACTOR = TextExtractor() 