"""AI 风控语义审核（OpenAI 兼容接口，如 DeepSeek / 火山方舟）。

设计要点
--------
* **零新增依赖**：只用标准库 ``urllib`` 发 POST，避免给演示环境加装包。
* **可回退**：未配置 ``FOODLINK_AI_API_KEY``、网络异常、返回不是合法 JSON、超时——
  一律抛 :class:`AiUnavailable`，由 :mod:`app.risk_control` 回退到本地规则引擎，
  保证商品发布流程永远不会因为 AI 不可用而挂掉。
* **输出对齐规则引擎**：返回 ``action``（pass/warn/block）+ ``risk_type``（1/2/3）+
  ``risk_detail``，与 ``run_risk_check`` 的结果结构一致，方便统一写进 ``risk_logs``。

接口约定（与 app/risk_control.py 完全一致）：
    risk_type = 1 价格异常 / 2 敏感词（违规宣传） / 3 有效期异常
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from app.config import settings

# 与 risk_control 保持一致的动作常量（此处不 import，避免循环依赖）
PASS = "pass"
WARN = "warn"
BLOCK = "block"
VALID_ACTIONS = (PASS, WARN, BLOCK)
VALID_TYPES = (1, 2, 3)

# 风控类型中文名（写进日志说明时不依赖 admin 模块）
RISK_TYPE_NAME = {1: "价格异常", 2: "敏感词", 3: "有效期异常"}

SYSTEM_PROMPT = """你是「食愿」——一个校园临期食品打折清仓平台的 AI 风控审核员。
平台目的：帮商家把当天卖不完的餐食折价清仓、减少浪费，同时让同学吃得便宜。因此审核要「严而不滥」：
明显违规的一定要拦，正常商品绝不能被误判（误判会让商家和学生的正常交易受损）。

只审三类风险，risk_type 必须取以下之一：
- 1 价格异常：折扣价 ≥ 原价（虚构原价）、折扣价 ≤ 0、折扣幅度极不合理（如原价 30 元折后 0.3 元）等；
- 2 敏感词 / 违规宣传：医疗功效宣称（包治百病、根治、治疗、特效药、药到病除）、
  绝对化或虚假承诺（百分百、稳赚不赔、0 风险）、导流广告（加微信、扫码、代购）、
  违禁品（烟酒、处方药、野生动物、毒品）、色情暴力与政治敏感内容；
- 3 有效期异常：领取截止时间已过期、距离截止不足 1 小时（提醒类，可警告）、时间明显不合理。

重要判定口径（避免误判）：
- 「药膳、山药、豆浆、菌汤、姜茶」等是正常的食品名称或饮食描述，属合规，**不要**判定为敏感词；
- 「特效」「包治百病」这类功效夸大用语才算违规宣传；
- 数值类问题（价格比、剩余时长）要按数据算准确，别凭空推断。

严格只输出一个 JSON 对象，不要输出任何解释、Markdown 或代码块围栏，格式：
{"action": "pass|warn|block", "risk_type": 1|2|3|null, "risk_detail": "一句话中文说明，含具体数值/命中词", "confidence": 0.0-1.0, "suggestions": ["给商家的修改建议，可为空数组"]}

字段要求：
- action：pass 正常放行；warn 可上架但需提示；block 拦截。
- risk_type：action 为 pass 时给 null；否则必须是命中的那一类（只报最主要的一类）。
- risk_detail：像审核结论一样写清楚「因为什么、哪一句/哪个数值」，例如
  「折扣价 22.00 元高于原价 20.00 元，疑似虚构原价」或「商品名含「特效」，属功效夸大用语」。
- confidence：你对本次判定的置信度，0~1 的小数。"""


class AiUnavailable(RuntimeError):
    """AI 风控不可用（未配置 key / 网络异常 / 返回非法），调用方应回退到规则引擎。"""


def is_enabled() -> bool:
    """是否配置了 AI 风控（没有 key 就走本地规则引擎）。"""
    return bool(settings.ai_api_key.strip())


def _endpoint() -> str:
    return settings.ai_base_url.rstrip("/") + "/chat/completions"


def _post_json(url: str, payload: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    """发送一次 OpenAI 兼容的 chat/completions 请求（标准库实现）。"""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + settings.ai_api_key.strip(),
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def _chat(messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
    """调用模型并返回文本内容；任何异常都转成 AiUnavailable。"""
    if not is_enabled():
        raise AiUnavailable("未配置 FOODLINK_AI_API_KEY")

    payload: Dict[str, Any] = {
        "model": settings.ai_model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "stream": False,
        "response_format": {"type": "json_object"},
    }
    try:
        data = _post_json(_endpoint(), payload, settings.ai_timeout)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        # 个别网关不支持 response_format，去掉后重试一次
        if exc.code in (400, 422) and "response_format" in detail:
            payload.pop("response_format", None)
            try:
                data = _post_json(_endpoint(), payload, settings.ai_timeout)
            except Exception as retry_exc:  # noqa: BLE001
                raise AiUnavailable(f"AI 调用失败：{retry_exc}") from retry_exc
        else:
            raise AiUnavailable(f"AI 调用失败：HTTP {exc.code} {detail}") from exc
    except Exception as exc:  # noqa: BLE001
        raise AiUnavailable(f"AI 调用失败：{type(exc).__name__}: {exc}") from exc

    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise AiUnavailable("AI 返回结构异常") from exc


def _loads_json(text: str) -> Dict[str, Any]:
    """从模型输出里取出 JSON 对象（容忍 ```json 围栏与前后废话）。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.lstrip().lower().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise AiUnavailable("AI 未返回 JSON")
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise AiUnavailable("AI 返回的 JSON 无法解析") from exc
    if not isinstance(parsed, dict):
        raise AiUnavailable("AI 返回的 JSON 不是对象")
    return parsed


def build_user_prompt(
    *,
    title: str,
    description: Optional[str],
    original_price: Any,
    discount_price: Any,
    quantity: Optional[int] = None,
    expire_time: Any = None,
    category: Optional[str] = None,
    now: Any = None,
) -> str:
    """把待审商品信息整理成用户消息（含剩余可售时长，模型才能判有效期风险）。"""
    remain = None
    if expire_time is not None and now is not None:
        try:
            seconds = (expire_time - now).total_seconds()
            remain = round(seconds / 3600, 2)
        except TypeError:
            remain = None

    original = float(original_price) if original_price is not None else None
    discount = float(discount_price) if discount_price is not None else None
    discount_ratio = None
    if original and discount is not None:
        discount_ratio = round(discount / original, 3)

    payload = {
        "商品名称": title or "",
        "商品描述": description or "",
        "分类": category or "",
        "原价(元)": original,
        "折扣价(元)": discount,
        "折扣率(折扣价/原价)": discount_ratio,
        "剩余可售库存(份)": quantity,
        "领取截止时间": str(expire_time) if expire_time is not None else None,
        "当前时间": str(now) if now is not None else None,
        "距截止还有(小时)": remain,
    }
    return (
        "请审核下面这个待发布的商品，按约定格式只输出 JSON：\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def _normalize(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """把模型输出规范成内部结构；缺失字段按保守策略补齐。"""
    action = str(parsed.get("action") or "").strip().lower()
    if action not in VALID_ACTIONS:
        raise AiUnavailable(f"AI 返回的 action 非法：{action!r}")

    raw_type = parsed.get("risk_type")
    risk_type: Optional[int] = None
    if action != PASS:
        try:
            candidate = int(raw_type)  # type: ignore[arg-type]
            risk_type = candidate if candidate in VALID_TYPES else 2
        except (TypeError, ValueError):
            risk_type = 2  # 内容类问题兜底

    detail = str(parsed.get("risk_detail") or "").strip()
    if action != PASS and not detail:
        detail = "AI 判定存在{}风险".format(RISK_TYPE_NAME.get(risk_type or 2, "内容"))

    try:
        confidence = float(parsed.get("confidence"))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = min(max(confidence, 0.0), 1.0)

    suggestions = parsed.get("suggestions")
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()][:5]

    return {
        "action": action,
        "risk_type": risk_type,
        "risk_detail": detail,
        "confidence": confidence,
        "suggestions": suggestions,
    }


def ai_check_product(
    *,
    title: str,
    description: Optional[str],
    original_price: Any,
    discount_price: Any,
    quantity: Optional[int] = None,
    expire_time: Any = None,
    category: Optional[str] = None,
    now: Any = None,
) -> Dict[str, Any]:
    """调用 AI 审核单个商品。

    成功返回 ``{"action", "risk_type", "risk_detail", "confidence", "suggestions",
    "model", "raw"}``；不可用时抛 :class:`AiUnavailable`。
    """
    user_prompt = build_user_prompt(
        title=title,
        description=description,
        original_price=original_price,
        discount_price=discount_price,
        quantity=quantity,
        expire_time=expire_time,
        category=category,
        now=now,
    )
    content = _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    result = _normalize(_loads_json(content))
    result["model"] = settings.ai_model
    result["raw"] = content.strip()[:1000]
    return result


def ai_review_text(text: str, instruction: str = "") -> Dict[str, Any]:
    """通用文本风控审核（备用入口，例如审核商家资料/评论）。"""
    content = _chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (instruction + "\n" if instruction else "") + text},
        ]
    )
    result = _normalize(_loads_json(content))
    result["model"] = settings.ai_model
    result["raw"] = content.strip()[:1000]
    return result
