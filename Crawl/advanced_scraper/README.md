# Advanced Scraper Implementation Plan

## 项目概述

高级爬虫系统用于在Scrapy正常爬取完成后，对失败的URL进行二次重试。采用All-in-One Playwright方案，应对各类WAF、反爬虫检测和JavaScript渲染问题。

## 目录结构

```
advanced_scraper/
├── README.md                    # 本文档
├── requirements.txt             # Python依赖包
├── config/
│   ├── __init__.py
│   ├── settings.py             # 配置参数
│   └── user_agents.txt         # 真实浏览器User-Agent库
├── core/
│   ├── __init__.py
│   ├── scraper.py              # 主要爬虫类
│   ├── proxy_pool.py           # 代理池管理
│   └── content_processor.py    # 内容处理器
├── utils/
│   ├── __init__.py
│   ├── log_analyzer.py         # 失败日志分析器
│   ├── file_utils.py           # 文件操作工具
│   └── validation.py           # 内容验证工具
├── scripts/
│   ├── __init__.py
│   ├── retry_manager.py        # 重试管理器主程序
│   └── test_scraper.py         # 测试脚本
└── logs/
    └── advanced_scraper.log    # 高级爬虫日志
```

## 核心功能模块

### 1. 失败日志分析器 (utils/log_analyzer.py)

**功能**: 分析Scrapy产生的失败日志，提取需要重试的URL

**关键任务**:
- 扫描 `log/{subject}/` 目录下的所有失败日志文件
- 识别最新爬取批次的时间戳
- 解析不同类型的失败记录 (HTTP403, HTTP404, TIMEOUT等)
- 按失败类型分类URL，优化重试策略
- 去重处理，避免重复重试

**核心方法**:
```python
class LogAnalyzer:
    def get_latest_failed_urls(self, subject_name: str) -> Dict[str, List[Dict]]
    def parse_failed_logs(self, log_dir: str) -> Dict[str, List[Dict]]
    def extract_latest_timestamp(self, log_files: List[str]) -> str
    def categorize_failures(self, failed_records: List[Dict]) -> Dict[str, List[Dict]]
```

### 2. 万能高级爬虫 (core/scraper.py)

**功能**: 使用Playwright实现的全能型反检测爬虫

**技术栈**:
- **Playwright + Chromium**: 主要浏览器引擎
- **反检测技术**: 移除webdriver痕迹、伪造浏览器特征
- **代理轮换**: 住宅代理、数据中心代理、移动代理
- **行为模拟**: 鼠标移动、滚动、停留时间
- **智能等待**: 网络空闲、元素加载、Cloudflare挑战检测

**核心方法**:
```python
class UniversalAdvancedScraper:
    async def scrape_url(self, url: str, max_retries: int = 3) -> Optional[Dict]
    async def _setup_stealth_browser(self, proxy: Optional[str] = None) -> BrowserContext
    async def _simulate_human_behavior(self, page: Page) -> None
    async def _intelligent_wait(self, page: Page, url: str) -> None
    async def _extract_content(self, page: Page) -> Dict
    def _validate_content(self, content: Dict, url: str) -> bool
```

**渐进式重试策略**:
1. **策略1**: 基础隐身模式 + 数据中心代理
2. **策略2**: 增强隐身模式 + 住宅代理 + 行为模拟
3. **策略3**: 最高级别 + 移动代理 + 额外请求头

### 3. 内容处理器 (core/content_processor.py)

**功能**: 完整复刻Scrapy（Crawl/program_crawler/spiders/program_spider.py）的内容提取逻辑，确保数据格式一致性

**必须复刻的Scrapy方法**:
- `extract_title_from_soup()` - 标题提取
- `extract_structured_content_from_soup()` - 结构化内容提取
- `extract_links_from_soup()` - 链接提取与过滤
- `extract_structured_headings()` - 标题层级提取
- `extract_structured_tables()` - 表格结构提取
- `extract_structured_text_elements()` - 段落和列表提取
- `is_content_meaningful()` - 内容质量验证
- URL过滤逻辑 (基于url_filter.py的白名单关键词)

**关键要求**:
- 保持与Scrapy完全相同的数据格式
- 使用相同的URL过滤白名单关键词
- 保持相同的链接提取和验证逻辑
- 生成相同格式的页面数据结构

**输出格式**:
```python
{
    'url': str,
    'depth': int,
    'title': str,
    'content': str,  # 结构化HTML内容
    'links': List[Dict],  # [{'url': str, 'anchor_text': str, 'matched_keyword': str}]
    'crawl_status': str,  # 'success' or 'content_quality_failed'
    'failure_reason': Optional[str]
}
```

### 4. 代理池管理器 (core/proxy_pool.py)

**功能**: 智能代理轮换，应对IP封锁

**代理类型**:
- **住宅代理**: 高成功率，适合严格WAF
- **数据中心代理**: 高速度，适合一般防护
- **移动代理**: 最高隐蔽性，应对极端情况

**核心方法**:
```python
class ProxyPool:
    def get_proxy_for_domain(self, domain: str) -> Optional[str]
    def mark_proxy_failed(self, proxy: str, domain: str) -> None
    def is_strict_domain(self, domain: str) -> bool
    def rotate_proxy(self, current_proxy: str) -> str
```

### 5. 重试管理器 (scripts/retry_manager.py)

**功能**: 主程序入口，协调整个重试流程

**工作流程**:
1. 接收学科名称参数
2. 分析该学科的最新失败日志
3. 按失败类型对URL进行分组
4. 调用高级爬虫进行批量重试
5. 保存重试结果到相应格式
6. 生成重试报告和统计信息

**核心方法**:
```python
class RetryManager:
    async def process_subject_failures(self, subject_name: str) -> Dict
    async def batch_retry_urls(self, failed_urls: List[Dict]) -> List[Dict]
    def save_retry_results(self, subject_name: str, results: List[Dict]) -> None
    def generate_retry_report(self, subject_name: str, results: List[Dict]) -> Dict
```

## 集成方案

### 修改 run_all_subjects.py

在现有的学科处理循环中，添加失败重试阶段：

```python
# 原始代码修改点
for i, csv_file in enumerate(selected_group, 1):
    print(f"\n[{i}/{len(selected_group)}] 爬取: {csv_file}")
    
    # 阶段1: Scrapy正常爬取
    try:
        subprocess.run([sys.executable, "run_crawler.py", csv_file], check=True)
        print(f"✓ Scrapy爬取完成")
        
        # 阶段2: 高级爬虫重试失败URL (新增)
        subject_name = extract_subject_name(csv_file)  # 从文件路径提取学科名
        retry_result = await run_advanced_retry(subject_name)
        print(f"✓ 高级重试完成: {retry_result['success_count']}/{retry_result['total_count']}")
        
    except subprocess.CalledProcessError:
        print(f"✗ Scrapy爬取失败")
        continue
```

### 新增函数

```python
def extract_subject_name(csv_file_path: str) -> str:
    """从CSV文件路径提取学科名称"""
    # 例: "urls_subject/交通运输/交通运输_urls.csv" -> "交通运输"
    
async def run_advanced_retry(subject_name: str) -> Dict:
    """运行高级爬虫重试"""
    from advanced_scraper.scripts.retry_manager import RetryManager
    
    retry_manager = RetryManager()
    results = await retry_manager.process_subject_failures(subject_name)
    
    return {
        'subject': subject_name,
        'total_count': results.get('total_attempted', 0),
        'success_count': results.get('successful_retries', 0),
        'failure_count': results.get('failed_retries', 0),
        'skip_count': results.get('skipped_404s', 0)
    }
```

## 技术实现细节

### 1. Cloudflare检测与处理

```python
async def _is_cloudflare_challenge(self, page: Page) -> bool:
    """检测Cloudflare挑战页面"""
    try:
        # 检测标题和页面元素
        title = await page.title()
        if 'just a moment' in title.lower():
            return True
            
        # 检测特征元素
        cf_elements = await page.query_selector_all('[data-ray], .cf-browser-verification')
        return len(cf_elements) > 0
        
    except Exception:
        return False

async def _wait_for_cloudflare_resolution(self, page: Page, timeout: int = 30000) -> bool:
    """等待Cloudflare挑战解决"""
    try:
        # 等待页面跳转或内容改变
        await page.wait_for_function(
            """
            () => {
                const title = document.title.toLowerCase();
                return !title.includes('just a moment') && !title.includes('please wait');
            }
            """,
            timeout=timeout
        )
        return True
    except TimeoutError:
        return False
```

### 2. 内容提取的Scrapy兼容性

```python
async def extract_scrapy_compatible_content(self, page: Page, url: str) -> Dict:
    """提取与Scrapy格式完全兼容的内容"""
    
    # 获取页面HTML
    html_content = await page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 使用与Scrapy相同的提取方法
    from ..utils.scrapy_compat import ScrapyCompatExtractor
    extractor = ScrapyCompatExtractor(soup, url)
    
    return {
        'url': url,
        'depth': 0,  # 重试的都是根URL，深度为0
        'title': extractor.extract_title(),
        'content': extractor.extract_structured_content(),
        'links': extractor.extract_links(),
        'crawl_status': 'success',
        'failure_reason': None
    }
```

### 3. 失败日志时间戳处理

```python
def get_latest_crawl_timestamp(self, log_dir: str) -> Optional[str]:
    """获取最新爬取批次的时间戳"""
    
    timestamp_pattern = re.compile(r'failed_urls_.*?_(\d{8}_\d{6})_.*?\.json')
    timestamps = set()
    
    for filename in os.listdir(log_dir):
        match = timestamp_pattern.search(filename)
        if match:
            timestamps.add(match.group(1))
    
    return max(timestamps) if timestamps else None

def load_latest_failed_urls(self, subject_name: str) -> List[Dict]:
    """加载最新批次的所有失败URL"""
    
    log_dir = f"/net/scratch/jingyang/GradPilot_DataBase/Crawl/log/{subject_name}"
    latest_timestamp = self.get_latest_crawl_timestamp(log_dir)
    
    if not latest_timestamp:
        return []
    
    failed_urls = []
    timestamp_pattern = f"*{latest_timestamp}*.json"
    
    for log_file in glob.glob(os.path.join(log_dir, timestamp_pattern)):
        with open(log_file, 'r', encoding='utf-8') as f:
            failed_records = json.load(f)
            failed_urls.extend(failed_records)
    
    return failed_urls
```

## 配置参数

### settings.py
```python
# 浏览器配置
BROWSER_CONFIG = {
    'headless': True,
    'viewport': {'width': 1920, 'height': 1080},
    'user_data_dir': None,  # 不使用持久化用户数据
    'timeout': 30000,
    'slow_mo': 0  # 生产环境不延迟
}

# 代理配置
PROXY_CONFIG = {
    'residential_providers': [
        # 'brightdata_api_endpoint',
        # 'smartproxy_api_endpoint'
    ],
    'datacenter_providers': [
        # 'proxy_provider_endpoint'
    ],
    'rotation_strategy': 'round_robin',
    'max_failures_per_proxy': 3
}

# 重试配置
RETRY_CONFIG = {
    'max_retries_per_url': 3,
    'retry_strategies': [
        {'proxy_type': 'datacenter', 'wait_time': 3, 'simulate_behavior': False},
        {'proxy_type': 'residential', 'wait_time': 5, 'simulate_behavior': True},
        {'proxy_type': 'mobile', 'wait_time': 8, 'simulate_behavior': True, 'extra_headers': True}
    ],
    'cooldown_between_retries': 2,
    'batch_size': 10,  # 并发处理的URL数量
    'batch_delay': 5   # 批次间延迟
}

# 内容验证
VALIDATION_CONFIG = {
    'min_content_length': 100,
    'error_indicators': [
        'access denied', '403 forbidden', '404 not found',
        'cloudflare', 'security check', 'captcha',
        'blocked', 'suspicious activity'
    ],
    'success_indicators': [
        'program', 'course', 'admission', 'requirement'
    ]
}
```

## 输出与报告

### 1. 重试结果保存

保存位置: `results/retry_results_{subject}_{timestamp}.json`

格式:
```json
{
    "subject": "交通运输",
    "retry_timestamp": "20241231_143022",
    "original_scrapy_timestamp": "20241231_120000",
    "summary": {
        "total_failed_urls": 45,
        "attempted_retries": 45,
        "successful_retries": 38,
        "failed_retries": 5,
        "skipped_404s": 2
    },
    "results": [
        {
            "original_failure": {
                "url": "https://example.com/program",
                "error_type": "HTTP403",
                "scrapy_error": "Forbidden"
            },
            "retry_result": {
                "status": "success",
                "attempts": 2,
                "final_strategy": "residential",
                "content": { ... },  // 完整的页面内容数据
                "retry_timestamp": "20241231_143045"
            }
        }
    ]
}
```

### 2. 集成到现有Pipeline

高级爬虫的成功结果需要合并到原始的Scrapy结果中，更新项目的完整数据。

**方案**: 创建专门的merger工具，将重试成功的页面数据合并到对应项目的JSON文件中。

## 部署与测试

### 1. 测试策略

- **单URL测试**: 对特定失败URL进行单独测试
- **小批量测试**: 选择10-20个失败URL进行批量测试  
- **学科级测试**: 对单个学科的所有失败URL进行完整重试
- **性能测试**: 测试并发处理能力和资源占用

### 2. 监控指标

- **成功率**: 重试成功的URL比例
- **耗时**: 单个URL平均重试时间
- **资源占用**: 内存和CPU使用情况
- **代理健康度**: 代理池的可用性和成功率
- **错误分布**: 不同类型错误的分布和解决率

## 预期效果

- **总体成功率提升**: 从当前65%提升至85-90%
- **WAF突破率**: HTTP 403错误解决率>95%
- **内容获取率**: JavaScript渲染问题解决率>90%
- **处理效率**: 单个URL重试时间<60秒
- **资源占用**: 合理的内存和网络使用

## 风险与备案

### 1. 技术风险
- **代理服务稳定性**: 准备多个代理服务商
- **反爬虫升级**: 持续更新反检测技术
- **资源消耗**: 设置合理的并发限制

### 2. 运营风险
- **IP封锁**: 使用代理轮换降低风险
- **法律合规**: 遵守robots.txt和网站条款
- **成本控制**: 监控代理服务使用量

此实现方案确保了高级爬虫系统的完整性、可靠性和与现有系统的兼容性，为显著提升爬取成功率提供了坚实的技术基础。