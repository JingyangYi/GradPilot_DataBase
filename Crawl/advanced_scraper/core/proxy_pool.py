"""代理池管理模块"""

import time
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class Proxy:
    host: str
    port: int
    username: str = ""
    password: str = ""
    proxy_type: str = "http"  # http, socks5
    fail_count: int = 0
    last_used: float = 0
    
    @property
    def url(self) -> str:
        if self.username:
            return f"{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type}://{self.host}:{self.port}"


class ProxyPool:
    def __init__(self, max_fail_count: int = 3):
        self.proxies: List[Proxy] = []
        self.max_fail_count = max_fail_count
        
    def add_proxy(self, host: str, port: int, username: str = "", password: str = "", proxy_type: str = "http"):
        """添加代理"""
        proxy = Proxy(host, port, username, password, proxy_type)
        self.proxies.append(proxy)
        
    def get_proxy(self) -> Optional[Proxy]:
        """获取可用代理"""
        available = [p for p in self.proxies if p.fail_count < self.max_fail_count]
        if not available:
            return None
            
        # 按上次使用时间排序，选择最久未使用的
        available.sort(key=lambda x: x.last_used)
        proxy = available[0]
        proxy.last_used = time.time()
        return proxy
        
    def mark_failed(self, proxy: Proxy):
        """标记代理失败"""
        proxy.fail_count += 1
        
    def mark_success(self, proxy: Proxy):
        """标记代理成功"""
        proxy.fail_count = max(0, proxy.fail_count - 1)  # 成功时减少失败计数
        
    def get_stats(self) -> Dict[str, int]:
        """获取代理池统计"""
        total = len(self.proxies)
        available = len([p for p in self.proxies if p.fail_count < self.max_fail_count])
        failed = total - available
        return {"total": total, "available": available, "failed": failed}


def create_default_pool() -> ProxyPool:
    """创建默认代理池（示例配置）"""
    pool = ProxyPool()
    # 这里可以添加你的代理配置
    # pool.add_proxy("proxy1.example.com", 8080, "user", "pass")
    # pool.add_proxy("proxy2.example.com", 1080, "", "", "socks5")
    return pool


if __name__ == "__main__":
    pool = create_default_pool()
    print(f"代理池统计: {pool.get_stats()}")