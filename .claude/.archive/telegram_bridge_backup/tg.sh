#!/bin/bash
# tg.sh - 极简TG通信：发一条命令完成检查+回复
# 用法: ./tg.sh              → 检查新消息（输出到终端）
#       ./tg.sh "回复内容"   → 发送消息

TOKEN="8791484754:AAF5siHC-G8YtIQsxypmWOAVNknQk3HAkok"
CHAT="8422191476"
FLAG="/tmp/tg_off"
INBOX="/Users/lee/Documents/ClaudeAI-TLX/telegram_bridge/inbox.md"

if [ -n "$1" ]; then
    # 发消息
    curl -s -x "http://127.0.0.1:7897" "https://api.telegram.org/bot${TOKEN}/sendMessage" \
        -d "chat_id=${CHAT}" -d "text=$1" -o /dev/null
    echo "[$(date '+%H:%M')] → $1"
    exit 0
fi

# 检查新消息
O=$(cat "$FLAG" 2>/dev/null || echo 0)
R=$(curl -s -x "http://127.0.0.1:7897" "https://api.telegram.org/bot${TOKEN}/getUpdates?offset=${O}&timeout=10")
NEW=$(echo "$R" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for u in d.get('result',[]):
    m=u.get('message',{})
    t=m.get('text','')
    n=m['from'].get('first_name','')
    print(f'{u[\"update_id\"]}|{n}|{t}')
" 2>/dev/null)

if [ -z "$NEW" ]; then
    echo "无新消息"
    exit 0
fi

LAST=$(echo "$NEW" | tail -1)
OID=$(echo "$LAST" | cut -d'|' -f1)
NAME=$(echo "$LAST" | cut -d'|' -f2)
TEXT=$(echo "$LAST" | cut -d'|' -f3-)
echo "$((OID+1))" > "$FLAG"
echo "[$(date '+%m-%d %H:%M')] ${NAME}: ${TEXT}" >> "$INBOX"
echo "新消息: ${NAME}: ${TEXT}"
