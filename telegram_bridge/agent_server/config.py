# Agent Server 配置（从环境变量/.env读取）
import os

def _load_dotenv():
    """从 .env 文件加载环境变量（不覆盖已有的环境变量）"""
    env_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )
    if not os.path.exists(env_file):
        return
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key not in os.environ:
                os.environ[key] = value

_load_dotenv()

# Claude CLI 命令路径
CLAUDE_CMD = "/opt/homebrew/bin/claude"

# 项目根目录
PROJECT_ROOT = "/Users/lee/Documents/ClaudeAI-TLX"

# 记忆文件
MEMORY_FILE = "/Users/lee/Documents/ClaudeAI-TLX/telegram_bridge/memory.json"

# Claude --print 超时（秒）
CLAUDE_TIMEOUT = 120

# 权限模式：bypassPermissions（推荐远程TG使用）或 default（需手动确认）
PERMISSION_MODE = os.environ.get("PERMISSION_MODE", "bypassPermissions")

# 系统指令（每次调用附带）
PRINT_PREFIX = "请直接回答，不要反问，不要推测我没有提供的信息。基于已知事实回答："

# DeepSeek API 配置
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic")
DEEPSEEK_AUTH_TOKEN = os.environ.get("DEEPSEEK_AUTH_TOKEN", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")

# Prompt 硬上限（字符数），防止 token 消耗失控
MAX_PROMPT_CHARS = 3000
