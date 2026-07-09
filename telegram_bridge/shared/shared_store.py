"""
共享对话仓库（Shared Conversation Store）

职责：让 TG Bot 和 Terminal Session 共享对话记录，实现双向上下文同步。

架构：
  - shared_conversations.json 是唯一的共享数据文件
  - TG Bot 收到消息 → 写入仓库
  - Terminal Session（Claude Code）回复 → 写入仓库
  - TG Bot 构建上下文前 → 读取仓库中 terminal 侧的对话
  - Terminal 处理消息前 → 读取仓库中 TG 侧的对话

线程安全：文件级锁（fcntl/flock），防止并发写冲突。
"""

import json, os, time, errno

SHARED_DIR = os.path.dirname(os.path.abspath(__file__))
STORE_FILE = os.path.join(SHARED_DIR, "shared_conversations.json")

MAX_CONVERSATIONS = 100  # 最多保留 100 条，防止无限膨胀


def _lock(f):
    """尝试加锁（macOS/Linux fcntl），不可用时降级"""
    try:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        return True
    except (ImportError, OSError):
        pass  # Windows 或不支持的环境
    return False


def _unlock(f):
    try:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (ImportError, OSError):
        pass


def init_store():
    """如果共享仓库文件不存在，创建空文件"""
    if not os.path.exists(STORE_FILE):
        with open(STORE_FILE, "w") as f:
            json.dump({"conversations": []}, f, ensure_ascii=False, indent=2)
        return True
    return False


def _load_raw() -> dict:
    """不加锁加载（内部用，调用方自己处理锁）"""
    if not os.path.exists(STORE_FILE):
        return {"conversations": []}
    try:
        with open(STORE_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"conversations": []}
        return data
    except (json.JSONDecodeError, OSError):
        return {"conversations": []}


def _save_raw(data: dict):
    """不加锁保存（内部用，调用方自己处理锁）"""
    # 裁剪过量记录
    convos = data.get("conversations", [])
    if len(convos) > MAX_CONVERSATIONS:
        data["conversations"] = convos[-MAX_CONVERSATIONS:]

    with open(STORE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_conversation(source: str, role: str, content: str):
    """
    写入一条对话记录。

    参数:
        source: "tg" 或 "terminal"
        role: "user" 或 "assistant"
        content: 消息内容
    """
    assert source in ("tg", "terminal"), f"source 必须是 tg 或 terminal，收到: {source}"
    assert role in ("user", "assistant"), f"role 必须是 user 或 assistant，收到: {role}"

    entry = {
        "source": source,
        "role": role,
        "content": content,
        "time": time.strftime("%m-%d %H:%M"),
    }

    try:
        with open(STORE_FILE, "r+") as f:
            locked = _lock(f)
            data = _load_raw()
            data.setdefault("conversations", []).append(entry)
            # 裁剪
            if len(data["conversations"]) > MAX_CONVERSATIONS:
                data["conversations"] = data["conversations"][-MAX_CONVERSATIONS:]
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=2)
            if locked:
                _unlock(f)
    except OSError:
        # 文件不存在等，降级写
        init_store()
        with open(STORE_FILE, "r+") as f:
            _lock(f)
            data = _load_raw()
            data.setdefault("conversations", []).append(entry)
            if len(data["conversations"]) > MAX_CONVERSATIONS:
                data["conversations"] = data["conversations"][-MAX_CONVERSATIONS:]
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=2)
            _unlock(f)


def read_conversations(limit: int = 20, source: str = None) -> list:
    """
    读取共享对话记录。

    参数:
        limit: 返回最近 N 条
        source: 筛选来源，"tg" 或 "terminal"，None 表示全部

    返回:
        list[dict]: 对话记录列表，按时间正序
    """
    init_store()
    data = _load_raw()
    convos = data.get("conversations", [])

    if source:
        convos = [c for c in convos if c.get("source") == source]

    return convos[-limit:]


def read_terminal_context(limit: int = 10) -> str:
    """
    读取 terminal 侧最近的对话，格式化为精简文本（供 TG bot 构建 prompt 用）。

    返回:
        精简格式的对话文本，如无则返回空字符串
    """
    convos = read_conversations(limit=limit, source="terminal")
    if not convos:
        return ""

    # 精简格式：一行一条，节省 token
    items = []
    for c in convos:
        prefix = "终端用户" if c["role"] == "user" else "终端助手"
        items.append(f"[{c['time']}] {prefix}: {c['content']}")
    return "【终端侧】\n" + "\n".join(items)


def get_stats() -> dict:
    """获取共享仓库统计信息"""
    data = _load_raw()
    convos = data.get("conversations", [])
    tg_count = sum(1 for c in convos if c.get("source") == "tg")
    terminal_count = sum(1 for c in convos if c.get("source") == "terminal")
    return {
        "total": len(convos),
        "tg": tg_count,
        "terminal": terminal_count,
        "file": STORE_FILE,
    }


# 初始化（模块加载时自动确保文件存在）
init_store()
