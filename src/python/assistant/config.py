"""智能助手配置 —— 极简 .env 加载（项目未装 python-dotenv，自己解析）

密钥只从本地 .env / 环境变量读取，绝不硬编码进代码。
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../src/python/assistant
_PY_DIR = os.path.dirname(_HERE)                             # .../src/python
_REPO_ROOT = os.path.dirname(os.path.dirname(_PY_DIR))       # 仓库根


def _load_env_file(path):
    """把 KEY=VALUE 形式的 .env 灌入 os.environ（已存在的环境变量优先，不覆盖）"""
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, val)
    except OSError:
        pass


# 优先 src/python/.env，其次仓库根 .env
_load_env_file(os.path.join(_PY_DIR, ".env"))
_load_env_file(os.path.join(_REPO_ROOT, ".env"))

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()
# 助手执行工具时回调本服务接口的基址（自调用）
INTERNAL_BASE = os.environ.get("ASSISTANT_INTERNAL_BASE", "http://127.0.0.1:8000").rstrip("/")


def has_key() -> bool:
    return bool(DEEPSEEK_API_KEY)
