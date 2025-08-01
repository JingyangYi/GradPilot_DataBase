import re
import requests
from bs4 import BeautifulSoup
from collections import Counter

def analyze_curriculum_content_enhanced(url_or_content, is_url=True):
    """
    增强版课程内容识别 - 专为英文网页和多学科设计
    """
    
    # 获取内容
    if is_url:
        try:
            response = requests.get(url_or_content, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code != 200:
                return {"is_curriculum": False, "reason": f"HTTP {response.status_code}"}
            html_content = response.text
            url = url_or_content
        except Exception as e:
            return {"is_curriculum": False, "reason": f"Failed to fetch: {str(e)}"}
    else:
        html_content = url_or_content
        url = "N/A"
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除不相关标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        text = soup.get_text().lower()
        original_text = soup.get_text()  # 保留原始大小写用于课程编号匹配
        
        analysis = {
            "url": url,
            "is_curriculum": False,
            "confidence_score": 0,
            "details": {},
            "course_codes_found": [],
            "subject_areas": [],
            "reasons": []
        }
        
        # === 1. 超强指示词 (40分/个) ===
        ultra_strong_indicators = [
            'degree requirements', 'graduation requirements', 'curriculum overview',
            'course requirements', 'academic requirements', 'program requirements',
            'course catalog', 'course listings', 'required coursework',
            'core curriculum', 'curriculum structure', 'degree plan'
        ]
        
        ultra_matches = sum(1 for indicator in ultra_strong_indicators if indicator in text)
        if ultra_matches > 0:
            analysis["confidence_score"] += ultra_matches * 40
            analysis["reasons"].append(f"Found {ultra_matches} ultra-strong curriculum indicators")
        
        # === 2. 强指示词 (25分/个) ===
        strong_indicators = [
            'course list', 'course sequence', 'required courses', 'elective courses',
            'core courses', 'foundation courses', 'prerequisite', 'prerequisites',
            'course descriptions', 'syllabus', 'credit hours', 'credit requirements',
            'semester plan', 'academic plan', 'study plan'
        ]
        
        strong_matches = sum(1 for indicator in strong_indicators if indicator in text)
        if strong_matches > 0:
            analysis["confidence_score"] += strong_matches * 25
            analysis["reasons"].append(f"Found {strong_matches} strong curriculum indicators")
        
        # === 3. 详细的学科编码模式 ===
        subject_codes = {
            # 计算机/数据科学
            'cs_data': ['CS', 'CSE', 'COMP', 'CMSC', 'CIS', 'INFO', 'INFOSCI', 'DATA', 'DSCI', 'STAT', 'STATS'],
            # 数学/统计
            'math_stat': ['MATH', 'STAT', 'STATS', 'APPL', 'PROB', 'STOC'],
            # 社会科学
            'social_sci': ['PSYC', 'PSYCH', 'SOC', 'SOCI', 'ANTH', 'ANTHRO', 'POLI', 'POLISCI', 'GOVT', 'POLS'],
            # 经济/商科
            'econ_business': ['ECON', 'ECON', 'BUS', 'BUSN', 'MGMT', 'MGTM', 'FIN', 'FINC', 'ACCT', 'MARK', 'MKTG'],
            # 教育
            'education': ['EDUC', 'ED', 'TEACH', 'CURR', 'INST', 'LING', 'APPL'],
            # 传媒/新闻
            'media_comm': ['COMM', 'CMCL', 'JOUR', 'JRNL', 'MEDIA', 'FILM', 'DIGT'],
            # 人文学科
            'humanities': ['ENGL', 'HIST', 'PHIL', 'RELI', 'CLAS', 'FREN', 'SPAN', 'GERM'],
            # 工程
            'engineering': ['ENGR', 'MECH', 'ELEC', 'CHEM', 'CIVL', 'BIOE', 'AERO'],
            # 医学/生物
            'bio_med': ['BIOL', 'CHEM', 'PHYS', 'MED', 'NURS', 'PUBH', 'EPID'],
            # 艺术/设计
            'arts': ['ART', 'ARTS', 'MUS', 'MUSC', 'THEA', 'DANC', 'DSGN']
        }
        
        # 课程编号匹配模式 (更精确)
        course_patterns = [
            # 标准格式: SUBJ 1234, SUBJ-1234, SUBJ1234
            r'\b([A-Z]{2,8})[\s\-]?(\d{3,4}[A-Z]?)\b',
            # 带点号: SUBJ.1234
            r'\b([A-Z]{2,8})\.(\d{3,4}[A-Z]?)\b',
            # 带冒号: SUBJ:1234
            r'\b([A-Z]{2,8}):(\d{3,4}[A-Z]?)\b',
            # 长格式: SUBJECT 1234
            r'\b([A-Z]{3,10})\s+(\d{3,4}[A-Z]?)\b'
        ]
        
        # 查找课程编号
        all_course_codes = []
        subject_areas_found = set()
        
        for pattern in course_patterns:
            matches = re.findall(pattern, original_text)
            for subject, number in matches:
                # 验证是否为有效的学科代码
                for category, codes in subject_codes.items():
                    if subject in codes:
                        course_code = f"{subject} {number}"
                        all_course_codes.append(course_code)
                        subject_areas_found.add(category)
                        break
                else:
                    # 如果不在预定义列表中，但符合常见模式，也可能是课程
                    if len(subject) >= 3 and subject.isalpha():
                        course_code = f"{subject} {number}"
                        all_course_codes.append(course_code)
        
        # 去重
        unique_courses = list(dict.fromkeys(all_course_codes))  # 保持顺序的去重
        analysis["course_codes_found"] = unique_courses[:15]  # 最多显示15个
        analysis["subject_areas"] = list(subject_areas_found)
        analysis["details"]["course_count"] = len(unique_courses)
        
        # 课程编号评分
        if len(unique_courses) >= 10:
            analysis["confidence_score"] += 50
            analysis["reasons"].append(f"Found {len(unique_courses)} course codes (excellent)")
        elif len(unique_courses) >= 5:
            analysis["confidence_score"] += 35
            analysis["reasons"].append(f"Found {len(unique_courses)} course codes (good)")
        elif len(unique_courses) >= 2:
            analysis["confidence_score"] += 20
            analysis["reasons"].append(f"Found {len(unique_courses)} course codes")
        
        # === 4. 学分/学时模式识别 ===
        credit_patterns = [
            r'(\d+)\s*credit[s]?\s*hour[s]?',
            r'(\d+)\s*credit[s]?',
            r'(\d+)\s*unit[s]?',
            r'(\d+)\s*hour[s]?\s*per\s*week',
            r'\((\d+)\s*cr\)',
            r'\((\d+)\s*credits?\)',
            r'(\d+)-credit',
            r'total\s*of\s*(\d+)\s*credit'
        ]
        
        credit_mentions = []
        for pattern in credit_patterns:
            matches = re.findall(pattern, text)
            credit_mentions.extend(matches)
        
        analysis["details"]["credit_mentions"] = len(credit_mentions)
        if len(credit_mentions) >= 5:
            analysis["confidence_score"] += 25
            analysis["reasons"].append(f"Found {len(credit_mentions)} credit/hour mentions")
        elif len(credit_mentions) >= 2:
            analysis["confidence_score"] += 15
            analysis["reasons"].append(f"Found {len(credit_mentions)} credit mentions")
        
        # === 5. 课程描述关键词 ===
        course_keywords = [
            'prerequisite', 'corequisite', 'enrollment', 'instructor', 'semester',
            'quarter', 'academic year', 'course load', 'full-time', 'part-time',
            'thesis', 'dissertation', 'capstone', 'internship', 'practicum',
            'seminar', 'workshop', 'laboratory', 'lecture', 'tutorial'
        ]
        
        keyword_matches = sum(1 for keyword in course_keywords if keyword in text)
        analysis["details"]["keyword_matches"] = keyword_matches
        if keyword_matches >= 5:
            analysis["confidence_score"] += 20
            analysis["reasons"].append(f"Found {keyword_matches} course-related keywords")
        elif keyword_matches >= 3:
            analysis["confidence_score"] += 10
            analysis["reasons"].append(f"Found {keyword_matches} course keywords")
        
        # === 6. 学位层次识别 ===
        degree_patterns = [
            r'master[\'s]?\s*degree', r'doctoral\s*degree', r'phd\s*degree',
            r'bachelor[\'s]?\s*degree', r'undergraduate', r'graduate',
            r'm\.?s\.?', r'm\.?a\.?', r'ph\.?d\.?', r'b\.?s\.?', r'b\.?a\.?'
        ]
        
        degree_mentions = sum(1 for pattern in degree_patterns if re.search(pattern, text))
        if degree_mentions >= 2:
            analysis["confidence_score"] += 10
            analysis["reasons"].append("Found degree-level indicators")
        
        # === 7. HTML结构分析 ===
        # 查找课程列表结构
        course_list_indicators = 0
        
        # 检查表格
        tables = soup.find_all('table')
        for table in tables:
            table_text = table.get_text().lower()
            if any(word in table_text for word in ['course', 'credit', 'semester', 'requirement']):
                course_list_indicators += 10
        
        # 检查列表
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            list_text = lst.get_text().lower()
            if any(word in list_text for word in ['course', 'credit', 'requirement']) and len(lst.find_all('li')) >= 3:
                course_list_indicators += 5
        
        # 检查标题结构
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        for header in headers:
            header_text = header.get_text().lower()
            if any(word in header_text for word in ['curriculum', 'course', 'requirement', 'program']):
                course_list_indicators += 3
        
        if course_list_indicators > 0:
            analysis["confidence_score"] += min(course_list_indicators, 25)
            analysis["reasons"].append("Found structured curriculum content")
        
        # === 8. 负面指标检测 ===
        negative_indicators = [
            'news', 'blog', 'event', 'calendar', 'faculty directory',
            'contact us', 'about us', 'homepage', 'main page',
            'research projects', 'publications', 'biography'
        ]
        
        negative_count = sum(1 for indicator in negative_indicators if indicator in text)
        if negative_count >= 3:
            analysis["confidence_score"] -= 15
            analysis["reasons"].append("Contains non-curriculum content indicators")
        
        # === 最终判断 ===
        # 动态阈值：如果发现很多课程编号，降低总体要求
        if len(unique_courses) >= 8:
            threshold = 40
        elif len(unique_courses) >= 4:
            threshold = 50
        else:
            threshold = 60
        
        analysis["is_curriculum"] = analysis["confidence_score"] >= threshold
        analysis["details"]["threshold_used"] = threshold
        
        # 置信度等级
        if analysis["confidence_score"] >= 80:
            analysis["confidence_level"] = "Very High"
        elif analysis["confidence_score"] >= 60:
            analysis["confidence_level"] = "High"
        elif analysis["confidence_score"] >= 40:
            analysis["confidence_level"] = "Medium"
        elif analysis["confidence_score"] >= 20:
            analysis["confidence_level"] = "Low"
        else:
            analysis["confidence_level"] = "Very Low"
        
        return analysis
        
    except Exception as e:
        return {"is_curriculum": False, "reason": f"Analysis failed: {str(e)}"}

def batch_analyze_enhanced(urls):
    """增强版批量分析"""
    results = []
    
    print("🎓 开始批量课程页面分析...")
    print("=" * 60)
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 🔍 分析: {url}")
        result = analyze_curriculum_content_enhanced(url)
        results.append(result)
        
        if result["is_curriculum"]:
            print(f"✅ **课程页面** (置信度: {result['confidence_score']}, 等级: {result.get('confidence_level', 'N/A')})")
            if result.get("course_codes_found"):
                print(f"   📚 课程编号示例: {', '.join(result['course_codes_found'][:5])}")
            if result.get("subject_areas"):
                print(f"   🎯 学科领域: {', '.join(result['subject_areas'])}")
        else:
            print(f"❌ 非课程页面 (置信度: {result['confidence_score']}, 等级: {result.get('confidence_level', 'N/A')})")
        
        if result.get("reasons"):
            print(f"   💡 判断依据: {'; '.join(result['reasons'][:3])}")  # 只显示前3个原因
        
        print("-" * 40)
    
    # 统计摘要
    curriculum_count = sum(1 for r in results if r["is_curriculum"])
    print(f"\n📊 分析完成:")
    print(f"   - 总计分析: {len(results)} 个URL")
    print(f"   - 识别为课程页面: {curriculum_count} 个")
    print(f"   - 识别率: {curriculum_count/len(results)*100:.1f}%")
    
    return results
