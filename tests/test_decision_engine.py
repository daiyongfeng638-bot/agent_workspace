from datetime import datetime, timedelta

from src.decision_engine import decide_action  # noqa: E402


def test_decide_hold_when_has_position():
    result = decide_action(
        {"has_position": True, "direction": "LONG", "lots": 2},
        {"action": "BUY", "allowed": True, "direction": "long", "confidence": 0.99, "entry_price": 1.23, "suggested_lots": 10},
    )
    assert result["action"] == "HOLD_POSITION"
    assert result["allowed"] is True


def test_decide_wait_when_cooldown_active():
    result = decide_action(
        {"has_position": False, "direction": None, "lots": 0},
        {"action": "BUY", "allowed": True, "direction": "long", "confidence": 0.99, "entry_price": 1.23, "suggested_lots": 10},
        last_exit_time=datetime.now() - timedelta(minutes=1),
    )
    assert result["action"] == "WAIT"
    assert result["allowed"] is False


def test_decide_open_order_when_signal_valid():
    result = decide_action(
        {"has_position": False, "direction": None, "lots": 0},
        {
            "action": "SELL",
            "allowed": True,
            "direction": "short",
            "confidence": 0.8,
            "entry_price": 2.34,
            "stop_loss": 2.50,
            "take_profit": 2.10,
            "suggested_lots": 50,
        },
    )
    assert result["action"] == "OPEN_ORDER"
    assert result["direction"] == "short"
    assert result["lots"] <= 30


def test_decide_wait_when_price_invalid():
    result = decide_action(
        {"has_position": False, "direction": None, "lots": 0},
        {"action": "BUY", "allowed": True, "direction": "long", "confidence": 0.9, "entry_price": 0, "stop_loss": 1, "take_profit": 2},
    )
    assert result["action"] == "WAIT"
    assert result["allowed"] is False

