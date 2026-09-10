from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.errors import BusinessError
from app.models import User

STUDENT_ROLE = 1
MERCHANT_ROLE = 2
ADMIN_ROLE = 3
VALID_ROLES = {STUDENT_ROLE, MERCHANT_ROLE, ADMIN_ROLE}

bearer_scheme = HTTPBearer(auto_error=False, description="登录接口返回的 JWT Token")


@dataclass(frozen=True)
class CurrentUser:
    id: int
    role: int


def create_access_token(
    user_id: int, role: int, expires_minutes: int = 120
) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise BusinessError(401, "未登录或登录已过期", 401)

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"], "verify_sub": False},
        )
        raw_user_id = payload.get("sub", payload.get("user_id"))
        user_id = int(raw_user_id)
        role = int(payload.get("role"))
    except (jwt.PyJWTError, TypeError, ValueError):
        raise BusinessError(401, "未登录或登录已过期", 401)

    if user_id <= 0 or role not in VALID_ROLES:
        raise BusinessError(401, "未登录或登录已过期", 401)

    user = db.get(User, user_id)
    if user is None or user.status != 1 or user.role != role:
        raise BusinessError(401, "未登录或登录已过期", 401)
    return CurrentUser(id=user.id, role=user.role)
