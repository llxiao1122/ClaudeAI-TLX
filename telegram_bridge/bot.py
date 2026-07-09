"""
Telegram → Mac mini Claude Agent 远程入口

职责：
  - 接收 Telegram 消息
  - 转发给本地 Agent Server（Claude Code CLI）
  - 返回结果到 Telegram
  - 双向同步：每次对话自动写入 shared_conversations.json

禁止：
  - 直接调用 Claude API
  - 处理 AI 逻辑
  - 判断任务内容
"""

import requests, time, datetime, os, sys, signal, atexit

from config import TOKEN, CHAT_ID, PROXY
from agent_server.agent import ask_with_retry
from agent_server.context_manager import load_memory, save_memory, add_message, build_prompt
from agent_server.task_router import route

# 共享仓库（TG ↔ Terminal 双向同步）
SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared")
sys.path.insert(0, SHARED_DIR)
try:
    from shared_store import write_conversation
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

PROXIES = {"http": PROXY, "https": PROXY}
BASE = os.path.dirname(os.path.abspath(__file__))
OFFSET_FILE = os.path.join(BASE, "offset.txt")
LOG_FILE = os.path.join(BASE, "logs", "bot.log")
PID_FILE = os.path.join(BASE, "bot.pid")


# ── PID 文件锁：防止多实例 ──────────────────────────────────

def _acquire_lock() -> bool:
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            try:
                old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                return False
            except (OSError, ValueError):
                os.remove(PID_FILE)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True


def _release_lock():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except:
        pass


atexit.register(_release_lock)
# ───────────────────────────────────────────────────────────


def log(msg: str):
    ts = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


def _save_offset(offset: int):
    try:
        with open(OFFSET_FILE, "w") as f:
            f.write(str(offset))
    except Exception as e:
        log(f"保存offset失败: {e}")


def tg_get_updates(offset: int) -> list:
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"offset": offset, "timeout": 30},
            proxies=PROXIES, timeout=35,
        )
        return r.json().get("result", [])
    except Exception as e:
        log(f"getUpdates错误: {e}")
        return []


def tg_send(chat_id: str, text: str) -> bool:
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": chat_id, "text": text},
            proxies=PROXIES, timeout=15,
        )
        data = r.json()
        if not data.get("ok"):
            desc = data.get("description", "unknown error")
            log(f"sendMessage失败: {desc}")
            return False
        return True
    except Exception as e:
        log(f"sendMessage错误: {e}")
        return False


def handle_message(text: str):
    memory = load_memory()
    add_message(memory, "user", text)

    route_type = route(text)

    if route_type == "direct":
        replies = {
            "你好": "你好！有什么需要帮忙的？",
            "hi": "hi，我在", "hello": "Hello，我在",
            "hey": "Hey，在的", "嗨": "嗨，我在",
            "在吗": "在的，你说", "在不在": "在的",
            "好了吗": "好了，你说",
            "嗯": "嗯？你说", "好的": "好的",
            "ok": "OK", "okk": "OK",
            "好": "好", "行": "行", "可以": "可以",
            "没问题": "没问题", "知道了": "好的",
            "明白": "明白", "收到": "收到",
            "谢谢": "不客气", "早": "早！", "晚安": "晚安！",
            "1": "👌", "👍": "👍",
        }
        reply = replies.get(text.strip().lower(), "在的，有什么事？")
        add_message(memory, "assistant", reply)
        save_memory(memory)
        if _HAS_SHARED:
            write_conversation("tg", "user", text)
            write_conversation("tg", "assistant", reply)
        return reply

    context = build_prompt(text, memory)
    log(f"→ Agent: {text[:50]}...")
    reply = ask_with_retry(text, context)
    add_message(memory, "assistant", reply)
    save_memory(memory)
    log(f"← Agent回复 ({len(reply)}字)")

    if _HAS_SHARED:
        write_conversation("tg", "user", text)
        write_conversation("tg", "assistant", reply)
    return reply


def main():
    if not _acquire_lock():
        print("❌ Telegram Bridge 已在运行中。如需重启请先停止旧实例。", flush=True)
        sys.exit(1)

    log("=== Telegram→Claude Agent Bridge 启动 ===")

    offset = 0
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            try:
                offset = int(f.read().strip())
            except:
                offset = 0

    log(f"监听 offset={offset}")
    error_count = 0

    while True:
        try:
            updates = tg_get_updates(offset)
            error_count = 0

            for up in updates:
                offset = up["update_id"] + 1
                if "message" in up:
                    msg = up["message"]
                    text = msg.get("text", "")
                    if text:
                        reply = handle_message(text)
                        tg_send(str(msg["chat"]["id"]), reply)
                _save_offset(offset)

        except KeyboardInterrupt:
            log("退出")
            break
        except Exception as e:
            error_count += 1
            delay = min(2 ** error_count, 60)
            log(f"循环错误(#{error_count}): {e}，{delay}s后重试")
            time.sleep(delay)


if __name__ == "__main__":
    main()
