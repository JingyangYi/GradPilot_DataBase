#!/usr/bin/env python3
"""测试修复后的高级爬虫逻辑"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.content_processor import ContentProcessor

def test_content_processor():
    """测试ContentProcessor的修复"""
    processor = ContentProcessor()
    
    # 测试HTML
    test_html = '''
    <html>
        <head><title>Master's Program in Transport Planning</title></head>
        <body>
            <header>
                <a href="/about">About Us</a>
            </header>
            <main>
                <h1>Master's Program in Transport Planning</h1>
                <p>This is a comprehensive program covering all aspects of transportation.</p>
                <a href="/apply">Apply Now</a>
                <a href="/requirements">Program Requirements</a>
                <a href="/curriculum">Curriculum Overview</a>
            </main>
            <footer>
                <a href="/contact">Contact</a>
            </footer>
        </body>
    </html>
    '''
    
    # 测试深度0（应该提取链接）
    result_depth_0 = processor.process_page(test_html, "https://example.com", depth=0)
    print("=== 深度0测试结果 ===")
    print(f"标题: {result_depth_0['title']}")
    print(f"链接数量: {len(result_depth_0['links'])}")
    
    for link in result_depth_0['links']:
        print(f"  链接: {link}")
    
    # 测试深度1（不应该提取链接）
    result_depth_1 = processor.process_page(test_html, "https://example.com", depth=1)
    print("\n=== 深度1测试结果 ===")
    print(f"标题: {result_depth_1['title']}")
    print(f"链接数量: {len(result_depth_1['links'])}")
    
    # 验证修复
    print("\n=== 修复验证 ===")
    success = True
    
    # 检查深度控制
    if len(result_depth_0['links']) == 0:
        print("❌ 深度0应该有链接但没有找到")
        success = False
    else:
        print("✅ 深度0正确提取了链接")
    
    if len(result_depth_1['links']) != 0:
        print("❌ 深度1不应该有链接但找到了链接")
        success = False
    else:
        print("✅ 深度1正确跳过了链接提取")
    
    # 检查链接格式
    if result_depth_0['links']:
        first_link = result_depth_0['links'][0]
        required_fields = ['url', 'anchor_text', 'matched_keyword']
        
        for field in required_fields:
            if field not in first_link:
                print(f"❌ 链接缺少字段: {field}")
                success = False
            else:
                print(f"✅ 链接包含字段: {field} = {first_link[field]}")
    
    return success

if __name__ == "__main__":
    print("开始测试修复后的ContentProcessor...")
    success = test_content_processor()
    
    if success:
        print("\n🎉 所有修复测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)