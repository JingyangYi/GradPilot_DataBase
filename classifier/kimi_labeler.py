#!/usr/bin/env python3
"""
使用Kimi API为URL标注relevant/irrelevant值的脚本
"""
import json
import requests
import time
import os
import sys

# Kimi API配置
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = "kimi-k2-0711-preview"  
api_key = "yourkeyhere"

def setup_kimi():
    """设置Kimi API"""
    api_key = os.getenv('KIMI_API_KEY')
    if not api_key:
        print("❌ 请设置KIMI_API_KEY环境变量")
        print("export KIMI_API_KEY='your_kimi_api_key_here'")
        return None
    
    # 测试连接
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "model": KIMI_MODEL,
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(KIMI_API_URL, headers=headers, json=test_payload, timeout=10)
        if response.status_code == 200:
            print("✅ Kimi API连接成功")
            return api_key
        else:
            print(f"❌ Kimi API测试失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Kimi API连接失败: {e}")
        return None

def call_kimi_api(api_key, content):
    """调用Kimi API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": KIMI_MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(KIMI_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"    ❌ API调用失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"    ❌ API调用异常: {e}")
        return None

def label_url(api_key, url_data, max_retries=3):
    """标注单个URL"""
    
    # 截取内容
    content = url_data.get('content', '')[:3000]
    title = url_data.get('title', 'No title')[:100]
    url = url_data.get('url', '')[:200]
    
    prompt = f"""Task: Determine if the webpage content is directly related to graduate program applications.

A webpage is RELEVANT if and only if:
1. It refers to a SPECIFIC graduate program (not general school information)
2. It contains ACTIONABLE APPLICATION INFORMATION such as:
   - Admission requirements (GPA, tests, prerequisites)
   - Application materials and deadlines
   - Program-specific details (curriculum, duration, fees)

A webpage is IRRELEVANT if it contains:
- General school/department information
- News, events, or stories
- Faculty/research information without admission context
- Student life or general policies

Output: relevant OR irrelevant

URL: {url}
Title: {title}
Content: {content}"""

    for attempt in range(max_retries):
        try:
            print(f"    🔄 API调用 (尝试 {attempt + 1}/{max_retries})...")
            result = call_kimi_api(api_key, prompt)
            
            if result is None:
                if attempt < max_retries - 1:
                    print(f"    ⏳ 等待 {2 ** attempt} 秒后重试...")
                    time.sleep(2 ** attempt)
                continue
            
            result_lower = result.lower()
            print(f"    📝 API响应: {result}")
            
            # 解析结果
            if 'relevant' in result_lower and 'irrelevant' not in result_lower:
                return True
            elif 'irrelevant' in result_lower:
                return False
            else:
                print(f"    ⚠️  无法解析结果: {result}")
                if attempt < max_retries - 1:
                    continue
                
        except Exception as e:
            print(f"    ❌ 标注异常 (尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
    
    print(f"    ❌ 标注失败，跳过")
    return None

def label_file(file_path):
    """标注指定文件"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"🚀 开始标注文件: {file_path}")
    
    # 设置Kimi API
    api_key = setup_kimi()
    if not api_key:
        return
    
    # 读取数据
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成输出文件名
    base_name = os.path.splitext(file_path)[0]
    output_file = f"{base_name}_labeled.json"
    
    # 统计信息
    total_sub_urls = 0
    labeled_count = 0
    start_time = time.time()
    
    print(f"📊 分析文件结构...")
    
    # 先统计总数
    for project in data['projects']:
        for url_data in project['urls']:
            if not url_data.get('is_root', False):
                if url_data.get('is_valuable') is None:
                    total_sub_urls += 1
                else:
                    labeled_count += 1  # 已标注的
    
    print(f"    - 待标注子URL: {total_sub_urls}")
    print(f"    - 已标注子URL: {labeled_count}")
    print(f"    - 总项目数: {len(data['projects'])}")
    
    if total_sub_urls == 0:
        print("✅ 所有URL已标注完成")
        return
    
    print(f"\n🎯 开始标注过程...")
    current_labeled = 0
    
    # 遍历每个项目
    for project_idx, project in enumerate(data['projects']):
        project_name = project.get('program_name', 'Unknown')[:60]
        print(f"\n📁 处理项目 {project_idx + 1}/{len(data['projects'])}: {project_name}...")
        
        project_has_changes = False
        
        # 遍历每个URL
        for url_idx, url_data in enumerate(project['urls']):
            # 只处理需要标注的子URL
            if not url_data.get('is_root', False) and url_data.get('is_valuable') is None:
                title = url_data.get('title', 'No title')[:50]
                print(f"  🔖 标注URL {url_idx + 1}: {title}...")
                
                # 调用Kimi标注
                is_valuable = label_url(api_key, url_data)
                
                if is_valuable is not None:
                    url_data['is_valuable'] = is_valuable
                    current_labeled += 1
                    project_has_changes = True
                    
                    result_text = '✅ relevant' if is_valuable else '❌ irrelevant'
                    progress = (current_labeled / total_sub_urls) * 100
                    print(f"    {result_text} | 进度: {current_labeled}/{total_sub_urls} ({progress:.1f}%)")
                
                # 控制API调用频率
                time.sleep(1.0)
        
        # 每处理完一个项目就保存
        if project_has_changes:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            elapsed = time.time() - start_time
            rate = current_labeled / elapsed * 60 if elapsed > 0 else 0
            print(f"    💾 进度已保存 | 速度: {rate:.1f}个/分钟")
    
    # 最终统计
    elapsed = time.time() - start_time
    print(f"\n🎉 标注完成！")
    print(f"📈 统计信息:")
    print(f"  - 成功标注: {current_labeled}/{total_sub_urls}")
    print(f"  - 用时: {elapsed/60:.1f}分钟")
    print(f"  - 平均速度: {current_labeled/elapsed*60:.1f}个/分钟" if elapsed > 0 else "")
    print(f"  - 结果保存到: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("📚 Kimi URL标注工具")
        print("\n用法:")
        print("  python kimi_labeler.py <json文件路径>")
        print("\n示例:")
        print("  python kimi_labeler.py classifier_training_data_part1.json")
        print("  python kimi_labeler.py classifier_training_data_part2.json")
        print("  python kimi_labeler.py classifier_training_data_part3.json")
        print("\n注意:")
        print("  - 需要设置环境变量: export KIMI_API_KEY='your_key'")
        print("  - 输出文件会自动添加 '_labeled' 后缀")
        return
    
    file_path = sys.argv[1]
    label_file(file_path)

if __name__ == "__main__":
    main()