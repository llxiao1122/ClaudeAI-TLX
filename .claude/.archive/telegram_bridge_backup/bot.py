"""
Telegram ↔ Claude 实时消息桥接（带记忆系统）
"""

import requests, time, datetime, sys, os, json, re

from config import TOKEN, CHAT_ID, PROXY
from claude_client import ask
import memory_manager as mem

PROXIES = {"http": PROXY, "https": PROXY}
BASE = os.path.dirname(__file__)
OFFSET_FILE = os.path.join(BASE, "offset.txt")
LOG_FILE = os.path.join(BASE, "logs", "bot.log")

# === 日志 ===
def log(msg: str):
    ts = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

# === Telegram API ===
def tg_get_updates(offset: int) -> list:
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"offset": offset, "timeout": 30},
            proxies=PROXIES,
            timeout=35,
        )
        return r.json().get("result", [])
    except Exception as e:
        log(f"getUpdates 错误: {e}")
        return []

def tg_send_message(chat_id: str, text: str):
    try:
        # 清理内存命令标记，用户看不到
        clean = re.sub(r'\n?\[MEMORY:(?:SAVE|DELETE).*?(?:\n|$)', '', text)
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": chat_id, "text": clean},
            proxies=PROXIES,
            timeout=15,
        )
    except Exception as e:
        log(f"sendMessage 错误: {e}")

def process_memory_commands(text: str, memory: dict):
    """解析并执行 [MEMORY:SAVE] 和 [MEMORY:DELETE] 命令"""
    changed = False
    for match in re.finditer(r'\[MEMORY:SAVE\]\s*(.+?)\s*=\s*(.+?)(?:\n|$)', text):
        key, value = match.group(1).strip(), match.group(2).strip()
        mem.set_fact(memory, key, value)
        log(f"记忆保存: {key} = {value}")
        changed = True
    for match in re.finditer(r'\[MEMORY:DELETE\]\s*(.+?)(?:\n|$)', text):
        key = match.group(1).strip()
        mem.delete_fact(memory, key)
        log(f"记忆删除: {key}")
        changed = True
    if changed:
        mem.save(memory)

# === 消息处理 ===
def handle_message(text: str, memory: dict):
    # 保存用户消息到历史
    mem.add_conversation(memory, "user", text)

    # 构建带记忆的提示
    memory_context = mem.to_context(memory)
    system_with_memory = SYSTEM_PROMPT
    if memory_context:
        system_with_memory += "\n\n" + memory_context

    log(f"← {text}")
    reply = ask(text, system=system_with_memory)

    # 处理记忆命令
    process_memory_commands(reply, memory)

    # 保存 Claude 回复到历史
    clean_reply = re.sub(r'\n?\[MEMORY:(?:SAVE|DELETE).*?(?:\n|$)', '', reply).strip()
    mem.add_conversation(memory, "assistant", clean_reply)

    return reply

# === 主循环 ===
def main():
    from config import SYSTEM_PROMPT as sp
    global SYSTEM_PROMPT
    SYSTEM_PROMPT = sp

    log("=== Telegram Bridge 启动（带记忆）===")

    # 加载记忆
    memory = mem.load()
    fact_count = len(memory.get("facts", {}))
    log(f"已加载记忆: {fact_count} 条事实, {len(memory.get('conversations', []))} 条对话")

    # 读取偏移量
    offset = 0
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            try:
                offset = int(f.read().strip())
            except:
                offset = 0
    log(f"监听 offset={offset}")

    while True:
        try:
            updates = tg_get_updates(offset)
            for up in updates:
                offset = up["update_id"] + 1
                if "message" in up:
                    msg = up["message"]
                    chat_id = str(msg["chat"]["id"])
                    text = msg.get("text", "")
                    if text:
                        reply = handle_message(text, memory)
                        tg_send_message(chat_id, reply)

            with open(OFFSET_FILE, "w") as f:
                f.write(str(offset))
        except KeyboardInterrupt:
            log("退出")
            break
        except Exception as e:
            log(f"错误: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
