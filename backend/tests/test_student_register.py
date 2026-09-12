"""学生注册：仅姓名必填，其余字段（学号/手机号/密码/学校）系统随机生成且唯一。"""


def test_student_register_only_name(client):
    r = client.post("/api/auth/register", json={"role": 1, "name": "张三"})
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["student_id"], "应回显系统生成的学号"
    assert d["password"], "应回显系统生成的密码"
    assert len(d["student_id"]) == 10, "学号=入学年份(4)+随机(6)"
    assert d["student_id"][:4].isdigit()
    assert len(d["password"]) == 8
    # 可用生成的凭证登录
    login = client.post(
        "/api/auth/login",
        json={"login_name": d["student_id"], "password": d["password"], "role": 1},
    )
    assert login.status_code == 200 and login.json()["code"] == 0


def test_student_register_two_names_unique(client):
    a = client.post("/api/auth/register", json={"role": 1, "name": "甲"}).json()["data"]
    b = client.post("/api/auth/register", json={"role": 1, "name": "乙"}).json()["data"]
    assert a["student_id"] != b["student_id"]
    assert a["phone"] != b["phone"]


def test_student_register_requires_name(client):
    r = client.post("/api/auth/register", json={"role": 1})
    assert r.json()["code"] == 400


def test_student_register_uses_provided_fields(client):
    r = client.post(
        "/api/auth/register",
        json={
            "role": 1,
            "name": "李四",
            "student_id": "2099010001",
            "password": "abc12345",
            "school": "测试大学",
        },
    )
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["student_id"] == "2099010001"
    assert d["password"] == "abc12345"
    login = client.post(
        "/api/auth/login",
        json={"login_name": "2099010001", "password": "abc12345", "role": 1},
    )
    assert login.json()["code"] == 0
