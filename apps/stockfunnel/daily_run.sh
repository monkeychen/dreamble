#!/bin/bash
# stockfunnel 每日选股任务
# 由 launchd（com.dreamble.stockfunnel）每天 17:00 触发，也可手动执行：
#   ./daily_run.sh
# 流程：增量更新 → 筛选最近 5 天信号 → 写入 output/daily_screen.txt
# 运行日志：output/daily_run.log

set -u

PROJECT_DIR="/Users/chenzhian/workspace/ai/dreamble/apps/stockfunnel"
OUTPUT_DIR="$PROJECT_DIR/output"
RESULT_FILE="$OUTPUT_DIR/daily_screen.txt"
LOG_FILE="$OUTPUT_DIR/daily_run.log"

# launchd 环境变量精简，补全 PATH 并固定 UTF-8 编码
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_DIR" || exit 1

START_TS=$(date +%s)
{
    echo "===== 每日选股任务开始 $(date '+%Y-%m-%d %H:%M:%S') ====="

    # 1. 增量更新（非交易日自动快速跳过；失败不阻断筛选，用已有数据兜底）
    UPDATE_OUTPUT=$(./stockfunnel update 2>&1)
    UPDATE_RC=$?
    echo "[update] 退出码 ${UPDATE_RC}"
    echo "$UPDATE_OUTPUT" | tail -8 | sed 's/^/[update] /'
    if [ $UPDATE_RC -ne 0 ]; then
        echo "[update] 警告：更新失败，将基于本地已有数据筛选"
    fi

    # 2. 筛选最近 5 天信号
    SCREEN_OUTPUT=$(./stockfunnel screen --days 5 2>&1)
    SCREEN_RC=$?

    # 3. 写结果文件：有信号保留完整输出，无信号注明"今日无信号"
    if [ $SCREEN_RC -ne 0 ]; then
        {
            echo "===== stockfunnel 每日筛选 $(date '+%Y-%m-%d %H:%M') ====="
            echo "[错误] 筛选命令执行失败（退出码 ${SCREEN_RC}），详见 daily_run.log"
        } > "$RESULT_FILE"
        echo "[screen] 退出码 ${SCREEN_RC}（失败）"
        echo "$SCREEN_OUTPUT" | tail -5 | sed 's/^/[screen] /'
    elif echo "$SCREEN_OUTPUT" | grep -qE '(sh|sz)\.[0-9]{6}'; then
        SIGNAL_COUNT=$(echo "$SCREEN_OUTPUT" | grep -cE '(sh|sz)\.[0-9]{6}')
        {
            echo "===== stockfunnel 每日筛选 $(date '+%Y-%m-%d %H:%M') ====="
            echo ""
            echo "$SCREEN_OUTPUT"
        } > "$RESULT_FILE"
        echo "[screen] 信号数：${SIGNAL_COUNT}"
        echo "[结果] 共 ${SIGNAL_COUNT} 条信号，已写入 daily_screen.txt"
    else
        {
            echo "===== stockfunnel 每日筛选 $(date '+%Y-%m-%d %H:%M') ====="
            echo "今日无信号"
        } > "$RESULT_FILE"
        echo "[结果] 今日无信号，已写入 daily_screen.txt"
    fi

    ELAPSED=$(( $(date +%s) - START_TS ))
    echo "===== 每日选股任务结束，用时 ${ELAPSED} 秒 ====="
    echo ""
} >> "$LOG_FILE" 2>&1
