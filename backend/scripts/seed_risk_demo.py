"""为「管理员端 - 风控日志」补充演示数据。

用法（在 backend 目录下）：
    PYTHONPATH=. python scripts/seed_risk_demo.py

会做四件事（可重复执行，已存在的同名商品会被同步为最新文案）：
1. 清理历史版本遗留的演示商品（LEGACY_TITLES 里处于风控拦截状态的商品）
2. 订正历史商品描述里会误导风控判断的旧文案（LEGACY_DESC_FIXES，整句替换）
3. 创建/更新 3 个演示商品（价格异常 / 敏感词 / 有效期）
4. 写入/更新对应的 risk_logs，让风控日志页有内容可点、可看商品详情、可「误判恢复」

重要：**商品本身不要动**（名称、价格、拦截状态保持原样），要动的是「风控原因」。
风控说明必须与 app/risk_control.py 的真实规则一一对应，否则超管点开详情会看到
「商品描述说 A、风控原因说 B」的自相矛盾。
（历史问题：敏感词案例的原因写成与商品无关的「药膳」、描述里也写着「自称药膳」，
看上去像风控判错了商品，实际命中的是商品名里的「特效」这一功效夸大用语。）
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.database import SessionLocal, init_database
from app.models import Merchant, Product, RiskLog
from app.timeutils import now_shanghai_naive

# (商品标题, 描述, 分类, 原价, 折扣价, 库存, 距现在几小时后过期, 风控类型, 风控说明, 商品状态)
# 风控类型：1 价格异常 2 敏感词 3 有效期
# 风控说明的措辞与 app/risk_control.py 的真实输出保持一致（引擎原文，必要时补极简括注）：
#   价格：_check_price 仅在「折扣价 > 原价」时拦截
#   敏感词：_check_words 输出「命中敏感词：xxx」
#   有效期：_check_expiry 不足 1 小时为警告、已过期为拦截
DEMO_RISK_PRODUCTS = [
    (
        "特效降温套餐",
        "冰镇绿豆沙配凉拌青瓜与酸梅汤，夏日解暑三件套，下单后现做现冷、到店即取。",
        "其他",
        Decimal("20.00"),
        Decimal("9.00"),
        3,
        4,
        2,
        # 命中的是商品名里的「特效」（功效夸大用语），与「药膳」等正常表述无关
        "命中敏感词：特效（功效夸大用语）",
        3,  # 敏感词 → 拦截
    ),
    (
        "超值双拼套餐",
        "折扣价高于原价，疑似虚构原价冲销量，演示用被拦截商品。",
        "简餐",
        Decimal("20.00"),
        Decimal("22.00"),  # 折扣价 > 原价，触发价格异常
        3,
        6,
        1,
        "折扣价(22.00)高于原价(20.00)，疑似虚假折扣",
        3,  # 价格异常 → 拦截
    ),
    (
        "临期烘焙盲盒",
        "剩余可售时间不足 1 小时，演示用被风控标注商品。",
        "烘焙",
        Decimal("16.00"),
        Decimal("4.90"),
        8,
        0.5,  # 不足 1 小时，触发有效期警告（非拦截）
        3,
        "商品有效期不足 1 小时，强制标注「即将过期」",
        1,  # 仅警告 → 仍在售、带风控标注
    ),
]

# 历史版本里被换掉的演示商品，重新播种时清掉（仅限风控拦截或无库存状态的商品）
LEGACY_TITLES = ("祖传秘制 包治百病养生汤", "昨晚的烘焙盲盒")

# 历史商品文案订正（幂等）：旧描述里写了「自称药膳」「含违禁夸大宣传词」等演示元信息，
# 会让超管误以为风控判的是「药膳」，实际命中的是商品名里的「特效」。只做整句替换，
# 不动商品名称/价格/其他描述。重跑脚本会把旧库里的这两句都订正成真实商品介绍。
REAL_DESC_TECHANG = "冰镇绿豆沙配凉拌青瓜与酸梅汤，夏日解暑三件套，下单后现做现冷、到店即取。"
LEGACY_DESC_FIXES = {
    "自称药膳，含违禁夸大宣传词，演示用被拦截商品。": REAL_DESC_TECHANG,
    "含违禁夸大宣传词，演示用被拦截商品。": REAL_DESC_TECHANG,
}


def _drop_legacy(db) -> int:
    """删除历史演示商品及其风控日志，避免日志页出现与商品对不上的旧文案。"""
    removed = 0
    for title in LEGACY_TITLES:
        rows = db.query(Product).filter(Product.title == title, Product.status == 3).all()
        for product in rows:
            db.query(RiskLog).filter(RiskLog.product_id == product.id).delete()
            db.delete(product)
            removed += 1
    return removed


def _fix_legacy_copy(db) -> int:
    """订正历史版本的商品描述文案（整句替换，幂等），不动商品名称/价格/其他描述。"""
    fixed = 0
    for old, new in LEGACY_DESC_FIXES.items():
        for product in db.query(Product).filter(Product.description == old).all():
            product.description = new
            fixed += 1
    return fixed


def main() -> None:
    init_database()
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).first()
        if merchant is None:
            print("[skip] 数据库里没有商家，请先执行 scripts/seed_demo.py")
            return

        dropped = _drop_legacy(db)
        copy_fixed = _fix_legacy_copy(db)
        now = now_shanghai_naive()
        created = updated = 0

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
            status,
        ) in DEMO_RISK_PRODUCTS:
            product = (
                db.query(Product)
                .filter(Product.merchant_id == merchant.id, Product.title == title)
                .first()
            )
            if product is None:
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
                    status=status,
                    risk_flag=1,
                    view_count=0,
                    fav_count=0,
                    order_count=0,
                    created_at=now,
                )
                db.add(product)
                created += 1
            else:
                # 已存在：只同步「演示口径 + 风控说明」，商品名称/描述保持原样
                updated += 1
                product.expire_time = now + timedelta(hours=expire_hours)
                product.status = status
                product.risk_flag = 1

            db.flush()

            log = (
                db.query(RiskLog)
                .filter(RiskLog.product_id == product.id)
                .order_by(RiskLog.id)
                .first()
            )
            if log is None:
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
            else:
                log.merchant_id = merchant.id
                log.risk_type = risk_type
                log.risk_detail = risk_detail
                log.is_resolved = 0
                log.created_at = now

        db.commit()
        print(
            f"[ok] 风控演示数据：清理遗留 {dropped} 条，文案订正 {copy_fixed} 条，新建 {created} 条，"
            f"更新 {updated} 条（商品 + 风控日志）"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
