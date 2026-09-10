from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.database import SessionLocal, init_database
from app.models import Merchant, Product, User, WalletAccount
from app.timeutils import now_shanghai_naive


def main() -> None:
    init_database()
    with SessionLocal() as db:
        if db.scalar(select(func.count(User.id))) != 0:
            print("数据库已有用户，未写入演示数据。")
            return

        student = User(
            role=1,
            login_name="2021001",
            password="demo-placeholder",
            school="XX大学",
            student_id="2021001",
            name="张三",
            phone="13800000000",
            status=1,
        )
        merchant_user = User(
            role=2,
            login_name="shop001",
            password="demo-placeholder",
            name="店铺账号",
            phone="13811112222",
            status=1,
        )
        admin = User(
            role=3,
            login_name="admin",
            password="demo-placeholder",
            name="超级管理员",
            phone="00000000000",
            status=1,
        )
        db.add_all([student, merchant_user, admin])
        db.flush()
        db.add_all(
            [
                WalletAccount(user_id=student.id, balance=Decimal("128.60")),
                WalletAccount(user_id=merchant_user.id, balance=Decimal("386.50")),
                WalletAccount(user_id=admin.id, balance=Decimal("0.00")),
            ]
        )

        merchant = Merchant(
            user_id=merchant_user.id,
            shop_name="XX风味小吃",
            location="XX大学南门15米",
            lat=Decimal("30.123456"),
            lng=Decimal("120.123456"),
            audit_status=1,
        )
        db.add(merchant)
        db.flush()

        product = Product(
            merchant_id=merchant.id,
            title="水煮鱼片 超值套餐",
            description="订单模块联调用演示商品",
            category="简餐",
            image="",
            original_price=Decimal("28.00"),
            discount_price=Decimal("12.00"),
            quantity=10,
            expire_time=now_shanghai_naive() + timedelta(days=1),
            location="XX大学南门15米",
            lat=Decimal("30.123456"),
            lng=Decimal("120.123456"),
            status=1,
        )
        db.add(product)
        db.commit()

        print("演示数据已创建：")
        print("学生 user_id={} role=1".format(student.id))
        print("商家 user_id={} role=2".format(merchant_user.id))
        print("管理员 user_id={} role=3".format(admin.id))
        print("商品 product_id={}".format(product.id))


if __name__ == "__main__":
    main()
