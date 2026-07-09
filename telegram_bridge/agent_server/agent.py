"""
Agent 核心

职责：接收文本消息 → 构建 prompt → 调用 claude --print → 返回结果
Claude Code 本地环境拥有完整的文件访问、Shell 执行和知识库调用能力。
"""

import subprocess, os, datetime, re, time

from .config import (
    CLAUDE_CMD, PROJECT_ROOT, PRINT_PREFIX, CLAUDE_TIMEOUT,
    PERMISSION_MODE, DEEPSEEK_BASE_URL, DEEPSEEK_AUTH_TOKEN,
    DEEPSEEK_MODEL, MAX_PROMPT_CHARS,
)


def _truncate_context(context: str, max_chars: int) -> str:
    """
    截断过长的上下文，保护 token 消耗不失控。

    策略：
      1. 总长度不超 max_chars 则直接返回
      2. 超出时，保留【当前问题】之后的内容不动，从前面开始裁
      3. 优先保留【事实】和【摘要】，裁剪【历史】中较早的条目
    """
    if len(context) <= max_chars:
        return context

    # 找到"当前问题"标记位置（兼容新旧格式）
    marker_patterns = ["【当前问题】", "【问题】"]
    marker_pos = -1
    for pat in marker_patterns:
        marker_pos = context.rfind(pat)
        if marker_pos != -1:
            break

    if marker_pos == -1:
        # 没有找到标记，直接截尾部
        return "...(上下文过长已截断)\n" + context[-(max_chars - 50):]

    tail = context[marker_pos:]  # 当前问题及之后的内容不动
    head_budget = max_chars - len(tail) - 50  # 留给前面的空间

    if head_budget <= 0:
        return "...(上下文过长已截断)\n" + tail

    return context[:head_budget] + "\n...(上下文过长已截断)\n" + tail


def ask(user_message: str, context: str = "") -> str:
    """
    调用本地 Claude Code CLI 处理消息。

    Claude 在本地运行，可以：
    - 读取 Enterprise_Brain/、Knowledge/、.claude/ 等目录
    - 执行 Shell 命令
    - 修改文件
    - 使用完整的项目管理上下文

    参数:
        user_message: 用户消息
        context: 上下文 prompt（包含历史对话+记忆）

    返回:
        Claude 的回复文本
    """
    # 构建完整 prompt
    if context:
        full_prompt = f"{context}\n\n{PRINT_PREFIX}\n{user_message}"
    else:
        full_prompt = f"{PRINT_PREFIX}\n{user_message}"

    # token 硬上限保护：截断过长上下文
    full_prompt = _truncate_context(full_prompt, MAX_PROMPT_CHARS)

    try:
        result = subprocess.run(
            [CLAUDE_CMD, "--print", "--permission-mode", PERMISSION_MODE, full_prompt],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=PROJECT_ROOT,
            env={**os.environ,
                "ANTHROPIC_BASE_URL": DEEPSEEK_BASE_URL,
                "ANTHROPIC_AUTH_TOKEN": DEEPSEEK_AUTH_TOKEN,
                "ANTHROPIC_MODEL": DEEPSEEK_MODEL,
            },
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip()[:200]
            return f"[Claude 调用失败: {error_msg}]"

        output = result.stdout.strip()
        if not output:
            return "[Claude 无输出]"

        return output

    except subprocess.TimeoutExpired:
        return "[Claude 超时]"
    except FileNotFoundError:
        return f"[未找到 claude 命令: {CLAUDE_CMD}]"
    except Exception as e:
        return f"[Agent 错误: {str(e)[:100]}]"


# 可重试的错误类型前缀
_RETRYABLE_PREFIXES = (
    "[Claude 调用失败",
    "[Claude 超时",
    "[Claude 无输出]",
    "[未找到 claude 命令]",
)


def ask_with_retry(user_message: str, context: str = "", max_retries: int = 2) -> str:
    """带指数退避的重试调用"""
    last_result = ""
    for attempt in range(max_retries + 1):
        result = ask(user_message, context)

        # 成功：不以可重试错误开头
        if not any(result.startswith(p) for p in _RETRYABLE_PREFIXES):
            return result

        last_result = result

        # 最后一次不 sleep
        if attempt < max_retries:
            delay = 2 ** attempt  # 0s, 1s, 2s, 4s...
            time.sleep(delay)

    return last_result
