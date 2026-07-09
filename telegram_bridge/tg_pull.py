#!/usr/bin/env python3
"""
拉取 TG 侧最近对话（共享仓库 → 终端）

用法:
  python3 tg_pull.py             # 显示最近 TG 对话
  python3 tg_pull.py -c          # 复制到剪贴板（供 Claude 直接引用）
  python3 tg_pull.py -n 20       # 显示最近 20 条
"""

import sys, os, subprocess, json

SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared")
sys.path.insert(0, SHARED_DIR)
from shared_store import read_conversations, write_conversation


def format_conversations(convos: list) -> str:
    """格式化对话记录"""
    if not convos:
        return "（暂无 TG 对话记录）"

    lines = ["【TG 侧最近对话】"]
    for c in convos:
        prefix = "📱 我（TG）" if c["role"] == "user" else "🤖 AI（TG）"
        lines.append(f"{prefix} [{c['time']}]: {c['content']}")
    return "\n".join(lines)


def main():
    limit = 10
    copy_mode = False

    args = sys.argv[1:]
    while args:
        if args[0] == "-c":
            copy_mode = True
            args = args[1:]
        elif args[0] == "-n" and len(args) > 1:
            limit = int(args[1])
            args = args[2:]
        else:
            args = args[1:]

    convos = read_conversations(limit=limit, source="tg")
    text = format_conversations(convos)

    print(text)

    if copy_mode:
        # macOS 剪贴板
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        p.communicate(text.encode("utf-8"))
        print("\n（已复制到剪贴板）")


if __name__ == "__main__":
    main()
