from app.models import Product, RiskLog


def test_risk_flagged_product_cannot_toggle_or_be_ordered(
    client, auth_headers, session_factory
):
    with session_factory() as db:
        product = db.get(Product, 1)
        product.risk_flag = 1
        db.commit()

    toggled = client.put(
        "/api/products/1/offline",
        headers=auth_headers(2, 2),
    )
    assert toggled.status_code == 400
    assert toggled.json()["code"] == 41004

    ordered = client.post(
        "/api/orders",
        json={"product_id": 1, "quantity": 1},
        headers=auth_headers(1, 1),
    )
    assert ordered.status_code == 400
    assert "风控拦截" in ordered.json()["message"]

    listed = client.get("/api/products").json()["data"]["items"]
    assert all(item["id"] != 1 for item in listed)


def test_resolving_last_risk_log_restores_product(
    client, auth_headers, session_factory
):
    with session_factory() as db:
        product = db.get(Product, 1)
        product.status = 3
        product.risk_flag = 1
        risk_log = RiskLog(
            product_id=product.id,
            merchant_id=product.merchant_id,
            risk_type=2,
            risk_detail="测试风控拦截",
            is_resolved=0,
        )
        db.add(risk_log)
        db.commit()
        log_id = risk_log.id

    restored = client.put(
        f"/api/admin/risk-logs/{log_id}/resolve",
        headers=auth_headers(4, 3),
    )
    assert restored.status_code == 200
    assert restored.json()["code"] == 0

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product.risk_flag == 0
        assert product.status == 1


def test_confirm_block_keeps_product_blocked(client, auth_headers, session_factory):
    with session_factory() as db:
        product = db.get(Product, 1)
        product.status = 3
        product.risk_flag = 1
        log = RiskLog(
            product_id=product.id,
            merchant_id=product.merchant_id,
            risk_type=2,
            risk_detail="测试风控拦截",
            is_resolved=0,
        )
        db.add(log)
        db.commit()
        log_id = log.id

    confirmed = client.post(
        f"/api/admin/risk-logs/{log_id}/confirm",
        headers=auth_headers(4, 3),
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["code"] == 0

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product.status == 3  # 确认拦截：商品持续挂起
        assert product.risk_flag == 1
        log = db.get(RiskLog, log_id)
        assert log.review_status == 1
        assert log.is_resolved == 1


def test_release_requires_all_logs_resolved(client, auth_headers, session_factory):
    with session_factory() as db:
        product = db.get(Product, 1)
        product.status = 3
        product.risk_flag = 1
        l1 = RiskLog(product_id=product.id, merchant_id=product.merchant_id, risk_type=2, risk_detail="a", is_resolved=0)
        l2 = RiskLog(product_id=product.id, merchant_id=product.merchant_id, risk_type=1, risk_detail="b", is_resolved=0)
        db.add_all([l1, l2])
        db.commit()
        id1, id2 = l1.id, l2.id

    # 只恢复一条，商品应保持拦截
    client.put(f"/api/admin/risk-logs/{id1}/resolve", headers=auth_headers(4, 3))
    with session_factory() as db:
        assert db.get(Product, 1).status == 3

    # 再恢复第二条，商品才解封
    client.put(f"/api/admin/risk-logs/{id2}/resolve", headers=auth_headers(4, 3))
    with session_factory() as db:
        product = db.get(Product, 1)
        assert product.status == 1
        assert product.risk_flag == 0


def test_risk_log_list_includes_review_status(client, auth_headers, session_factory):
    with session_factory() as db:
        product = db.get(Product, 1)
        log = RiskLog(
            product_id=product.id,
            merchant_id=product.merchant_id,
            risk_type=2,
            risk_detail="测试",
            is_resolved=0,
            review_status=0,
        )
        db.add(log)
        db.commit()

    resp = client.get("/api/admin/risk-logs", headers=auth_headers(4, 3))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any("review_status" in l and "review_status_name" in l for l in data)
    assert data[0]["review_status_name"] in ("待人工复核", "已确认拦截", "已误判恢复")
