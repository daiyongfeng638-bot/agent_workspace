"""半自动填单模块，默认 dry_run=True，严禁提交订单。"""

from __future__ import annotations

from typing import Literal

import pyautogui

from .config import BUY_BUTTON_POS, LOT_INPUT_POS, PRICE_INPUT_POS, SELL_BUTTON_POS
from .logger import log_message, save_trade_event

Direction = Literal["LONG", "SHORT"]


def fill_order(direction: Direction, price: float, lots: int, dry_run: bool = True) -> bool:
    """根据方向执行半自动填单：只填充，不提交。"""
    action_button = BUY_BUTTON_POS if direction == "LONG" else SELL_BUTTON_POS
    save_trade_event(
        {
            "direction": direction,
            "price": price,
            "lots": lots,
            "dry_run": dry_run,
            "submit_order": False,
            "message": "当前为 dry_run 模式，已禁止自动提交订单。",
        }
    )

    if dry_run:
        print("当前为 dry_run 模式：仅模拟填单，不执行真实点击。")
        log_message(f"dry_run 填单模拟 direction={direction}, price={price}, lots={lots}")
        return True

    # 保留未来切换真实点击的结构，但默认不提交订单。
    pyautogui.click(action_button)
    pyautogui.click(PRICE_INPUT_POS)
    pyautogui.write(str(price), interval=0.02)
    pyautogui.click(LOT_INPUT_POS)
    pyautogui.write(str(lots), interval=0.02)
    log_message("已执行真实填单流程，但仍未提交订单（安全模式）。")
    print("当前为 dry_run 模式：未提交订单，仅完成填单辅助步骤。")
    return True
