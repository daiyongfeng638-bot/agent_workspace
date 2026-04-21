"""OCR/状态识别模块，占位实现。"""

from __future__ import annotations

from typing import Dict, Optional

from .logger import log_message


def detect_position_status(image_path: Optional[str] = None) -> Dict[str, object]:
    """检测当前持仓状态，第一版返回稳定结构。"""
    log_message(f"OCR 状态检测调用，image_path={image_path}")
    return {"has_position": False, "direction": None, "lots": 0}
