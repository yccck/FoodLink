"""认证模块业务逻辑（何睿涵负责）。

接口契约见仓库根目录 api.md。业务错误码：
- 20001 账号或密码错误
- 20002 账号被禁用
- 20003 商家未通过审核（待审核/已驳回）
- 20004 身份验证失败（重置密码）
- 20005 账号已存在
- 20006 手机号已存在

密码哈希使用标准库 scrypt（app.security_password），不新增第三方依赖。
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import CurrentUser, create_access_token
from app.errors import BusinessError
from app.models import Behavior, Merchant, Product, User, WalletAccount
from app.schemas import (
    LoginOut,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterOut,
    RegisterRequest,
    ResetPasswordRequest,
    UserOut,
)
from app.security_password import hash_password, verify_password

DEFAULT_PASSWORD = "123456"

STUDENT_ROLE = 1
MERCHANT_ROLE = 2
ADMIN_ROLE = 3


# ---------------------------------------------------------------- 工具


def _parse_json(text: Optional[str]) -> dict:
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def _get_merchant(db: Session, user_id: int) -> Optional[Merchant]:
    return db.scalars(select(Merchant).where(Merchant.user_id == user_id)).first()


def _to_user_out(db: Session, user: User) -> UserOut:
    merchant = _get_merchant(db, user.id) if user.role == MERCHANT_ROLE else None
    return UserOut(
        id=user.id,
        role=user.role,
        login_name=user.login_name,
        name=user.name,
        avatar=user.avatar or "",
        school=user.school or "",
        student_id=user.student_id or "",
        phone=user.phone,
        preferences=_parse_json(user.preferences),
        taboo=_parse_json(user.taboo),
        monthly_budget=user.monthly_budget,
        status=user.status,
        shop_name=merchant.shop_name if merchant else "",
        license_img=(merchant.license_img or "") if merchant else "",
        audit_status=merchant.audit_status if merchant else -1,
    )


def _ensure_wallet(db: Session, user_id: int) -> None:
    """注册时为用户开立钱包账户（余额 0），供订单模块使用。"""
    if db.get(WalletAccount, user_id) is None:
        db.add(WalletAccount(user_id=user_id))


# ---------------------------------------------------------------- 登录


def login(db: Session, request: LoginRequest) -> LoginOut:
    user = db.scalars(
        select(User).where(User.login_name == request.login_name)
    ).first()

    # 账号不存在 / 角色不匹配 / 密码错误，统一报 20001（不泄露账号是否存在）
    if user is None or user.role != request.role:
        raise BusinessError(20001, "账号或密码错误", 200)
    if not verify_password(request.password, user.password):
        raise BusinessError(20001, "账号或密码错误", 200)

    if user.status != 1:
        raise BusinessError(20002, "账号已被禁用，请联系管理员", 200)

    # 商家未通过审核不可登录
    if user.role == MERCHANT_ROLE:
        merchant = _get_merchant(db, user.id)
        if merchant is None or merchant.audit_status == 0:
            raise BusinessError(20003, "商家账号审核中，请耐心等待", 200)
        if merchant.audit_status == 2:
            raise BusinessError(20003, "商家审核未通过，请联系管理员", 200)

    token = create_access_token(user_id=user.id, role=user.role)
    return LoginOut(token=token, user=_to_user_out(db, user))


# ---------------------------------------------------------------- 注册


def register(db: Session, request: RegisterRequest) -> RegisterOut:
    if request.role == STUDENT_ROLE:
        return _register_student(db, request)
    if request.role == MERCHANT_ROLE:
        return _register_merchant(db, request)
    raise BusinessError(400, "role 仅支持 1（学生）/ 2（商家）", 400)


def _check_duplicate(db: Session, login_name: str, phone: str) -> None:
    if db.scalars(select(User.id).where(User.login_name == login_name)).first():
        raise BusinessError(20005, "账号已存在", 200)
    if db.scalars(select(User.id).where(User.phone == phone)).first():
        raise BusinessError(20006, "手机号已注册", 200)


def _register_student(db: Session, request: RegisterRequest) -> RegisterOut:
    for field in ("school", "student_id", "name", "phone", "password"):
        if not getattr(request, field):
            raise BusinessError(400, "学生注册缺少字段：{}".format(field), 400)

    _check_duplicate(db, request.student_id, request.phone)
    if db.scalars(select(User.id).where(User.student_id == request.student_id)).first():
        raise BusinessError(20005, "该学号已注册", 200)

    user = User(
        role=STUDENT_ROLE,
        login_name=request.student_id,  # 学生学号即登录账号
        password=hash_password(request.password),
        school=request.school,
        student_id=request.student_id,
        name=request.name,
        phone=request.phone,
        status=1,
    )
    db.add(user)
    db.flush()
    _ensure_wallet(db, user.id)
    db.commit()
    return RegisterOut(id=user.id)


def _register_merchant(db: Session, request: RegisterRequest) -> RegisterOut:
    for field in ("shop_name", "location", "lat", "lng", "login_name", "password", "phone", "name"):
        if getattr(request, field) is None:
            raise BusinessError(400, "商家注册缺少字段：{}".format(field), 400)

    _check_duplicate(db, request.login_name, request.phone)

    user = User(
        role=MERCHANT_ROLE,
        login_name=request.login_name,
        password=hash_password(request.password),
        name=request.name,
        phone=request.phone,
        status=1,
    )
    db.add(user)
    db.flush()
    db.add(
        Merchant(
            user_id=user.id,
            shop_name=request.shop_name,
            license_img=request.license_img or "",
            location=request.location,
            lat=request.lat,
            lng=request.lng,
            audit_status=0,  # 待审核
        )
    )
    _ensure_wallet(db, user.id)
    db.commit()
    return RegisterOut(id=user.id, audit_status=0)


# ---------------------------------------------------------------- 重置密码


def reset_password(db: Session, request: ResetPasswordRequest) -> None:
    if request.role == STUDENT_ROLE:
        if not (request.student_id and request.name and request.phone):
            raise BusinessError(400, "请提供学号、姓名、手机号", 400)
        user = db.scalars(
            select(User).where(
                User.role == STUDENT_ROLE,
                User.student_id == request.student_id,
                User.name == request.name,
                User.phone == request.phone,
            )
        ).first()
    elif request.role == MERCHANT_ROLE:
        if not (request.login_name and request.shop_name and request.phone):
            raise BusinessError(400, "请提供商家账号、店铺名、手机号", 400)
        user = db.scalars(
            select(User).where(
                User.role == MERCHANT_ROLE,
                User.login_name == request.login_name,
                User.phone == request.phone,
            )
        ).first()
        if user is not None:
            merchant = _get_merchant(db, user.id)
            if merchant is None or merchant.shop_name != request.shop_name:
                user = None
    else:
        raise BusinessError(400, "role 仅支持 1（学生）/ 2（商家）", 400)

    if user is None:
        raise BusinessError(20004, "身份验证失败，请核对信息", 200)

    user.password = hash_password(DEFAULT_PASSWORD)
    db.commit()


# ---------------------------------------------------------------- 个人资料


def get_profile(db: Session, current_user: CurrentUser) -> UserOut:
    user = db.get(User, current_user.id)
    if user is None:
        raise BusinessError(401, "未登录或登录已过期", 401)
    return _to_user_out(db, user)


def update_profile(
    db: Session, current_user: CurrentUser, request: ProfileUpdateRequest
) -> UserOut:
    user = db.get(User, current_user.id)
    if user is None:
        raise BusinessError(401, "未登录或登录已过期", 401)

    data = request.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        user.name = data["name"]
    if "phone" in data and data["phone"]:
        # 换绑手机号需唯一
        exists = db.scalars(
            select(User.id).where(User.phone == data["phone"], User.id != user.id)
        ).first()
        if exists:
            raise BusinessError(20006, "手机号已注册", 200)
        user.phone = data["phone"]
    if "avatar" in data and data["avatar"] is not None:
        user.avatar = data["avatar"]
    if "preferences" in data and data["preferences"] is not None:
        user.preferences = json.dumps(data["preferences"], ensure_ascii=False)
    if "taboo" in data and data["taboo"] is not None:
        user.taboo = json.dumps(data["taboo"], ensure_ascii=False)
    if "monthly_budget" in data and data["monthly_budget"] is not None:
        user.monthly_budget = data["monthly_budget"]

    db.commit()
    db.refresh(user)
    return _to_user_out(db, user)


# ---------------------------------------------------------------- 行为记录


def record_behavior(
    db: Session, current_user: CurrentUser, product_id: int, behavior_type: int
) -> None:
    if behavior_type not in (1, 2, 3, 4):
        raise BusinessError(400, "behavior_type 仅支持 1-4", 400)
    if db.get(Product, product_id) is None:
        raise BusinessError(404, "商品不存在", 404)
    db.add(
        Behavior(user_id=current_user.id, product_id=product_id, behavior_type=behavior_type)
    )
    db.commit()
