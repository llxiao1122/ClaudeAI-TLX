#!/usr/bin/env python3
"""
TG 消息发送脚本（终端→TG）

用法:
  python3 tg_send.py "消息内容"
  python3 tg_send.py -s "消息内容"   # 静默模式，只发不写入共享仓库

功能:
  1. 发送消息到 Telegram
  2. 自动写入 shared_conversations.json（标记来源为 terminal）
"""

import sys, os, warnings
warnings.filterwarnings("ignore", message=".*OpenSSL.*")
import requests

# 确保能找到 shared 模块
SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared")
sys.path.insert(0, SHARED_DIR)

from shared_store import write_conversation

# 从上级 config 导入配置
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CONFIG_DIR)

from config import TOKEN, PROXY

PROXIES = {"http": PROXY, "https": PROXY}


def send_message(text: str, chat_id: str = None) -> bool:
    """发送消息到 Telegram"""
    if chat_id is None:
        from config import CHAT_ID
        chat_id = CHAT_ID

    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": chat_id, "text": text},
            proxies=PROXIES,
            timeout=15,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[TG Send Error] {e}", file=sys.stderr)
        return False


def main():
    silent = False
    args = sys.argv[1:]

    if not args:
        print("用法: python3 tg_send.py [-s] \"消息内容\"", file=sys.stderr)
        sys.exit(1)

    if args[0] == "-s":
        silent = True
        args = args[1:]

    message = " ".join(args)

    # 发送到 TG
    ok = send_message(message)
    if not ok:
        print("❌ 发送失败", file=sys.stderr)
        sys.exit(1)

    # 写入共享仓库
    if not silent:
        write_conversation("terminal", "assistant", message)

    print("✅ 已发送到 Telegram")


if __name__ == "__main__":
    main()
