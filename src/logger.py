"""统一日志与结构化 JSON 记录。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .config import ANALYSIS_LOG_DIR, LOG_DIR, TRADE_LOG_DIR


def _ensure_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def log_message(message: str) -> str:
    """写入通用文本日志，便于排查。"""
    _ensure_dir(LOG_DIR)
    path = LOG_DIR / "app.log"
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
    return str(path)


def _save_json(data: Dict[str, Any], directory: Path, prefix: str) -> str:
    _ensure_dir(directory)
    filename = f"{prefix}_{_timestamp()}.json"
    output_path = directory / filename
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(output_path)


def save_analysis_result(data: Dict[str, Any]) -> str:
    return _save_json(data, ANALYSIS_LOG_DIR, "analysis")


def save_trade_event(data: Dict[str, Any]) -> str:
    return _save_json(data, TRADE_LOG_DIR, "trade")
