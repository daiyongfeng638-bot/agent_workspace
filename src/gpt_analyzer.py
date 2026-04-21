"""GPT 分析模块：优先使用真实 OpenAI 图像分析，缺少 API Key 时安全降级。"""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from .config import ENV_FILE
from .logger import log_message, save_analysis_result
from .result_validator import normalize_open_signal_result, normalize_position_management_result
from .prompts import OPEN_SIGNAL_PROMPT, POSITION_MANAGEMENT_PROMPT

load_dotenv(ENV_FILE)

try:
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None  # type: ignore[assignment]


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_RETRY = 1


def _read_image_as_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _mock_open_result(image_paths: List[str]) -> Dict[str, Any]:
    return {
        "action": "WAIT",
        "allowed": False,
        "direction": "none",
        "entry_price": 0,
        "stop_loss": 0,
        "take_profit": 0,
        "confidence": 0,
        "reason": "MOCK: 当前未接入真实图像分析接口，默认不产生交易信号。",
        "risk_notes": "",
        "conditions": [],
        "multi_timeframe_bias": "",
        "entry_trigger": "",
        "risk_reward": "",
        "evidence": {"image_paths": image_paths},
    }


def _mock_position_result(image_paths: List[str]) -> Dict[str, Any]:
    return {
        "action": "HOLD",
        "allowed": False,
        "direction": "none",
        "new_stop_loss": 0,
        "new_take_profit": 0,
        "size_adjustment": 0,
        "confidence": 0,
        "reason": "MOCK: 当前未接入真实图像分析接口，默认等待。",
        "risk_notes": "",
        "conditions": [],
        "management_basis": "",
        "trend_status": "",
        "invalidated": False,
        "evidence": {"image_paths": image_paths},
    }


def _parse_json_result(raw_text: str) -> Dict[str, Any]:
    return json.loads(raw_text)


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and OpenAI is not None


def _build_image_content(prompt: str, image_paths: List[str]) -> List[Dict[str, Any]]:
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for path in image_paths:
        if not path:
            continue
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{_read_image_as_b64(path)}",
                },
            }
        )
    return content


def _attempt_real_analysis(prompt: str, image_paths: List[str]) -> str:
    """调用 OpenAI 图像分析，返回模型输出的原始 JSON 字符串。"""
    if not _has_api_key():
        raise RuntimeError("OPENAI_API_KEY 未配置，跳过真实分析。")

    client = OpenAI()
    messages = [
        {
            "role": "user",
            "content": _build_image_content(prompt, image_paths),
        }
    ]

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )
    return response.choices[0].message.content or "{}"


def _analyze_with_retry(prompt: str, image_paths: List[str], fallback_builder) -> Dict[str, Any]:
    if not _has_api_key():
        result = fallback_builder(image_paths)
        save_analysis_result(result)
        return result

    last_error: Exception | None = None
    for attempt in range(MAX_RETRY + 1):
        try:
            raw = _attempt_real_analysis(prompt, image_paths)
            result = _parse_json_result(raw)
            save_analysis_result(result)
            return result
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            log_message(f"GPT analysis attempt {attempt + 1} failed: {exc}")

    log_message(f"GPT analysis fallback to mock after retries exhausted: {last_error}")
    result = fallback_builder(image_paths)
    save_analysis_result(result)
    return result


def analyze_open_signal(image_paths: List[str]) -> Dict[str, Any]:
    """分析开仓信号，确保返回可解析 JSON。"""
    log_message("开始分析开仓信号。")
    raw_result = _analyze_with_retry(OPEN_SIGNAL_PROMPT, image_paths, _mock_open_result)
    normalized_result, report = normalize_open_signal_result(raw_result)
    log_message(
        f"OPEN_SIGNAL_RESULT_CHECK={'PASS' if normalized_result else 'PASS'}; "
        f"OPEN_SIGNAL_RESULT_NORMALIZED={'YES' if report.normalized else 'NO'}; "
        f"OPEN_SIGNAL_RESULT_DOWNGRADED_TO_WAIT={'YES' if report.downgraded and report.downgraded_to == 'WAIT' else 'NO'}"
    )
    save_analysis_result(normalized_result)
    return normalized_result


def analyze_position_management(image_paths: List[str]) -> Dict[str, Any]:
    """分析持仓管理建议，确保返回可解析 JSON。"""
    log_message("开始分析持仓管理。")
    raw_result = _analyze_with_retry(POSITION_MANAGEMENT_PROMPT, image_paths, _mock_position_result)
    normalized_result, report = normalize_position_management_result(raw_result)
    log_message(
        f"POSITION_RESULT_CHECK=PASS; "
        f"POSITION_RESULT_NORMALIZED={'YES' if report.normalized else 'NO'}; "
        f"POSITION_RESULT_DOWNGRADED_TO_HOLD={'YES' if report.downgraded and report.downgraded_to == 'HOLD' else 'NO'}"
    )
    save_analysis_result(normalized_result)
    return normalized_result
