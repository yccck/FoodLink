"""AI 推荐模块：首页个性化推荐 + 猜你喜欢（协同过滤，纯 Python 计算）。

- 首页推荐：候选集 → 规则过滤（禁忌/预算）→ 加权精排（距离/偏好/价格/热度/时效）。
- 猜你喜欢：基于历史行为构建用户画像向量，余弦相似度找相似学生，推荐其喜欢的商品。
- 纯本地计算，无需训练模型；后续可切换 DeepSeek，接口结构不变。
"""
from __future__ import annotations

import json
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Behavior, Product, User
from app.timeutils import now_shanghai_naive


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    """经纬度球面距离（公里）。入参可为 Decimal，内部统一转 float。"""
    lat1, lng1, lat2, lng2 = float(lat1), float(lng1), float(lat2), float(lng2)
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _parse_json(text):
    """把 JSON 字符串字段解析为 dict，容错返回 {}。"""
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def _user_pref_words(user: User) -> set:
    words = set()
    prefs = _parse_json(user.preferences)
    for key in ("cuisine", "taste"):
        for w in (prefs.get(key) or []):
            words.add(str(w))
    return words


def _user_taboo_words(user: User) -> set:
    words = set()
    taboo = _parse_json(user.taboo)
    for key in ("allergens", "dislikes"):
        for w in (taboo.get(key) or []):
            words.add(str(w))
    return words


def _prod_text(p: Product) -> str:
    return "{} {} {}".format(p.title or "", p.description or "", p.category or "")


def recommend(user: User, db: Session, lat=None, lng=None) -> list:
    """首页个性化推荐：返回按综合分排序的 Top N（含 distance 与 match_tags）。"""
    products = db.scalars(
        select(Product).where(Product.status == 1, Product.risk_flag == 0)
    ).all()
    if not products:
        return []

    pref_words = _user_pref_words(user)
    taboo_words = _user_taboo_words(user)
    budget = float(user.monthly_budget or 0)

    max_hot = max((p.view_count + 2 * p.fav_count + 3 * p.order_count) for p in products) or 1
    max_hot = float(max_hot)

    now = now_shanghai_naive()
    scored = []
    for p in products:
        text = _prod_text(p)
        # 硬过滤：禁忌命中
        if any(w in text for w in taboo_words):
            continue
        # 硬过滤：价格超过月生活费预算比例
        if budget > 0 and float(p.discount_price) > budget * settings.budget_ratio:
            continue

        # 距离分（无位置给中性分）
        if lat is not None and lng is not None:
            dkm = haversine_km(lat, lng, p.lat, p.lng)
            dist_score = max(0.0, 1 - dkm / settings.nearby_km)
        else:
            dkm = None
            dist_score = 0.5

        # 偏好匹配分
        if pref_words:
            hits = [w for w in pref_words if w in text]
            pref_score = len(hits) / len(pref_words)
        else:
            pref_score = 0.0

        # 价格适配分
        if budget > 0:
            price_score = max(0.0, 1 - float(p.discount_price) / (budget * settings.budget_ratio))
        else:
            price_score = 0.5

        # 热度分（对数平滑）
        hot = p.view_count + 2 * p.fav_count + 3 * p.order_count
        hot_score = math.log(float(hot) + 1) / math.log(max_hot + 1)

        # 时效分（越临近过期越高，清仓优先级）
        remaining_h = (p.expire_time - now).total_seconds() / 3600.0
        expiry_score = max(0.0, min(1.0, 1 - remaining_h / settings.expiry_window_hours))

        total = (
            dist_score * 0.25
            + pref_score * 0.30
            + price_score * 0.20
            + hot_score * 0.15
            + expiry_score * 0.10
        )

        match_tags = []
        if pref_words:
            match_tags = [w for w in pref_words if w in text]
        if price_score > 0.7:
            match_tags.append("性价比高")
        if remaining_h <= 3:
            match_tags.append("限时特惠")

        scored.append({
            "product": p,
            "score": total,
            "distance": dkm,
            "match_tags": match_tags,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[: settings.recommend_top]


def _build_vector(user: User, db: Session) -> dict:
    """用户画像向量：偏好词 + 行为加权。"""
    vec = {}
    prefs = _parse_json(user.preferences)
    for key in ("cuisine", "taste"):
        for w in (prefs.get(key) or []):
            vec.setdefault(str(w), 0.0)
            vec[str(w)] += 1.0

    wmap = {1: 0.5, 2: 0.7, 3: 1.0, 4: 0.3}  # 浏览/收藏/下单/分享
    for b in db.scalars(select(Behavior).where(Behavior.user_id == user.id)).all():
        prod = db.get(Product, b.product_id)
        if not prod:
            continue
        text = _prod_text(prod)
        for w in list(vec.keys()):
            if w in text:
                vec[w] += wmap.get(b.behavior_type, 0.3)
    return vec


def _cosine(a: dict, b: dict) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def guess_you_like(user: User, db: Session) -> list:
    """猜你喜欢：协同过滤找相似学生，推荐他们收藏/下单的商品。

    返回 ``[(product, liked_weight), ...]``；冷启动回退到热门商品。
    """
    cur_vec = _build_vector(user, db)
    touched = {
        b.product_id
        for b in db.scalars(select(Behavior).where(Behavior.user_id == user.id)).all()
    }

    students = db.scalars(
        select(User).where(User.role == 1, User.id != user.id, User.status == 1)
    ).all()

    sims = []
    for s in students:
        sim = _cosine(cur_vec, _build_vector(s, db))
        if sim > 0:
            sims.append((s.id, sim))
    sims.sort(key=lambda x: x[1], reverse=True)
    top_ids = [sid for sid, _ in sims[: settings.similar_user_top]]

    # 冷启动：无相似用户 → 热门商品
    if not top_ids:
        hot = db.scalars(
            select(Product)
            .where(Product.status == 1, Product.risk_flag == 0)
            .order_by((Product.order_count + Product.fav_count).desc())
            .limit(settings.guess_top)
        ).all()
        return [(p, 0) for p in hot]

    # 收集相似用户 收藏/下单 的商品（下单权重高于收藏）
    cand = {}
    for sid in top_ids:
        rows = db.scalars(
            select(Behavior).where(
                Behavior.user_id == sid,
                Behavior.behavior_type.in_([2, 3]),
            )
        ).all()
        for b in rows:
            if b.product_id in touched:
                continue
            prod = db.get(Product, b.product_id)
            if not prod or prod.status != 1 or prod.risk_flag:
                continue
            w = 3 if b.behavior_type == 3 else 2
            cand[b.product_id] = cand.get(b.product_id, 0) + w

    ranked = sorted(cand.items(), key=lambda x: x[1], reverse=True)
    return [(db.get(Product, pid), w) for pid, w in ranked[: settings.guess_top]]
