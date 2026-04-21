import json
from pathlib import Path

import src.logger as logger  # noqa: E402


def test_log_message_creates_file():
    path = Path(logger.log_message("pytest log test"))
    assert path.exists()
    assert path.name == "app.log"


def test_save_analysis_result_creates_json():
    data = {"signal": "NONE", "confidence": 0}
    path = Path(logger.save_analysis_result(data))
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == data


def test_save_trade_event_creates_json():
    data = {"action": "WAIT", "allowed": False}
    path = Path(logger.save_trade_event(data))
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == data
