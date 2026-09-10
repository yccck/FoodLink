from __future__ import annotations

import re
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.models import Behavior, Order, Product, WalletAccount
from app.timeutils import now_shanghai_naive


def _create(client, headers, product_id=1, quantity=1):
    return client.post(
        "/api/orders",
        json={"product_id": product_id, "quantity": quantity},
        headers=headers,
    )


def test_create_order_generates_unique_six_digit_code_and_updates_stock(
    client, auth_headers, session_factory
):
    headers = auth_headers(1, 1)
    first = _create(client, headers)
    second = _create(client, headers)

    assert first.status_code == 200
    assert first.json()["code"] == 0
    first_order = first.json()["data"]
    second_order = second.json()["data"]
    assert re.fullmatch(r"\d{6}", first_order["pickup_code"])
    assert first_order["pickup_code"] != second_order["pickup_code"]
    assert first_order["price"] == "12.00"
    assert first_order["original_price"] == "28.00"
    assert first_order["total_amount"] == "12.00"
    assert first_order["payment_status"] == "escrowed"
    assert first_order["platform_fee_rate"] == "0.1%"
    assert first_order["platform_fee"] == "0.01"
    assert first_order["merchant_receivable"] == "11.99"
    assert "completion_type" not in first_order
    assert 0 < first_order["remaining_seconds"] <= 6 * 60 * 60
    created_at = datetime.strptime(first_order["created_at"], "%Y-%m-%d %H:%M:%S")
    pickup_deadline = datetime.strptime(
        first_order["pickup_deadline"], "%Y-%m-%d %H:%M:%S"
    )
    assert pickup_deadline - created_at == timedelta(hours=6)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", first_order["created_at"])
    assert "student_name" not in first_order

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product.quantity == 1
        assert product.order_count == 2
        assert db.scalar(select(func.count(Order.id))) == 2
        assert db.scalar(select(func.count(Behavior.id))) == 2


def test_create_order_prevents_overselling_and_marks_sold_out(
    client, auth_headers, session_factory
):
    headers = auth_headers(1, 1)
    too_many = _create(client, headers, quantity=4)
    assert too_many.status_code == 400
    assert too_many.json()["message"] == "商品库存不足"

    sold_out = _create(client, headers, quantity=3)
    assert sold_out.status_code == 200
    rejected = _create(client, auth_headers(5, 1), quantity=1)
    assert rejected.status_code == 400
    assert rejected.json()["message"] == "商品已售罄或已下架"

    with session_factory() as db:
        product = db.get(Product, 1)
        assert product.quantity == 0
        assert product.status == 2
        assert db.scalar(select(func.count(Order.id))) == 1


def test_only_students_can_create_orders_and_request_identity_is_rejected(
    client, auth_headers
):
    merchant = _create(client, auth_headers(2, 2))
    assert merchant.status_code == 403
    assert merchant.json()["code"] == 403

    forged = client.post(
        "/api/orders",
        json={"product_id": 1, "quantity": 1, "user_id": 5},
        headers=auth_headers(1, 1),
    )
    assert forged.status_code == 400
    assert forged.json()["code"] == 400


def test_expired_and_offline_products_cannot_be_ordered(client, auth_headers):
    headers = auth_headers(1, 1)
    expired = _create(client, headers, product_id=3)
    offline = _create(client, headers, product_id=4)
    assert expired.status_code == 400
    assert expired.json()["message"] == "商品已过期，无法下单"
    assert offline.status_code == 400
    assert offline.json()["message"] == "商品已售罄或已下架"


def test_order_lists_are_scoped_to_student_or_merchant(client, auth_headers):
    student_one = auth_headers(1, 1)
    student_two = auth_headers(5, 1)
    _create(client, student_one, product_id=1)
    _create(client, student_two, product_id=1)
    _create(client, student_one, product_id=2)

    student_orders = client.get("/api/orders?status=", headers=student_one).json()["data"]
    assert len(student_orders) == 2
    assert {order["product_id"] for order in student_orders} == {1, 2}
    assert all("student_name" not in order for order in student_orders)

    merchant_one_orders = client.get("/api/orders", headers=auth_headers(2, 2)).json()["data"]
    assert len(merchant_one_orders) == 2
    assert {order["student_id"] for order in merchant_one_orders} == {"S001", "S002"}
    assert all(order["product_id"] == 1 for order in merchant_one_orders)

    merchant_two_orders = client.get("/api/orders", headers=auth_headers(3, 2)).json()["data"]
    assert len(merchant_two_orders) == 1
    assert merchant_two_orders[0]["product_id"] == 2


def test_order_keeps_price_snapshot_when_product_price_changes(
    client, auth_headers, session_factory
):
    _create(client, auth_headers(1, 1))
    with session_factory() as db:
        product = db.get(Product, 1)
        product.original_price = Decimal("88.00")
        product.discount_price = Decimal("66.00")
        db.commit()

    order = client.get("/api/orders", headers=auth_headers(1, 1)).json()["data"][0]
    assert order["original_price"] == "28.00"
    assert order["price"] == "12.00"


def test_merchant_can_pick_up_own_order_but_not_another_merchants_order(
    client, auth_headers, session_factory
):
    created = _create(client, auth_headers(1, 1), product_id=1).json()["data"]
    forbidden = client.put(
        "/api/orders/{}/pickup".format(created["id"]),
        headers=auth_headers(3, 2),
    )
    assert forbidden.status_code == 403

    picked = client.put(
        "/api/orders/{}/pickup".format(created["id"]),
        headers=auth_headers(2, 2),
    )
    assert picked.status_code == 200
    assert picked.json()["data"]["status"] == 1
    assert picked.json()["data"]["student_id"] == "S001"
    assert picked.json()["data"]["picked_at"] is not None
    assert picked.json()["data"]["payment_status"] == "settled"
    assert picked.json()["data"]["platform_fee"] == "0.01"
    assert picked.json()["data"]["merchant_receivable"] == "11.99"
    assert picked.json()["data"]["completion_type"] == "merchant_confirmed"
    assert picked.json()["data"]["settled_at"] == picked.json()["data"]["picked_at"]

    repeated = client.put(
        "/api/orders/{}/pickup".format(created["id"]),
        headers=auth_headers(2, 2),
    )
    assert repeated.status_code == 400
    assert "已核销" in repeated.json()["message"]

    with session_factory() as db:
        wallet = db.get(WalletAccount, 2)
        assert wallet.balance == Decimal("11.99")


def test_pickup_code_verification_checks_owner_and_role(client, auth_headers):
    created = _create(client, auth_headers(1, 1), product_id=1).json()["data"]
    payload = {"pickup_code": created["pickup_code"]}

    student = client.post(
        "/api/orders/verify", json=payload, headers=auth_headers(1, 1)
    )
    assert student.status_code == 403

    wrong_shop = client.post(
        "/api/orders/verify", json=payload, headers=auth_headers(3, 2)
    )
    assert wrong_shop.status_code == 403

    verified = client.post(
        "/api/orders/verify", json=payload, headers=auth_headers(2, 2)
    )
    assert verified.status_code == 200
    assert verified.json()["data"]["status"] == 1

    repeated = client.post(
        "/api/orders/verify", json=payload, headers=auth_headers(2, 2)
    )
    assert repeated.status_code == 400


def test_pending_order_auto_completes_and_settles_after_six_hours(
    client, auth_headers, session_factory
):
    created_at = now_shanghai_naive() - timedelta(hours=7)
    with session_factory() as db:
        order = Order(
            user_id=1,
            product_id=1,
            quantity=1,
            original_price=Decimal("28.00"),
            price=Decimal("12.00"),
            pickup_code="123456",
            status=0,
            created_at=created_at,
        )
        db.add(order)
        db.commit()

    completed = client.get("/api/orders?status=1", headers=auth_headers(1, 1))
    assert completed.status_code == 200
    assert len(completed.json()["data"]) == 1
    auto_order = completed.json()["data"][0]
    assert auto_order["status"] == 1
    assert auto_order["payment_status"] == "settled"
    assert auto_order["completion_type"] == "auto_timeout"
    assert auto_order["platform_fee"] == "0.01"
    assert auto_order["merchant_receivable"] == "11.99"
    expected_deadline = created_at + timedelta(hours=6)
    assert auto_order["picked_at"] == expected_deadline.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    assert auto_order["settled_at"] == auto_order["picked_at"]
    assert auto_order["remaining_seconds"] == 0

    verify = client.post(
        "/api/orders/verify",
        json={"pickup_code": "123456"},
        headers=auth_headers(2, 2),
    )
    assert verify.status_code == 400
    assert "已核销" in verify.json()["message"]

    with session_factory() as db:
        stored = db.scalar(select(Order).where(Order.pickup_code == "123456"))
        assert stored.status == 1
        assert stored.picked_at == expected_deadline
        wallet = db.get(WalletAccount, 2)
        assert wallet.balance == Decimal("11.99")

    # Repeated reads must not settle or credit the same order again.
    repeated_summary = client.get(
        "/api/orders/summary", headers=auth_headers(2, 2)
    )
    assert repeated_summary.status_code == 200
    with session_factory() as db:
        wallet = db.get(WalletAccount, 2)
        assert wallet.balance == Decimal("11.99")


def test_order_summary_reports_student_and_merchant_wallets(
    client, auth_headers, session_factory
):
    student_headers = auth_headers(1, 1)
    merchant_headers = auth_headers(2, 2)
    first = _create(client, student_headers, product_id=1, quantity=2).json()["data"]

    student = client.get("/api/orders/summary", headers=student_headers)
    assert student.status_code == 200
    assert student.json()["data"] == {
        "role": 1,
        "available_balance": "50.00",
        "escrow_amount": "24.00",
        "monthly_sales": "0.00",
        "monthly_spending": "24.00",
        "monthly_income": "0.00",
        "monthly_platform_fee": "0.00",
        "monthly_order_count": 1,
        "monthly_item_count": 2,
        "monthly_completed_count": 0,
    }

    pending_merchant = client.get("/api/orders/summary", headers=merchant_headers)
    assert pending_merchant.status_code == 200
    assert pending_merchant.json()["data"] == {
        "role": 2,
        "available_balance": "0.00",
        "escrow_amount": "24.00",
        "monthly_sales": "24.00",
        "monthly_spending": "0.00",
        "monthly_income": "0.00",
        "monthly_platform_fee": "0.00",
        "monthly_order_count": 1,
        "monthly_item_count": 2,
        "monthly_completed_count": 0,
    }

    picked = client.put(
        "/api/orders/{}/pickup".format(first["id"]), headers=merchant_headers
    )
    assert picked.status_code == 200

    settled_merchant = client.get("/api/orders/summary", headers=merchant_headers)
    summary = settled_merchant.json()["data"]
    assert summary["available_balance"] == "23.98"
    assert summary["escrow_amount"] == "0.00"
    assert summary["monthly_sales"] == "24.00"
    assert summary["monthly_income"] == "23.98"
    assert summary["monthly_platform_fee"] == "0.02"
    assert summary["monthly_order_count"] == 1
    assert summary["monthly_item_count"] == 2
    assert summary["monthly_completed_count"] == 1

    repeated = client.put(
        "/api/orders/{}/pickup".format(first["id"]), headers=merchant_headers
    )
    assert repeated.status_code == 400
    with session_factory() as db:
        wallet = db.get(WalletAccount, 2)
        assert wallet.balance == Decimal("23.98")


def test_admin_can_pick_up_any_merchants_order(client, auth_headers):
    created = _create(client, auth_headers(1, 1), product_id=2).json()["data"]
    response = client.put(
        "/api/orders/{}/pickup".format(created["id"]),
        headers=auth_headers(4, 3),
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == 1


def test_auth_and_validation_errors_use_unified_response(client, auth_headers):
    unauthorized = client.get("/api/orders")
    assert unauthorized.status_code == 401
    assert unauthorized.json() == {
        "code": 401,
        "message": "未登录或登录已过期",
        "data": None,
    }

    disabled = client.get("/api/orders", headers=auth_headers(6, 1))
    assert disabled.status_code == 401

    invalid_quantity = _create(client, auth_headers(1, 1), quantity=0)
    assert invalid_quantity.status_code == 400
    assert invalid_quantity.json()["code"] == 400

    invalid_code = client.post(
        "/api/orders/verify",
        json={"pickup_code": "123"},
        headers=auth_headers(2, 2),
    )
    assert invalid_code.status_code == 400

    invalid_status = client.get("/api/orders?status=9", headers=auth_headers(1, 1))
    assert invalid_status.status_code == 400
    assert invalid_status.json()["code"] == 400
