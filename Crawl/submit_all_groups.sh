#!/bin/bash

# 自动提交5个SLURM job，每个对应一个组

for group in {1..5}; do
    sbatch --job-name="crawl_${group}" \
           --partition=general \
           --nodes=1 \
           --ntasks=1 \
           --cpus-per-task=4 \
           --mem=16G \
           --time=12:00:00 \
           --output=/net/scratch/jingyang/GradPilot_DataBase/Crawl/slurm_log/slurm_group${group}_%j.out \
           --error=/net/scratch/jingyang/GradPilot_DataBase/Crawl/slurm_log/slurm_group${group}_%j.err \
           --wrap="cd /net/scratch/jingyang/GradPilot_DataBase/Crawl && conda activate gp && python3 run_all_subjects.py ${group}"
    echo "已提交第${group}组任务"
done

echo "所有5个组的任务已提交完成！"