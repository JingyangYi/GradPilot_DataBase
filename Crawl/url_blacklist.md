# URL过滤黑名单

## 使用说明
爬取时检查URL路径，包含以下关键词或正则模式的链接跳过爬取。

## 简单关键词匹配

### 媒体传播类
- news, media, press, events, event-calendar, stories, story, press-office, podcasts, videos, webinars, magazine, newsletter, campaigns, blogs, features, spotlights
- 多语言：actualites, actualités, evenements, veranstaltungen, nachrichten, medien, presse, nieuws, evenementen, pers

### 人员相关类  
- people, staff, faculty, team, directory, profiles, experts, researchers
- 组织结构：departments, schools, centres, centers, institutes

### 校友捐赠类
- alumni, advancement, giving, donate, support-us, fundraising, foundation

### 法律政策类
- legal, privacy, terms, policy, policies, accessibility, cookies, disclaimer, compliance, gdpr, governance, sitemap

### 机构信息类
- about, contact, history, leadership, organization
- 地图访问：maps, visit, find-us, directions, parking, transport

### 学生服务类
- accommodation, housing, student-life, campus-life, sports, health, counseling, welfare, support, clubs, societies

### 招聘就业类
- jobs, careers, vacancies, recruitment, work-with-us, hr
- 多语言：carrieres, carrières, empleo, karriere, vacatures

### 图书馆商店类
- library, archives, collections, bookstore, shop, merchandise

### 学位层级过滤类
- 本科：undergraduate, ug, bachelors, ba-, bs-, minor, foundation-year
- 博士：phd, doctoral, doctorate, postdoc, dphil

### 研究输出类
- publications, journals, papers, reports, theses, dissertations
- research-（非research-degrees）, projects, labs

### 技术系统类
- search, login, sign-in, account, profile, basket, cart, portal, intranet, admin, dashboard, system

### 社交媒体类
- facebook, twitter, instagram, linkedin, youtube, social

## 正则表达式过滤模式

```python
import re

URL_BLACKLIST_PATTERNS = [
    # 媒体/新闻/宣传
    r'(?i)(^|/)(news|events?|event-calendar|stories|story|press(-office)?|media|podcasts?|videos?|webinars?|magazine|newsletter|campaigns?)(/|$)',
    r'(?i)(^|/)(blogs?|features?|spotlights?)(/|$)',
    r'(?i)(^|/)(actualit(e|é)s?|evenements?|veranstaltungen|nachrichten|medien|presse|nieuws|evenementen|pers)(/|$)',
    
    # 人员/目录/组织结构
    r'(?i)(^|/)(people|staff|faculty|team|directory|profiles?|experts?|researchers?)(/|$)',
    r'(?i)(^|/)(departments?|schools?|centres?|centers?|institutes?)(/|$)',
    
    # 校友/捐赠
    r'(?i)(^|/)(alumni|advancement|giving|donate|support-us|fundraising|foundation)(/|$)',
    
    # 法务/政策/站点信息
    r'(?i)(^|/)(legal|privacy|cookies?|terms|accessibility|sitemap|disclaimer|governance|polic(y|ies))(/|$)',
    
    # 联系/地图/参观/校园生活
    r'(?i)(^|/)(contact|maps?|visit|find[-_ ]?us|directions|parking|transport|accommodation|housing|campus-life|student[-_ ]life|clubs|societies)(/|$)',
    
    # 招聘/就业/HR
    r'(?i)(^|/)(jobs?|careers?|vacancies|recruit(ment)?|work-with-us|hr)(/|$)',
    r'(?i)(^|/)(carri(e|è)res?|empleo|karriere|vacatures?)(/|$)',
    
    # 图书馆/档案/商店
    r'(?i)(^|/)(library|archives?|collections?|bookstore|shop|merch(andise)?)(/|$)',
    
    # 学位层级无关页
    r'(?i)(^|/)(undergraduate|ug|bachelors?|ba-|bs-|minor|foundation(-year)?)(/|$)',
    r'(?i)(^|/)(phd|doctoral|doctorate|postdoc|dphil)(/|$)',
    
    # 研究输出/非学位研究项目
    r'(?i)(^|/)(publications?|journals?|papers?|reports?|theses?|dissertations?)(/|$)',
    r'(?i)(^|/)(research-(?!degrees)|projects?|labs?)(/|$)',
    
    # 账号/搜索/系统页
    r'(?i)(^|/)(search|login|sign[-_ ]?in|account|profile|basket|cart)(/|$)',
    
    # 静态资源/大文件
    r'\.(jpg|jpeg|png|gif|svg|ico|mp4|mp3|mov|zip|rar|pptx?|xls[x]?|docx?)$'
]

def should_skip_url(url):
    """检查URL是否应该跳过"""
    for pattern in URL_BLACKLIST_PATTERNS:
        if re.search(pattern, url):
            return True
    return False
```

## 简化版Python配置
```python
URL_BLACKLIST_KEYWORDS = [
    # 媒体传播
    'news', 'media', 'press', 'events', 'blog', 'stories', 'podcasts', 'videos', 'webinars',
    # 人员相关
    'people', 'staff', 'faculty', 'alumni', 'directory', 'profiles', 'experts', 'researchers',
    # 法律政策
    'legal', 'privacy', 'terms', 'policy', 'accessibility', 'cookies', 'disclaimer', 'compliance', 'gdpr',
    # 机构信息
    'about', 'contact', 'jobs', 'careers', 'governance', 'history', 'leadership', 'organization',
    # 学生服务
    'accommodation', 'housing', 'student-life', 'campus-life', 'sports', 'health', 'counseling', 'clubs', 'societies',
    # 技术系统
    'sitemap', 'search', 'login', 'portal', 'intranet', 'admin', 'dashboard', 'system',
    # 社交媒体
    'facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'social',
    # 其他服务
    'library', 'map', 'calendar', 'giving', 'donations', 'fundraising', 'shop', 'bookstore',
    # 学位层级
    'undergraduate', 'bachelor', 'phd', 'doctoral', 'doctorate'
]

def should_skip_url_simple(url):
    url_lower = url.lower()
    return any(keyword in url_lower for keyword in URL_BLACKLIST_KEYWORDS)
```