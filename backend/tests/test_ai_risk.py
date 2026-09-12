"""AI 风控（大模型语义审核）测试。

约定：测试环境不联网（conftest 已把 FOODLINK_AI_API_KEY 置空），
所有 AI 分支都通过 monkeypatch ``app.ai_risk._chat`` / ``is_enabled`` 注入假响应。
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from app import ai_risk, risk_control
from app.models import Product, RiskLog
from app.timeutils import now_shanghai_naive

AI_BLOCK_JSON = json.dumps(
    {
        "action": "block",
        "risk_type": 2,
        "risk_detail": "商品名含「特效」，属功效夸大用语，不得使用",
        "confidence": 0.92,
        "suggestions": ["去掉「特效」二字", "改为「冰镇降温套餐」"],
    },
    ensure_ascii=False,
)

AI_PASS_JSON = json.dumps(
    {
        "action": "pass",
        "risk_type": None,
        "risk_detail": "",
        "confidence": 0.88,
        "suggestions": [],
    },
    ensure_ascii=False,
)


def _enable_fake_ai(monkeypatch, payload: str) -> None:
    monkeypatch.setattr(ai_risk, "is_enabled", lambda: True)
    monkeypatch.setattr(ai_risk, "_chat", lambda *args, **kwargs: payload)


# ------------------------------------------------------------------ 引擎层


def test_rule_engine_only_when_ai_disabled():
    """未配置 AI 时走纯规则引擎，结果带 risk_source=rule。"""
    assert ai_risk.is_enabled() is False
    action, results = risk_control.decide_product_risk(
        original=Decimal("20.00"),
        discount=Decimal("22.00"),
        title="超值双拼套餐",
        description="折扣价高于原价",
        expire_time=now_shanghai_naive() + risk_control.timedelta(hours=6),
    )
    assert action == risk_control.BLOCK
    assert results[0]["risk_type"] == risk_control.RISK_PRICE
    assert results[0]["risk_source"] == risk_control.SOURCE_RULE


def test_ai_verdict_overrides_rule_detail(monkeypatch):
    """AI 命中同一风险类型时，用 AI 的结论替换规则文案并标记来源。"""
    _enable_fake_ai(monkeypatch, AI_BLOCK_JSON)
    action, results = risk_control.decide_product_risk(
        original=Decimal("20.00"),
        discount=Decimal("9.00"),
        title="特效降温套餐",
        description="含违禁夸大宣传词",
        expire_time=now_shanghai_naive() + risk_control.timedelta(hours=4),
    )
    assert action == risk_control.BLOCK
    assert len(results) == 1
    entry = results[0]
    assert entry["risk_type"] == risk_control.RISK_WORDS
    assert entry["risk_source"] == risk_control.SOURCE_AI
    assert entry["risk_detail"] == "商品名含「特效」，属功效夸大用语，不得使用"
    assert entry["confidence"] == pytest.approx(0.92)
    assert entry["suggestions"] == ["去掉「特效」二字", "改为「冰镇降温套餐」"]


def test_ai_can_add_risk_type_rules_missed(monkeypatch):
    """规则没抓到、AI 抓到的风险类型会补一条（规则结果保留）。"""
    _enable_fake_ai(monkeypatch, AI_BLOCK_JSON)
    action, results = risk_control.decide_product_risk(
        original=Decimal("20.00"),
        discount=Decimal("22.00"),  # 规则命中价格异常
        title="特效降温套餐",
        description="含违禁夸大宣传词",
        expire_time=now_shanghai_naive() + risk_control.timedelta(hours=6),
    )
    assert action == risk_control.BLOCK
    types = {item["risk_type"]: item["risk_source"] for item in results}
    assert types == {risk_control.RISK_PRICE: "rule", risk_control.RISK_WORDS: "ai"}


def test_ai_pass_keeps_rule_block(monkeypatch):
    """AI 误判为 pass 时，规则的确定性拦截仍然生效（兜底不放松）。"""
    _enable_fake_ai(monkeypatch, AI_PASS_JSON)
    action, results = risk_control.decide_product_risk(
        original=Decimal("20.00"),
        discount=Decimal("22.00"),
        title="超值双拼套餐",
        description="折扣价高于原价",
        expire_time=now_shanghai_naive() + risk_control.timedelta(hours=6),
    )
    assert action == risk_control.BLOCK
    assert results[0]["risk_source"] == risk_control.SOURCE_RULE


def test_ai_failure_falls_back_to_rules(monkeypatch):
    """AI 抛 AiUnavailable 时不抛错，等价于纯规则结果。"""
    monkeypatch.setattr(ai_risk, "is_enabled", lambda: True)

    def _boom(*args, **kwargs):
        raise ai_risk.AiUnavailable("网络不可达")

    monkeypatch.setattr(ai_risk, "_chat", _boom)
    action, results = risk_control.decide_product_risk(
        original=Decimal("20.00"),
        discount=Decimal("9.00"),
        title="特效降温套餐",
        description="含违禁夸大宣传词",
        expire_time=now_shanghai_naive() + risk_control.timedelta(hours=4),
    )
    assert action == risk_control.BLOCK
    assert results[0]["risk_source"] == risk_control.SOURCE_RULE


def test_ai_json_parsing_tolerates_code_fence(monkeypatch):
    """模型输出带 ```json 围栏也能解析。"""
    _enable_fake_ai(monkeypatch, "```json\n" + AI_BLOCK_JSON + "\n```")
    verdict = ai_risk.ai_check_product(
        title="特效降温套餐",
        description="x",
        original_price=Decimal("20.00"),
        discount_price=Decimal("9.00"),
    )
    assert verdict["action"] == "block"
    assert verdict["risk_type"] == 2


def test_ai_bad_output_raises_unavailable(monkeypatch):
    """输出不是 JSON → AiUnavailable（由上层回退）。"""
    _enable_fake_ai(monkeypatch, "我觉得这个商品没问题")
    with pytest.raises(ai_risk.AiUnavailable):
        ai_risk.ai_check_product(
            title="测试", description="x", original_price=1, discount_price=1
        )


# ------------------------------------------------------------------ 管理员接口


def _make_log(session_factory) -> int:
    """造一条风控日志（商品名含「特效」，模拟真实误判场景）。"""
    with session_factory() as db:
        product = db.get(Product, 1)
        product.title = "特效降温套餐"
        product.description = "含违禁夸大宣传词"
        product.status = 3
        product.risk_flag = 1
        log = RiskLog(
            product_id=product.id,
            merchant_id=product.merchant_id,
            risk_type=2,
            risk_detail="命中敏感词：特效",
            risk_source="rule",
            is_resolved=0,
        )
        db.add(log)
        db.commit()
        return log.id


def test_admin_ai_review_removed():
    """手动「AI 复核」端点已移除：风控日志由发布时 AI 自动拦截生成，超管仅做人工复核。"""
    pass
