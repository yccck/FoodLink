"""为「优惠分配 / 学生消费排行」补充演示数据。

用法（在 backend 目录下）：
    PYTHONPATH=. python scripts/seed_subsidy_demo.py

会做三件事（已有数据则跳过，可重复执行）：
1. 补足若干名学生（澳门科技大学），密码统一 123456
2. 按学生生成不同笔数的已完成订单，形成消费次数 / 金额排行
3. 为平台注入一笔演示补贴资金，保证「可分配余额」大于 0
"""

from __future__ import annotations

import sys
from datetime import timedelta
from decimal import Decimal

from app.database import SessionLocal, init_database
from app.models import Order, Product, SubsidyGrant, User, WalletAccount
from app.security_password import hash_password
from app.timeutils import now_shanghai_naive

DEMO_PASSWORD = "123456"
SCHOOL = "澳门科技大学"

# (学号, 姓名, 手机号, 订单笔数, 每笔数量)
DEMO_STUDENTS = [
    ("2021002", "李思", "13800000002", 6, 2),
    ("2021003", "王宇", "13800000003", 5, 1),
    ("2021004", "陈小雨", "13800000004", 4, 3),
    ("2021005", "赵敏", "13800000005", 3, 1),
    ("2021006", "孙悦", "13800000006", 2, 2),
    ("2021007", "周航", "13800000007", 1, 1),
]

INJECT_AMOUNT = Decimal("200.00")


def main() -> int:
    init_database()
    db = SessionLocal()
    try:
        product = db.query(Product).order_by(Product.id).first()
        if product is None:
            print("没有商品数据，请先执行 scripts/seed_demo.py")
            return 1

        now = now_shanghai_naive()
        admin = db.query(User).filter(User.role == 3).order_by(User.id).first()

        # 1) 学生
        created_users = 0
        for student_id, name, phone, _count, _qty in DEMO_STUDENTS:
            exists = (
                db.query(User).filter(User.login_name == student_id).first()
            )
            if exists:
                continue
            user = User(
                role=1,
                login_name=student_id,
                password=hash_password(DEMO_PASSWORD),
                school=SCHOOL,
                student_id=student_id,
                name=name,
                phone=phone,
                status=1,
                created_at=now,
            )
            db.add(user)
            db.flush()
            db.add(WalletAccount(user_id=user.id, balance=Decimal("0.00")))
            created_users += 1
        db.commit()

        # 2) 订单
        created_orders = 0
        pickup_seq = 900000
        for student_id, _name, _phone, count, qty in DEMO_STUDENTS:
            user = db.query(User).filter(User.login_name == student_id).first()
            if user is None:
                continue
            have = (
                db.query(Order).filter(Order.user_id == user.id).count()
            )
            for i in range(have, count):
                pickup_seq += 1
                db.add(
                    Order(
                        user_id=user.id,
                        product_id=product.id,
                        quantity=qty,
                        original_price=Decimal(str(product.original_price)),
                        price=Decimal(str(product.discount_price)),
                        pickup_code=str(pickup_seq),
                        status=1,
                        picked_at=now - timedelta(days=i),
                        created_at=now - timedelta(days=i),
                    )
                )
                created_orders += 1
        db.commit()

        # 3) 平台注入演示资金
        injected = 0
        if admin is not None:
            has_inject = (
                db.query(SubsidyGrant)
                .filter(SubsidyGrant.grant_type == 2)
                .count()
            )
            if has_inject == 0:
                db.add(
                    SubsidyGrant(
                        grant_type=2,
                        amount=INJECT_AMOUNT,
                        remark="演示注入",
                        operator_id=admin.id,
                        created_at=now,
                    )
                )
                injected = 1
                db.commit()

        print(
            f"完成：新增学生 {created_users} 名、订单 {created_orders} 笔、注入记录 {injected} 条"
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
