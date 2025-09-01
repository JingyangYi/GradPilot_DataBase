"""高级爬虫核心模块 - Playwright反检测爬虫"""

import asyncio
import random
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.proxy_pool import Proxy


class AdvancedScraper:
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-dev-shm-usage'
            ]
        )
        
    async def stop(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def create_stealth_page(self, proxy: Optional[Proxy] = None) -> Page:
        """创建反检测页面"""
        context_kwargs = {
            'viewport': {'width': 1366, 'height': 768},
            'user_agent': self._get_random_user_agent(),
            'locale': 'en-US',
            'timezone_id': 'America/New_York'
        }
        
        if proxy:
            context_kwargs['proxy'] = {
                'server': proxy.url,
                'username': proxy.username,
                'password': proxy.password
            }
            
        context = await self.browser.new_context(**context_kwargs)
        page = await context.new_page()
        
        # 反检测脚本
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
                app: { isInstalled: false }
            };
        """)
        
        return page
        
    async def fetch_page(self, url: str, proxy: Optional[Proxy] = None) -> Optional[Dict[str, Any]]:
        """获取页面内容"""
        page = None
        try:
            page = await self.create_stealth_page(proxy)
            
            # 随机延迟
            await asyncio.sleep(random.uniform(1, 3))
            
            # 导航到页面
            response = await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
            
            if not response:
                return None
                
            # 检查是否被Cloudflare阻挡
            if await self._is_cloudflare_challenge(page):
                await asyncio.sleep(5)  # 等待Cloudflare处理
                
            # 等待页面加载
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # 获取页面内容
            content = await page.content()
            title = await page.title()
            
            return {
                'url': url,
                'content': content,
                'title': title,
                'status_code': response.status,
                'headers': dict(response.headers)
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'status_code': None
            }
        finally:
            if page:
                await page.context.close()
                
    async def _is_cloudflare_challenge(self, page: Page) -> bool:
        """检测Cloudflare挑战页面"""
        try:
            # 检查常见的Cloudflare元素
            cf_selectors = [
                'div[class*="cf-browser-verification"]',
                'div[id*="cf-wrapper"]',
                'div[class*="cf-error-overview"]',
                'title:has-text("Just a moment...")',
                'h1:has-text("Please wait...")'
            ]
            
            for selector in cf_selectors:
                element = await page.query_selector(selector)
                if element:
                    return True
                    
            # 检查页面标题
            title = await page.title()
            if 'just a moment' in title.lower() or 'please wait' in title.lower():
                return True
                
            return False
            
        except Exception:
            return False
            
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)


async def main():
    """测试函数"""
    scraper = AdvancedScraper()
    await scraper.start()
    
    try:
        result = await scraper.fetch_page("https://httpbin.org/user-agent")
        if result and 'content' in result:
            print(f"成功获取页面，状态码: {result.get('status_code')}")
            print(f"标题: {result.get('title')}")
        else:
            print(f"获取失败: {result}")
    finally:
        await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())