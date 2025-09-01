BOT_NAME = 'program_crawler'

SPIDER_MODULES = ['program_crawler.spiders']
NEWSPIDER_MODULE = 'program_crawler.spiders'

ROBOTSTXT_OBEY = False

# USER_AGENT 现在由 RandomUserAgentMiddleware 动态设置

# 🚀 阶段1保守优化：提升并发和减少延迟，保持高稳定性
CONCURRENT_REQUESTS = 40           # ↑ 从28提升到40 (+43%)
CONCURRENT_REQUESTS_PER_DOMAIN = 10  # ↑ 从6提升到10 (+67%)

DOWNLOAD_DELAY = 0.4              # ↓ 从0.6降低到0.4 (-33%)
RANDOMIZE_DOWNLOAD_DELAY = 0.2     # ↓ 从0.3降低到0.2，实际延迟范围：0.2-0.6秒

COOKIES_ENABLED = True

TELNETCONSOLE_ENABLED = False

# DEFAULT_REQUEST_HEADERS 现在由 BrowserHeadersMiddleware 动态生成

# ------------------------------------------------------------
# AutoThrottle — 按延迟自动调节并发，降低触发 429/403 概率
# ------------------------------------------------------------

AUTOTHROTTLE_ENABLED = True
# 🚀 阶段1 AutoThrottle优化：适度提升目标并发
AUTOTHROTTLE_START_DELAY = 0.4      # ↓ 从0.6降低到0.4，与DOWNLOAD_DELAY保持一致
AUTOTHROTTLE_MAX_DELAY = 4          # 保持不变
# 目标并发提升到4.0，在稳定性和速度间取得平衡
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0  # ↑ 从3.0提升到4.0 (+33%)
# 关闭 AutoThrottle 调试信息，避免日志过度冗余
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

RETRY_TIMES = 5                # ↑ 从3提升到5 (+67%) 提高成功率
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 403]  # + 添加403到重试列表

DOWNLOAD_TIMEOUT = 20

DEPTH_LIMIT = 2

LOG_LEVEL = 'INFO'

# 确保Scrapy不会过早关闭
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.LifoMemoryQueue'
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleLifoDiskQueue'

# 调整调度器设置，防止过早关闭
SCHEDULER_PRIORITY_QUEUE = 'scrapy.pqueues.ScrapyPriorityQueue'

# ============================================================
# 🚀 阶段1优化配置监控
# ============================================================
# 优化生效时间：2025-09-01
# 预期效果：速度提升30-50%，错误率增长<5%
# 监控重点：
# - 成功率保持 >90%
# - HTTP 429 错误 <5%
# - HTTP 403 错误 <3%
# - 总体错误率 <15%
# ============================================================