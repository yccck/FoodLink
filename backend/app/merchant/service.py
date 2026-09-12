"""商家端个人中心：店铺资料查看与提交修改（何睿涵负责）。

约定（与前端 mock/vite-mock.js 保持一致）：
- 商家在个人中心修改资料后**不直接生效**，而是写入 pending_profile 等待超管审核；
- GET 返回正式资料 + pending（若有），前端优先展示 pending 并提示"等待超管审核"。
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import BusinessError
from app.models import Merchant, User
from app.schemas import MerchantPendingInfo, MerchantProfileOut

PHONE_PATTERN = re.compile(r"^1\d{10}$")
MAX_CATEGORIES = 12


def _load_categories(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _load_pending(raw: Optional[str]) -> Optional[MerchantPendingInfo]:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    return MerchantPendingInfo(**{
        "shop_name": value.get("shop_name", ""),
        "name": value.get("name", ""),
        "phone": value.get("phone", ""),
        "location": value.get("location", ""),
        "license_img": value.get("license_img", "") or "",
        "categories": [str(item) for item in (value.get("categories") or [])][:MAX_CATEGORIES],
    })


def _merchant_of_user(db: Session, user_id: int) -> Merchant:
    merchant = (
        db.execute(select(Merchant).where(Merchant.user_id == user_id))
        .scalars()
        .first()
    )
    if merchant is None:
        raise BusinessError(404, "商家信息不存在", 404)
    return merchant


def _to_out(db: Session, merchant: Merchant, user: User) -> MerchantProfileOut:
    return MerchantProfileOut(
        shop_name=merchant.shop_name,
        location=merchant.location,
        lat=merchant.lat,
        lng=merchant.lng,
        license_img=merchant.license_img or "",
        name=user.name or "",
        phone=user.phone or "",
        audit_status=merchant.audit_status,
        categories=_load_categories(merchant.categories),
        pending=_load_pending(merchant.pending_profile),
    )


def get_profile(db: Session, user_id: int) -> MerchantProfileOut:
    """商家查看自己的店铺资料。"""

    merchant = _merchant_of_user(db, user_id)
    user = db.get(User, user_id)
    if user is None:
        raise BusinessError(404, "账号不存在", 404)
    return _to_out(db, merchant, user)


def update_profile(db: Session, user_id: int, request) -> MerchantProfileOut:
    """商家提交资料修改：写入待审核区，等超管审核后生效。"""

    merchant = _merchant_of_user(db, user_id)
    user = db.get(User, user_id)
    if user is None:
        raise BusinessError(404, "账号不存在", 404)

    shop_name = (request.shop_name or "").strip()
    name = (request.name or "").strip()
    phone = (request.phone or "").strip()
    location = (request.location or "").strip()
    if not (shop_name and name and phone and location):
        raise BusinessError(40002, "请填写完整店铺资料", 400)
    if not PHONE_PATTERN.match(phone):
        raise BusinessError(40003, "请输入正确的手机号", 400)

    categories = []
    if isinstance(request.categories, list):
        categories = [str(item).strip() for item in request.categories if str(item).strip()]
    categories = categories[:MAX_CATEGORIES]

    payload = {
        "shop_name": shop_name,
        "name": name,
        "phone": phone,
        "location": location,
        "license_img": (request.license_img or "").strip() or (merchant.license_img or ""),
        "categories": categories,
    }
    merchant.pending_profile = json.dumps(payload, ensure_ascii=False)
    db.commit()
    db.refresh(merchant)
    return _to_out(db, merchant, user)
