# FoodLink Backend

FoodLink 的 Python 公共后端。当前已完成订单模块，其他同学可以继续在同一个 `app` 中增加认证、商品和管理模块。

## 技术栈

- Python 3.9+
- FastAPI
- SQLAlchemy 2
- SQLite
- JWT（HS256）
- Swagger UI：`/doc.html`

## 第一次启动

在 `backend` 目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

启动后访问：

- 健康检查：<http://localhost:8080/api/health>
- Swagger 接口文档：<http://localhost:8080/doc.html>
- OpenAPI JSON：<http://localhost:8080/openapi.json>

数据库默认创建在 `backend/data/foodlink.db`，该文件已被 Git 忽略。

## 订单接口

- `POST /api/orders`：学生下单，原子扣减库存并生成唯一 6 位数字取货码
- `GET /api/orders?status=0`：学生查看本人订单，商家查看本店订单
- `PUT /api/orders/{id}/pickup`：商家或管理员按订单 ID 核销
- `POST /api/orders/verify`：商家或管理员按取货码核销

订单状态：`0` 待领取、`1` 已领取、`2` 已过期。待领取订单在查询或核销时会根据商品有效期自动更新为已过期。

## 接口约定

- 请求和响应字段统一使用 `snake_case`。
- 时间统一为 `yyyy-MM-dd HH:mm:ss`，时区为 `Asia/Shanghai`。
- 数据库金额使用 `DECIMAL(10,2)`；API 将金额序列化为两位小数字符串，例如 `"12.00"`，避免浮点精度损失。
- 所有响应统一为 `{ "code": 0, "message": "success", "data": ... }`。
- `code = 0` 表示成功，其他值表示失败。
- 身份、角色和商家归属只从 JWT 与数据库读取，不接收请求体传入的用户身份。

## 与认证模块衔接

JWT 使用 `Authorization: Bearer <token>`。Token 至少包含：

```json
{
  "sub": "1",
  "user_id": 1,
  "role": 1,
  "exp": 1789030800
}
```

`sub` 为字符串形式的用户 ID，`role` 为 `1` 学生、`2` 商家、`3` 管理员。认证同学可以直接复用 `app.auth.create_access_token`，并让登录接口与本项目使用相同的 `FOODLINK_JWT_SECRET`。

## Swagger 演示数据

新数据库可执行一次：

```bash
python -m scripts.seed_demo
python -m scripts.create_dev_token --user-id 1 --role 1
```

把第二条命令输出的 Token 填进 Swagger 右上角 `Authorize`，即可调试订单接口。商家和管理员演示账号的 ID 会由种子脚本打印。

## 测试

```bash
pytest
```
