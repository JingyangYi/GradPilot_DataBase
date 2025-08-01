import scrapy

class ProgramPageItem(scrapy.Item):
    """
    项目页面数据结构定义
    
    定义爬虫输出的数据字段，确保数据结构一致性
    """
    # 项目基本信息
    project_id = scrapy.Field()      # 项目唯一标识符
    program_name = scrapy.Field()    # 项目名称（中文）
    source_file = scrapy.Field()     # 来源文件名
    
    # 爬取信息
    root_url = scrapy.Field()        # 根URL
    crawl_time = scrapy.Field()      # 爬取时间戳
    
    # 页面数据
    pages = scrapy.Field()           # 所有页面数据列表
    total_pages = scrapy.Field()     # 页面总数
    
    # 状态信息
    status = scrapy.Field()          # 爬取状态