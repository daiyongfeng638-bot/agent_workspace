import json
from pathlib import Path

import src.logger as logger  # noqa: E402


def test_log_message_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "LOG_DIR", tmp_path)
    path = Path(logger.log_message("pytest log test"))
    assert path.exists()
    assert path.name == "app.log"


def test_save_analysis_result_creates_json(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "ANALYSIS_LOG_DIR", tmp_path)
    data = {"signal": "NONE", "confidence": 0}
    path = Path(logger.save_analysis_result(data))
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == data


def test_save_trade_event_creates_json(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "TRADE_LOG_DIR", tmp_path)
    data = {"action": "WAIT", "allowed": False}
    path = Path(logger.save_trade_event(data))
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == data
