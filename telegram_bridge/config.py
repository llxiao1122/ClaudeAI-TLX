# Telegram Bridge 配置（从环境变量/.env读取）
import os

def _load_dotenv():
    """从 .env 文件加载环境变量（不覆盖已有的环境变量）"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
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

TOKEN = os.environ.get("TG_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
PROXY = os.environ.get("PROXY", "http://127.0.0.1:7897")
