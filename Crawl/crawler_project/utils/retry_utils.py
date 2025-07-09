#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试机制工具
实现智能重试策略，提高爬虫稳定性
"""

import asyncio
import random
import time
from typing import Any, Callable, List, Optional, Dict
from dataclasses import dataclass
from functools import wraps


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True  # 添加随机性避免雷达效应
    
    # 可重试的异常类型
    retriable_exceptions: List[str] = None
    
    def __post_init__(self):
        if self.retriable_exceptions is None:
            self.retriable_exceptions = [
                'TimeoutError',
                'ConnectionError', 
                'NetworkError',
                'TemporaryFailure'
            ]


class RetryManager:
    """重试管理器"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.attempt_history: Dict[str, List[float]] = {}
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟时间
        
        Args:
            attempt: 当前重试次数
            
        Returns:
            float: 延迟时间（秒）
        """
        # 指数退避
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        # 添加随机抖动
        if self.config.jitter:
            jitter_range = delay * 0.1  # 10%的随机性
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(delay, 0.1)  # 最小延迟0.1秒
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        判断是否应该重试
        
        Args:
            exception: 发生的异常
            attempt: 当前重试次数
            
        Returns:
            bool: 是否应该重试
        """
        # 检查是否超过最大重试次数
        if attempt >= self.config.max_attempts:
            return False
        
        # 检查异常类型是否可重试
        exception_name = type(exception).__name__
        return exception_name in self.config.retriable_exceptions
    
    async def retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        异步重试装饰器
        
        Args:
            func: 要重试的异步函数
            *args, **kwargs: 函数参数
            
        Returns:
            Any: 函数返回值
            
        Raises:
            Exception: 最后一次失败的异常
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return await func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                # 记录重试历史
                func_name = func.__name__
                if func_name not in self.attempt_history:
                    self.attempt_history[func_name] = []
                self.attempt_history[func_name].append(time.time())
                
                print(f"函数 {func_name} 第 {attempt + 1} 次尝试失败: {e}")
                
                # 判断是否应该重试
                if not self.should_retry(e, attempt):
                    raise e
                
                # 最后一次尝试不需要延迟
                if attempt < self.config.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    print(f"等待 {delay:.2f} 秒后重试...")
                    await asyncio.sleep(delay)
        
        # 如果所有重试都失败，抛出最后的异常
        raise last_exception
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """获取重试统计信息"""
        stats = {}
        
        for func_name, attempts in self.attempt_history.items():
            stats[func_name] = {
                'total_attempts': len(attempts),
                'success_rate': 1.0 if len(attempts) == 1 else 0.0,  # 简化计算
                'last_attempt': max(attempts) if attempts else None
            }
        
        return stats


def retry_on_failure(config: RetryConfig = None):
    """
    重试装饰器 - 用于同步函数
    
    Args:
        config: 重试配置
        
    Returns:
        装饰器函数
    """
    retry_config = config or RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(retry_config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    print(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}")
                    
                    # 判断是否应该重试
                    exception_name = type(e).__name__
                    if (attempt >= retry_config.max_attempts - 1 or 
                        exception_name not in retry_config.retriable_exceptions):
                        raise e
                    
                    # 计算延迟
                    delay = min(
                        retry_config.base_delay * (retry_config.exponential_base ** attempt),
                        retry_config.max_delay
                    )
                    
                    if retry_config.jitter:
                        jitter = delay * 0.1 * random.uniform(-1, 1)
                        delay += jitter
                    
                    print(f"等待 {delay:.2f} 秒后重试...")
                    time.sleep(max(delay, 0.1))
            
            raise last_exception
        
        return wrapper
    return decorator


async def retry_on_network_error(func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
    """
    网络错误重试 - 专门用于网络相关操作
    
    Args:
        func: 要重试的异步函数
        max_retries: 最大重试次数
        *args, **kwargs: 函数参数
        
    Returns:
        Any: 函数返回值
    """
    network_errors = [
        'TimeoutError', 'ConnectionError', 'NetworkError',
        'ConnectTimeout', 'ReadTimeout', 'DNSLookupError'
    ]
    
    config = RetryConfig(
        max_attempts=max_retries,
        base_delay=2.0,
        max_delay=30.0,
        retriable_exceptions=network_errors
    )
    
    retry_manager = RetryManager(config)
    return await retry_manager.retry_async(func, *args, **kwargs)


class CircuitBreaker:
    """断路器模式 - 防止持续失败"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过断路器调用函数
        
        Args:
            func: 要调用的函数
            *args, **kwargs: 函数参数
            
        Returns:
            Any: 函数返回值
            
        Raises:
            Exception: 断路器开启时的异常
        """
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置断路器"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """成功时的处理"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """失败时的处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


# 默认重试管理器实例
DEFAULT_RETRY_MANAGER = RetryManager()
DEFAULT_CIRCUIT_BREAKER = CircuitBreaker() 