"""配置管理模块"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ScraperConfig:
    """爬虫配置"""
    headless: bool = True
    timeout: int = 30000
    max_attempts: int = 3
    delay_between_requests: float = 2.0
    user_agents: List[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]


@dataclass 
class ProxyConfig:
    """代理配置"""
    enabled: bool = False
    proxies: List[Dict[str, Any]] = None
    max_fail_count: int = 3
    
    def __post_init__(self):
        if self.proxies is None:
            self.proxies = []


@dataclass
class PathConfig:
    """路径配置"""
    log_dir: str = "log"
    output_dir: str = "output" 
    retry_output_dir: str = "advanced_scraper/results"
    
    def __post_init__(self):
        # 确保输出目录存在
        os.makedirs(self.retry_output_dir, exist_ok=True)
    
    def get_advanced_scraper_log_dir(self, subject_name: str) -> str:
        """获取高级爬虫日志目录"""
        advanced_log_dir = os.path.join(self.log_dir, subject_name, "advanced_scraper")
        os.makedirs(advanced_log_dir, exist_ok=True)
        return advanced_log_dir


class Config:
    """统一配置管理"""
    
    def __init__(self):
        self.scraper = ScraperConfig()
        self.proxy = ProxyConfig()
        self.paths = PathConfig()
        
    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量加载配置"""
        config = cls()
        
        # 爬虫配置
        config.scraper.headless = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
        config.scraper.timeout = int(os.getenv('SCRAPER_TIMEOUT', '30000'))
        config.scraper.max_attempts = int(os.getenv('SCRAPER_MAX_ATTEMPTS', '3'))
        
        # 代理配置
        config.proxy.enabled = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
        
        return config
    
    def get_retry_output_file(self, subject_name: str) -> str:
        """获取重试结果输出文件路径（带时间戳）"""
        from datetime import datetime
        # 将重试结果保存到subject的log目录下的advanced_scraper子目录
        advanced_log_dir = self.paths.get_advanced_scraper_log_dir(subject_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"retry_results_{subject_name}_{timestamp}.json"
        return os.path.join(advanced_log_dir, filename)
    
    def get_retry_log_file(self, subject_name: str) -> str:
        """获取重试过程日志文件路径（带时间戳）"""
        from datetime import datetime
        advanced_log_dir = self.paths.get_advanced_scraper_log_dir(subject_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"retry_log_{subject_name}_{timestamp}.log"
        return os.path.join(advanced_log_dir, filename)
    
    def get_final_failed_urls_file(self, subject_name: str) -> str:
        """获取最终失败URL文件路径（保存到advanced_scraper/final_failed_urls目录）"""
        from datetime import datetime
        # 获取advanced_scraper目录的绝对路径
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 创建final_failed_urls子目录
        final_failed_dir = os.path.join(current_dir, "final_failed_urls")
        os.makedirs(final_failed_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_failed_urls_{subject_name}_{timestamp}.json"
        return os.path.join(final_failed_dir, filename)


# 默认配置实例
default_config = Config()


if __name__ == "__main__":
    config = Config.from_env()
    print(f"爬虫配置: headless={config.scraper.headless}, timeout={config.scraper.timeout}")
    print(f"代理配置: enabled={config.proxy.enabled}")
    print(f"输出目录: {config.paths.retry_output_dir}")