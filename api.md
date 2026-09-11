# FoodLink（食愿）后端接口文档 · 草案 V1.0

> 更新日期：2026-09-10
> 状态标记：✅ 已实现并验证 ｜ 🚧 草案（待实现）
> 本文档是前后端联调的**接口契约**，路径、字段、错误码均与前端 `api-integration.md` 及 `mock/vite-mock.js` 对齐。

---

## 一、通用约定

### 1.1 基础信息
| 项 | 约定 |
|---|---|
| Base URL（本地） | `http://localhost:8080` |
| Content-Type | `application/json; charset=utf-8` |
| 时间格式 | `yyyy-MM-dd HH:mm:ss` |
| 金额 | 数字（元，保留 2 位小数，如 `12.0`） |
| 角色 role | `1` 学生 ｜ `2` 商家 ｜ `3` 超管 |

### 1.2 统一响应
```json
{ "code": 0, "message": "success", "data": {} }
```
- `code = 0` 成功；非 0 失败，`message` 为可直接展示的提示文案。
- `data` 成功时返回业务数据，失败时为 `null`。

### 1.3 鉴权
除「公开」接口外，请求头需携带：
```
Authorization: Bearer <token>
```
- 登录成功返回 `data.token`，前端写入本地存储 key `shiyuan_token`。
- **鉴权失败返回 HTTP 401**（前端据此清理 token 并跳登录），无权限返回 HTTP 403。

### 1.4 错误码
| code | 含义 |
|---|---|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未登录 / Token 失效（HTTP 401） |
| 403 | 无权限（HTTP 403） |
| 404 | 资源不存在 |
| 20001 | 账号或密码错误 |
| 20002 | 账号已被禁用 |
| 20003 | 商家未通过审核 |
| 20004 | 忘记密码身份验证失败 |
| 20005 | 账号/学号已存在 |
| 20006 | 手机号已存在 |
| 40001 | 商品发布被风控拦截（通用） |
| 41001 | 风控-价格异常 |
| 41002 | 风控-违规内容（敏感词） |
| 41003 | 风控-有效期异常 |
| 50000 | 服务器内部错误 |

---

## 二、数据模型（6 张表）

### users
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键自增 |
| role | INTEGER | 1学生 2商家 3超管 |
| login_name | TEXT | 登录账号，唯一 |
| password | TEXT | BCrypt 哈希 |
| school / student_id | TEXT | 学生：学校/学号 |
| name | TEXT | 姓名（商家=店名） |
| phone | TEXT | 手机号 |
| avatar | TEXT | 头像（前端扩展） |
| preferences | JSON | `{"cuisine":[...],"taste":[...],"meal_time":[...]}` |
| taboo | JSON | `{"allergens":[...],"dislikes":[...]}` |
| monthly_budget | NUMERIC | 月生活费 |
| status | INTEGER | 1正常 0禁用 |

### merchants
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| user_id | INTEGER | 关联 users.id，唯一 |
| shop_name | TEXT | 店名 |
| license_img | TEXT | 营业执照 Base64 |
| location / lat / lng | TEXT/FLOAT | 店铺位置 |
| audit_status | INTEGER | 0待审核 1通过 2驳回 |

### products
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| merchant_id | INTEGER | 关联 merchants.id |
| title / description | TEXT | 标题/描述 |
| image | TEXT | 商品图（前端扩展） |
| category | TEXT | 简餐/饮品/烘焙/水果/其他 |
| original_price / discount_price | NUMERIC | 原价/折扣价 |
| quantity | INTEGER | 数量 |
| expire_time | DATETIME | 截止有效期 |
| business_open_time / business_close_time | TEXT | 每日开门/关门时间，格式 HH:mm |
| location / lat / lng | TEXT/FLOAT | 取货位置 |
| status | INTEGER | 1在售 0下架 2售罄 3风控拦截 |
| view_count / fav_count / order_count | INTEGER | 浏览/收藏/下单数 |
| risk_flag | INTEGER | 是否触发风控 |

### orders
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| user_id / product_id | INTEGER | 学生/商品 |
| pickup_code | TEXT | 6 位取货码，唯一 |
| status | INTEGER | 0待领取 1已领取 2过期 |
| picked_at | DATETIME | 领取时间 |

### behaviors
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| user_id / product_id | INTEGER | 用户/商品 |
| behavior_type | INTEGER | 1浏览 2收藏 3下单 4分享 |

### risk_logs
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键 |
| product_id / merchant_id | INTEGER | 商品/商家 |
| risk_type | INTEGER | 1价格 2敏感词 3有效期 |
| risk_detail | TEXT | 详情 |
| is_resolved | INTEGER | 0未处理 1已处理 |

---

## 三、接口清单

### 3.1 认证模块 ✅
| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/auth/login` | 统一登录 | 公开 |
| POST | `/api/auth/register` | 统一注册 | 公开 |
| POST | `/api/auth/reset-password` | 重置密码为 123456 | 公开 |

**POST /api/auth/login**
```json
// 请求
{ "login_name": "2021001", "password": "123456", "role": 1 }
// 响应 data
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1, "role": 1, "login_name": "2021001", "name": "张三",
    "avatar": "", "school": "澳门科技大学", "student_id": "2021001", "phone": "13800000000",
    "preferences": { "cuisine": ["川菜"], "taste": ["麻辣"], "meal_time": ["午餐"] },
    "taboo": { "allergens": ["花生"], "dislikes": ["香菜"] },
    "monthly_budget": 1500.0, "status": 1,
    "shop_name": "", "license_img": "", "audit_status": -1
  }
}
```
- 学生 `login_name`=学号，商家=自定义账号，超管=`admin`。
- 商家 `audit_status` 非 1 时返回 `20003`。

**POST /api/auth/register**
```json
// 学生（role=1），学号自动作为登录账号
{ "role": 1, "school": "澳门科技大学", "student_id": "2021001", "name": "张三", "phone": "13800000000", "password": "123456" }
// 商家（role=2）
{ "role": 2, "shop_name": "科大风味小厨", "license_img": "data:image/...", "location": "澳门科技大学学生餐厅取货点",
  "lat": 22.1496, "lng": 113.565, "login_name": "shop001", "password": "123456", "phone": "13811112222" }
```
- 学生响应 `data`：`{ "id": 3 }`；商家响应 `data`：`{ "id": 4, "audit_status": 0 }`。
- 账号冲突 `20005`，手机号冲突 `20006`。

**POST /api/auth/reset-password**
```json
// 学生
{ "role": 1, "student_id": "2021001", "name": "张三", "phone": "13800000000" }
// 商家
{ "role": 2, "login_name": "shop001", "shop_name": "XX风味小吃", "phone": "13811112222" }
```
- 验证失败 `20004`；成功响应 `data`：`{ "message": "密码已重置为123456" }`。

### 3.2 用户模块 ✅
| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/user/profile` | 获取个人资料 | Token |
| PUT | `/api/user/profile` | 修改个人资料 | Token |
| POST | `/api/user/behavior` | 记录行为 | Token |

**GET /api/user/profile** → `data` 为完整 user 对象（同登录）。
**PUT /api/user/profile**
```json
{ "name": "张三", "phone": "13800000000", "avatar": "",
  "preferences": {...}, "taboo": {...}, "monthly_budget": 1500.0 }
```
**POST /api/user/behavior**
```json
{ "product_id": 1, "behavior_type": 1 }   // 1浏览 2收藏 3下单 4分享
```

### 3.3 商品模块 ✅
| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/products` | 发布商品（触发 AI 风控） | 商家 |
| GET | `/api/products` | 商品列表（分页/筛选/排序） | Token |
| GET | `/api/products/recommend` | AI 个性化推荐首页 | Token |
| GET | `/api/products/guess-you-like` | 猜你喜欢（协同过滤） | Token |
| GET | `/api/products/{id}` | 商品详情（记录浏览） | Token |
| POST | `/api/products/{id}/favorite` | 收藏/取消收藏 | Token |
| PUT | `/api/products/{id}/offline` | 下架商品 | 商家/超管 |

**POST /api/products**
```json
{ "title": "水煮鱼片", "description": "...", "category": "简餐", "image": "",
  "original_price": "18.00", "discount_price": "8.80", "quantity": 10,
  "expire_time": "2026-09-10 23:00:00", "business_open_time": "08:00",
  "business_close_time": "22:00", "location": "澳门科技大学学生餐厅取货点", "lat": 22.1496, "lng": 113.565 }
```
- 风控拦截返回 `40001`/`41001`/`41002`/`41003`，商品以 `status=3` 入库并记 `risk_logs`。

**GET /api/products** — 参数：`page`/`size`/`category`/`status`/`sort`（`default|hot|new|price_asc|price_desc`）。
**GET /api/products/recommend?lat=30.1&lng=120.1** → 加权排序（距离0.25+偏好0.30+价格0.20+热度0.15+时效0.10），返回 Top20。
**GET /api/products/{id}** → `data` 含 `is_favorite` 与 `merchant: { shop_name }`。

**POST /api/products/{id}/favorite**
```json
{ "favorite": true }          // 请求：指定目标状态
// 响应 data：{ "favorite": true, "fav_count": 13 }
```

### 3.4 订单模块 🚧
| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/orders` | 学生下单（生成 6 位取货码） | 学生 |
| GET | `/api/orders` | 我的订单列表（学生/商家双视角） | 学生/商家 |
| GET | `/api/orders/summary` | 本月消费/经营统计 | 学生/商家 |
| PUT | `/api/orders/{id}/refund` | 付款后 5 分钟内取消并原路退款 | 学生 |
| GET | `/api/orders/refund-requests` | 查看本人食品问题退款申请 | 学生 |
| POST | `/api/orders/{id}/refund-request` | 实际领取后提交食品问题退款申请 | 学生 |
| PUT | `/api/orders/{id}/pickup` | 确认领取（核销取货码） | 商家/超管 |
| POST | `/api/orders/verify` | 按 6 位取货码核销 | 商家/超管 |

**订单对象结构**（前端 `orderView` 已约定，实现需一致）：
```json
{
  "id": 101, "product_id": 1, "product_title": "水煮鱼片 超值套餐", "product_image": "",
  "shop_name": "科大风味小厨", "original_price": "28.00", "price": "8.80", "total_amount": "8.80", "quantity": 1,
  "status": 0, "pickup_code": "483920", "expire_time": "2026-09-10 23:00:00",
  "business_open_time": "08:00", "business_close_time": "22:00",
  "pickup_deadline": "2026-09-09 22:00:00", "remaining_seconds": 16200,
  "refund_deadline": "2026-09-09 17:35:00", "refundable": true,
  "location": "澳门科技大学学生餐厅取货点", "created_at": "2026-09-09 17:30:00", "picked_at": null,
  "payment_status": "paid", "platform_fee_rate": "0.1%", "platform_fee": "0.01",
  "merchant_receivable": "8.79", "merchant_payout_status": "pending", "merchant_payout_at": null,
  "completion_type": null, "close_reason": null, "closed_at": null
}
```
- **POST** 请求：`{ "product_id": 1, "quantity": 1 }`；商品售罄/下架返回 `400`/`404`。
- **GET** 参数：`status`（0待领取/1已完成/2已关闭，不传返回全部），响应为订单数组。
- **PUT /pickup**：状态流转 `0→1`，记录 `picked_at`；下单应扣减 `products.quantity` 并写 `behaviors(3下单)`。
- **PUT /refund**：仅下单学生可在付款后 5 分钟内且尚未核销时调用；状态流转 `0→2`，`close_reason=student_refund`，恢复库存并原路退款。
- **食品问题售后**：超过 5 分钟不能自行退款。只有商家实际核销后，学生才可通过 `POST /{id}/refund-request` 提交 5 至 500 字问题说明及可选照片；未领取自动完成、食品期限已过和已退款订单不可申请。
- **领取截止**：取下单后的下一次 `business_close_time`；若 `expire_time` 更早则以商品有效期为准。关门先到时 `status=1`、`completion_type=auto_timeout`；食品期限先到时 `status=2`、`close_reason=product_expired`。两者均扣除 0.1% 服务费并结算给商家，不视为学生退款。
- **商家到账**：订单完成时收入实时记账，`merchant_payout_status` 从 `pending` 变为 `scheduled`，`merchant_payout_at` 为完成时间次日；到达该时间后状态为 `paid`。退款订单状态为 `refunded`。当前为微信支付对接演示逻辑。
- **商家端领取操作**：当前页面不要求商家手动输入取货码；`PUT /pickup` 与 `POST /verify` 保留给后续二维码扫码设备接入。

### 3.5 超管后台 🚧
| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/api/admin/merchants/pending` | 待审核商家列表 | 超管 |
| PUT | `/api/admin/merchants/{id}/audit` | 商家审核（通过/驳回） | 超管 |
| GET | `/api/admin/statistics` | 数据看板 | 超管 |
| GET | `/api/admin/risk-logs` | 风控日志列表 | 超管 |
| PUT | `/api/admin/users/{id}/status` | 用户禁用/启用 | 超管 |
| GET | `/api/admin/refund-requests` | 食品问题退款申请列表 | 超管 |
| PUT | `/api/admin/refund-requests/{id}/audit` | 通过退款或驳回申请 | 超管 |

退款审核请求为 `{ "audit_status": 1, "admin_remark": "凭证有效，同意退款" }`，其中 `audit_status` 为 `1` 通过、`2` 驳回。通过后订单流转为 `status=2`、`close_reason=admin_refund`，款项原路退回并冲回原商家结算；驳回后订单仍保持已结算。

**商家审核** 请求：`{ "audit_status": 1 }`（1通过 2驳回）。
**数据看板** 返回建议字段：总用户数、总订单数、贫困生领取统计、风控拦截统计、推荐点击率。

---

## 四、状态码枚举

| 字段 | 值 | 含义 |
|---|---|---|
| `users.status` | 1 / 0 | 正常 / 禁用 |
| `merchants.audit_status` | 0 / 1 / 2 | 待审核 / 通过 / 驳回 |
| `products.status` | 1 / 0 / 2 / 3 | 在售 / 下架 / 售罄 / 风控拦截 |
| `orders.status` | 0 / 1 / 2 | 待领取 / 已完成 / 已关闭（已过期或已退款） |
| `behaviors.behavior_type` | 1/2/3/4 | 浏览/收藏/下单/分享 |
| `risk_logs.risk_type` | 1/2/3 | 价格/敏感词/有效期 |

---

## 附：项目结构
```
backend/
├── app/
│   ├── main.py              # 应用入口（统一响应/异常处理/路由注册）
│   ├── config.py            # 全局配置（JWT 密钥/推荐参数等）
│   ├── database.py          # SQLAlchemy 连接与会话
│   ├── core/                # response(统一响应) security(JWT+BCrypt) deps(鉴权) serializers(序列化)
│   ├── models/entities.py   # 6 张表 ORM 模型
│   ├── schemas/dto.py       # Pydantic 请求体
│   ├── services/            # risk_control(风控) recommend(推荐) sensitive_words(敏感词库)
│   └── routers/             # auth / user / product
├── docs/api.md              # 本文档（接口草案）
├── init_db.py               # 建表 + 预置演示账号
├── run.py                   # 启动脚本（端口 8080）
├── requirements.txt         # 依赖
└── README.md                # 快速启动说明
```
