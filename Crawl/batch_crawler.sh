#!/bin/bash
#SBATCH --job-name=GP_Crawler          # 任务名称
#SBATCH --output=/net/scratch/jingyang/GradPilot_DataBase/Crawl/slurm_log/GP_Crawler_%j.out   # 标准输出日志
#SBATCH --error=/net/scratch/jingyang/GradPilot_DataBase/Crawl/slurm_log/GP_Crawler_%j.err    # 错误输出日志
#SBATCH --time=10:00:00                # 任务最长运行时间 (12小时)
#SBATCH --nodes=1                      # 节点数
#SBATCH --ntasks=1                     # 总任务数
#SBATCH --cpus-per-task=16              # 每个任务使用的CPU核心数
#SBATCH --mem=64G                      # 内存需求
#SBATCH --partition=general   


# ========== 工作目录 ==========
cd /net/scratch/jingyang/GradPilot_DataBase/Crawl

# ========== 启动爬虫 ==========
# 确保你的爬虫脚本是可执行的，比如 scrapy 或 python 脚本
# python batch_crawler.py --all
python batch_crawler.py --status
python batch_crawler.py --subject "计算机,金融,机械工程,工商管理"
