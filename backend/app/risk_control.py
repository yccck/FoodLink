"""AI 风控检测（规则引擎 + 敏感词库，纯本地，无 GPU/外网）。

商品发布时触发，检测价格 / 敏感词 / 有效期三类风险。
后续可平滑替换为 DeepSeek 模型，仅改 :func:`run_risk_check` 内部实现。
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Optional

from app.sensitive_words import check_sensitive
from app.timeutils import now_shanghai_naive

# 风控动作
BLOCK = "block"
WARN = "warn"
PASS = "pass"

# 风险类型（与 risk_logs.risk_type 对应）
RISK_PRICE = 1     # 价格异常
RISK_WORDS = 2     # 敏感词
RISK_EXPIRY = 3    # 有效期异常


def _check_price(original: Decimal, discount: Decimal):
    """价格检测：折扣价>原价 或 折扣价<=0 拦截；折扣幅度<1折 警告。"""
    if discount > original:
        return BLOCK, RISK_PRICE, "折扣价({})高于原价({})，疑似虚假折扣".format(discount, original)
    if discount <= 0:
        return BLOCK, RISK_PRICE, "折扣价必须大于 0"
    if original > 0 and discount < original * Decimal("0.1"):
        return WARN, RISK_PRICE, "折扣幅度异常（低于 1 折：{}/{}）".format(discount, original)
    return PASS, None, None


def _check_words(title: str, description: Optional[str]):
    """敏感词检测：命中即拦截。"""
    text = "{} {}".format(title or "", description or "")
    hits = check_sensitive(text)
    if hits:
        return BLOCK, RISK_WORDS, "命中敏感词：" + "、".join(hits)
    return PASS, None, None


def _check_expiry(expire_time):
    """有效期检测：已过期拦截；不足 1 小时警告（即将过期）。"""
    now = now_shanghai_naive()
    if expire_time <= now:
        return BLOCK, RISK_EXPIRY, "商品已过期，禁止发布"
    if expire_time - now < timedelta(hours=1):
        return WARN, RISK_EXPIRY, "商品有效期不足 1 小时，强制标注「即将过期」"
    return PASS, None, None


def run_risk_check(
    original: Decimal,
    discount: Decimal,
    title: str,
    description: Optional[str],
    expire_time,
):
    """综合风控检测。

    返回 ``(action, results)``：

    - ``action``：``'block'`` | ``'warn'`` | ``'pass'``
    - ``results``：``[{"risk_type": int, "risk_detail": str, "action": str}, ...]``
    """
    results = []
    blocked = False

    for fn, args in (
        (_check_price, (original, discount)),
        (_check_words, (title, description)),
        (_check_expiry, (expire_time,)),
    ):
        action, risk_type, detail = fn(*args)
        if action == PASS:
            continue
        results.append({"risk_type": risk_type, "risk_detail": detail, "action": action})
        if action == BLOCK:
            blocked = True

    if blocked:
        return BLOCK, results
    if any(r["action"] == WARN for r in results):
        return WARN, results
    return PASS, results
