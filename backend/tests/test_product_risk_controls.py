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
