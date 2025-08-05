"""
数据处理管道 - JSON文件保存器

功能：
1. 接收Spider爬取的结构化数据
2. 生成安全的文件名
3. 保存为格式化的JSON文件
4. 处理中文字符编码

保存策略：
- 每个项目独立保存为一个JSON文件
- 文件名格式：{项目名}_{来源文件}.json
- 使用UTF-8编码确保中文正确显示
"""

import json
import os
import re


class JsonWriterPipeline:
    """
    JSON文件写入管道
    
    负责将爬取的项目数据保存为JSON文件
    每个项目生成一个独立的JSON文件，便于后续处理
    """
    
    def __init__(self):
        """
        初始化管道
        
        创建输出目录，准备文件保存环境
        """
        self.output_dir = 'output'  # 输出目录名
        
        # 如果输出目录不存在，则创建
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"创建输出目录: {self.output_dir}")
    
    def process_item(self, item, spider):
        """
        处理每个爬取完成的项目数据
        
        执行流程：
        1. 提取项目名称和来源文件信息
        2. 生成安全的文件名（处理特殊字符）
        3. 构建完整的文件路径
        4. 保存为格式化的JSON文件
        5. 记录保存日志
        
        Args:
            item: 包含项目数据的Item对象
            spider: 当前运行的Spider实例
            
        Returns:
            item: 原始Item对象（管道链传递）
        """
        # 提取项目基本信息，设置默认值防止KeyError
        program_name = item.get('program_name', 'unknown_program')
        source_file = item.get('source_file', 'unknown.json')
        
        # 清理文件名，确保文件系统兼容性
        safe_program_name = self.sanitize_filename(program_name)
        safe_source_file = source_file.replace('.json', '')  # 移除原有扩展名
        
        # 根据来源文件创建子文件夹
        subject_dir = os.path.join(self.output_dir, safe_source_file)
        if not os.path.exists(subject_dir):
            os.makedirs(subject_dir)
        
        # 构建文件名：项目名_来源文件.json
        filename = f"{safe_program_name}_{safe_source_file}.json"
        filepath = os.path.join(subject_dir, filename)
        
        # 保存JSON文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(
                    dict(item),  # 将Item转换为字典
                    f,
                    ensure_ascii=False,  # 保持中文字符不转义
                    indent=2,  # 格式化缩进，便于阅读
                    sort_keys=True  # 对键进行排序，便于比较
                )
            
            # 记录成功保存的日志
            spider.logger.info(f'成功保存项目数据: {filepath}')
            
        except Exception as e:
            # 记录保存失败的错误
            spider.logger.error(f'保存文件失败 {filepath}: {str(e)}')
            raise
        
        return item  # 返回原始item，供下一个管道处理
    
    def sanitize_filename(self, filename):
        """
        清理文件名，确保文件系统兼容性
        
        处理策略：
        1. 移除特殊字符，只保留字母、数字、空格、连字符
        2. 将空格和连字符统一替换为下划线
        3. 限制文件名长度，避免路径过长问题
        
        Args:
            filename (str): 原始文件名
            
        Returns:
            str: 清理后的安全文件名
            
        Example:
            >>> sanitize_filename("哈佛大学-数据科学硕士项目!")
            "哈佛大学_数据科学硕士项目"
        """
        if not filename:
            return "unknown"
        
        # 移除不安全的字符，保留中文、英文、数字、空格、连字符
        # 使用\w匹配字母数字下划线，\s匹配空格，-匹配连字符
        filename = re.sub(r'[^\w\s\-\u4e00-\u9fff]', '', filename)
        
        # 将多个空格或连字符替换为单个下划线
        filename = re.sub(r'[-\s]+', '_', filename)
        
        # 移除首尾的下划线
        filename = filename.strip('_')
        
        # 限制文件名长度为50个字符，避免路径过长
        return filename[:50] if len(filename) > 50 else filename