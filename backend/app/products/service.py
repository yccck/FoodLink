"""商品模块业务逻辑（何睿涵负责）。

接口契约见仓库根目录 api.md。业务错误码：
- 41001 标题/描述触发敏感词
- 41002 定价异常
- 41003 有效期异常
- 40001 无权限操作他人商品
- 404   商品不存在

商品状态：0 已下架，1 在售，2 已售罄，3 风控拦截。
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.business_hours import validate_business_hours
from app.errors import BusinessError
from app.models import Behavior, Merchant, Product, RiskLog, User
from app.recommend import guess_you_like, recommend
from app.risk_control import BLOCK, WARN, decide_product_risk
from app.schemas import (
    MerchantBriefOut,
    ProductCreateRequest,
    ProductOut,
    ProductPageOut,
)

STATUS_OFFLINE = 0
STATUS_ONSALE = 1
STATUS_SOLDOUT = 2
STATUS_RISK_BLOCKED = 3

# 风控错误码映射（risk_type → code）
_RISK_CODE = {1: 41002, 2: 41001, 3: 41003}


# ---------------------------------------------------------------- 序列化


def _merchant_brief(db: Session, merchant_id: int) -> MerchantBriefOut:
    m = db.get(Merchant, merchant_id)
    if m is None:
        return MerchantBriefOut(id=merchant_id, shop_name="未知商家")
    return MerchantBriefOut(id=m.id, shop_name=m.shop_name, location=m.location or "")


def _to_product_out(
    p: Product,
    db: Optional[Session] = None,
    is_favorite: Optional[bool] = None,
    distance: Optional[float] = None,
    match_tags: Optional[List[str]] = None,
) -> ProductOut:
    return ProductOut(
        id=p.id,
        merchant_id=p.merchant_id,
        title=p.title,
        description=p.description,
        category=p.category,
        image=p.image or "",
        original_price=p.original_price,
        discount_price=p.discount_price,
        quantity=p.quantity,
        expire_time=p.expire_time.strftime("%Y-%m-%d %H:%M:%S"),
        business_open_time=p.business_open_time,
        business_close_time=p.business_close_time,
        location=p.location,
        lat=p.lat,
        lng=p.lng,
        status=p.status,
        risk_flag=p.risk_flag,
        view_count=p.view_count,
        fav_count=p.fav_count,
        order_count=p.order_count,
        created_at=p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        distance=round(distance, 2) if distance is not None else None,
        is_favorite=is_favorite,
        match_tags=match_tags,
        merchant=_merchant_brief(db, p.merchant_id) if db is not None else None,
    )


def _is_favorite(db: Session, user_id: int, product_id: int) -> bool:
    return db.scalars(
        select(Behavior.id).where(
            Behavior.user_id == user_id,
            Behavior.product_id == product_id,
            Behavior.behavior_type == 2,
        )
    ).first() is not None


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise BusinessError(401, "未登录或登录已过期", 401)
    return user


def get_merchant_or_403(db: Session, user_id: int) -> Merchant:
    """取当前登录商家，要求已实名审核通过。"""
    merchant = db.scalars(select(Merchant).where(Merchant.user_id == user_id)).first()
    if merchant is None:
        raise BusinessError(403, "当前账号不是商家", 403)
    if merchant.audit_status != 1:
        raise BusinessError(20003, "商家未通过审核，暂不能发布商品", 200)
    return merchant


# ---------------------------------------------------------------- 发布（含 AI 风控）


def create_product(db: Session, merchant: Merchant, body: ProductCreateRequest) -> ProductOut:
    expire_time = _parse_expire_time(body.expire_time)
    try:
        validate_business_hours(body.business_open_time, body.business_close_time)
    except ValueError as exc:
        raise BusinessError(400, str(exc), 400) from exc

    product = Product(
        merchant_id=merchant.id,
        title=body.title,
        description=body.description,
        category=body.category,
        image=body.image or "",
        original_price=body.original_price,
        discount_price=body.discount_price,
        quantity=body.quantity,
        expire_time=expire_time,
        business_open_time=body.business_open_time,
        business_close_time=body.business_close_time,
        location=body.location,
        lat=body.lat,
        lng=body.lng,
        status=STATUS_ONSALE,
        risk_flag=0,
    )
    db.add(product)
    db.flush()  # 取得 product.id 供风控日志使用

    # ---- AI 风控（规则引擎 + 大模型语义审核，发布即触发）----
    action, results = decide_product_risk(
        original=body.original_price,
        discount=body.discount_price,
        title=body.title,
        description=body.description,
        expire_time=expire_time,
        quantity=body.quantity,
        category=body.category,
    )
    if results:
        product.risk_flag = 1
        for r in results:
            db.add(
                RiskLog(
                    product_id=product.id,
                    merchant_id=merchant.id,
                    risk_type=r["risk_type"],
                    risk_detail=r["risk_detail"],
                    risk_source=r.get("risk_source", "rule"),
                    is_resolved=0,
                )
            )

    if action == BLOCK:
        product.status = STATUS_RISK_BLOCKED
        db.commit()  # 保留商品记录与风控日志，便于超管后台追溯
        first = results[0]
        message = "发布被风控拦截，已进入人工复核队列：{}".format(first["risk_detail"])
        tips = [str(s) for s in (first.get("suggestions") or []) if str(s).strip()]
        if tips:
            message += "｜整改建议：{}".format("；".join(tips[:2]))
        raise BusinessError(
            _RISK_CODE.get(first["risk_type"], 40001),
            message,
            200,
        )

    db.commit()
    db.refresh(product)
    return _to_product_out(product, db)


def _parse_expire_time(raw: str):
    from datetime import datetime

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise BusinessError(400, "expire_time 格式应为 yyyy-MM-dd HH:mm:ss", 400)


# ---------------------------------------------------------------- 列表


def list_products(
    db: Session,
    page: int,
    size: int,
    category: Optional[str],
    keyword: Optional[str],
    sort: str,
) -> ProductPageOut:
    conds = [Product.status == STATUS_ONSALE, Product.risk_flag == 0]
    if category:
        conds.append(Product.category == category)
    if keyword:
        like = "%{}%".format(keyword)
        conds.append(or_(Product.title.like(like), Product.description.like(like)))

    total = db.scalar(select(func.count(Product.id)).where(*conds)) or 0

    order_col = {
        "price_asc": Product.discount_price.asc(),
        "price_desc": Product.discount_price.desc(),
        "expire": Product.expire_time.asc(),
        "newest": Product.created_at.desc(),
    }.get(sort, Product.created_at.desc())

    rows = db.scalars(
        select(Product).where(*conds).order_by(order_col).offset((page - 1) * size).limit(size)
    ).all()

    return ProductPageOut(
        total=total,
        page=page,
        size=size,
        items=[_to_product_out(p, db) for p in rows],
    )


# ---------------------------------------------------------------- 详情（自动记录浏览）


def get_product_detail(db: Session, product_id: int, user: Optional[User]) -> ProductOut:
    p = db.get(Product, product_id)
    if p is None:
        raise BusinessError(404, "商品不存在", 404)

    p.view_count += 1
    if user is not None and user.role == 1:
        # 浏览行为去重（同一用户同一商品只记一次）
        exists = db.scalars(
            select(Behavior.id).where(
                Behavior.user_id == user.id,
                Behavior.product_id == product_id,
                Behavior.behavior_type == 1,
            )
        ).first()
        if not exists:
            db.add(Behavior(user_id=user.id, product_id=product_id, behavior_type=1))
    db.commit()
    db.refresh(p)

    fav = _is_favorite(db, user.id, product_id) if user is not None else None
    return _to_product_out(p, db, is_favorite=fav)


# ---------------------------------------------------------------- 收藏


def toggle_favorite(db: Session, user_id: int, product_id: int, favorite: bool):
    p = db.get(Product, product_id)
    if p is None:
        raise BusinessError(404, "商品不存在", 404)

    existing = db.scalars(
        select(Behavior).where(
            Behavior.user_id == user_id,
            Behavior.product_id == product_id,
            Behavior.behavior_type == 2,
        )
    ).first()

    if favorite and existing is None:
        db.add(Behavior(user_id=user_id, product_id=product_id, behavior_type=2))
        p.fav_count += 1
    elif not favorite and existing is not None:
        db.delete(existing)
        p.fav_count = max(0, p.fav_count - 1)

    db.commit()
    db.refresh(p)
    return {"favorite": favorite, "fav_count": p.fav_count}


# ---------------------------------------------------------------- 下架


def offline_product(db: Session, merchant: Merchant, product_id: int) -> ProductOut:
    p = db.get(Product, product_id)
    if p is None:
        raise BusinessError(404, "商品不存在", 404)
    if p.merchant_id != merchant.id:
        raise BusinessError(40001, "无权限操作他人商品", 200)
    if p.risk_flag:
        raise BusinessError(
            41004,
            "风控拦截商品需由超管人工复核（确认拦截/误判恢复）后才能操作",
            400,
        )
    if p.status == STATUS_OFFLINE:
        p.status = STATUS_ONSALE
    else:
        p.status = STATUS_OFFLINE
    db.commit()
    db.refresh(p)
    return _to_product_out(p, db)


# ---------------------------------------------------------------- AI 推荐 / 猜你喜欢


def get_recommendations(
    db: Session, user_id: int, lat: Optional[float], lng: Optional[float]
) -> List[ProductOut]:
    user = _get_user(db, user_id)
    scored = recommend(user, db, lat=lat, lng=lng)
    return [
        _to_product_out(
            item["product"],
            db,
            is_favorite=_is_favorite(db, user_id, item["product"].id),
            distance=item["distance"],
            match_tags=item["match_tags"],
        )
        for item in scored
    ]


def get_guess_you_like(db: Session, user_id: int) -> List[ProductOut]:
    user = _get_user(db, user_id)
    pairs = guess_you_like(user, db)
    return [
        _to_product_out(p, db, is_favorite=_is_favorite(db, user_id, p.id))
        for p, _w in pairs
        if p is not None
    ]


# ---------------------------------------------------------------- 我的收藏（个人中心用）


def list_my_favorites(db: Session, user_id: int) -> List[ProductOut]:
    rows = db.scalars(
        select(Product)
        .join(
            Behavior,
            (Behavior.product_id == Product.id)
            & (Behavior.user_id == user_id)
            & (Behavior.behavior_type == 2),
        )
        .order_by(Behavior.created_at.desc())
    ).all()
    return [_to_product_out(p, db, is_favorite=True) for p in rows]
