from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from app.business_hours import calculate_pickup_deadline
from app.models import Order, Product, RefundApplication, WalletAccount
from app.timeutils import now_shanghai_naive


def _create_order(client, headers):
    response = client.post(
        "/api/orders",
        json={"product_id": 1, "quantity": 1},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]


def _submit_application(client, order_id, headers, reason="餐品有明显异味，无法正常食用"):
    return client.post(
        "/api/orders/{}/refund-request".format(order_id),
        json={"reason": reason, "evidence_image": "data:image/jpeg;base64,demo"},
        headers=headers,
    )


def test_quality_refund_requires_admin_approval_and_reverses_settlement(
    client, auth_headers, session_factory
):
    student_headers = auth_headers(1, 1)
    merchant_headers = auth_headers(2, 2)
    admin_headers = auth_headers(4, 3)
    created = _create_order(client, student_headers)

    picked = client.put(
        "/api/orders/{}/pickup".format(created["id"]),
        headers=merchant_headers,
    )
    assert picked.status_code == 200
    assert picked.json()["data"]["completion_type"] == "merchant_confirmed"

    submitted = _submit_application(client, created["id"], student_headers)
    assert submitted.status_code == 200
    application = submitted.json()["data"]
    assert application["status"] == 0
    assert application["order_id"] == created["id"]
    assert application["total_amount"] == "12.00"

    duplicate = _submit_application(client, created["id"], student_headers)
    assert duplicate.status_code == 400
    assert "已经提交" in duplicate.json()["message"]

    pending = client.get(
        "/api/admin/refund-requests?status=0", headers=admin_headers
    )
    assert pending.status_code == 200
    assert [item["id"] for item in pending.json()["data"]] == [application["id"]]

    approved = client.put(
        "/api/admin/refund-requests/{}/audit".format(application["id"]),
        json={"audit_status": 1, "admin_remark": "凭证有效，同意退款"},
        headers=admin_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == 1
    assert approved.json()["data"]["reviewed_at"] is not None

    order = client.get("/api/orders", headers=student_headers).json()["data"][0]
    assert order["status"] == 2
    assert order["close_reason"] == "admin_refund"
    assert order["payment_status"] == "refunded"
    assert order["platform_fee"] == "0.00"
    assert order["merchant_receivable"] == "0.00"

    student_summary = client.get(
        "/api/orders/summary", headers=student_headers
    ).json()["data"]
    merchant_summary = client.get(
        "/api/orders/summary", headers=merchant_headers
    ).json()["data"]
    assert student_summary["monthly_spending"] == "0.00"
    assert student_summary["monthly_order_count"] == 0
    assert merchant_summary["monthly_sales"] == "0.00"
    assert merchant_summary["monthly_income"] == "0.00"
    with session_factory() as db:
        assert db.get(WalletAccount, 2).balance == Decimal("0.00")


def test_rejected_quality_application_keeps_completed_order_settled(
    client, auth_headers, session_factory
):
    student_headers = auth_headers(1, 1)
    merchant_headers = auth_headers(2, 2)
    admin_headers = auth_headers(4, 3)
    created = _create_order(client, student_headers)
    client.put(
        "/api/orders/{}/pickup".format(created["id"]),
        headers=merchant_headers,
    )
    application = _submit_application(
        client, created["id"], student_headers
    ).json()["data"]

    missing_remark = client.put(
        "/api/admin/refund-requests/{}/audit".format(application["id"]),
        json={"audit_status": 2, "admin_remark": ""},
        headers=admin_headers,
    )
    assert missing_remark.status_code == 400

    rejected = client.put(
        "/api/admin/refund-requests/{}/audit".format(application["id"]),
        json={"audit_status": 2, "admin_remark": "凭证不足，请补充现场照片"},
        headers=admin_headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == 2

    order = client.get("/api/orders", headers=student_headers).json()["data"][0]
    assert order["status"] == 1
    assert order["payment_status"] == "settled"
    with session_factory() as db:
        assert db.get(WalletAccount, 2).balance == Decimal("11.99")
        assert db.get(RefundApplication, application["id"]).status == 2


def test_pending_or_no_show_orders_cannot_claim_food_quality_refund(
    client, auth_headers, session_factory
):
    student_headers = auth_headers(1, 1)
    created = _create_order(client, student_headers)

    pending = _submit_application(client, created["id"], student_headers)
    assert pending.status_code == 400
    assert "实际领取" in pending.json()["message"]

    with session_factory() as db:
        order = db.get(Order, created["id"])
        assert order is not None
        product = db.get(Product, order.product_id)
        assert product is not None
        now = now_shanghai_naive()
        order.created_at = now - timedelta(hours=2)
        product.business_close_time = (now - timedelta(hours=1)).strftime("%H:%M")
        deadline = calculate_pickup_deadline(
            order.created_at, product.expire_time, product.business_close_time
        )
        order.status = 1
        order.picked_at = deadline
        db.commit()

    no_show = _submit_application(client, created["id"], student_headers)
    assert no_show.status_code == 400
    assert "未按时领取" in no_show.json()["message"]


def test_refund_application_permissions(client, auth_headers):
    student_headers = auth_headers(1, 1)
    created = _create_order(client, student_headers)
    client.put(
        "/api/orders/{}/pickup".format(created["id"]),
        headers=auth_headers(2, 2),
    )

    other_student = _submit_application(
        client, created["id"], auth_headers(5, 1)
    )
    assert other_student.status_code == 403
    assert client.get(
        "/api/admin/refund-requests", headers=student_headers
    ).status_code == 403
    assert client.get(
        "/api/orders/refund-requests", headers=auth_headers(2, 2)
    ).status_code == 403
