"""商品交易半自动助手主程序：单次流程。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

from .config import AUTO_FILL_ORDER, AUTO_SUBMIT_ORDER, DEFAULT_LOT_SIZE
from .decision_engine import decide_action
from .gpt_analyzer import analyze_open_signal, analyze_position_management
from .logger import log_message, save_trade_event
from .ocr_state import detect_position_status
from .order_filler import fill_order
from .result_validator import (
    normalize_open_signal_result,
    normalize_position_management_result,
)
from .screenshot import capture_all_regions


def _safe_capture_all_regions() -> List[str]:
    """优先执行真实截图；若环境不支持则回退到占位结果，确保主流程可运行。"""
    try:
        image_paths = capture_all_regions()
        print(f"截图完成，共 {len(image_paths)} 个区域。")
        return image_paths
    except Exception as exc:  # noqa: BLE001
        fallback = ["mock_chart.png", "mock_order_panel.png", "mock_position.png", "mock_price.png"]
        log_message(f"截图失败，已切换为 mock 占位结果: {exc}")
        print(f"截图失败，已使用 mock 占位结果: {exc}")
        return fallback


def _log_result_check(prefix: str, report: object) -> None:
    """输出简洁结果检查日志。"""
    normalized = bool(getattr(report, "normalized", False))
    downgraded = bool(getattr(report, "downgraded", False))
    downgraded_to = str(getattr(report, "downgraded_to", "") or "")

    if downgraded:
        marker = f"{prefix}_RESULT_CHECK=DOWNGRADED"
        if downgraded_to:
            marker += f"_{downgraded_to}"
        log_message(marker)
        print(marker)
    elif normalized:
        marker = f"{prefix}_RESULT_CHECK=FIXED"
        log_message(marker)
        print(marker)
    else:
        marker = f"{prefix}_RESULT_CHECK=PASS"
        log_message(marker)
        print(marker)


def main() -> None:
    """执行单次交易辅助流程。"""
    startup_time = datetime.now().isoformat(timespec="seconds")
    print("=== 商品交易半自动助手启动 ===")
    print(f"启动时间: {startup_time}")
    print(f"AUTO_FILL_ORDER={AUTO_FILL_ORDER}, AUTO_SUBMIT_ORDER={AUTO_SUBMIT_ORDER}, DEFAULT_LOT_SIZE={DEFAULT_LOT_SIZE}")
    print("当前模式: 单次流程 / 默认 dry_run=True / 严禁自动提交订单")
    log_message("主程序启动，准备执行单次流程。")

    image_paths = _safe_capture_all_regions()
    position_state = detect_position_status(image_paths[0] if image_paths else None)
    print(f"持仓状态: {position_state}")

    if position_state.get("has_position"):
        print("检测到持仓，执行持仓分析。")
        analysis_result = analyze_position_management(image_paths)
        analysis_result, position_report = normalize_position_management_result(analysis_result)
        _log_result_check("POSITION", position_report)
    else:
        print("当前无持仓，执行开仓分析。")
        analysis_result = analyze_open_signal(image_paths)
        analysis_result, open_report = normalize_open_signal_result(analysis_result)
        _log_result_check("OPEN_SIGNAL", open_report)

    print(f"分析结果: {analysis_result}")
    decision = decide_action(position_state, analysis_result, last_exit_time=None)
    print(f"决策结果: {decision}")
    log_message(f"决策结果: {decision}")

    trade_note = "本次未执行开仓填单。"
    if decision["action"] == "OPEN_ORDER" and decision["allowed"] and AUTO_FILL_ORDER:
        lots = decision.get("lots") or DEFAULT_LOT_SIZE
        fill_order(
            direction=decision["direction"],
            price=decision.get("price", 0),
            lots=lots,
            dry_run=True,
        )
        trade_note = "已完成半自动填单辅助，未提交订单。"

    result_record = {
        "timestamp": datetime.now().isoformat(),
        "decision": decision,
        "position_state": position_state,
        "analysis_result": analysis_result,
        "image_paths": image_paths,
        "note": trade_note,
    }
    trade_log_path = save_trade_event(result_record)
    print(f"交易记录已写入: {trade_log_path}")

    log_message("主程序单次流程结束。")
    print("=== 本次执行结束 ===")
    print(f"摘要: action={decision.get('action')}, allowed={decision.get('allowed')}, note={trade_note}")


if __name__ == "__main__":
    main()
