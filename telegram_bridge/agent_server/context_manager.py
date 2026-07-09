"""
上下文管理器

职责：保存对话历史，构建 Claude --print 的上下文 prompt。
每次调用生成一个包含历史+当前消息的完整 prompt。

Token 优化策略：
  - 对话超过 8 条自动生成摘要压缩历史
  - 终端侧上下文从 10 条减到 3 条
  - prompt 标题精简，去掉冗余分隔

双向同步：构建上下文时自动读取 shared_conversations.json 中终端侧的对话。
"""

import json, os, datetime, sys

from .config import MEMORY_FILE

# 加载共享仓库模块（TG ↔ Terminal 双向同步用）
SHARED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shared"
)
sys.path.insert(0, SHARED_DIR)
try:
    from shared_store import read_terminal_context
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

MAX_HISTORY = 10        # 保留最近对话条数
MAX_CONTEXT_MSGS = 4    # build_prompt 中展示的最近对话数
SUMMARY_TRIGGER = 8     # 超过此条数触发摘要压缩


def load_memory() -> dict:
    """加载记忆文件"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f:
                data = json.load(f)
                data.setdefault("facts", {})
                data.setdefault("conversations", [])
                data.setdefault("summary", "")
                return data
        except:
            pass
    return {"facts": {}, "conversations": [], "summary": ""}


def save_memory(memory: dict):
    """保存记忆"""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_message(memory: dict, role: str, content: str):
    """追加一条对话记录，超过阈值时触发摘要压缩"""
    memory.setdefault("conversations", []).append({
        "role": role,
        "content": content,
        "time": datetime.datetime.now().strftime("%m-%d %H:%M"),
    })
    if len(memory["conversations"]) > MAX_HISTORY:
        memory["conversations"] = memory["conversations"][-MAX_HISTORY:]

    # 超过触发阈值 → 生成摘要
    if len(memory["conversations"]) >= SUMMARY_TRIGGER:
        _summarize_history(memory)


def set_fact(memory: dict, key: str, value: str):
    """保存事实"""
    memory.setdefault("facts", {})[key] = value


def _summarize_history(memory: dict):
    """
    将早期对话压缩为一句摘要，减少后续 prompt 中的上下文长度。

    取 oldest_count 条最早对话，用关键词提取生成摘要，
    存到 memory["summary"]；保留最近 MAX_CONTEXT_MSGS 条不动。
    """
    convos = memory.get("conversations", [])
    if len(convos) <= MAX_CONTEXT_MSGS:
        return

    oldest_count = len(convos) - MAX_CONTEXT_MSGS
    oldest = convos[:oldest_count]

    # 简单关键词摘要（不调用任何 LLM，零成本）
    user_topics = set()
    for c in oldest:
        if c["role"] == "user":
            # 取前 15 个字作为主题词
            topic = c["content"][:15].replace("\n", " ")
            user_topics.add(topic)

    topic_str = "、".join(list(user_topics)[:3])
    memory["summary"] = f"用户询问了: {topic_str}（共{oldest_count}条历史已压缩）"


def build_prompt(user_message: str, memory: dict) -> str:
    """
    构建发送给 Claude --print 的完整 prompt（精简版以减少 token 消耗）。

    格式:
      【摘要】...（如有）
      【历史】最近N条
      【事实】...（如有）
      【终端侧】...（如有，精简格式）
      用户消息（无标签）
    """
    parts = []
    facts = memory.get("facts", {})
    convos = memory.get("conversations", [])
    summary = memory.get("summary", "")

    # 摘要（如有）
    if summary:
        parts.append(f"【摘要】{summary}")

    # 最近对话（仅展示最后几条）
    if convos:
        recent = convos[-MAX_CONTEXT_MSGS:]
        parts.append("【历史】")
        for c in recent:
            prefix = "用户" if c["role"] == "user" else "助手"
            parts.append(f"[{c['time']}] {prefix}: {c['content']}")

    # 已记住的事实
    if facts:
        parts.append("【事实】")
        for k, v in facts.items():
            parts.append(f"- {k}: {v}")

    # 终端侧共享对话（精简格式）
    if _HAS_SHARED:
        term_ctx = read_terminal_context(limit=3)
        if term_ctx:
            parts.append(term_ctx)

    # 当前消息（不加标签节省 token）
    parts.append(user_message)

    return "\n".join(parts)
