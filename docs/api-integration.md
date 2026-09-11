# 食愿 · 页面与接口对接清单

> 版本：V1.0 ｜ 前端负责模块：认证登录注册 / 学生端个人中心
> 适用范围：前端（Uni-app）与后端（Spring Boot）共同遵循的接口契约。
> 说明：接口路径、字段命名尽量与 `FoodLink_readme_V1.0.docx` 保持一致；文档中标注“【前端扩展】”的字段为前端展示所需、由后端据需补齐，其余均按 Word 文档原约定。

---

## 一、通用约定

### 1. 基础信息
- **Base URL（本地）**：`http://localhost:8080`
- **Content-Type**：`application/json; charset=utf-8`
- **时间格式**：`yyyy-MM-dd HH:mm:ss`（如 `2026-09-10 18:00:00`）
- **金额**：`REAL`，单位元，保留 2 位小数
- **角色编号（role）**：`1` 学生 ｜ `2` 商家 ｜ `3` 超管

### 2. 响应统一封装
所有接口返回统一结构：
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```
- `code = 0` 表示成功；非 0 表示失败，`message` 为可直接展示给用户的提示文案。
- `data` 成功时返回业务数据，失败时可省略或为 `null`。

### 3. 错误码约定
| code | 含义 | 前端处理 |
| --- | --- | --- |
| 0 | 成功 | — |
| 400 | 请求参数错误 | 提示 `message` |
| 401 | 未登录 / Token 失效 | 清理本地 Token，跳转登录页 |
| 403 | 无权限（角色不匹配） | 提示无权限，跳转登录页 |
| 404 | 资源不存在 | 提示“商品/订单不存在” |
| 20001 | 账号或密码错误 | 提示 `message` |
| 20002 | 账号已被禁用 | 提示 `message` |
| 20003 | 商家未通过审核 | 提示“商家账号待审核/未通过，暂无法登录” |
| 20004 | 忘记密码身份验证失败 | 提示“验证信息不匹配” |
| 20005 | 账号/学号已存在 | 提示“该账号已注册” |
| 20006 | 手机号已存在 | 提示“该手机号已注册” |
| 40001 | 商品发布被风控拦截（通用） | 展示 `message`/`riskReason` |
| 41001 | 风控-价格异常 | 展示原因（如“折扣价不得高于原价”） |
| 41002 | 风控-违规内容（敏感词） | 展示命中的敏感词原因 |
| 41003 | 风控-有效期异常 | 展示“有效期过短/已过期” |
| 50000 | 服务器内部错误 | 提示“服务器繁忙，请稍后再试” |

### 4. 鉴权与 Token（前端负责）
- 登录成功后将 `data.token` 写入本地存储，key 统一为：`shiyuan_token`。
- 请求拦截器统一在 Header 追加：`Authorization: Bearer <token>`。
- 收到 `401` 时：清除 `shiyuan_token` 与本地用户信息，跳转登录页。
- 本地用户信息缓存 key：`shiyuan_user`（存登录/查询返回的 `data.user`）。

---

## 二、页面清单（前端两个模块）

| 页面 | 路由 | 主要接口 |
| --- | --- | --- |
| 登录页（角色 Tab） | `/pages/login/index` | POST `/api/auth/login` |
| 学生注册页 | `/pages/register/student` | POST `/api/auth/register` |
| 商家注册页 | `/pages/register/merchant` | POST `/api/auth/register`（含地图选点） |
| 忘记密码页 | `/pages/login/forgot` | POST `/api/auth/reset-password` |
| 个人中心页 | `/pages/user/index` | GET `/api/user/profile` |
| 资料修改页 | `/pages/user/profile-edit` | GET + PUT `/api/user/profile` |
| 我的订单列表 | `/pages/order/list` | GET `/api/orders`、GET `/api/orders/summary`、PUT `/api/orders/{id}/refund` |
| 商品详情页 | `/pages/product/detail` | GET `/api/products/{id}`、POST `/api/products/{id}/favorite`、POST `/api/orders`、POST `/api/user/behavior` |
| 取货凭证码展示页 | `/pages/order/pickup` | 下单成功后接收订单对象直接展示 |

---

## 三、模块一：登录与注册

### 3.1 统一登录
```
POST /api/auth/login      权限：公开
```

请求体：
```json
{
  "login_name": "2021001",
  "password": "123456",
  "role": 1
}
```
- `role`：1 学生 ｜ 2 商家 ｜ 3 超管（与登录页 Tab 对应）。
- 学生 `login_name` = 学号；商家 = 自定义账号；超管 = `admin`。

响应 `data.user`（字段与 `users`/`merchants` 表对应）：
```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "role": 1,
    "login_name": "2021001",
    "name": "张三",
    "avatar": "",                      /* 【前端扩展】头像 */
    "school": "澳门科技大学",
    "student_id": "2021001",
    "phone": "13800000000",
    "preferences": { "cuisine": ["川菜"], "taste": ["麻辣"], "meal_time": ["午餐", "晚餐"] },
    "taboo": { "allergens": ["花生"], "dislikes": ["香菜"] },
    "monthly_budget": 1500.0,
    "status": 1,
    "shop_name": "",                    /* 商家时有值 */
    "license_img": "",                  /* 商家时有值 */
    "audit_status": -1                  /* 商家时有值：0待审核 1通过 2驳回 */
  }
}
```
- 商家登录：若 `audit_status = 0/2`，后端返回 `20003`，`message` 提示“账号待审核或未通过”。超管无 `audit_status`（可省略或置 -1）。
- 特殊错误：`20001` 账号或密码错误；`20002` 账号被禁用。

### 3.2 统一注册
```
POST /api/auth/register    权限：公开
```
按 `role` 区分注册主体。

**学生注册（role=1）**，学号自动作为登录账号：
```json
{
  "role": 1,
  "school": "澳门科技大学",
  "student_id": "2021001",
  "name": "张三",
  "phone": "13800000000",
  "password": "123456"
}
```
响应 `data`：`{ "id": 3 }`。前端成功后跳转登录页并自动填入学号。

**商家注册（role=2）**：
```json
{
  "role": 2,
  "shop_name": "XX风味小吃",
  "license_img": "data:image/jpeg;base64,...",   /* 拍照/上传，Base64 */
  "location": "澳门科技大学学生餐厅取货点",       /* 地图选点文字地址 */
  "lat": 22.149600,
  "lng": 113.565000,
  "login_name": "shop001",
  "password": "123456"
}
```
- `lat/lng` 由前端地图选点 SDK 获取并传参。
- 响应 `data`：`{ "id": 4, "audit_status": 0 }`。前端提示“提交成功，等待商家资质审核”，然后跳转登录页。
- 账号冲突返回 `20005`，手机号冲突返回 `20006`。

### 3.3 忘记密码
```
POST /api/auth/reset-password   权限：公开
```
身份验证通过后，密码重置为 `123456`。

**学生（role=1）**：
```json
{ "role": 1, "student_id": "2021001", "name": "张三", "phone": "13800000000" }
```
**商家（role=2）**：
```json
{ "role": 2, "login_name": "shop001", "shop_name": "XX风味小吃", "phone": "13811112222" }
```
- 验证失败返回 `20004`。
- 成功响应 `data`：`{ "message": "密码已重置为123456" }`，前端提示后跳转登录页。

---

## 四、模块二：学生端个人中心

### 4.1 获取个人资料
```
GET /api/user/profile    权限：需 Token（学生）
```
响应 `data`：即登录接口中的 `user` 对象（同上），含 `preferences` / `taboo` / `monthly_budget`。

### 4.2 修改个人资料
```
PUT /api/user/profile    权限：需 Token（学生）
```
请求体（仅提交需要修改的字段）：
```json
{
  "name": "张三",
  "phone": "13800000000",
  "avatar": "",            /* 【前端扩展】可选 */
  "preferences": { "cuisine": ["川菜", "粤菜"], "taste": ["麻辣", "清淡"], "meal_time": ["早餐", "午餐", "晚餐", "夜宵"] },
  "taboo": { "allergens": ["花生", "海鲜"], "dislikes": ["香菜"] },
  "monthly_budget": 1500.0,
  "school": "澳门科技大学",
  "student_id": "2021001"
}
```
> 注意：`student_id`/`school` 一般不允许改，仅作占位说明；若后端禁止修改请返回 `400`。
响应 `data`：更新后的 `user` 对象。前端刷新个人中心页数据。

### 4.3 商品详情
```
GET /api/products/{id}    权限：需 Token
```
> 访问该接口即记录一次浏览行为（等价 `POST /api/user/behavior` type=1）。

响应 `data`：
```json
{
  "id": 1,
  "title": "水煮鱼片 超值套餐",
  "description": "...",
  "category": "简餐",
  "image": "",                     /* 【前端扩展】商品图，可选 */
  "original_price": "28.00",
  "discount_price": "8.80",
  "quantity": 10,
  "expire_time": "2026-09-10 23:00:00",
  "business_open_time": "08:00",
  "business_close_time": "22:00",
  "location": "澳门科技大学学生餐厅取货点",
  "lat": 22.149600,
  "lng": 113.565000,
  "status": 1,
  "view_count": 96,
  "fav_count": 12,
  "order_count": 8,
  "distance": 0.3,
  "is_favorite": false,            /* 【前端扩展】当前用户是否已收藏，控制收藏按钮态 */
  "merchant": { "shop_name": "XX风味小吃" }
}
```

### 4.4 收藏 / 取消收藏
```
POST /api/products/{id}/favorite   权限：需 Token
```
请求体明确目标状态：
```json
{ "favorite": true }
```
- `true` 收藏，`false` 取消收藏。（也可约定前端仅做 toggle、body 可传空对象，以后端实现为准，建议本方式明确无歧义。）
响应 `data`：
```json
{ "favorite": true, "fav_count": 13 }
```

### 4.5 下单（生成取货码）
```
POST /api/orders    权限：需 Token（学生）
```
请求体：
```json
{ "product_id": 1, "quantity": 1 }
```
响应 `data`（返回完整订单，含 6 位取货码，供前端跳转凭证页展示）：
```json
{
  "id": 101,
  "product_id": 1,
  "product_title": "水煮鱼片 超值套餐",
  "product_image": "",
  "shop_name": "科大风味小厨",
  "original_price": "28.00",
  "price": "8.80",
  "total_amount": "8.80",
  "quantity": 1,
  "status": 0,
  "pickup_code": "483920",
  "expire_time": "2026-09-10 23:00:00",
  "business_open_time": "08:00",
  "business_close_time": "22:00",
  "pickup_deadline": "2026-09-09 22:00:00",
  "remaining_seconds": 16200,
  "refund_deadline": "2026-09-09 17:35:00",
  "refundable": true,
  "location": "澳门科技大学学生餐厅取货点",
  "created_at": "2026-09-09 17:30:00",
  "picked_at": null,
  "payment_status": "paid",
  "platform_fee_rate": "0.1%",
  "platform_fee": "0.01",
  "merchant_receivable": "8.79",
  "completion_type": null,
  "close_reason": null,
  "closed_at": null
}
```
- 商品已售罄/下架则返回 `404` 或 `400`，前端提示。
- 领取截止为下单后的下一次商家关门时间；若商品更早到期，则以 `expire_time` 为准。
- `refund_deadline` 为付款后 5 分钟与领取截止时间中的较早值；仅 `refundable=true` 时显示“申请退款”。

### 4.6 我的订单列表
```
GET /api/orders    权限：需 Token（学生）
```
查询参数（可选）：
- `status`：`0` 待领取 ｜ `1` 已完成 ｜ `2` 已关闭；不传返回全部。

响应 `data`（数组）：
```json
[
  {
    "id": 101,
    "product_id": 1,
    "product_title": "水煮鱼片 超值套餐",
    "product_image": "",
    "shop_name": "科大风味小厨",
    "price": "8.80",
    "quantity": 1,
    "status": 0,
    "pickup_code": "483920",
    "expire_time": "2026-09-10 23:00:00",
    "business_open_time": "08:00",
    "business_close_time": "22:00",
    "pickup_deadline": "2026-09-09 22:00:00",
    "remaining_seconds": 16200,
    "refund_deadline": "2026-09-09 17:35:00",
    "refundable": true,
    "created_at": "2026-09-09 17:30:00",
    "picked_at": null,
    "payment_status": "paid",
    "close_reason": null,
    "closed_at": null
  }
]
```
前端按 `status` 做 Tab 筛选展示。

#### 4.6.1 学生限时退款
```
PUT /api/orders/{id}/refund    权限：需 Token（下单学生）
```
- 仅订单创建后 5 分钟内且 `status=0` 时允许；成功后恢复库存并原路退款。
- 成功状态为 `status=2`、`close_reason=student_refund`、`payment_status=refunded`。
- 超过 5 分钟后，因商品已为学生保留，接口拒绝自行退款；商家关门或食品领取期限到达后正常结算给商家。
- 关门先到：`status=1`、`completion_type=auto_timeout`；食品期限先到：`status=2`、`close_reason=product_expired`。两者不是退款。

#### 4.6.2 食品问题退款审核
```
GET  /api/orders/refund-requests              权限：需 Token（学生）
POST /api/orders/{id}/refund-request          权限：需 Token（下单学生）
GET  /api/admin/refund-requests               权限：需 Token（超管）
PUT  /api/admin/refund-requests/{id}/audit    权限：需 Token（超管）
```
- 只有商家实际核销、学生领取食品后，才可提交食品质量问题申请；请求体为 `{ "reason": "至少 5 字的问题说明", "evidence_image": "可选图片 URL 或 Base64" }`。
- 管理员审核请求为 `{ "audit_status": 1, "admin_remark": "审核说明" }`，`1` 通过、`2` 驳回，驳回时必须填写说明。
- 通过后订单为 `status=2`、`close_reason=admin_refund`、`payment_status=refunded`，原商家结算同步冲回；驳回则订单保持已结算。
- `completion_type=auto_timeout` 的未领取订单和 `close_reason=product_expired` 的食品期限已过订单均不可申请退款。

### 4.7 记录用户行为（补充）
```
POST /api/user/behavior   权限：需 Token
```
```json
{ "product_id": 1, "behavior_type": 1 }
```
- `behavior_type`：1 浏览 ｜ 2 收藏 ｜ 3 下单 ｜ 4 分享。
- 浏览行为通常由商品详情接口自动记录；收藏/下单由对应接口内部记录。此接口主要用于分享等补充行为，可做冗余上报（不阻塞下单流程）。

---


### 4.8 首页推荐（学生端首页流）
小红书式双栏推荐流，后端按 AI 个性化排序返回，前端只需渲染。区分标签由后端返回的 `recommend_type` 决定。

```
GET /api/products/recommend   权限：需 Token（学生）
```
查询参数（分页/上拉加载）：
- `page`：页码，从 1 开始。
- `pageSize`：每页数量，建议 6~10。

响应 `data`：
```json
{
  "recommend_reason": "基于你的饮食偏好（川菜、麻辣）和月生活费¥1500推荐",
  "list": [ { "商品卡片字段，见下" } ],
  "total": 10,
  "page": 1,
  "page_size": 6,
  "has_more": true
}
```

`list[]` 元素 = 商品卡片字段（同商品详情，另含）：
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `recommend_type` | string | `''` 首页综合 ｜ `guess` 猜你喜欢 ｜ `prefer` 为你优选 |
| `distance` | number | 距离（km） |
| `gradient` / `emoji` | string | 【前端扩展·占位图】可选，无图时前端用色块+emoji 占位 |

前端标签映射：
| `recommend_type` | 图片右下角标签 |
| --- | --- |
| `guess` | 猜你喜欢（基于历史行为·协同过滤） |
| `prefer` | 为你优选（基于填报资料·画像匹配） |
| `''` 或其他 | 不显示标签 |

补充接口（供“猜你喜欢”独立栏目复用）：
```
GET /api/products/guess-you-like   权限：需 Token（学生）
```
响应 `data` 同上，仅返回来自协同过滤的商品。

> 分页/刷新约定：前端“上拉到底”按 `page+1` 追加，`has_more=false` 停止；“下拉刷新”重置到 `page=1`。
> AI 个性化由后端 DeepSeek 计算，前端不涉及 key；接口结构与字段保持不变。

### 4.9 商家端接口（登录商家 role=2，需 Token）
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/products/mine | 我的商品列表（product card 数组） |
| POST | /api/products | 发布商品，填写 `business_open_time`/`business_close_time`；实时触发 AI 风控 |
| PUT | /api/products/{id}/offline | 下架/上架切换，返回更新后的商品卡 |
| GET | /api/orders | 商家视角：订单附带学生信息 `student_name/student_id/phone` |
| GET | /api/orders/summary | 本月销售额、销量、订单、服务费和净收入 |
| PUT | /api/orders/{id}/pickup | 核销领取（照 `orders.status` 0→1，记 picked_at） |
| POST | /api/orders/verify | 按取货码核销，body `{ "pickup_code": "6位" }` |

**发布风控返回**（前端直接展示 `message`）：
- `41001` 价格异常（折扣价 ≥ 原价）
- `41002` 命中违禁词
- `41003` 距过期不足 30 分钟

### 4.10 超管端接口（登录超管 role=3，需 Token）
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/admin/merchants/pending | 待审核商家列表（含店铺/营业执照/账号/电话/经纬度） |
| PUT | /api/admin/merchants/{id}/audit | 审核，body `{ "audit_status": 1|2, "reason": "" }` |
| GET | /api/admin/risk-logs?resolved=0\|1 | 风控日志列表（默认全部，可按处理状态过滤） |
| PUT | /api/admin/risk-logs/{id}/resolve | 误判恢复，body `{ "restore": true }`；恢复后商品重新上架 |
| GET | /api/admin/statistics | 数据看板聚合数据 |

**`GET /api/admin/statistics` 响应 `data`**：
```json
{
  "total_users": 5, "total_orders": 5,
  "student_count": 2, "merchant_count": 2, "admin_count": 1,
  "pending_merchants": 1,
  "help": { "low_income_user_count": 1, "pickup_count": 3, "pending_count": 1, "total_fav": 86 },
  "risk": { "total": 3, "resolved": 1, "active": 2 },
  "users_by_role": [ { "label": "学生", "value": 2 } ],
  "orders_by_day": [ { "date": "2026-09-04", "count": 0 } ],
  "risk_by_type": [ { "label": "价格异常", "value": 1 } ]
}
```
## 五、状态码速查（前端 UI 映射）

| 状态码/字段 | 值 | 前端文案 |
| --- | --- | --- |
| `orders.status` | 0 | 待领取 |
| `orders.status` | 1 | 已领取 |
| `orders.status` | 2 | 已关闭；结合 `close_reason` 显示“已过期”或“已退款” |
| `products.status` | 1 | 在售 |
| `products.status` | 0 | 已下架 |
| `products.status` | 2 | 售罄 |
| `products.status` | 3 | 风控拦截 |
| `merchants.audit_status` | 0 | 待审核 |
| `merchants.audit_status` | 1 | 已通过 |
| `merchants.audit_status` | 2 | 已驳回 |

---

## 六、需要后端确认的前端扩展字段

以下字段在 Word 文档未定义，但前端页面展示需要，请后端在后端同步实现时一并补充：

| 字段 | 出现位置 | 说明 |
| --- | --- | --- |
| `user.avatar` | 用户对象 | 个人中心头像 |
| `product.image` | 商品详情/订单 | 商品图（可用于上传或占位图），单选卡可退化为空 |
| `product.is_favorite` | 商品详情 | 当前用户收藏态，控制收藏按钮 |
| `order.product_image` | 订单列表/凭证页 | 商品缩略图 |
| 收藏/下单行为冗余 | — | 是否由 `favorite`/`orders` 接口内部记录 `behaviors`，需后端明确 |

---

## 附录：全量接口速查（含商家端/超管端，供后端对照）

> 以下路径均与 Word 文档第 4 节保持一致。

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | /api/auth/login | 统一登录 | 公开 |
| POST | /api/auth/register | 统一注册 | 公开 |
| POST | /api/auth/reset-password | 重置密码 | 公开 |
| GET | /api/user/profile | 获取个人信息 | Token |
| PUT | /api/user/profile | 修改个人资料 | Token |
| POST | /api/user/behavior | 记录行为 | Token |
| POST | /api/products | 商家发布（触发 AI 风控） | 商家 |
| GET | /api/products/nearby | 附近推荐 | Token |
| GET | /api/products/recommend | AI 个性化首页推荐 | Token |
| GET | /api/products/guess-you-like | 猜你喜欢（协同过滤/DeepSeek） | Token |
| GET | /api/products/{id} | 商品详情（记录浏览） | Token |
| POST | /api/products/{id}/favorite | 收藏/取消收藏 | Token |
| PUT | /api/products/{id}/offline | 下架商品 | 商家/超管 |
| POST | /api/orders | 下单（生成取货码） | 学生 |
| GET | /api/orders | 我的订单列表 | 学生/商家 |
| GET | /api/orders/summary | 本月订单与经营统计 | 学生/商家 |
| PUT | /api/orders/{id}/refund | 5 分钟内取消并原路退款 | 学生 |
| GET | /api/orders/refund-requests | 查看本人食品问题退款申请 | 学生 |
| POST | /api/orders/{id}/refund-request | 提交食品问题退款申请 | 学生 |
| PUT | /api/orders/{id}/pickup | 确认领取 | 商家/超管 |
| GET | /api/admin/merchants/pending | 待审核商家列表 | 超管 |
| PUT | /api/admin/merchants/{id}/audit | 商家审核 | 超管 |
| GET | /api/admin/statistics | 数据看板 | 超管 |
| GET | /api/admin/risk-logs | 风控日志列表 | 超管 |
| GET | /api/admin/refund-requests | 食品问题退款申请列表 | 超管 |
| PUT | /api/admin/refund-requests/{id}/audit | 审核食品问题退款 | 超管 |
| GET | /api/products/mine | 我的商品列表 | 商家 |
| POST | /api/orders/verify | 按取货码核销 | 商家/超管 |
| PUT | /api/admin/risk-logs/{id}/resolve | 误判恢复 | 超管 |

> 注：AI 风控与 AI 个性推荐将改用 DeepSeek 模型实现，`key` 最后再配。接口路径与返回结构不变，前端无需改动。
