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
import random
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
    wallet = db.get(WalletAccount, user.id) if user.role == STUDENT_ROLE else None
    return UserOut(
        id=user.id,
        role=user.role,
        login_name=user.login_name,
        name=user.name,
        avatar=user.avatar or "",
        school=user.school or "",
        student_id=user.student_id or "",
        phone=user.phone,
        position=user.position or "",
        preferences=_parse_json(user.preferences),
        taboo=_parse_json(user.taboo),
        monthly_budget=user.monthly_budget,
        reward_balance=wallet.balance if wallet else 0,
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

    # 管理员注册后需超管审核（status=0 表示待审核）
    if user.role == ADMIN_ROLE and user.status == 0:
        raise BusinessError(20003, "管理员账号审核中，请耐心等待", 200)

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
    if request.role == ADMIN_ROLE:
        return _register_admin(db, request)
    raise BusinessError(400, "role 仅支持 1（学生）/ 2（商家）/ 3（管理员）", 400)


def _register_admin(db: Session, request: RegisterRequest) -> RegisterOut:
    """管理员注册：学校 / 姓名 / 职务 / 管理账号 / 联系方式 / 密码，需超管审核。"""
    for field in ("school", "name", "position", "login_name", "phone", "password"):
        if not getattr(request, field):
            raise BusinessError(400, "管理员注册缺少字段：{}".format(field), 400)

    _check_duplicate(db, request.login_name, request.phone)

    user = User(
        role=ADMIN_ROLE,
        login_name=request.login_name,
        password=hash_password(request.password),
        school=request.school,
        name=request.name,
        position=request.position,
        phone=request.phone,
        status=0,  # 待超管审核，审核通过前不可登录
    )
    db.add(user)
    db.commit()
    return RegisterOut(id=user.id, audit_status=0)


def _check_duplicate(db: Session, login_name: str, phone: str) -> None:
    if db.scalars(select(User.id).where(User.login_name == login_name)).first():
        raise BusinessError(20005, "账号已存在", 200)
    if db.scalars(select(User.id).where(User.phone == phone)).first():
        raise BusinessError(20006, "手机号已注册", 200)


# ---------------------------------------------------------------- 学生注册随机字段
# 学生注册只需填姓名，学号/手机号/密码/学校由系统随机生成（演示与快速注册场景）。

_STUDENT_SCHOOLS = [
    "澳门科技大学", "澳门大学", "北京大学", "清华大学", "复旦大学",
    "上海交通大学", "中山大学", "浙江大学", "南京大学", "武汉大学",
    "四川大学", "华中科技大学", "西安交通大学", "哈尔滨工业大学", "厦门大学",
]


def _gen_password() -> str:
    """生成 8 位易记初始密码（小写字母+数字，避开易混淆字符）。"""
    alphabet = "abcdefghijkmnpqrstuvwxyz23456789"
    return "".join(random.choices(alphabet, k=8))


def _pick_school() -> str:
    return random.choice(_STUDENT_SCHOOLS)


def _gen_student_id(db: Session) -> str:
    """生成唯一学号：入学年份(2018-2025) + 6 位随机数字，碰撞则重试。"""
    for _ in range(30):
        sid = "{}{:06d}".format(random.randint(2018, 2025), random.randint(0, 999999))
        if not db.scalars(select(User.id).where(User.student_id == sid)).first():
            return sid
    raise BusinessError(500, "生成学号失败，请重试", 500)


def _gen_phone(db: Session) -> str:
    """生成唯一 11 位手机号（13/15/18/19 开头），碰撞则重试。"""
    prefixes = ("13", "15", "18", "19")
    for _ in range(30):
        phone = random.choice(prefixes) + "".join(random.choices("0123456789", k=9))
        if not db.scalars(select(User.id).where(User.phone == phone)).first():
            return phone
    raise BusinessError(500, "生成手机号失败，请重试", 500)


def _register_student(db: Session, request: RegisterRequest) -> RegisterOut:
    """学生注册：姓名必填；学号/手机号/密码/学校未提供时由系统随机生成且保证唯一。"""
    if not request.name:
        raise BusinessError(400, "学生注册请填写姓名", 400)

    student_id = request.student_id or _gen_student_id(db)
    phone = request.phone or _gen_phone(db)
    school = request.school or _pick_school()
    password = request.password or _gen_password()

    _check_duplicate(db, student_id, phone)

    user = User(
        role=STUDENT_ROLE,
        login_name=student_id,  # 学生学号即登录账号
        password=hash_password(password),
        school=school,
        student_id=student_id,
        name=request.name,
        phone=phone,
        status=1,
    )
    db.add(user)
    db.flush()
    _ensure_wallet(db, user.id)
    db.commit()
    return RegisterOut(id=user.id, student_id=student_id, phone=phone, password=password)


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
    elif request.role == ADMIN_ROLE:
        if not (request.login_name and request.name and request.phone):
            raise BusinessError(400, "请提供管理员账号、姓名、手机号", 400)
        user = db.scalars(
            select(User).where(
                User.role == ADMIN_ROLE,
                User.login_name == request.login_name,
                User.name == request.name,
                User.phone == request.phone,
            )
        ).first()
    else:
        raise BusinessError(400, "role 仅支持 1（学生）/ 2（商家）/ 3（管理员）", 400)

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
