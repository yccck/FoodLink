"""优惠分配（学生消费排行 + 发放）接口测试。"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.models import Order, Product
from app.timeutils import now_shanghai_naive


def _make_orders(db, pairs):
    """pairs: [(user_id, product_id, quantity, price), ...]"""

    now = now_shanghai_naive()
    for idx, (user_id, product_id, quantity, price) in enumerate(pairs, start=1):
        db.add(
            Order(
                id=idx,
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                original_price=Decimal("28.00"),
                price=Decimal(price),
                pickup_code="{:06d}".format(idx),
                status=1,
                created_at=now - timedelta(days=idx),
            )
        )
    db.commit()


def test_consumption_ranking_and_subsidy_grant(client, auth_headers, session_factory):
    with session_factory() as db:
        _make_orders(
            db,
            [
                (1, 1, 2, "12.00"),  # 学生甲：3 单
                (1, 2, 1, "9.90"),
                (1, 1, 1, "12.00"),
                (5, 1, 5, "12.00"),  # 学生乙：1 单但金额 60
            ],
        )

    admin = auth_headers(4, 3)

    # 1) 消费排行：按次数降序，学生甲（3 单）居首
    r = client.get("/api/admin/students/consumption", headers=admin)
    assert r.status_code == 200 and r.json()["code"] == 0, r.text
    rows = r.json()["data"]
    assert [x["user_id"] for x in rows] == [1, 5], rows
    assert rows[0]["order_count"] == 3
    assert rows[0]["total_amount"] == "45.90", rows[0]
    assert rows[1]["total_amount"] == "60.00", rows[1]

    # 2) 资金池：初始只有平台服务费（0.1%）
    r = client.get("/api/admin/subsidy/pool", headers=admin)
    assert r.status_code == 200, r.text
    pool = r.json()["data"]
    assert pool["platform_profit"] == "0.11", pool  # 96.00 * 0.001
    assert pool["available"] == "0.11", pool

    # 3) 余额不足时应拒绝
    r = client.post(
        "/api/admin/subsidy/grants",
        json={"user_ids": [1, 5], "amount": "5.00"},
        headers=admin,
    )
    assert r.json()["code"] != 0 and "可分配余额不足" in r.json()["message"], r.text

    # 4) 平台注入资金
    r = client.put(
        "/api/admin/subsidy/pool/inject",
        json={"amount": "100.00", "remark": "演示注入"},
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["available"] == "100.11", r.json()["data"]

    # 5) 发放：每人 5 元
    r = client.post(
        "/api/admin/subsidy/grants",
        json={"user_ids": [1, 5], "amount": "5.00", "remark": "困难学生优惠"},
        headers=admin,
    )
    assert r.status_code == 200 and r.json()["code"] == 0, r.text
    grants = r.json()["data"]
    assert len(grants) == 2
    assert all(g["amount"] == "5.00" for g in grants)
    assert grants[0]["user_name"] in ("学生甲", "学生乙")

    # 6) 钱包自动划拨：学生甲 50 -> 55
    with session_factory() as db:
        from app.models import WalletAccount

        wallet = db.get(WalletAccount, 1)
        assert wallet.balance == Decimal("55.00"), wallet.balance

    # 7) 资金池扣减
    r = client.get("/api/admin/subsidy/pool", headers=admin)
    pool = r.json()["data"]
    assert pool["granted"] == "10.00", pool
    assert pool["available"] == "90.11", pool

    # 8) 发放记录
    r = client.get("/api/admin/subsidy/grants", headers=admin)
    assert r.status_code == 200, r.text
    records = r.json()["data"]
    assert len(records) == 3  # 2 笔发放 + 1 笔注入
    assert records[0]["grant_type"] == 1

    # 9) 学生端通知：发放后有一条未读，称号按排名生成
    student = auth_headers(1, 1)
    r = client.get("/api/user/subsidy/notices", headers=student)
    assert r.status_code == 200 and r.json()["code"] == 0, r.text
    notices = r.json()["data"]
    assert len(notices) == 1, notices
    assert notices[0]["amount"] == "5.00"
    assert notices[0]["title"] == "本月消费达人", notices[0]  # 学生甲排名第 1
    assert notices[0]["is_read"] == 0, notices[0]

    # 10) 标记已读后仍保留在通知中心，只是 is_read 变 1
    grant_id = notices[0]["id"]
    r = client.put(f"/api/user/subsidy/notices/{grant_id}/read", headers=student)
    assert r.status_code == 200 and r.json()["code"] == 0, r.text
    r = client.get("/api/user/subsidy/notices", headers=student)
    after = r.json()["data"]
    assert len(after) == 1 and after[0]["is_read"] == 1, after

    # 11) 非超管不可访问管理端接口
    r = client.get("/api/admin/subsidy/pool", headers=student)
    assert r.status_code == 403, r.status_code
