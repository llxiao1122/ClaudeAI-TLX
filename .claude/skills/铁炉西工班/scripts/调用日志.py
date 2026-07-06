#!/usr/bin/env python3
"""
铁炉西工班调用日志记录器
========================
记录每次技能调用的上下文、输出摘要和优化建议，用于动态迭代更新。
保留最近50条记录。

用法：
  python3 调用日志.py add --request "..." --output "..."  # 追加记录
  python3 调用日志.py list                                  # 列出最近记录
  python3 调用日志.py optimize                              # 分析并输出优化建议
"""

import argparse
import json
import os
import sys
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "调用日志.json")
MAX_RECORDS = 50


def load_logs() -> list:
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_logs(logs: list):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs[-MAX_RECORDS:], f, ensure_ascii=False, indent=2)


def add_log(request: str, output_summary: str, optimize_suggestion: str = ""):
    logs = load_logs()
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "request": request,
        "output_summary": output_summary,
        "optimize_suggestion": optimize_suggestion,
    })
    save_logs(logs)
    count = len(logs[-MAX_RECORDS:])
    print(f"✅ 日志已记录（共{count}条）")


def list_logs(limit: int = 10):
    logs = load_logs()
    if not logs:
        print("暂无调用记录")
        return
    print(f"\n📋 调用日志（最近{min(limit, len(logs))}条 / 共{len(logs)}条）")
    print("=" * 80)
    for entry in logs[-limit:]:
        print(f"[{entry['time']}]")
        print(f"  请求：{entry['request'][:60]}")
        print(f"  输出：{entry['output_summary'][:60]}")
        if entry.get("optimize_suggestion"):
            print(f"  建议：{entry['optimize_suggestion'][:60]}")
        print("-" * 40)


def analyze_optimizations() -> list:
    """分析日志，提取高频优化建议"""
    logs = load_logs()
    suggestions = {}
    for entry in logs:
        sug = entry.get("optimize_suggestion", "").strip()
        if sug and len(sug) > 5:
            suggestions[sug] = suggestions.get(sug, 0) + 1
    return sorted(suggestions.items(), key=lambda x: -x[1])


def parse_args():
    parser = argparse.ArgumentParser(description="铁炉西工班调用日志管理")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加调用记录")
    p_add.add_argument("--request", required=True, help="用户请求摘要")
    p_add.add_argument("--output", default="", help="输出摘要")
    p_add.add_argument("--optimize", default="", help="优化建议")

    p_list = sub.add_parser("list", help="列出最近记录")
    p_list.add_argument("--limit", type=int, default=10, help="显示条数")

    p_opt = sub.add_parser("optimize", help="分析优化建议")

    return parser.parse_args()


def main():
    args = parse_args()
    if args.command == "add":
        add_log(args.request, args.output, args.optimize)
    elif args.command == "list":
        list_logs(args.limit)
    elif args.command == "optimize":
        suggestions = analyze_optimizations()
        if suggestions:
            print("\n📊 高频优化建议TOP5：")
            for sug, count in suggestions[:5]:
                print(f"  [{count}次] {sug}")
        else:
            print("暂无优化建议数据")


if __name__ == "__main__":
    main()
