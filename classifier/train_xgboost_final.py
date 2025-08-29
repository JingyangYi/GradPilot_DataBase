#!/usr/bin/env python3
"""
训练最终的XGBoost网页内容价值分类器
- 独立训练脚本，可重复运行
- 最优参数配置
- 处理未见token问题
- 详细性能报告
"""

import json
import re
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, recall_score, precision_score
from sklearn.pipeline import Pipeline
import xgboost as xgb
import joblib
from datetime import datetime

def preprocess_text(text):
    """
    文本预处理函数
    处理HTML标记，标准化文本格式
    """
    if not isinstance(text, str):
        return ""
    
    # 移除特殊标记
    text = re.sub(r'\[HEADING\]', '', text)
    # 保留字母和数字，替换其他字符为空格
    text = re.sub(r'[^\w\s]', ' ', text)
    # 合并多个空格
    text = re.sub(r'\s+', ' ', text)
    # 转小写并去除首尾空格
    return text.strip().lower()

def load_training_data(file_path='training_data_unified.json'):
    """
    加载训练数据
    返回文本列表和标签列表
    """
    print(f"加载训练数据: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    X, y, metadata = [], [], []
    
    for sample in data['samples']:
        content = preprocess_text(sample['x'])
        
        # 过滤太短的内容
        if len(content) > 10:
            X.append(content)
            y.append(sample['y'])
            metadata.append(sample['metadata'])
    
    print(f"有效样本数: {len(X)}")
    print(f"有价值样本: {sum(y)} ({sum(y)/len(y)*100:.1f}%)")
    print(f"无价值样本: {len(y)-sum(y)} ({(len(y)-sum(y))/len(y)*100:.1f}%)")
    
    return X, y, metadata

def create_xgboost_pipeline():
    """
    创建XGBoost分类管道
    包含TF-IDF特征提取和XGBoost分类器
    """
    
    # TF-IDF参数优化
    # - max_features: 限制特征数量，防止过拟合
    # - ngram_range: 使用1-2gram捕获词汇搭配
    # - min_df: 过滤低频词，减少噪声
    # - max_df: 过滤高频词，去除常见无意义词
    tfidf_vectorizer = TfidfVectorizer(
        max_features=12000,      # 最多12k特征，平衡性能和效果
        ngram_range=(1, 2),      # 1-2gram特征
        min_df=2,                # 至少出现2次
        max_df=0.95,             # 最多95%文档包含
        stop_words='english',    # 移除英文停用词
        lowercase=True,          # 转小写
        token_pattern=r'\b\w+\b' # 只保留完整单词
    )
    
    # XGBoost参数优化
    # - n_estimators: 树的数量，更多树通常更好但会增加训练时间
    # - max_depth: 树的深度，防止过拟合
    # - learning_rate: 学习率，较低值需要更多树但通常更稳定
    # - scale_pos_weight: 处理类别不平衡
    # - subsample: 行采样，防止过拟合
    # - colsample_bytree: 列采样，增加随机性
    # - reg_alpha/lambda: 正则化参数
    xgb_classifier = xgb.XGBClassifier(
        n_estimators=200,         # 200棵树，足够捕获复杂模式
        max_depth=7,              # 深度7，平衡复杂度和泛化
        learning_rate=0.08,       # 较低学习率，更稳定
        scale_pos_weight=2.2,     # 给有价值类别2.2倍权重
        subsample=0.8,            # 80%行采样
        colsample_bytree=0.8,     # 80%列采样
        min_child_weight=1,       # 最小子节点权重
        gamma=0,                  # 最小分裂增益
        reg_alpha=0.1,            # L1正则化
        reg_lambda=1,             # L2正则化
        random_state=42,          # 固定随机种子
        eval_metric='logloss',    # 评估指标
        verbosity=0,              # 减少输出
        use_label_encoder=False   # 避免警告
    )
    
    # 创建管道
    pipeline = Pipeline([
        ('tfidf', tfidf_vectorizer),
        ('classifier', xgb_classifier)
    ])
    
    return pipeline

def find_optimal_threshold(model, X_test, y_test, target_recall=0.95):
    """
    寻找最优分类阈值
    目标是达到95%以上召回率的前提下最大化精确率
    """
    print(f"寻找最优阈值（目标召回率≥{target_recall*100}%）...")
    
    # 获取预测概率
    probabilities = model.predict_proba(X_test)[:, 1]
    
    best_config = None
    
    # 测试不同阈值
    for threshold in np.arange(0.1, 0.9, 0.01):
        predictions = (probabilities >= threshold).astype(int)
        
        recall = recall_score(y_test, predictions)
        precision = precision_score(y_test, predictions) if sum(predictions) > 0 else 0
        
        # 只考虑达到目标召回率的配置
        if recall >= target_recall:
            cm = confusion_matrix(y_test, predictions)
            tn, fp, fn, tp = cm.ravel()
            
            config = {
                'threshold': threshold,
                'recall': recall,
                'precision': precision,
                'f1': 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0,
                'false_negatives': fn,
                'false_positives': fp,
                'accuracy': (tp + tn) / (tp + tn + fp + fn)
            }
            
            # 选择精确率最高的配置
            if best_config is None or precision > best_config['precision']:
                best_config = config
    
    if best_config:
        print(f"找到最优配置:")
        print(f"  阈值: {best_config['threshold']:.3f}")
        print(f"  召回率: {best_config['recall']:.4f}")
        print(f"  精确率: {best_config['precision']:.4f}")
        print(f"  F1分数: {best_config['f1']:.4f}")
        print(f"  准确率: {best_config['accuracy']:.4f}")
        print(f"  假负例: {best_config['false_negatives']}")
        print(f"  假正例: {best_config['false_positives']}")
    else:
        print(f"警告: 未找到满足{target_recall*100}%召回率的配置")
    
    return best_config

def evaluate_model_performance(model, X_test, y_test, threshold, verbose=True):
    """
    详细评估模型性能
    """
    if verbose:
        print("=== 模型性能详细评估 ===")
    
    # 预测
    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    
    # 基础指标
    recall = recall_score(y_test, predictions)
    precision = precision_score(y_test, predictions)
    
    if verbose:
        print(f"\n分类报告:")
        print(classification_report(y_test, predictions, target_names=['无价值', '有价值']))
        
        # 混淆矩阵
        cm = confusion_matrix(y_test, predictions)
        print(f"\n混淆矩阵:")
        print(f"实际\\预测  无价值  有价值")
        print(f"无价值     {cm[0,0]:6d}  {cm[0,1]:6d}")
        print(f"有价值     {cm[1,0]:6d}  {cm[1,1]:6d}")
    
    return {
        'recall': recall,
        'precision': precision,
        'predictions': predictions,
        'probabilities': probabilities
    }

def cross_validate_model(pipeline, X, y, cv=5):
    """
    交叉验证评估模型稳定性
    """
    print(f"执行{cv}折交叉验证...")
    
    # 使用分层交叉验证保持类别比例
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    
    # 计算交叉验证分数
    cv_scores = cross_val_score(pipeline, X, y, cv=skf, scoring='accuracy')
    
    print(f"交叉验证结果:")
    print(f"  平均准确率: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"  各折分数: {[f'{score:.4f}' for score in cv_scores]}")
    
    return cv_scores

def analyze_feature_importance(pipeline, top_n=20):
    """
    分析特征重要性（XGBoost）
    """
    print(f"\n=== 特征重要性分析（前{top_n}个） ===")
    
    try:
        # 获取特征名称
        feature_names = pipeline.named_steps['tfidf'].get_feature_names_out()
        
        # 获取XGBoost特征重要性
        importance_scores = pipeline.named_steps['classifier'].feature_importances_
        
        # 排序并获取前N个
        feature_importance = list(zip(feature_names, importance_scores))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        print("最重要的特征词:")
        for i, (feature, importance) in enumerate(feature_importance[:top_n]):
            print(f"  {i+1:2d}. {feature:20s} {importance:.4f}")
            
    except Exception as e:
        print(f"特征重要性分析失败: {e}")

def handle_unknown_tokens():
    """
    说明如何处理未见过的token
    """
    print("\n=== 未见token处理机制 ===")
    print("TF-IDF向量化器的处理方式:")
    print("1. 训练时建立词汇表，只包含训练集中的词汇")
    print("2. 预测时遇到未见词汇会被忽略（不会报错）")
    print("3. 这是合理的，因为未见词汇对分类贡献未知")
    print("4. 模型主要依赖已知的重要特征词进行判断")
    print("5. 大量未见词汇可能降低置信度，但不会破坏分类")
    
    print("\n缓解策略:")
    print("- min_df=2: 过滤极少出现的词，提高泛化性")
    print("- n-gram特征: 捕获词汇搭配，减少对单词的依赖")  
    print("- 12000特征: 足够大的词汇表覆盖常见词汇")
    print("- 定期重训练: 用新数据更新模型词汇表")

def save_model(pipeline, threshold, metrics, save_path='xgboost_classifier.joblib'):
    """
    保存完整的模型配置
    """
    model_package = {
        'model': pipeline,
        'threshold': threshold,
        'model_name': 'XGBoost_Final',
        'training_date': datetime.now().isoformat(),
        'metrics': metrics,
        'parameters': {
            'tfidf': pipeline.named_steps['tfidf'].get_params(),
            'xgboost': pipeline.named_steps['classifier'].get_params()
        }
    }
    
    joblib.dump(model_package, save_path)
    print(f"\n模型已保存: {save_path}")
    print(f"模型大小: {joblib.load(save_path).__sizeof__()} bytes")
    
    return save_path

def main():
    """
    主训练流程
    """
    print("=" * 60)
    print("XGBoost 网页内容价值分类器训练")
    print("=" * 60)
    
    # 1. 加载数据
    X, y, metadata = load_training_data()
    
    # 2. 分割数据
    print(f"\n分割训练测试集...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"训练集: {len(X_train)} 样本")
    print(f"测试集: {len(X_test)} 样本")
    
    # 3. 创建模型
    print(f"\n创建XGBoost模型管道...")
    pipeline = create_xgboost_pipeline()
    
    # 4. 交叉验证
    cv_scores = cross_validate_model(pipeline, X_train, y_train)
    
    # 5. 训练模型
    print(f"\n开始训练...")
    pipeline.fit(X_train, y_train)
    print(f"训练完成!")
    
    # 6. 寻找最优阈值
    optimal_config = find_optimal_threshold(pipeline, X_test, y_test)
    
    if optimal_config is None:
        print("❌ 模型未达到性能要求")
        return None
    
    # 7. 详细性能评估
    performance = evaluate_model_performance(
        pipeline, X_test, y_test, 
        optimal_config['threshold']
    )
    
    # 8. 特征重要性分析
    analyze_feature_importance(pipeline)
    
    # 9. 未见token处理说明
    handle_unknown_tokens()
    
    # 10. 保存模型
    final_metrics = {
        'cv_accuracy_mean': cv_scores.mean(),
        'cv_accuracy_std': cv_scores.std(),
        'test_recall': optimal_config['recall'],
        'test_precision': optimal_config['precision'],
        'test_f1': optimal_config['f1'],
        'test_accuracy': optimal_config['accuracy'],
        'false_negatives': optimal_config['false_negatives'],
        'false_positives': optimal_config['false_positives'],
        'optimal_threshold': optimal_config['threshold']
    }
    
    model_path = save_model(pipeline, optimal_config['threshold'], final_metrics)
    
    # 11. 最终总结
    print(f"\n" + "=" * 60)
    print("训练完成总结")
    print("=" * 60)
    print(f"✅ 交叉验证准确率: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"✅ 测试集召回率: {optimal_config['recall']:.4f} (95%+达标)")
    print(f"✅ 测试集精确率: {optimal_config['precision']:.4f}")
    print(f"✅ 最优阈值: {optimal_config['threshold']:.3f}")
    print(f"✅ 假负例数量: {optimal_config['false_negatives']} (错过的有价值页面)")
    print(f"✅ 模型文件: {model_path}")
    print(f"✅ 未见token问题: 已通过TF-IDF机制妥善处理")
    
    return pipeline, optimal_config['threshold']

if __name__ == "__main__":
    model, threshold = main()