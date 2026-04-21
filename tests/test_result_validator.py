from src.result_validator import (
    normalize_open_signal_result,
    normalize_position_management_result,
)


def test_wait_auto_fix():
    result, report = normalize_open_signal_result(
        {
            "action": "WAIT",
            "allowed": True,
            "direction": "LONG",
            "entry_price": 1.23,
            "stop_loss": 1.10,
            "take_profit": 1.40,
            "confidence": 0.8,
        }
    )

    assert result["action"] == "WAIT"
    assert result["allowed"] is False
    assert result["direction"] == "none"
    assert result["entry_price"] == 0
    assert result["stop_loss"] == 0
    assert result["take_profit"] == 0
    assert report.normalized is True
    assert report.downgraded is False


def test_buy_invalid_price_downgrade_to_wait():
    result, report = normalize_open_signal_result(
        {
            "action": "BUY",
            "allowed": True,
            "direction": "long",
            "entry_price": 1.20,
            "stop_loss": 1.25,
            "take_profit": 1.40,
            "confidence": 0.9,
        }
    )

    assert result["action"] == "WAIT"
    assert result["allowed"] is False
    assert result["direction"] == "none"
    assert result["entry_price"] == 0
    assert result["stop_loss"] == 0
    assert result["take_profit"] == 0
    assert report.downgraded is True
    assert report.downgraded_to == "WAIT"


def test_sell_invalid_price_downgrade_to_wait():
    result, report = normalize_open_signal_result(
        {
            "action": "SELL",
            "allowed": True,
            "direction": "short",
            "entry_price": 1.20,
            "stop_loss": 1.10,
            "take_profit": 1.30,
            "confidence": 0.9,
        }
    )

    assert result["action"] == "WAIT"
    assert result["allowed"] is False
    assert result["direction"] == "none"
    assert report.downgraded is True
    assert report.downgraded_to == "WAIT"


def test_hold_consistent():
    result, report = normalize_position_management_result(
        {
            "action": "HOLD",
            "allowed": False,
            "direction": "none",
            "reason": "",
            "confidence": 0.2,
        }
    )

    assert result["action"] == "HOLD"
    assert result["allowed"] is False
    assert result["direction"] == "none"
    assert result["size_adjustment"] == 0
    assert result["reason"] == "暂无充分理由调整持仓"
    assert report.normalized is False
    assert report.downgraded is False


def test_add_insufficient_conditions_downgrade_to_hold():
    result, report = normalize_position_management_result(
        {
            "action": "ADD",
            "allowed": True,
            "direction": "long",
            "size_adjustment": 1,
            "confidence": 0.3,
        }
    )

    assert result["action"] == "HOLD"
    assert result["allowed"] is False
    assert result["direction"] == "none"
    assert result["size_adjustment"] == 0
    assert report.downgraded is True
    assert report.downgraded_to == "HOLD"


def test_move_sl_missing_stop_loss_downgrade_to_hold():
    result, report = normalize_position_management_result(
        {
            "action": "MOVE_SL",
            "allowed": True,
            "direction": "long",
            "new_stop_loss": 0,
            "confidence": 0.9,
        }
    )

    assert result["action"] == "HOLD"
    assert result["allowed"] is False
    assert result["direction"] == "none"
    assert result["size_adjustment"] == 0
    assert report.downgraded is True
    assert report.downgraded_to == "HOLD"
