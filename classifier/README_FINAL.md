# 网页内容价值分类器 - 最终版本

## 快速开始

### 1. 训练模型
```bash
python train_xgboost_final.py
```

### 2. 使用模型
```python
from use_xgboost_classifier import XGBoostWebpageClassifier

classifier = XGBoostWebpageClassifier()
result = classifier.classify("webpage content here")

print(f"是否有价值: {result['is_valuable']}")
print(f"置信度: {result['confidence']:.3f}")
```

## 项目结构

```
classifier/
├── 📄 README_FINAL.md              # 本文件
├── 📄 MODEL_SELECTION.md           # 详细的模型选择说明
├── 
├── 🔧 train_xgboost_final.py       # 独立训练脚本
├── 🔧 use_xgboost_classifier.py    # 模型应用接口
├── 
├── 📊 xgboost_best_classifier.joblib    # 最佳模型文件
├── 📊 training_data_unified.json        # 训练数据
├── 
└── 📁 data_20250812/               # 原始标注数据
    ├── classifier_training_data_part1_labeled.json
    ├── classifier_training_data_part2_labeled.json
    └── classifier_training_data_part3_labeled.json
```

## 模型性能

🎯 **核心指标**
- ✅ **召回率**: 95.7% (几乎不错过有价值页面)
- ✅ **精确率**: 96.4% (很少误判)
- ✅ **假负例**: 仅18个 (错过的有价值页面)
- ✅ **F1分数**: 96.0%

📊 **详细性能**
```
              precision    recall  f1-score   support
    无价值       0.96      0.97      0.96       437
    有价值       0.96      0.96      0.96       419
    
    accuracy                         0.96       856
```

## 模型特点

### ✅ 优势
1. **高召回率**: 95.7%，满足"绝不放过有价值页面"的需求
2. **高精确率**: 96.4%，误判率很低
3. **强泛化性**: 处理未见词汇的能力强
4. **快速部署**: 单文件模型，易于集成

### ⚠️ 注意事项
1. **新领域适应**: 包含大量专业术语的新领域可能需要重新训练
2. **置信度监控**: 建议监控预测置信度，对低置信度结果人工审核
3. **定期更新**: 建议每季度用新数据重新训练

## 技术细节

### 🧠 模型架构
- **特征提取**: TF-IDF (12000特征, 1-2gram)
- **分类器**: XGBoost (200棵树)
- **优化阈值**: 0.780 (降低假负例)

### 🔧 关键参数
```python
# TF-IDF
max_features=12000, ngram_range=(1,2), min_df=2

# XGBoost  
n_estimators=200, max_depth=7, learning_rate=0.08,
scale_pos_weight=2.2, reg_alpha=0.1, reg_lambda=1
```

## 使用场景

### ✅ 适用场景
- 研究生项目网页内容筛选
- 申请信息vs无关信息分类
- 教育网站内容价值判断
- 自动化内容审核

### 📝 分类示例
| 内容类型 | 判断结果 | 置信度 |
|---------|---------|--------|
| 申请要求 | ✅ 有价值 | 0.86 |
| 课程信息 | ❌ 无价值 | 0.39 |
| 联系信息 | ❌ 无价值 | 0.30 |
| 奖学金信息 | ✅ 有价值 | 0.82 |

## 未见Token处理

### 🔍 问题说明
实际使用中可能遇到训练时未见过的词汇（新术语、机构名等）。

### ✅ 解决方案
1. **TF-IDF机制**: 自动忽略未见词汇，不会报错
2. **已知词依赖**: 主要依赖已知重要特征词判断
3. **N-gram特征**: 通过词汇搭配减少单词依赖
4. **大词汇表**: 12000特征覆盖常见词汇

### 📊 测试结果
- **正常文本**: 预测可靠，置信度0.86+
- **少量新词**: 基本不受影响，置信度0.8+  
- **大量新词**: 置信度下降但不崩溃，置信度0.3+
- **全新词汇**: 返回默认判断，建议人工审核

## 部署指南

### 🚀 生产环境
```python
import joblib

# 加载模型
model_data = joblib.load('xgboost_best_classifier.joblib')
model = model_data['model']
threshold = model_data['threshold']  # 0.780

# 分类函数
def classify_webpage(content):
    prob = model.predict_proba([content])[0][1]
    is_valuable = prob >= threshold
    
    return {
        'is_valuable': is_valuable,
        'confidence': prob,
        'recommendation': 'review' if prob < 0.6 else 'confident'
    }
```

### 📈 监控建议
1. **预测置信度分布**: 正常应集中在高置信度区间
2. **假负例监控**: 核心指标，应保持<5%
3. **人工反馈**: 收集错误案例持续改进
4. **新词汇监控**: 决定重训练时机

## 开发历程

### 🔬 模型选择过程
1. **Logistic Regression**: 基线模型，87%准确率
2. **Random Forest**: 改进版本，95.5%召回率
3. **Support Vector Machine**: 备选方案，95%召回率  
4. **XGBoost**: 最终选择，95.7%召回率 + 96.4%精确率

### 🎯 优化过程
1. **类别权重调整**: 处理样本不平衡
2. **特征工程**: TF-IDF参数优化
3. **阈值调优**: 从0.5优化到0.78
4. **正则化**: 防止过拟合
5. **交叉验证**: 确保模型稳定性

## FAQ

**Q: 为什么选择XGBoost而不是深度学习？**
A: 对于这个中等规模的文本分类问题，XGBoost提供了最佳的性能/复杂度平衡，训练快速且易于部署。

**Q: 如何处理非英文内容？**
A: 当前模型针对英文优化。对于其他语言，需要重新训练或使用多语言预处理。

**Q: 模型多久需要重新训练？**
A: 建议每季度评估一次。如果假负例率上升或置信度显著下降，则需要重新训练。

**Q: 如何扩展到其他领域？**
A: 收集目标领域的标注数据，使用现有模型作为预训练基础进行微调。

## 许可证

本项目仅供学习和研究使用。

---

📞 **技术支持**: 如有问题请查看 `MODEL_SELECTION.md` 获取详细技术说明。