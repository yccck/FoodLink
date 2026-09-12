"""为「超管后台 - 风控日志」补充演示数据。

用法（在 backend 目录下）：
    PYTHONPATH=. python scripts/seed_risk_demo.py

会做两件事（已有同名商品则跳过，可重复执行）：
1. 创建 3 个被风控拦截的商品（价格异常 / 敏感词 / 有效期过短），status=3、risk_flag=1
2. 对应写入 risk_logs，让风控日志页有内容可点、可看商品详情、可「误判恢复」
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.database import SessionLocal, init_database
from app.models import Merchant, Product, RiskLog
from app.timeutils import now_shanghai_naive

# (商品标题, 描述, 分类, 原价, 折扣价, 库存, 距现在几小时后过期, 风控类型, 风控说明)
# 风控类型：1 价格异常 2 敏感词 3 有效期
DEMO_RISK_PRODUCTS = [
    (
        "特效降温套餐",
        "自称药膳，含违禁夸大宣传词，演示用被拦截商品。",
        "其他",
        Decimal("20.00"),
        Decimal("19.90"),  # 折扣价接近原价，触发价格异常
        3,
        6,
        1,
        "折扣价高于原价的 90%，疑似未真正让利（原价 20.00，折扣价 19.90）",
    ),
    (
        "祖传秘制 包治百病养生汤",
        "含绝对化用语与医疗功效宣传，演示用被拦截商品。",
        "汤品",
        Decimal("38.00"),
        Decimal("12.00"),
        5,
        10,
        2,
        "命中敏感词：包治百病",
    ),
    (
        "临期烘焙盲盒",
        "距离领取截止不足 1 小时，演示用被拦截商品。",
        "烘焙",
        Decimal("16.00"),
        Decimal("4.90"),
        8,
        0.5,
        3,
        "可售时长不足 1 小时，学生难以到店领取",
    ),
]


def main() -> None:
    init_database()
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        if merchant is None:
            print("[skip] 数据库里没有商家，请先执行 scripts/seed_demo.py")
            return

        now = now_shanghai_naive()
        created = 0
        for (
            title,
            desc,
            category,
            original,
            discount,
            quantity,
            expire_hours,
            risk_type,
            risk_detail,
        ) in DEMO_RISK_PRODUCTS:
            exists = (
                db.query(Product)
                .filter(Product.merchant_id == merchant.id, Product.title == title)
                .first()
            )
            if exists:
                continue

            product = Product(
                merchant_id=merchant.id,
                title=title,
                description=desc,
                category=category,
                image="",
                original_price=original,
                discount_price=discount,
                quantity=quantity,
                expire_time=now + timedelta(hours=expire_hours),
                business_open_time="08:00",
                business_close_time="22:00",
                location=merchant.location or "澳门科技大学学生餐厅取货点",
                lat=Decimal("22.149600"),
                lng=Decimal("113.565000"),
                status=3,  # 3 = 风控拦截
                risk_flag=1,
                view_count=0,
                fav_count=0,
                order_count=0,
                created_at=now,
            )
            db.add(product)
            db.flush()

            db.add(
                RiskLog(
                    product_id=product.id,
                    merchant_id=merchant.id,
                    risk_type=risk_type,
                    risk_detail=risk_detail,
                    is_resolved=0,
                    created_at=now,
                )
            )
            created += 1

        db.commit()
        print(f"[ok] 新增 {created} 条风控演示数据（商品 + 风控日志）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
