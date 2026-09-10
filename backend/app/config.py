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


settings = Settings()
