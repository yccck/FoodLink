"""商家端个人中心 /api/merchant/profile 接口测试。"""

from __future__ import annotations


def test_merchant_profile_get(client, auth_headers):
    headers = auth_headers(2, 2)
    r = client.get("/api/merchant/profile", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0, body
    data = body["data"]
    assert data["shop_name"] == "甲店"
    assert data["location"] == "南门"
    assert data["name"] == "商家甲账号"
    assert data["phone"] == "13800000002"
    assert data["audit_status"] == 1
    assert data["categories"] == []
    assert data["pending"] is None


def test_merchant_profile_update_creates_pending(client, auth_headers):
    headers = auth_headers(2, 2)
    payload = {
        "shop_name": "甲店（新）",
        "name": "张三",
        "phone": "13900001111",
        "location": "南门二号",
        "categories": ["中式快餐", "甜品饮品"],
    }
    r = client.put("/api/merchant/profile", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()["data"]

    # 正式资料不变，修改进入 pending
    assert data["shop_name"] == "甲店"
    assert data["pending"] is not None
    assert data["pending"]["shop_name"] == "甲店（新）"
    assert data["pending"]["name"] == "张三"
    assert data["pending"]["phone"] == "13900001111"
    assert data["pending"]["categories"] == ["中式快餐", "甜品饮品"]

    # 再次 GET 依然能读到 pending
    r2 = client.get("/api/merchant/profile", headers=headers)
    assert r2.json()["data"]["pending"]["shop_name"] == "甲店（新）"


def test_merchant_profile_update_validation(client, auth_headers):
    headers = auth_headers(2, 2)

    # 缺字段 → 40002
    r = client.put(
        "/api/merchant/profile",
        json={"shop_name": "甲店", "name": "", "phone": "13900001111", "location": "南门"},
        headers=headers,
    )
    assert r.status_code == 400, r.status_code
    assert r.json()["code"] == 40002, r.text

    # 手机号格式错 → 40003
    r = client.put(
        "/api/merchant/profile",
        json={"shop_name": "甲店", "name": "张三", "phone": "12345", "location": "南门"},
        headers=headers,
    )
    assert r.status_code == 400, r.status_code
    assert r.json()["code"] == 40003, r.text


def test_merchant_profile_role_guard(client, auth_headers):
    # 学生访问 → 403
    r = client.get("/api/merchant/profile", headers=auth_headers(1, 1))
    assert r.status_code == 403, r.status_code

    # 超管访问 → 403
    r = client.get("/api/merchant/profile", headers=auth_headers(4, 3))
    assert r.status_code == 403, r.status_code

    # 未登录 → 401
    r = client.get("/api/merchant/profile")
    assert r.status_code == 401, r.status_code
