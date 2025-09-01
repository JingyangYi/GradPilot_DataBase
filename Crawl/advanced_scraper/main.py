"""高级爬虫主入口 - 重试失败的URL"""

import asyncio
import sys
import os
import argparse

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from utils.log_analyzer import LogAnalyzer
from core.proxy_pool import ProxyPool
from core.retry_manager import RetryManager
from config.config import Config


async def retry_failed_urls(subject_name: str, config: Config = None):
    """重试指定科目的失败URL"""
    if config is None:
        config = Config()
    
    print(f"开始处理科目: {subject_name}")
    
    # 1. 分析失败日志
    analyzer = LogAnalyzer(config.paths.log_dir)
    failed_urls, stats = analyzer.get_latest_failed_urls(subject_name)
    
    if not failed_urls:
        print(f"科目 {subject_name} 没有失败的URL需要重试")
        return
    
    print(f"发现 {len(failed_urls)} 个失败URL:")
    for error_type, count in stats.items():
        print(f"  {error_type}: {count}")
    
    # 2. 获取可重试的URL
    retryable_urls = analyzer.get_retryable_urls(subject_name)
    if not retryable_urls:
        print("没有可重试的URL（全部是404错误）")
        return
    
    print(f"可重试URL数量: {len(retryable_urls)}")
    
    # 3. 设置代理池（如果启用）
    proxy_pool = None
    if config.proxy.enabled and config.proxy.proxies:
        proxy_pool = ProxyPool(config.proxy.max_fail_count)
        for proxy_config in config.proxy.proxies:
            proxy_pool.add_proxy(**proxy_config)
        print(f"代理池已启用，共 {len(config.proxy.proxies)} 个代理")
    
    # 4. 设置日志并执行重试
    log_file = config.get_retry_log_file(subject_name)
    retry_manager = RetryManager(proxy_pool, config.scraper.max_attempts, log_file, config)
    await retry_manager.start()
    
    try:
        results = await retry_manager.retry_failed_urls(retryable_urls)
        
        # 5. 保存结果（双重保存机制）
        output_file = config.get_retry_output_file(subject_name)
        retry_manager.save_results(results, output_file)
        
        # 5.1 同时合并到原始输出目录（output/subject/）
        successful_results = [r for r in results if r.success]
        
        # 6. 输出统计
        print(f"\n📊 === 高级爬虫执行完成 ===")
        print(f"📋 科目: {subject_name}")
        print(f"🔄 总重试项目: {len(results)}")
        print(f"✅ 成功项目: {len(successful_results)}")
        print(f"❌ 失败项目: {len(results) - len(successful_results)}")
        print(f"📈 成功率: {len(successful_results)/len(results)*100:.1f}%")
        
        # 统计子页面信息
        total_child_pages = 0
        if successful_results:
            await retry_manager.merge_to_original_output(successful_results)
            
            # 计算子页面数量
            for result in successful_results:
                if result.extracted_links:
                    total_child_pages += min(len(result.extracted_links), 20)
            
            print(f"🌐 子页面爬取: 最多 {total_child_pages} 个")
        
        # 统计最终失败的URL
        final_failed_count = len(results) - len(successful_results)
        if final_failed_count > 0:
            final_failed_file = output_file.replace('retry_results_', 'final_failed_urls_')
            print(f"❌ 最终失败URL: {final_failed_count} 个")
            print(f"   - 详细记录: {final_failed_file}")
        
        print(f"💾 输出位置:")
        print(f"   - 日志: {output_file}")
        print(f"   - 项目文件: output/{subject_name}/")
        
        print(f"\n🔍 详细日志请查看: {config.get_retry_log_file(subject_name)}")
        
    finally:
        await retry_manager.stop()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='高级爬虫 - 重试失败URL')
    parser.add_argument('subject', help='科目名称（如"交通运输"）')
    parser.add_argument('--headless', action='store_true', default=True, 
                       help='无头模式运行（默认启用）')
    parser.add_argument('--max-attempts', type=int, default=3,
                       help='最大重试次数（默认3次）')
    parser.add_argument('--timeout', type=int, default=30000,
                       help='请求超时时间（毫秒，默认30000）')
    
    args = parser.parse_args()
    
    # 创建配置
    config = Config.from_env()
    config.scraper.headless = args.headless
    config.scraper.max_attempts = args.max_attempts
    config.scraper.timeout = args.timeout
    
    try:
        await retry_failed_urls(args.subject, config)
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())