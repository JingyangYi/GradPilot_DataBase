# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import HtmlResponse
import random

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class ProgramCrawlerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ProgramCrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


# =============================================================================
# RandomUserAgentMiddleware — 随机 UA 轮换中间件
# =============================================================================

class RandomUserAgentMiddleware:
    """
    随机轮换 User-Agent 的下载器中间件
    从预定义的真实浏览器 UA 池中随机选择，增加请求多样性，降低被识别为爬虫的概率
    """
    
    def __init__(self):
        self.user_agent_list = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            
            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            
            # Firefox on Windows  
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
            
            # Firefox on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0',
            
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
            
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
        ]
    
    def process_request(self, request, spider):
        """为每个请求随机分配一个 User-Agent"""
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        return None


# =============================================================================
# BrowserHeadersMiddleware — 优化浏览器请求头中间件  
# =============================================================================

class BrowserHeadersMiddleware:
    """
    根据当前 User-Agent 动态生成对应的浏览器请求头
    确保 UA 与 Sec-Ch-Ua 等头部信息保持一致，提高真实性
    """
    
    def process_request(self, request, spider):
        """根据 UA 动态调整请求头"""
        ua = request.headers.get('User-Agent', b'').decode('utf-8')
        
        # 基础头部
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # 根据 UA 调整 Sec-Ch-Ua 头部
        if 'Chrome/126' in ua:
            headers.update({
                'Sec-Ch-Ua': '"Not)A;Brand";v="99", "Google Chrome";v="126", "Chromium";v="126"',
                'Sec-Ch-Ua-Full-Version': '"126.0.6478.127"',
            })
        elif 'Chrome/125' in ua:
            headers.update({
                'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"', 
                'Sec-Ch-Ua-Full-Version': '"125.0.6422.142"',
            })
        elif 'Chrome/124' in ua:
            headers.update({
                'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'Sec-Ch-Ua-Full-Version': '"124.0.6367.243"',
            })
        elif 'Firefox' in ua:
            # Firefox 不需要 Sec-Ch-Ua 头部
            pass
        elif 'Safari' in ua and 'Chrome' not in ua:
            # Safari 不需要 Sec-Ch-Ua 头部
            pass
        elif 'Edg' in ua:
            if 'Edg/126' in ua:
                headers.update({
                    'Sec-Ch-Ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="126", "Chromium";v="126"',
                    'Sec-Ch-Ua-Full-Version': '"126.0.2592.102"',
                })
            elif 'Edg/125' in ua:
                headers.update({
                    'Sec-Ch-Ua': '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
                    'Sec-Ch-Ua-Full-Version': '"125.0.2535.92"',
                })
        
        # 添加平台信息（基于 UA 推断）
        if 'Windows NT 10.0' in ua:
            headers.update({
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Ch-Ua-Platform-Version': '"15.0.0"',
            })
        elif 'Macintosh' in ua:
            headers.update({
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Ch-Ua-Platform-Version': '"14.5.0"',
            })
        
        # 通用客户端提示
        if 'Chrome' in ua or 'Edg' in ua:
            headers.update({
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Arch': '"x86"',
                'Sec-Ch-Ua-Bitness': '"64"',
                'Sec-Ch-Ua-Model': '""',
                'Sec-Ch-Ua-Wow64': '?0',
            })
        
        # 更新请求头
        for key, value in headers.items():
            request.headers[key] = value
            
        return None 