from __future__ import annotations

import secrets
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import case, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import ADMIN_ROLE, MERCHANT_ROLE, STUDENT_ROLE, CurrentUser
from app.errors import BusinessError
from app.models import Behavior, Merchant, Order, Product, User
from app.schemas import CreateOrderRequest, OrderOut
from app.timeutils import format_datetime, now_shanghai_naive

ORDER_PENDING = 0
ORDER_PICKED_UP = 1
ORDER_EXPIRED = 2
PRODUCT_OFFLINE = 0
PRODUCT_ON_SALE = 1
PRODUCT_SOLD_OUT = 2
MERCHANT_APPROVED = 1
ORDER_BEHAVIOR = 3
MAX_PICKUP_CODE_ATTEMPTS = 20
MAX_CREATE_ATTEMPTS = 3


def _order_query():
    return (
        select(Order, Product, Merchant, User)
        .join(Product, Product.id == Order.product_id)
        .join(Merchant, Merchant.id == Product.merchant_id)
        .join(User, User.id == Order.user_id)
    )


def _to_order_out(row, include_student: bool) -> OrderOut:
    order, product, merchant, student = row
    return OrderOut(
        id=order.id,
        product_id=product.id,
        product_title=product.title,
        product_image=product.image or "",
        shop_name=merchant.shop_name,
        original_price=order.original_price,
        price=order.price,
        quantity=order.quantity,
        status=order.status,
        pickup_code=order.pickup_code,
        expire_time=format_datetime(product.expire_time),
        location=product.location,
        created_at=format_datetime(order.created_at),
        picked_at=format_datetime(order.picked_at),
        student_name=student.name if include_student else None,
        student_id=student.student_id if include_student else None,
        phone=student.phone if include_student else None,
    )


def _merchant_for_user(db: Session, user_id: int) -> Merchant:
    merchant = db.scalar(select(Merchant).where(Merchant.user_id == user_id))
    if merchant is None or merchant.audit_status != MERCHANT_APPROVED:
        raise BusinessError(403, "商家账号未通过审核或无商家资料", 403)
    return merchant


def _expire_pending_orders(db: Session) -> None:
    now = now_shanghai_naive()
    expired_product_ids = select(Product.id).where(Product.expire_time <= now)
    db.execute(
        update(Order)
        .where(
            Order.status == ORDER_PENDING,
            Order.product_id.in_(expired_product_ids),
        )
        .values(status=ORDER_EXPIRED)
        .execution_options(synchronize_session=False)
    )
    db.commit()


def _generate_pickup_code(db: Session) -> str:
    for _ in range(MAX_PICKUP_CODE_ATTEMPTS):
        code = str(secrets.randbelow(900000) + 100000)
        exists = db.scalar(select(Order.id).where(Order.pickup_code == code))
        if exists is None:
            return code
    raise BusinessError(50000, "取货码生成失败，请稍后重试", 500)


def _load_order(db: Session, order_id: int):
    return db.execute(_order_query().where(Order.id == order_id)).one_or_none()


def _raise_product_unavailable(db: Session, product_id: int, quantity: int) -> None:
    product = db.get(Product, product_id)
    if product is None:
        raise BusinessError(404, "商品不存在", 404)
    if product.status != PRODUCT_ON_SALE:
        raise BusinessError(400, "商品已售罄或已下架", 400)
    if product.expire_time <= now_shanghai_naive():
        raise BusinessError(400, "商品已过期，无法下单", 400)
    if product.quantity < quantity:
        raise BusinessError(400, "商品库存不足", 400)
    raise BusinessError(400, "商品暂时无法下单，请刷新后重试", 400)


def create_order(
    db: Session, current_user: CurrentUser, request: CreateOrderRequest
) -> OrderOut:
    if current_user.role != STUDENT_ROLE:
        raise BusinessError(403, "仅学生可以下单", 403)

    for attempt in range(MAX_CREATE_ATTEMPTS):
        product = db.get(Product, request.product_id)
        if product is None:
            raise BusinessError(404, "商品不存在", 404)
        now = now_shanghai_naive()
        if product.status != PRODUCT_ON_SALE:
            raise BusinessError(400, "商品已售罄或已下架", 400)
        if product.expire_time <= now:
            raise BusinessError(400, "商品已过期，无法下单", 400)
        if product.quantity < request.quantity:
            raise BusinessError(400, "商品库存不足", 400)

        pickup_code = _generate_pickup_code(db)
        decrement = db.execute(
            update(Product)
            .where(
                Product.id == product.id,
                Product.status == PRODUCT_ON_SALE,
                Product.expire_time > now,
                Product.quantity >= request.quantity,
            )
            .values(
                quantity=Product.quantity - request.quantity,
                status=case(
                    (Product.quantity == request.quantity, PRODUCT_SOLD_OUT),
                    else_=Product.status,
                ),
                order_count=Product.order_count + 1,
            )
            .execution_options(synchronize_session=False)
        )
        if decrement.rowcount != 1:
            db.rollback()
            _raise_product_unavailable(db, request.product_id, request.quantity)

        order = Order(
            user_id=current_user.id,
            product_id=product.id,
            quantity=request.quantity,
            original_price=Decimal(product.original_price),
            price=Decimal(product.discount_price),
            pickup_code=pickup_code,
            status=ORDER_PENDING,
            created_at=now,
        )
        db.add(order)
        db.add(
            Behavior(
                user_id=current_user.id,
                product_id=product.id,
                behavior_type=ORDER_BEHAVIOR,
                created_at=now,
            )
        )

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            if "pickup_code" in str(exc) and attempt + 1 < MAX_CREATE_ATTEMPTS:
                continue
            raise BusinessError(50000, "订单创建失败，请稍后重试", 500)

        row = _load_order(db, order.id)
        if row is None:
            raise BusinessError(50000, "订单创建失败，请稍后重试", 500)
        return _to_order_out(row, include_student=False)

    raise BusinessError(50000, "取货码生成失败，请稍后重试", 500)


def list_orders(
    db: Session, current_user: CurrentUser, status: Optional[int]
) -> List[OrderOut]:
    if current_user.role not in (STUDENT_ROLE, MERCHANT_ROLE):
        raise BusinessError(403, "仅学生或商家可以查看订单", 403)

    merchant = None
    if current_user.role == MERCHANT_ROLE:
        merchant = _merchant_for_user(db, current_user.id)

    _expire_pending_orders(db)
    statement = _order_query()
    include_student = current_user.role == MERCHANT_ROLE
    if include_student:
        statement = statement.where(Product.merchant_id == merchant.id)
    else:
        statement = statement.where(Order.user_id == current_user.id)
    if status is not None:
        statement = statement.where(Order.status == status)
    rows = db.execute(statement.order_by(Order.created_at.desc(), Order.id.desc())).all()
    return [_to_order_out(row, include_student=include_student) for row in rows]


def _pickup_loaded_order(
    db: Session,
    current_user: CurrentUser,
    row,
    merchant: Optional[Merchant],
) -> OrderOut:
    order, product, _shop, _student = row
    if merchant is not None and product.merchant_id != merchant.id:
        raise BusinessError(403, "无权核销该订单", 403)
    if order.status == ORDER_PICKED_UP:
        raise BusinessError(400, "订单已核销，请勿重复操作", 400)
    if order.status == ORDER_EXPIRED:
        raise BusinessError(400, "订单已过期，无法核销", 400)

    picked_at = now_shanghai_naive()
    result = db.execute(
        update(Order)
        .where(Order.id == order.id, Order.status == ORDER_PENDING)
        .values(status=ORDER_PICKED_UP, picked_at=picked_at)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        latest = _load_order(db, order.id)
        if latest is not None and latest[0].status == ORDER_PICKED_UP:
            raise BusinessError(400, "订单已核销，请勿重复操作", 400)
        raise BusinessError(400, "订单状态已变化，请刷新后重试", 400)

    db.commit()
    db.expire_all()
    updated = _load_order(db, order.id)
    if updated is None:
        raise BusinessError(404, "订单不存在", 404)
    return _to_order_out(updated, include_student=True)


def pickup_order(
    db: Session, current_user: CurrentUser, order_id: int
) -> OrderOut:
    if current_user.role not in (MERCHANT_ROLE, ADMIN_ROLE):
        raise BusinessError(403, "仅商家或管理员可以核销订单", 403)
    merchant = (
        _merchant_for_user(db, current_user.id)
        if current_user.role == MERCHANT_ROLE
        else None
    )
    _expire_pending_orders(db)
    row = _load_order(db, order_id)
    if row is None:
        raise BusinessError(404, "订单不存在", 404)
    return _pickup_loaded_order(db, current_user, row, merchant)


def verify_pickup_code(
    db: Session, current_user: CurrentUser, pickup_code: str
) -> OrderOut:
    if current_user.role not in (MERCHANT_ROLE, ADMIN_ROLE):
        raise BusinessError(403, "仅商家或管理员可以核销订单", 403)
    merchant = (
        _merchant_for_user(db, current_user.id)
        if current_user.role == MERCHANT_ROLE
        else None
    )
    _expire_pending_orders(db)
    row = db.execute(
        _order_query().where(Order.pickup_code == pickup_code)
    ).one_or_none()
    if row is None:
        raise BusinessError(400, "取货码无效", 400)
    return _pickup_loaded_order(db, current_user, row, merchant)
