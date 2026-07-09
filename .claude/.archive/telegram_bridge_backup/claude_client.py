"""
Claude API 调用模块

职责：接收文本消息 → 调用 Claude 生成回复 → 返回文本
不涉及任何文件 I/O、消息队列、状态管理
"""

import requests, json, time

def ask(message: str, system: str = None, max_retries: int = 2) -> str:
    """
    向 Claude 发送消息并获取回复。

    参数:
        message: 用户消息文本
        system: 系统提示词（覆盖默认，传 None 使用 config 中的默认提示）
        max_retries: 失败重试次数

    返回:
        回复文本字符串
    """
    from config import API_BASE, API_KEY, MODEL, MAX_TOKENS, SYSTEM_PROMPT

    system_prompt = system if system is not None else SYSTEM_PROMPT

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{API_BASE}/messages",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": message}],
                },
                timeout=60,
            )
            if resp.status_code != 200:
                raise Exception(f"API {resp.status_code}: {resp.text[:200]}")

            data = resp.json()
            # Anthropic Messages API 格式
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]

            # 兼容其他格式
            if "content" in data and isinstance(data["content"], str):
                return data["content"]

            raise Exception(f"未知返回格式: {str(data)[:200]}")

        except Exception as e:
            if attempt < max_retries:
                time.sleep(2)
                continue
            return f"[Claude 调用失败: {str(e)[:100]}]"


def ask_stream(message: str, system: str = None):
    """
    流式版本（预留），用法同 ask() 但逐块 yield 文本。
    """
    from config import API_BASE, API_KEY, MODEL, MAX_TOKENS, SYSTEM_PROMPT

    system_prompt = system if system is not None else SYSTEM_PROMPT
    resp = requests.post(
        f"{API_BASE}/messages",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": system_prompt,
            "messages": [{"role": "user", "content": message}],
            "stream": True,
        },
        timeout=120,
        stream=True,
    )
    for line in resp.iter_lines():
        if line:
            yield line.decode()
