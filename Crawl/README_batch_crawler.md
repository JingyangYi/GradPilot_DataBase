# 分批爬虫使用指南

## 概述

针对8928条数据的大规模爬取，提供了分批处理、断点续传、失败恢复的完整解决方案。

## 核心功能

### 1. 按学科自动分批
- 自动将8928条数据按学科分组（共60+个学科）
- 大学科（如计算机461条）单独处理
- 小学科可合并处理

### 2. 断点续传
- 自动记录每个学科的爬取状态
- 支持从中断处继续，无需重复爬取
- 状态文件：`crawl_status.json`

### 3. 三级日志系统
- **全局进度日志**：`logs/global_progress_*.log` - 整体进度追踪
- **学科级别日志**：`logs/subject_*_*.log` - 每个学科详细日志  
- **错误汇总日志**：`logs/error_summary_*.log` - 所有错误集中记录

### 4. 失败项目追踪
- 自动记录失败项目详情
- 支持失败项目重试
- 失败原因追踪

## 使用方法

### 基本命令

```bash
# 爬取所有学科（推荐）
python batch_crawler.py --all

# 爬取指定学科
python batch_crawler.py --subjects "计算机,医学,法律"

# 从断点继续（如果之前中断了）
python batch_crawler.py --resume

# 查看当前状态
python batch_crawler.py --status
```

### 推荐流程

1. **首次运行**：
   ```bash
   python batch_crawler.py --all
   ```

2. **如果中断，继续爬取**：
   ```bash
   python batch_crawler.py --resume
   ```

3. **查看进度**：
   ```bash
   python batch_crawler.py --status
   ```

## 输出结构

```
crawl/
├── output/                    # JSON输出目录
│   ├── 计算机/               # 按学科分类的文件夹
│   ├── 医学/
│   └── ...
├── logs/                     # 日志目录
│   ├── global_progress_*.log # 全局进度
│   ├── subject_*_*.log      # 学科日志
│   └── error_summary_*.log  # 错误汇总
├── crawl_status.json        # 状态文件
└── batch_crawler.py         # 主控制脚本
```

## 状态文件说明

`crawl_status.json` 记录：
- 各学科爬取状态（pending/running/completed/failed）
- 成功/失败项目计数
- 失败项目详细信息
- 最后更新时间

## 容错机制

1. **网络中断**：自动保存当前状态，可通过 `--resume` 继续
2. **单个学科失败**：不影响其他学科，记录失败原因
3. **系统崩溃**：状态实时保存，重启后可继续

## 监控建议

1. **实时监控**：
   ```bash
   tail -f logs/global_progress_*.log
   ```

2. **错误监控**：
   ```bash
   tail -f logs/error_summary_*.log
   ```

3. **进度查看**：
   ```bash
   python batch_crawler.py --status
   ```

## 性能优化

- 每个学科间有2秒间隔，避免系统压力
- 大学科优先处理，小学科合并
- 自动清理临时文件
- 状态实时保存，内存占用可控

## 故障恢复

如果爬虫意外停止：

1. 检查状态：`python batch_crawler.py --status`
2. 查看错误：`cat logs/error_summary_*.log`
3. 继续爬取：`python batch_crawler.py --resume`

## 预计时间

- 单个项目平均2-5秒
- 8928个项目预计需要5-12小时
- 分批处理可随时中断和恢复