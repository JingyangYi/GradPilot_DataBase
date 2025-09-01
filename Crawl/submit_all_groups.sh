#!/bin/bash

# 自动提交8个SLURM job，每个对应一个组 (受QOS限制，最多8个并发任务)
# 添加了时间跟踪功能，记录每个组任务的执行时间

# 生成日期时间戳 (格式：MMDD)
DATE_STAMP=$(date +%m%d)

# 记录总体开始时间
OVERALL_START_TIME=$(date)
echo "=== 开始提交所有组任务 ==="
echo "开始时间: ${OVERALL_START_TIME}"

for group in {1..8}; do
    # 创建带简单时间跟踪的任务命令
    TIMED_COMMAND="
    echo '第${group}组任务开始执行: '$(date)
    
    START_TIME=\$(date +%s)
    cd /net/scratch/jingyang/GradPilot_DataBase/Crawl && /home/jingyang22/.conda/envs/gp/bin/python run_all_subjects.py ${group}
    EXIT_CODE=\$?
    END_TIME=\$(date +%s)
    
    DURATION=\$((\$END_TIME - \$START_TIME))
    
    echo '第${group}组任务完成: '$(date)' (用时: '\$DURATION'秒)'
    echo '退出代码: '\$EXIT_CODE
    "
    
    sbatch --job-name="crawl_${group}" \
           --partition=general \
           --nodes=1 \
           --ntasks=1 \
           --cpus-per-task=4 \
           --mem=16G \
           --time=12:00:00 \
           --output=/net/scratch/jingyang/GradPilot_DataBase/Crawl/slurm_log/${DATE_STAMP}_group${group}_%j.out \
           --error=/net/scratch/jingyang/GradPilot_DataBase/Crawl/slurm_log/${DATE_STAMP}_group${group}_%j.err \
           --wrap="${TIMED_COMMAND}"
    
    echo "已提交第${group}组任务 (带时间跟踪)"
done

echo ""
echo "所有8个组的任务已提交完成！"
echo "提交时间: $(date)"
echo "日志位置: /net/scratch/jingyang/GradPilot_DataBase/Crawl/slurm_log/${DATE_STAMP}_group*"
echo ""
echo "查看实时日志的命令示例:"
echo "  tail -f slurm_log/${DATE_STAMP}_group1_*.out"
echo "  tail -f slurm_log/${DATE_STAMP}_group2_*.out"
echo ""
echo "查看所有任务时间统计:"
echo "  grep '执行时长' slurm_log/${DATE_STAMP}_group*.out"