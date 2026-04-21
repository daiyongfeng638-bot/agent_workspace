"""决策引擎：统一输出 OPEN_ORDER / HOLD_POSITION / WAIT。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .config import CONFIDENCE_THRESHOLD, COOLDOWN_AFTER_EXIT_MINUTES, MAX_SINGLE_DIRECTION_LOTS


def _empty_decision(action: str, allowed: bool, reason: str) -> Dict[str, Any]:
    return {
        "action": action,
        "allowed": allowed,
        "direction": None,
        "price": 0,
        "lots": 0,
        "reason": reason,
    }


def decide_action(
    position_state: Dict[str, Any],
    analysis_result: Dict[str, Any],
    last_exit_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """根据持仓状态与分析结果输出统一决策结构。"""
    has_position = bool(position_state.get("has_position", False))
    now = datetime.now()

    if last_exit_time is not None:
        cooldown_until = last_exit_time + timedelta(minutes=COOLDOWN_AFTER_EXIT_MINUTES)
        if now < cooldown_until:
            return _empty_decision("WAIT", False, "仍处于止盈/止损后的冷却期。")

    if has_position:
        return {
            "action": "HOLD_POSITION",
            "allowed": True,
            "direction": position_state.get("direction"),
            "price": 0,
            "lots": int(position_state.get("lots", 0) or 0),
            "reason": "当前已有持仓，仅允许持仓管理，不允许新开仓。",
        }

    action = str(analysis_result.get("action", "WAIT") or "WAIT").upper()
    allowed = bool(analysis_result.get("allowed", False))
    direction = str(analysis_result.get("direction", "none") or "none").lower()
    confidence_raw = analysis_result.get("confidence", 0)
    confidence = int(float(confidence_raw) * 100) if isinstance(confidence_raw, (int, float)) and confidence_raw <= 1 else int(float(confidence_raw or 0))

    if action not in {"BUY", "SELL", "WAIT"}:
        return _empty_decision("WAIT", False, f"无法识别的开仓动作: {action}")

    if action == "WAIT" or not allowed or confidence < CONFIDENCE_THRESHOLD:
        return _empty_decision(
            "WAIT",
            False,
            f"信号不足或置信度未达标(action={action}, allowed={allowed}, confidence={confidence})。",
        )

    if direction not in {"long", "short"}:
        return _empty_decision("WAIT", False, f"方向不合法: {direction}")

    lots = int(float(analysis_result.get("suggested_lots", analysis_result.get("lots", 0)) or 0))
    lots = min(max(lots, 0), MAX_SINGLE_DIRECTION_LOTS)
    if lots <= 0:
        lots = 1

    price = float(analysis_result.get("entry_price", analysis_result.get("price", 0)) or 0)
    if price <= 0:
        return _empty_decision("WAIT", False, "开仓价格缺失或非法。")

    mapped_action = "OPEN_ORDER"
    return {
        "action": mapped_action,
        "allowed": True,
        "direction": direction,
        "price": price,
        "lots": lots,
        "reason": f"信号满足阈值，confidence={confidence}。",
    }
