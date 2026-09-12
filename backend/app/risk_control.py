"""AI 风控检测（规则引擎 + 敏感词库 + 可选的大模型语义审核）。

商品发布时触发，检测价格 / 敏感词 / 有效期三类风险。

两种模式：
- **规则引擎**（:func:`run_risk_check`）：纯本地、零延迟、结果确定，永远可用；
- **AI 语义审核**（:func:`decide_product_risk`，走 app/ai_risk.py 的 OpenAI 兼容接口）：
  在规则之上再让大模型读一遍商品文案，能识别规则词库抓不到的夸大宣传 / 诱导表述。
  配置了 ``FOODLINK_AI_API_KEY`` 才启用；AI 不可用时自动回退，不影响发布流程。
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app import ai_risk
from app.ai_risk import AiUnavailable
from app.sensitive_words import check_sensitive
from app.timeutils import now_shanghai_naive

# 风控动作
BLOCK = "block"
WARN = "warn"
PASS = "pass"

# 风控类型（与 risk_logs.risk_type 对应）
RISK_PRICE = 1     # 价格异常
RISK_WORDS = 2     # 敏感词
RISK_EXPIRY = 3    # 有效期异常

# 风控来源（写进 risk_logs.risk_source，前端据此打标签）
SOURCE_RULE = "rule"   # 本地规则引擎
SOURCE_AI = "ai"       # 大模型语义审核


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


def _merge_ai_verdict(verdict: Dict[str, Any], results: List[Dict[str, Any]]) -> None:
    """把 AI 判定并入规则结果（原地修改 results）。

    同类型时 AI 的说明更完整（会写明命中的词/数值），所以覆盖规则文案并标记来源为 AI；
    AI 额外发现的风险类型则追加一条，规则结果作为确定性兜底保留。
    """
    risk_type = verdict.get("risk_type") or RISK_WORDS
    ai_entry = {
        "risk_type": risk_type,
        "risk_detail": verdict.get("risk_detail") or "",
        "action": verdict.get("action") or WARN,
        "risk_source": SOURCE_AI,
        "confidence": verdict.get("confidence", 0.0),
        "suggestions": verdict.get("suggestions") or [],
        "ai_model": verdict.get("model", ""),
    }
    for index, item in enumerate(results):
        if item["risk_type"] == risk_type:
            # AI 判 pass 时不改动规则结果；否则用 AI 的说明替换（保留规则的严重级别下限）
            if verdict["action"] == PASS:
                return
            merged = dict(item)
            merged.update(
                {
                    "risk_detail": ai_entry["risk_detail"] or item["risk_detail"],
                    "risk_source": SOURCE_AI,
                    "confidence": ai_entry["confidence"],
                    "suggestions": ai_entry["suggestions"],
                    "ai_model": ai_entry["ai_model"],
                }
            )
            if item["action"] == BLOCK:
                merged["action"] = BLOCK  # 规则已拦截就不因 AI 判 warn 而降级
            results[index] = merged
            return
    if verdict["action"] != PASS:
        results.append(ai_entry)


def decide_product_risk(
    *,
    original: Decimal,
    discount: Decimal,
    title: str,
    description: Optional[str] = None,
    expire_time: Any = None,
    quantity: Optional[int] = None,
    category: Optional[str] = None,
    now: Any = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """规则引擎 + AI 语义审核的综合判定（发布商品时调用）。

    返回 ``(action, results)``，其中每个 result 额外带 ``risk_source``（rule/ai），
    AI 命中时还会带 ``confidence`` / ``suggestions`` / ``ai_model``。
    AI 未配置或调用失败时等价于纯规则引擎的结果，不会抛异常。
    """
    rule_action, rule_results = run_risk_check(
        original, discount, title, description, expire_time
    )
    results: List[Dict[str, Any]] = [
        dict(item, risk_source=SOURCE_RULE) for item in rule_results
    ]

    if ai_risk.is_enabled():
        moment = now or now_shanghai_naive()
        try:
            verdict = ai_risk.ai_check_product(
                title=title,
                description=description,
                original_price=original,
                discount_price=discount,
                quantity=quantity,
                expire_time=expire_time,
                category=category,
                now=moment,
            )
        except AiUnavailable:
            verdict = None
        if verdict is not None:
            _merge_ai_verdict(verdict, results)

    if any(item["action"] == BLOCK for item in results):
        return BLOCK, results
    if results:
        return WARN, results
    return PASS, results


def ai_review_product(
    *,
    title: str,
    description: Optional[str],
    original: Decimal,
    discount: Decimal,
    expire_time: Any = None,
    quantity: Optional[int] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """只跑一次 AI 语义审核（管理员端「AI 复核」使用），不做规则兜底。

    AI 不可用时抛 :class:`app.ai_risk.AiUnavailable`，由调用方转成业务错误。
    """
    return ai_risk.ai_check_product(
        title=title,
        description=description,
        original_price=original,
        discount_price=discount,
        quantity=quantity,
        expire_time=expire_time,
        category=category,
        now=now_shanghai_naive(),
    )
