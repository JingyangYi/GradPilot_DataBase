BOT_NAME = 'program_crawler'

SPIDER_MODULES = ['program_crawler.spiders']
NEWSPIDER_MODULE = 'program_crawler.spiders'

ROBOTSTXT_OBEY = False

# USER_AGENT 现在由 RandomUserAgentMiddleware 动态设置

CONCURRENT_REQUESTS = 20
CONCURRENT_REQUESTS_PER_DOMAIN = 5

DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.8

COOKIES_ENABLED = True

TELNETCONSOLE_ENABLED = False

# DEFAULT_REQUEST_HEADERS 现在由 BrowserHeadersMiddleware 动态生成

# ------------------------------------------------------------
# AutoThrottle — 按延迟自动调节并发，降低触发 429/403 概率
# ------------------------------------------------------------

AUTOTHROTTLE_ENABLED = True
# 初始延迟 2 秒，最大可以放宽到 10 秒
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
# 目标并发 1.0 表示每个远端平均保持 1 个并发请求
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# 启用 AutoThrottle 调试信息
AUTOTHROTTLE_DEBUG = False

SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,  # 禁用OffsiteMiddleware
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'program_crawler.middlewares.RandomUserAgentMiddleware': 400,
    'program_crawler.middlewares.BrowserHeadersMiddleware': 500,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
}

ITEM_PIPELINES = {
    'program_crawler.pipelines.JsonWriterPipeline': 300,
}

RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

DOWNLOAD_TIMEOUT = 30

DEPTH_LIMIT = 2

LOG_LEVEL = 'INFO'

# 确保Scrapy不会过早关闭
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.LifoMemoryQueue'
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleLifoDiskQueue'

# 调整调度器设置，防止过早关闭
SCHEDULER_PRIORITY_QUEUE = 'scrapy.pqueues.ScrapyPriorityQueue'