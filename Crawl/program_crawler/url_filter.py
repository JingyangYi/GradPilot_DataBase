"""
URL过滤模块 - 黑名单过滤系统

功能：
1. 基于关键词的快速过滤
2. 基于正则表达式的精确过滤
3. 统一的过滤接口

目的：
- 减少无关页面爬取，提高效率
- 避免爬取法律、人员、媒体等非学术页面
- 控制爬取范围，专注于项目相关内容
"""

import re

# 白名单关键词 - 仅当 URL 或链接文本包含下列关键词时才会被爬取
URL_WHITELIST_KEYWORDS = [
    'master', 'graduate', 'program', 'course', 'curriculum', 'structure', 'module',
    'apply', 'admission', 'requirements', 'deadline', 'application', 'entry requirements',
    'tuition', 'funding', 'scholarship',
    'duration', 'thesis', 'dissertation',
    'toefl', 'ielts',
    'transcript', 'recommendation', 'cv', 'personal-statement'
]

# 链接文本黑名单 - 基于链接描述文本的过滤
ANCHOR_TEXT_BLACKLIST = [
    # 常见的无关链接文本
    'contact us', 'about us', 'news', 'events', 'careers', 'jobs',
    'privacy policy', 'terms of service', 'sitemap', 'login', 'sign in',
    'facebook', 'twitter', 'instagram', 'linkedin', 'youtube',
    'library', 'bookstore', 'shop', 'donate', 'giving',
    'alumni', 'staff directory', 'faculty directory',
    'campus map', 'virtual tour', 'visit us', 'parking',
    'student life', 'sports', 'clubs', 'societies',
    'undergraduate', 'bachelor', 'phd', 'doctoral',
    'scholarship', 'financial aid', 'funding'
]

# URL黑名单关键词 - 用于快速匹配
URL_BLACKLIST_KEYWORDS = [
    # 媒体传播类：新闻、活动、博客等
    'news', 'media', 'press', 'events', 'event', 'blog', 'stories', 'story', 'podcasts', 'videos', 'webinars',
    'newsletter', 'magazine', 'publication', 'announce', 'announcement',
    
    # 人员相关类：员工、校友、专家目录等
    'people', 'staff', 'faculty', 'alumni', 'directory', 'profiles', 'profile', 'experts', 'researchers',
    'team', 'member', 'biography', 'bio', 'cv', 'resume',
    
    # 法律政策类：隐私政策、使用条款等
    'legal', 'privacy', 'terms', 'policy', 'policies', 'accessibility', 'cookies', 'disclaimer', 'compliance', 'gdpr',
    'copyright', 'license', 'agreement',
    
    # 机构信息类：关于我们、联系方式、招聘等
    'about', 'contact', 'jobs', 'job', 'careers', 'career', 'governance', 'history', 'leadership', 'organization',
    'mission', 'vision', 'values', 'overview', 'welcome', 'introduction',
    
    # 学生服务类：住宿、校园生活、体育活动等
    'accommodation', 'housing', 'student-life', 'campus-life', 'sports', 'sport', 'health', 'counseling', 'clubs', 'societies',
    'welfare', 'support', 'service', 'recreation', 'dining', 'transport', 'parking',
    
    # 技术系统类：搜索、登录、管理后台等
    'sitemap', 'search', 'login', 'portal', 'intranet', 'admin', 'dashboard', 'system',
    'help', 'faq', 'support', 'download', 'upload', 'register', 'signup',
    
    # 社交媒体类：各种社交平台链接
    'facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'social', 'share',
    
    # 奖学金和资助
    'scholarship', 'scholarships', 'funding', 'financial-aid', 'bursary', 'bursaries', 'grant', 'grants',
    
    # 其他服务类：图书馆、商店、捐赠等
    'library', 'libraries', 'map', 'maps', 'calendar', 'giving', 'donations', 'fundraising', 'shop', 'bookstore',
    'visit', 'tour', 'virtual-tour', 'gallery', 'photo', 'image',
    
    # 学位层级过滤：排除本科和博士
    'undergraduate', 'bachelor', 'bachelors', 'phd', 'doctoral', 'doctorate', 'postdoc',
    
    # 新增：非学术相关的常见页面
    'conference', 'workshop', 'seminar', 'webinar', 'meeting', 'award', 'awards',
    'research-output', 'publication', 'journal', 'paper', 'report'
]

# 正则表达式黑名单 - 用于精确匹配
# 优点：匹配精确，减少误杀
# 缺点：速度较慢，正则表达式复杂
URL_BLACKLIST_PATTERNS = [
    # 媒体/新闻/宣传 - 匹配路径中的媒体相关目录
    r'(?i)(^|/)(news|events?|event-calendar|stories|story|press(-office)?|media|podcasts?|videos?|webinars?|magazine|newsletter|campaigns?)(/|$)',
    r'(?i)(^|/)(blogs?|features?|spotlights?)(/|$)',
    
    # 人员/目录/组织结构 - 匹配人员和组织相关页面
    r'(?i)(^|/)(people|staff|faculty|team|directory|profiles?|experts?|researchers?)(/|$)',
    r'(?i)(^|/)(departments?|schools?|centres?|centers?|institutes?)(/|$)',
    
    # 校友/捐赠 - 匹配校友关系和捐赠相关页面
    r'(?i)(^|/)(alumni|advancement|giving|donate|support-us|fundraising|foundation)(/|$)',
    
    # 法务/政策/站点信息 - 匹配法律和政策相关页面
    r'(?i)(^|/)(legal|privacy|cookies?|terms|accessibility|sitemap|disclaimer|governance|polic(y|ies))(/|$)',
    
    # 联系/地图/参观/校园生活 - 匹配服务和生活相关页面
    r'(?i)(^|/)(contact|maps?|visit|find[-_ ]?us|directions|parking|transport|accommodation|housing|campus-life|student[-_ ]life|clubs|societies)(/|$)',
    
    # 招聘/就业/HR - 匹配就业和招聘相关页面
    r'(?i)(^|/)(jobs?|careers?|vacancies|recruit(ment)?|work-with-us|hr)(/|$)',
    
    # 图书馆/档案/商店 - 匹配图书馆和商店相关页面
    r'(?i)(^|/)(library|archives?|collections?|bookstore|shop|merch(andise)?)(/|$)',
    
    # 学位层级无关页 - 精确匹配本科和博士相关页面
    r'(?i)(^|/)(undergraduate|ug|bachelors?|ba-|bs-|minor|foundation(-year)?)(/|$)',
    r'(?i)(^|/)(phd|doctoral|doctorate|postdoc|dphil)(/|$)',
    
    # 研究输出/非学位研究项目 - 匹配学术出版物和研究项目
    r'(?i)(^|/)(publications?|journals?|papers?|reports?|theses?|dissertations?)(/|$)',
    r'(?i)(^|/)(research-(?!degrees)|projects?|labs?)(/|$)',  # 排除research-degrees
    
    # 账号/搜索/系统页 - 匹配系统功能页面
    r'(?i)(^|/)(search|login|sign[-_ ]?in|account|profile|basket|cart)(/|$)',
    
    # 静态资源/大文件 - 匹配文件扩展名
    r'\.(jpg|jpeg|png|gif|svg|ico|mp4|mp3|mov|zip|rar|pptx?|xls[x]?|docx?)$'
]


def should_skip_url(url):
    """
    基于关键词的简单URL过滤
    
    策略：将URL转换为小写后，检查是否包含黑名单关键词
    
    优点：
    - 执行速度快
    - 内存占用少
    - 逻辑简单
    
    缺点：
    - 可能出现误杀（如"news"匹配到"business"）
    - 无法处理复杂的URL结构
    
    Args:
        url (str): 要检查的URL
        
    Returns:
        bool: True表示应该跳过该URL，False表示可以爬取
    """
    url_lower = url.lower()  # 转换为小写，忽略大小写差异
    
    # 遍历黑名单关键词，只要匹配到一个就返回True
    return any(keyword in url_lower for keyword in URL_BLACKLIST_KEYWORDS)


def should_skip_url_regex(url):
    """
    基于正则表达式的精确URL过滤
    
    策略：使用预定义的正则表达式模式精确匹配URL结构
    
    优点：
    - 匹配精确，减少误杀
    - 可以处理复杂的URL结构
    - 支持路径边界匹配
    
    缺点：
    - 执行速度较慢
    - 正则表达式复杂，维护成本高
    
    Args:
        url (str): 要检查的URL
        
    Returns:
        bool: True表示应该跳过该URL，False表示可以爬取
    """
    # 遍历正则表达式模式列表
    for pattern in URL_BLACKLIST_PATTERNS:
        if re.search(pattern, url):  # 使用re.search进行模式匹配
            return True
    return False


def has_whitelist_keywords(url: str, anchor_text: str = "") -> bool:
    """仅根据 *anchor text* 判断是否包含白名单关键词。
 
    URL 本身的字符串不再参与匹配。
     
    Args:
        url (str): 保留参数，已忽略。
        anchor_text (str): 链接显示文本。
 
    Returns:
        bool: 若锚文本包含白名单关键词则返回 ``True``。
    """
    if not anchor_text:
        return False
 
    text_lower = anchor_text.lower()
    return any(keyword in text_lower for keyword in URL_WHITELIST_KEYWORDS)

def should_skip_by_anchor_text(anchor_text):
    """
    基于链接文本判断是否应该跳过
    
    Args:
        anchor_text (str): 链接的描述文本
        
    Returns:
        bool: True表示应该跳过
    """
    if not anchor_text:
        return False
        
    text_lower = anchor_text.lower().strip()
    return any(blacklist_text in text_lower for blacklist_text in ANCHOR_TEXT_BLACKLIST)

def filter_url(url, use_regex=False, enable_whitelist=True, anchor_text=''):
    """
    统一的URL过滤接口（纯白名单模式）
    
    过滤逻辑：
    1. 只要 URL 或 anchor text 包含白名单关键词 -> 允许爬取（返回 False）
    2. 其余情况一律跳过（返回 True）
    
    Args:
        url (str): 要过滤的 URL
        use_regex (bool): 保留参数以兼容旧调用，当前忽略
        enable_whitelist (bool): 保留参数以兼容旧调用，当前忽略
        anchor_text (str): 链接文本
    
    Returns:
        bool: True 表示跳过 (不爬取)，False 表示允许爬取
    """
    # 纯白名单判断：匹配关键词即通过
    if has_whitelist_keywords(url, anchor_text):
        return False  # 不跳过，允许爬取
    
    # 其他任何情况都跳过
    return True