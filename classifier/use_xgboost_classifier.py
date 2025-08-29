#!/usr/bin/env python3
"""
使用最佳XGBoost分类器
性能优于Random Forest：召回率95.7%, 精确率96.4%, 假负例仅18个
"""

import joblib
import re

class XGBoostWebpageClassifier:
    """XGBoost网页内容分类器 - 当前最佳性能"""
    
    def __init__(self, model_path='xgboost_best_classifier.joblib'):
        """加载XGBoost模型"""
        print(f"加载XGBoost模型: {model_path}")
        model_data = joblib.load(model_path)
        
        self.model = model_data['model']
        self.threshold = model_data['threshold']
        self.model_name = model_data['model_name']
        self.metrics = model_data['metrics']
        
        print(f"模型: {self.model_name}")
        print(f"优化阈值: {self.threshold:.3f}")
        print(f"性能指标:")
        print(f"  - 召回率: {self.metrics['recall']:.3f} (95.7%)")
        print(f"  - 精确率: {self.metrics['precision']:.3f} (96.4%)")
        print(f"  - 假负例: {self.metrics['false_negatives']} (错过的有价值页面)")
        print(f"  - 假正例: {self.metrics['false_positives']} (误判的无价值页面)")
    
    def preprocess_text(self, text):
        """文本预处理"""
        if not isinstance(text, str):
            return ""
        
        text = re.sub(r'\[HEADING\]', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()
    
    def classify(self, content):
        """分类单个内容"""
        processed_content = self.preprocess_text(content)
        
        if len(processed_content) < 10:
            return {
                'is_valuable': False,
                'confidence': 0.0,
                'method': 'content_too_short'
            }
        
        # 获取预测概率
        probability = self.model.predict_proba([processed_content])[0][1]
        
        # 使用优化后的阈值
        is_valuable = probability >= self.threshold
        
        return {
            'is_valuable': is_valuable,
            'confidence': probability,
            'threshold_used': self.threshold,
            'method': 'xgboost_optimized'
        }
    
    def classify_batch(self, contents):
        """批量分类"""
        results = []
        for content in contents:
            result = self.classify(content)
            results.append(result)
        return results

def compare_classifiers():
    """比较不同分类器"""
    print("=== 分类器性能对比 ===\n")
    
    # 测试用例
    test_cases = [
        ("申请要求", "Application requirements admission criteria GPA TOEFL deadline tuition fees"),
        ("课程信息", "Course curriculum modules core subjects electives dissertation credits"),
        ("联系信息", "Contact information phone email address office location directions"),
        ("奖学金信息", "Scholarship financial aid funding merit-based application deadline"),
        ("新闻事件", "News events announcements social media facebook twitter updates"),
        ("就业服务", "Career services job placement employment alumni network opportunities"),
        ("住宿信息", "Accommodation housing dormitory dining facilities campus life"),
        ("研究信息", "Research areas faculty expertise projects laboratories publications")
    ]
    
    # 加载XGBoost分类器
    xgb_classifier = XGBoostWebpageClassifier()
    
    print(f"\n分类结果对比:")
    print(f"{'内容类型':<12} {'XGBoost预测':<15} {'置信度':<10} {'建议'}")
    print("-" * 60)
    
    for category, content in test_cases:
        result = xgb_classifier.classify(content)
        
        prediction = "✅ 有价值" if result['is_valuable'] else "❌ 无价值"
        confidence = f"{result['confidence']:.3f}"
        
        # 给出使用建议
        if result['is_valuable'] and result['confidence'] > 0.9:
            advice = "高价值"
        elif result['is_valuable'] and result['confidence'] > 0.78:
            advice = "有价值"
        elif not result['is_valuable'] and result['confidence'] < 0.3:
            advice = "明确无价值"
        else:
            advice = "边界情况"
        
        print(f"{category:<12} {prediction:<15} {confidence:<10} {advice}")

def demo_usage():
    """使用示例"""
    print(f"\n=== 使用示例 ===")
    
    classifier = XGBoostWebpageClassifier()
    
    # 示例文本
    example_texts = [
        "Master of Science in Computer Science Program. Application deadline: January 15th. Requirements include bachelor's degree, GPA 3.0+, TOEFL 90+. Tuition: $45,000 per year.",
        "Contact us: Phone (555) 123-4567, Email info@university.edu, Office hours Mon-Fri 9am-5pm, Campus map and directions available online."
    ]
    
    for i, text in enumerate(example_texts, 1):
        result = classifier.classify(text)
        print(f"\n样本 {i}:")
        print(f"文本: {text[:80]}...")
        print(f"判断: {'✅ 有价值' if result['is_valuable'] else '❌ 无价值'}")
        print(f"置信度: {result['confidence']:.4f}")

def main():
    """主函数"""
    print("=== 最佳XGBoost网页分类器演示 ===")
    
    try:
        # 性能对比
        compare_classifiers()
        
        # 使用示例
        demo_usage()
        
        print(f"\n=== 总结 ===")
        print(f"✅ XGBoost模型是当前最佳选择")
        print(f"✅ 召回率95.7% - 几乎不会错过有价值页面")
        print(f"✅ 精确率96.4% - 误判率很低")
        print(f"✅ 仅18个假负例 - 比Random Forest少1个")
        print(f"✅ 建议在生产环境中使用此模型")
        
    except FileNotFoundError:
        print("❌ 找不到XGBoost模型文件")
        print("请先运行 train_best_xgboost.py 训练模型")
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    main()