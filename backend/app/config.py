from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")

load_dotenv(BACKEND_DIR / ".env")


def _default_database_url() -> str:
    return "sqlite:///{}".format(DATA_DIR / "foodlink.db")


def _cors_origins() -> Tuple[str, ...]:
    raw = os.getenv(
        "FOODLINK_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("FOODLINK_DATABASE_URL", _default_database_url())
    jwt_secret: str = os.getenv(
        "FOODLINK_JWT_SECRET", "foodlink-local-development-secret"
    )
    jwt_algorithm: str = os.getenv("FOODLINK_JWT_ALGORITHM", "HS256")
    cors_origins: Tuple[str, ...] = _cors_origins()
    # AI 推荐算法参数（可用环境变量覆盖）
    nearby_km: float = float(os.getenv("FOODLINK_NEARBY_KM", "3.0"))
    budget_ratio: float = float(os.getenv("FOODLINK_BUDGET_RATIO", "0.05"))
    expiry_window_hours: float = float(os.getenv("FOODLINK_EXPIRY_WINDOW_HOURS", "24"))
    recommend_top: int = int(os.getenv("FOODLINK_RECOMMEND_TOP", "20"))
    similar_user_top: int = int(os.getenv("FOODLINK_SIMILAR_USER_TOP", "10"))
    guess_top: int = int(os.getenv("FOODLINK_GUESS_TOP", "10"))
    # AI 风控（OpenAI 兼容接口，如 DeepSeek / 火山方舟）
    # 未配置 ai_api_key 或调用失败时，自动回退到 app/risk_control.py 的本地规则引擎
    ai_api_key: str = os.getenv("FOODLINK_AI_API_KEY", "")
    ai_base_url: str = os.getenv("FOODLINK_AI_BASE_URL", "https://api.deepseek.com")
    ai_model: str = os.getenv("FOODLINK_AI_MODEL", "deepseek-chat")
    ai_timeout: float = float(os.getenv("FOODLINK_AI_TIMEOUT", "20"))


settings = Settings()
