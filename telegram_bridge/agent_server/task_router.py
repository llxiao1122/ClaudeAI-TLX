"""
任务路由

职责：判断消息类型，决定处理方式。
- direct: 简单问候/确认，零 token 消耗直接回复
- claude:  走 Claude Code 完整处理（默认）

Token 优化：尽量扩大 direct 覆盖范围，减少不必要的 LLM 调用。
"""

import re

# 工作任务关键词（出现这些词的短消息也走 Claude）
_TASK_KEYWORDS = [
    "安排", "整理", "汇总", "汇报", "检查", "跟进", "处理", "回复",
    "通知", "提醒", "创建", "修改", "删除", "查询", "搜索", "分析",
    "盘点", "验收", "整改", "评估",
]


def route(message: str) -> str:
    """
    分析消息，返回处理方式。

    返回:
        "claude"  - 走 Claude Code 完整处理（默认）
        "direct"  - 简单回复，不调用 LLM
    """
    msg = message.strip()
    msg_lower = msg.lower()

    # 纯问候/简单确认 → 直接回复
    if re.match(
        r"^(你好|hi|hello|hey|嗨|在吗|在不在|好了吗|嗯|好的|收到|ok|okk|"
        r"好|行|可以|没问题|谢谢|知道了|明白|早|晚安|1|👍|\?|？)$",
        msg_lower
    ):
        return "direct"

    # 所有其他消息走 Claude（短消息也不拦截，避免误伤"你是"、"执行了"等简短但需要理解的问题）
    return "claude"


def is_task_request(message: str) -> bool:
    """判断是否包含工作任务请求"""
    return any(k in message for k in _TASK_KEYWORDS)
