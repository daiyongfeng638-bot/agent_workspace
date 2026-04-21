"""分析结果字段级校验、合法值校验、场景约束与自动归一化。"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


OPEN_DEFAULTS: Dict[str, Any] = {
    "action": "WAIT",
    "allowed": False,
    "direction": "none",
    "entry_price": 0,
    "stop_loss": 0,
    "take_profit": 0,
    "confidence": 0,
    "reason": "",
    "risk_notes": "",
    "conditions": [],
    "multi_timeframe_bias": "",
    "entry_trigger": "",
    "risk_reward": "",
}

POSITION_DEFAULTS: Dict[str, Any] = {
    "action": "HOLD",
    "allowed": False,
    "direction": "none",
    "new_stop_loss": 0,
    "new_take_profit": 0,
    "size_adjustment": 0,
    "confidence": 0,
    "reason": "",
    "risk_notes": "",
    "conditions": [],
    "management_basis": "",
    "trend_status": "",
    "invalidated": False,
}

OPEN_ACTIONS = {"WAIT", "BUY", "SELL"}
POSITION_ACTIONS = {"HOLD", "ADD", "EXIT", "REDUCE", "MOVE_SL"}


class ValidationReport(str):
    """简洁状态报告；兼容字符串和属性访问。"""

    def __new__(
        cls,
        message: str = "",
        *,
        normalized: bool = False,
        downgraded: bool = False,
        downgraded_to: str = "",
        checks: Tuple[str, ...] = (),
    ) -> "ValidationReport":
        text = message or ""
        obj = str.__new__(cls, text)
        obj.message = text
        obj.normalized = normalized
        obj.downgraded = downgraded
        obj.downgraded_to = downgraded_to
        obj.checks = checks
        return obj

    def summary(self) -> str:
        if self.downgraded:
            target = self.downgraded_to or "安全默认值"
            return f"已自动降级为 {target}"
        if self.normalized:
            return "已完成归一化"
        return "结果有效"


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "t"}:
            return True
        if lowered in {"false", "0", "no", "n", "f"}:
            return False
    return default


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text or text.lower() == "none":
            return default
        try:
            return float(text)
        except ValueError:
            return default
    return default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return [value]


def _normalize_confidence(value: Any) -> float:
    confidence = _as_float(value, 0.0)
    if confidence > 1:
        confidence = confidence / 100.0 if confidence <= 100 else 1.0
    return _clamp(confidence, 0.0, 1.0)


def _normalize_open_action(action: Any) -> str:
    text = _as_str(action, "WAIT").strip().upper()
    if text in OPEN_ACTIONS:
        return text
    return "WAIT"


def _normalize_open_direction(direction: Any, action: str) -> str:
    text = _as_str(direction, "none").strip().lower()
    if text in {"long", "short", "none"}:
        return text
    if action == "BUY":
        return "long"
    if action == "SELL":
        return "short"
    return "none"


def _normalize_position_action(action: Any) -> str:
    text = _as_str(action, "HOLD").strip().upper()
    if text in POSITION_ACTIONS:
        return text
    return "HOLD"


def _normalize_position_direction(direction: Any) -> str:
    text = _as_str(direction, "none").strip().lower()
    if text in {"long", "short", "none"}:
        return text
    return "none"


def _build_report(
    *,
    normalized: bool,
    downgraded: bool,
    downgraded_to: str,
    checks: List[str],
    prefix: str,
) -> ValidationReport:
    if downgraded:
        message = f"{prefix}已自动降级为 {downgraded_to or '安全默认值'}"
    elif normalized:
        message = f"{prefix}已完成归一化"
    else:
        message = f"{prefix}结果有效"
    return ValidationReport(
        message,
        normalized=normalized or downgraded,
        downgraded=downgraded,
        downgraded_to=downgraded_to,
        checks=tuple(checks),
    )


def _ensure_reason(reason: str, default_reason: str) -> str:
    return reason if reason else default_reason


def normalize_open_signal_result(raw: Dict[str, Any]) -> Tuple[Dict[str, Any], ValidationReport]:
    """归一化开仓结果，返回 (结果, 简洁状态报告)。"""

    result = dict(OPEN_DEFAULTS)
    result.update(raw or {})

    checks: List[str] = []
    normalized = False
    downgraded = False
    downgraded_to = ""

    action_source = result.get("action", result.get("signal"))
    action = _normalize_open_action(action_source)
    if action != _as_str(action_source, "WAIT").strip().upper():
        normalized = True
        checks.append("action")

    allowed_source = result.get("allowed")
    allowed = _as_bool(allowed_source, False)
    if allowed != allowed_source:
        normalized = True
        checks.append("allowed")

    direction_source = result.get("direction")
    direction = _normalize_open_direction(direction_source, action)
    if direction != _as_str(direction_source, "none").strip().lower():
        normalized = True
        checks.append("direction")

    entry_price_source = result.get("entry_price", result.get("price", result.get("entry")))
    stop_loss_source = result.get("stop_loss", result.get("sl"))
    take_profit_source = result.get("take_profit", result.get("tp"))

    entry_price = _as_float(entry_price_source, 0.0)
    stop_loss = _as_float(stop_loss_source, 0.0)
    take_profit = _as_float(take_profit_source, 0.0)

    if entry_price != _as_float(entry_price_source, 0.0):
        normalized = True
        checks.append("entry_price")
    if stop_loss != _as_float(stop_loss_source, 0.0):
        normalized = True
        checks.append("stop_loss")
    if take_profit != _as_float(take_profit_source, 0.0):
        normalized = True
        checks.append("take_profit")

    confidence_source = result.get("confidence")
    confidence = _normalize_confidence(confidence_source)
    if confidence != _as_float(confidence_source, 0.0):
        normalized = True
        checks.append("confidence")

    reason = _as_str(result.get("reason"), "")
    risk_notes = _as_str(result.get("risk_notes"), "")
    multi_timeframe_bias = _as_str(result.get("multi_timeframe_bias"), "")
    entry_trigger = _as_str(result.get("entry_trigger"), "")
    risk_reward = _as_str(result.get("risk_reward"), "")
    conditions = _as_list(result.get("conditions"))

    result.update(
        {
            "action": action,
            "allowed": allowed,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "confidence": confidence,
            "reason": reason,
            "risk_notes": risk_notes,
            "conditions": conditions,
            "multi_timeframe_bias": multi_timeframe_bias,
            "entry_trigger": entry_trigger,
            "risk_reward": risk_reward,
        }
    )

    def downgrade_to_wait(extra_reason: str, check_key: str) -> None:
        nonlocal action, downgraded, downgraded_to, normalized
        action = "WAIT"
        downgraded = True
        downgraded_to = "WAIT"
        result["allowed"] = False
        result["direction"] = "none"
        result["entry_price"] = 0
        result["stop_loss"] = 0
        result["take_profit"] = 0
        result["reason"] = (
            f"{result['reason']}；{extra_reason}" if result.get("reason") else extra_reason
        )
        normalized = True
        checks.append(check_key)

    if action == "WAIT":
        if result["allowed"] is not False:
            normalized = True
            checks.append("wait.allowed")
        result["allowed"] = False
        if result["direction"] != "none":
            normalized = True
            checks.append("wait.direction")
        result["direction"] = "none"
        if any(v != 0 for v in (result["entry_price"], result["stop_loss"], result["take_profit"])):
            normalized = True
            checks.append("wait.prices")
        result["entry_price"] = 0
        result["stop_loss"] = 0
        result["take_profit"] = 0
        if result["confidence"] > 0.4:
            result["confidence"] = 0.4
            normalized = True
            checks.append("wait.confidence")
        result["reason"] = _ensure_reason(result["reason"], "信号不足或条件未满足")

    elif action == "BUY":
        if not allowed:
            downgrade_to_wait("BUY 场景下 allowed 为 false，已保守降级为 WAIT", "buy.allowed")
        else:
            if direction != "long":
                result["direction"] = "long"
                normalized = True
                checks.append("buy.direction")
            if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
                downgrade_to_wait("BUY 场景价格字段缺失或非法，已自动降级为 WAIT", "buy.prices")
            elif not (stop_loss < entry_price < take_profit):
                downgrade_to_wait("BUY 场景止损/入场/止盈关系不合法，已自动降级为 WAIT", "buy.price_relation")

    elif action == "SELL":
        if not allowed:
            downgrade_to_wait("SELL 场景下 allowed 为 false，已保守降级为 WAIT", "sell.allowed")
        else:
            if direction != "short":
                result["direction"] = "short"
                normalized = True
                checks.append("sell.direction")
            if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
                downgrade_to_wait("SELL 场景价格字段缺失或非法，已自动降级为 WAIT", "sell.prices")
            elif not (take_profit < entry_price < stop_loss):
                downgrade_to_wait("SELL 场景止损/入场/止盈关系不合法，已自动降级为 WAIT", "sell.price_relation")

    if action == "WAIT":
        result["action"] = "WAIT"
    elif action in {"BUY", "SELL"}:
        result["action"] = action

    result["reason"] = _ensure_reason(result["reason"], "信号不足或条件未满足")
    report = _build_report(
        normalized=normalized,
        downgraded=downgraded,
        downgraded_to=downgraded_to,
        checks=checks,
        prefix="开仓结果：",
    )
    return result, report


def normalize_position_management_result(raw: Dict[str, Any]) -> Tuple[Dict[str, Any], ValidationReport]:
    """归一化持仓管理结果，返回 (结果, 简洁状态报告)。"""

    result = dict(POSITION_DEFAULTS)
    result.update(raw or {})

    checks: List[str] = []
    normalized = False
    downgraded = False
    downgraded_to = ""

    action_source = result.get("action", result.get("suggested_action"))
    action = _normalize_position_action(action_source)
    if action != _as_str(action_source, "HOLD").strip().upper():
        normalized = True
        checks.append("action")

    allowed_source = result.get("allowed")
    allowed = _as_bool(allowed_source, False)
    if allowed != allowed_source:
        normalized = True
        checks.append("allowed")

    direction_source = result.get("direction")
    direction = _normalize_position_direction(direction_source)
    if direction != _as_str(direction_source, "none").strip().lower():
        normalized = True
        checks.append("direction")

    new_stop_loss_source = result.get("new_stop_loss", result.get("stop_loss"))
    new_take_profit_source = result.get("new_take_profit", result.get("take_profit"))
    size_adjustment_source = result.get("size_adjustment", result.get("adjustment"))

    new_stop_loss = _as_float(new_stop_loss_source, 0.0)
    new_take_profit = _as_float(new_take_profit_source, 0.0)
    size_adjustment = _as_float(size_adjustment_source, 0.0)

    if new_stop_loss != _as_float(new_stop_loss_source, 0.0):
        normalized = True
        checks.append("new_stop_loss")
    if new_take_profit != _as_float(new_take_profit_source, 0.0):
        normalized = True
        checks.append("new_take_profit")
    if size_adjustment != _as_float(size_adjustment_source, 0.0):
        normalized = True
        checks.append("size_adjustment")

    confidence_source = result.get("confidence")
    confidence = _normalize_confidence(confidence_source)
    if confidence != _as_float(confidence_source, 0.0):
        normalized = True
        checks.append("confidence")

    reason = _as_str(result.get("reason"), "")
    risk_notes = _as_str(result.get("risk_notes"), "")
    conditions = _as_list(result.get("conditions"))
    management_basis = _as_str(result.get("management_basis"), "")
    trend_status = _as_str(result.get("trend_status"), "")
    invalidated = _as_bool(result.get("invalidated"), False)

    result.update(
        {
            "action": action,
            "allowed": allowed,
            "direction": direction,
            "new_stop_loss": new_stop_loss,
            "new_take_profit": new_take_profit,
            "size_adjustment": size_adjustment,
            "confidence": confidence,
            "reason": reason,
            "risk_notes": risk_notes,
            "conditions": conditions,
            "management_basis": management_basis,
            "trend_status": trend_status,
            "invalidated": invalidated,
        }
    )

    def downgrade_to_hold(extra_reason: str, check_key: str) -> None:
        nonlocal action, downgraded, downgraded_to, normalized
        action = "HOLD"
        downgraded = True
        downgraded_to = "HOLD"
        result["allowed"] = False
        result["direction"] = "none"
        result["size_adjustment"] = 0
        result["reason"] = (
            f"{result['reason']}；{extra_reason}" if result.get("reason") else extra_reason
        )
        normalized = True
        checks.append(check_key)

    if action == "HOLD":
        result["allowed"] = False
        result["size_adjustment"] = 0
        if result["direction"] != "none":
            result["direction"] = "none"
            normalized = True
            checks.append("hold.direction")
        result["reason"] = _ensure_reason(result["reason"], "暂无充分理由调整持仓")

    elif action == "ADD":
        if invalidated:
            downgrade_to_hold("持仓逻辑已失效，已保守降级为 HOLD", "add.invalidated")
        elif direction == "none" or size_adjustment <= 0 or confidence <= 0.5:
            downgrade_to_hold("加仓条件不足，已自动降级为 HOLD", "add.downgrade")
        else:
            result["allowed"] = True
            if size_adjustment < 0:
                result["size_adjustment"] = abs(size_adjustment)
                normalized = True
                checks.append("add.size_sign")

    elif action == "REDUCE":
        if direction == "none" or size_adjustment == 0:
            downgrade_to_hold("减仓方向或幅度不明确，已自动降级为 HOLD", "reduce.downgrade")
        else:
            result["allowed"] = True
            if size_adjustment > 0:
                result["size_adjustment"] = -abs(size_adjustment)
                normalized = True
                checks.append("reduce.size_sign")

    elif action == "EXIT":
        if direction == "none":
            downgrade_to_hold("离场方向不明确，已自动降级为 HOLD", "exit.downgrade")
        else:
            result["allowed"] = True
            result["size_adjustment"] = -1 if size_adjustment == 0 else -abs(size_adjustment)
            if result["reason"] == "":
                result["reason"] = "满足离场条件"

    elif action == "MOVE_SL":
        if direction == "none" or new_stop_loss <= 0:
            downgrade_to_hold("移动止损条件不足，已自动降级为 HOLD", "move_sl.downgrade")
        else:
            result["allowed"] = True
            if result["reason"] == "":
                result["reason"] = "满足移动止损条件"

    if invalidated and action == "ADD":
        action = "REDUCE"
        downgraded = True
        downgraded_to = "REDUCE"
        result["allowed"] = True
        result["direction"] = direction if direction != "none" else "none"
        result["size_adjustment"] = -abs(size_adjustment) if size_adjustment else -1
        result["reason"] = (
            f"{result['reason']}；原持仓逻辑已失效，已自动降级为 REDUCE"
            if result.get("reason")
            else "原持仓逻辑已失效，已自动降级为 REDUCE"
        )
        normalized = True
        checks.append("invalidated.add")

    result["action"] = action
    result["reason"] = _ensure_reason(result["reason"], "暂无充分理由调整持仓")

    report = _build_report(
        normalized=normalized,
        downgraded=downgraded,
        downgraded_to=downgraded_to,
        checks=checks,
        prefix="持仓结果：",
    )
    return result, report
