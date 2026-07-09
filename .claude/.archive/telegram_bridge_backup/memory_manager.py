"""
记忆管理器

职责：持久化对话历史和关键事实，让 bot 具备长期记忆能力。
bot.py 在每次调用 API 前加载记忆，调用后保存更新。
"""

import json, os, datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")
MAX_HISTORY = 20  # 保留最近 N 条对话

def load() -> dict:
    """加载全部记忆"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"facts": {}, "conversations": []}


def save(memory: dict):
    """持久化记忆"""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_conversation(memory: dict, role: str, content: str):
    """追加一条对话记录"""
    memory.setdefault("conversations", []).append({
        "role": role,
        "content": content,
        "time": datetime.datetime.now().strftime("%m-%d %H:%M"),
    })
    # 截断保留最近 N 条
    if len(memory["conversations"]) > MAX_HISTORY:
        memory["conversations"] = memory["conversations"][-MAX_HISTORY:]


def set_fact(memory: dict, key: str, value: str):
    """保存一条事实"""
    memory.setdefault("facts", {})[key] = value


def delete_fact(memory: dict, key: str):
    """删除一条事实"""
    memory.get("facts", {}).pop(key, None)


def to_context(memory: dict) -> str:
    """将记忆压缩为提示词上下文"""
    facts = memory.get("facts", {})
    convos = memory.get("conversations", [])

    parts = []
    if facts:
        parts.append("【已记住的事实】")
        for k, v in facts.items():
            parts.append(f"- {k}: {v}")
        parts.append("")

    if convos:
        parts.append("【最近对话】")
        for c in convos[-6:]:  # 最近 6 条
            prefix = "你" if c["role"] == "user" else "我"
            parts.append(f"[{c['time']}] {prefix}: {c['content']}")
        parts.append("")

    return "\n".join(parts)
