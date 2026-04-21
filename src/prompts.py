"""分析提示词模板加载器。启动时自动校验 analysis_prompt.json。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .config import BASE_DIR
from .logger import log_message

PROMPT_FILE = Path(BASE_DIR) / "src" / "analysis_prompt.json"
REQUIRED_KEYS = (
    "system_role",
    "open_signal_prompt",
    "position_management_prompt",
)

CONTENT_CHECK_RULES = {
    "system_role": {
        "label": "system_role",
        "keywords": ["角色", "助手", "输出", "JSON", "结构化", "原则", "边界"],
        "required_count": 4,
        "required_must_include": ["角色", "助手", "输出"],
        "hint": "缺少角色/边界/结构化输出相关描述",
    },
    "open_signal_prompt": {
        "label": "open_signal_prompt",
        "keywords": ["开仓", "信号", "条件", "判断", "风险", "JSON", "结构化"],
        "required_count": 4,
        "required_must_include": ["开仓", "信号", "条件"],
        "hint": "缺少开仓判断、条件驱动、风险控制或 JSON 输出要求",
    },
    "position_management_prompt": {
        "label": "position_management_prompt",
        "keywords": ["持仓", "仓位", "止损", "止盈", "减仓", "加仓", "风险", "JSON", "结构化"],
        "required_count": 4,
        "required_must_include": ["持仓", "仓位", "风险"],
        "hint": "缺少持仓管理、风险控制或 JSON 输出要求",
    },
}

JSON_RULE_CHECKS = {
    "system_role": {
        "must_have": ["json", "结构化", "可解析", "风险控制"],
        "min_hits": 3,
        "hint": "缺少 JSON/结构化/可解析/风险控制/保守 边界要求",
    },
    "open_signal_prompt": {
        "must_have": [
            "开仓",
            "信号",
            "判断",
            "json",
            "结构化",
            "action",
            "allowed",
            "direction",
            "stop_loss",
            "take_profit",
            "confidence",
            "wait",
            "风险",
            "条件",
            "证据不足",
        ],
        "min_hits": 9,
        "hint": "缺少 action/allowed/direction/stop_loss/take_profit/confidence/WAIT 等 JSON 输出约束",
    },
    "position_management_prompt": {
        "must_have": [
            "持仓",
            "仓位",
            "管理",
            "json",
            "结构化",
            "action",
            "allowed",
            "new_stop_loss",
            "new_take_profit",
            "confidence",
            "hold",
            "exit",
            "reduce",
            "add",
            "move_sl",
            "风险",
            "调整",
            "保守",
        ],
        "min_hits": 10,
        "hint": "缺少 action/new_stop_loss/new_take_profit/HOLD/EXIT/REDUCE/ADD/MOVE_SL 等 JSON 输出约束",
    },
}


def load_prompt_bundle() -> Dict[str, Any]:
    """加载并严格校验结构化分析提示词配置。"""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"analysis_prompt.json 不存在: {PROMPT_FILE}"
        )

    try:
        with PROMPT_FILE.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"analysis_prompt.json 无法解析为 JSON: {exc.msg} (line={exc.lineno}, col={exc.colno})"
        ) from exc

    if not isinstance(payload, dict):
        raise TypeError("analysis_prompt.json 顶层必须是 JSON 对象（dict）。")

    missing_keys = [key for key in REQUIRED_KEYS if key not in payload]
    if missing_keys:
        raise KeyError(
            f"analysis_prompt.json 缺少必需字段: {', '.join(missing_keys)}"
        )

    for key in REQUIRED_KEYS:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"analysis_prompt.json 中字段 {key!r} 必须是非空字符串。"
            )

    unexpected_keys = [key for key in payload.keys() if key not in REQUIRED_KEYS]
    if unexpected_keys:
        raise ValueError(
            "analysis_prompt.json 仅允许 3 个核心字段: "
            f"{', '.join(REQUIRED_KEYS)}；发现额外字段: {', '.join(unexpected_keys)}"
        )

    return payload


def _check_prompt_content(prompt_name: str, prompt_text: str) -> list[str]:
    rule = CONTENT_CHECK_RULES[prompt_name]
    missing: list[str] = []
    lowered = prompt_text.lower()

    matched_keywords = [kw for kw in rule["keywords"] if kw.lower() in lowered]
    if len(matched_keywords) < rule["required_count"]:
        missing.append(rule["hint"])

    for kw in rule["required_must_include"]:
        if kw.lower() not in lowered:
            missing.append(f"缺少关键意图关键词: {kw}")

    if "json" not in lowered:
        missing.append("缺少 JSON 输出要求")

    return missing


def run_prompt_content_check() -> tuple[bool, list[str]]:
    """执行轻量级 prompt 内容自检。"""
    issues: list[str] = []
    for key in REQUIRED_KEYS:
        issues.extend([f"{key}: {item}" for item in _check_prompt_content(key, str(PROMPT_BUNDLE[key]))])
    return (len(issues) == 0, issues)


def _check_json_rule(prompt_name: str, prompt_text: str) -> list[str]:
    rule = JSON_RULE_CHECKS[prompt_name]
    lowered = prompt_text.lower()
    matched = [kw for kw in rule["must_have"] if kw.lower() in lowered]
    issues: list[str] = []
    if len(matched) < rule["min_hits"]:
        issues.append(rule["hint"])

    if prompt_name == "open_signal_prompt":
        if "action" not in lowered:
            issues.append("缺少 action 字段约束")
        if "allowed" not in lowered:
            issues.append("缺少 allowed 字段约束")
        if "direction" not in lowered:
            issues.append("缺少 direction 字段约束")
        if "stop_loss" not in lowered:
            issues.append("缺少 stop_loss 字段约束")
        if "take_profit" not in lowered:
            issues.append("缺少 take_profit 字段约束")
        if "confidence" not in lowered:
            issues.append("缺少 confidence 字段约束")
        if "wait" not in lowered:
            issues.append("缺少 WAIT 保守分支要求")

    if prompt_name == "position_management_prompt":
        if "action" not in lowered:
            issues.append("缺少 action 字段约束")
        if "new_stop_loss" not in lowered:
            issues.append("缺少 new_stop_loss 字段约束")
        if "new_take_profit" not in lowered:
            issues.append("缺少 new_take_profit 字段约束")
        if not any(term in lowered for term in ["hold", "exit", "reduce", "add", "move_sl"]):
            issues.append("缺少 HOLD/EXIT/REDUCE/ADD/MOVE_SL 结果分支要求")

    if prompt_name == "system_role":
        if "json" not in lowered:
            issues.append("缺少 JSON 输出要求")
        if not any(term in lowered for term in ["结构化", "可解析"]):
            issues.append("缺少结构化/可解析输出要求")
        if not any(term in lowered for term in ["风险控制", "保守", "边界"]):
            issues.append("缺少风险控制/保守/边界要求")

    return issues


def run_prompt_json_rule_check() -> tuple[bool, list[str]]:
    issues: list[str] = []
    for key in REQUIRED_KEYS:
        issues.extend([f"{key}: {item}" for item in _check_json_rule(key, str(PROMPT_BUNDLE[key]))])
    return (len(issues) == 0, issues)


PROMPT_BUNDLE = load_prompt_bundle()
SYSTEM_ROLE = PROMPT_BUNDLE["system_role"]
OPEN_SIGNAL_PROMPT = PROMPT_BUNDLE["open_signal_prompt"]
POSITION_MANAGEMENT_PROMPT = PROMPT_BUNDLE["position_management_prompt"]

PROMPTS_OK = bool(SYSTEM_ROLE and OPEN_SIGNAL_PROMPT and POSITION_MANAGEMENT_PROMPT)
PROMPT_CONTENT_CHECK_PASSED, PROMPT_CONTENT_CHECK_ISSUES = run_prompt_content_check()
PROMPT_JSON_RULE_CHECK_PASSED, PROMPT_JSON_RULE_CHECK_ISSUES = run_prompt_json_rule_check()

print(f"PROMPTS_OK={'PASS' if PROMPTS_OK else 'FAIL'}")
if PROMPT_CONTENT_CHECK_PASSED:
    print("PROMPT_CONTENT_CHECK=PASS")
    log_message("PROMPT_CONTENT_CHECK=PASS")
else:
    print("PROMPT_CONTENT_CHECK=FAIL")
    for issue in PROMPT_CONTENT_CHECK_ISSUES:
        print(f"PROMPT_CONTENT_CHECK_ISSUE: {issue}")
        log_message(f"PROMPT_CONTENT_CHECK_ISSUE: {issue}")

if PROMPT_JSON_RULE_CHECK_PASSED:
    print("PROMPT_JSON_RULE_CHECK=PASS")
    log_message("PROMPT_JSON_RULE_CHECK=PASS")
else:
    print("PROMPT_JSON_RULE_CHECK=FAIL")
    for issue in PROMPT_JSON_RULE_CHECK_ISSUES:
        print(f"PROMPT_JSON_RULE_CHECK_ISSUE: {issue}")
        log_message(f"PROMPT_JSON_RULE_CHECK_ISSUE: {issue}")
