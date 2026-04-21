"""固定区域截图模块。"""

from __future__ import annotations

import ctypes
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import mss
from PIL import Image

try:
    import pyautogui
except Exception:  # noqa: BLE001
    pyautogui = None

from .config import (
    CHART_15M_REGION,
    CHART_1M_REGION,
    CHART_5M_REGION,
    CHART_60M_REGION,
    CHART_GRID_REGION,
    CROP_INSET_X,
    CROP_INSET_Y,
    ORDER_BOOK_REGION,
    SCREENSHOT_DIR,
)
from .logger import log_message

REGION_MAP = {
    "chart_60m": CHART_60M_REGION,
    "chart_15m": CHART_15M_REGION,
    "chart_5m": CHART_5M_REGION,
    "chart_1m": CHART_1M_REGION,
    "order_book": ORDER_BOOK_REGION,
}

TRADING_WINDOW_TITLE_KEYWORD = "OkFarm社区行情"

# 最近一轮微调的参考值，仅用于日志对比，不参与裁剪逻辑。
PREV_CHART_GRID_REGION = {"left": 2, "top": 66, "width": 1590, "height": 908}
PREV_ORDER_BOOK_REGION = {"left": 1594, "top": 66, "width": 274, "height": 908}
PREV_CHART_15M_REGION = {"left": 813, "top": 0, "width": 787, "height": 469}
PREV_CHART_5M_REGION = {"left": 0, "top": 457, "width": 829, "height": 469}
PREV_CHART_1M_REGION = {"left": 813, "top": 457, "width": 789, "height": 471}


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def focus_trading_window() -> bool:
    """尽可能激活行情端窗口；失败则记录日志后继续。"""
    found = {"hwnd": None, "title": None}

    EnumWindows = ctypes.windll.user32.EnumWindows
    GetWindowTextW = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    IsIconic = ctypes.windll.user32.IsIconic
    ShowWindow = ctypes.windll.user32.ShowWindow
    SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
    SW_RESTORE = 9

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def _enum_proc(hwnd, lparam):  # noqa: ANN001, ARG001
        if not IsWindowVisible(hwnd):
            return True
        length = GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value
        if TRADING_WINDOW_TITLE_KEYWORD in title:
            found["hwnd"] = hwnd
            found["title"] = title
            return False
        return True

    try:
        EnumWindows(WNDENUMPROC(_enum_proc), 0)
    except Exception as exc:  # noqa: BLE001
        log_message(f"截图前查找行情端窗口失败: {exc}")
        return False

    if not found["hwnd"]:
        log_message(f"未找到标题包含 {TRADING_WINDOW_TITLE_KEYWORD} 的窗口，继续按原逻辑截图。")
        return False

    hwnd = found["hwnd"]
    title = found["title"] or ""
    log_message(f"找到行情端窗口: {title}")

    try:
        if IsIconic(hwnd):
            ShowWindow(hwnd, SW_RESTORE)
            log_message("行情端窗口处于最小化状态，已执行 restore。")
        SetForegroundWindow(hwnd)
        log_message("已将行情端窗口切换到前台并激活。")
        time.sleep(0.5)
        log_message("截图前等待 0.5 秒完成。")
        return True
    except Exception as exc:  # noqa: BLE001
        log_message(f"激活行情端窗口失败，继续截图: {exc}")
        return False


def _click_into_trading_window(hwnd: int) -> Optional[Tuple[int, int]]:
    """点击行情窗口内部安全位置，用于触发界面稳定渲染。"""
    try:
        window_rect = _get_window_rect(hwnd)
    except Exception as exc:  # noqa: BLE001
        log_message(f"获取窗口矩形失败，无法执行进入行情点击: {exc}")
        return None

    click_x = window_rect["left"] + min(120, max(10, window_rect["width"] // 8))
    click_y = window_rect["top"] + min(120, max(10, window_rect["height"] // 8))
    log_message(f"点击进入行情坐标: ({click_x}, {click_y}) | window_rect={window_rect}")

    if pyautogui is None:
        log_message("pyautogui 不可用，已跳过真实点击，仅保留稳定化等待。")
        return (click_x, click_y)

    try:
        pyautogui.click(click_x, click_y)
        return (click_x, click_y)
    except Exception as exc:  # noqa: BLE001
        log_message(f"点击进入行情失败，继续执行等待流程: {exc}")
        return (click_x, click_y)


def _wait_for_window_stable(hwnd: int, wait_seconds: float = 0.8, checks: int = 3) -> Dict[str, int]:
    """等待窗口布局稳定，并重新获取最新窗口矩形。"""
    log_message(f"点击后等待界面稳定: wait_seconds={wait_seconds}, checks={checks}")
    time.sleep(wait_seconds)
    previous_rect: Optional[Dict[str, int]] = None
    stable_rect = _get_window_rect(hwnd)
    for _ in range(checks):
        current_rect = _get_window_rect(hwnd)
        if previous_rect is not None and current_rect == previous_rect:
            stable_rect = current_rect
            break
        previous_rect = current_rect
        stable_rect = current_rect
        time.sleep(0.2)
    log_message(f"等待稳定后重新获取窗口矩形: {stable_rect}")
    return stable_rect


def _find_trading_window() -> Tuple[Optional[int], str]:
    """返回行情端窗口句柄和标题。"""
    found = {"hwnd": None, "title": ""}

    EnumWindows = ctypes.windll.user32.EnumWindows
    GetWindowTextW = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def _enum_proc(hwnd, lparam):  # noqa: ANN001, ARG001
        if not IsWindowVisible(hwnd):
            return True
        length = GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value
        if TRADING_WINDOW_TITLE_KEYWORD in title:
            found["hwnd"] = hwnd
            found["title"] = title
            return False
        return True

    try:
        EnumWindows(WNDENUMPROC(_enum_proc), 0)
    except Exception as exc:  # noqa: BLE001
        log_message(f"查找行情端窗口失败: {exc}")

    return found["hwnd"], found["title"]


def _get_window_rect(hwnd: int) -> Dict[str, int]:
    rect = RECT()
    GetWindowRect = ctypes.windll.user32.GetWindowRect
    if not GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("获取窗口矩形失败")
    return {
        "left": int(rect.left),
        "top": int(rect.top),
        "width": int(rect.right - rect.left),
        "height": int(rect.bottom - rect.top),
    }


def _capture_window_full(hwnd: int, title: str, window_rect: Optional[Dict[str, int]] = None) -> Tuple[str, Image.Image, Dict[str, int]]:
    """保存完整行情端窗口截图，用于校准区域。"""
    if window_rect is None:
        window_rect = _get_window_rect(hwnd)
    _ensure_dir(SCREENSHOT_DIR)
    full_path = SCREENSHOT_DIR / f"window_full_{_timestamp()}.png"
    with mss.mss() as sct:
        shot = sct.grab(window_rect)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        image.save(full_path)
    log_message(f"完整行情端窗口截图已保存: {full_path} | 标题={title} | 矩形={window_rect}")
    return str(full_path), image, window_rect


def _crop_chart_grid(window_image: Image.Image, window_rect: Dict[str, int]) -> Tuple[Image.Image, Dict[str, int]]:
    grid_box = (
        CHART_GRID_REGION["left"],
        CHART_GRID_REGION["top"],
        CHART_GRID_REGION["left"] + CHART_GRID_REGION["width"],
        CHART_GRID_REGION["top"] + CHART_GRID_REGION["height"],
    )
    chart_grid = window_image.crop(grid_box)
    chart_grid_path = SCREENSHOT_DIR / f"chart_grid_{_timestamp()}.png"
    chart_grid.save(chart_grid_path)
    log_message(f"chart_grid 已保存: {chart_grid_path} | chart_grid_region={CHART_GRID_REGION} | window_rect={window_rect}")
    return chart_grid, {"left": 0, "top": 0, "width": chart_grid.size[0], "height": chart_grid.size[1]}


def _apply_inset(region: Dict[str, int]) -> Dict[str, int]:
    width = max(1, region["width"] - (2 * CROP_INSET_X))
    height = max(1, region["height"] - (2 * CROP_INSET_Y))
    return {
        "left": region["left"] + CROP_INSET_X,
        "top": region["top"] + CROP_INSET_Y,
        "width": width,
        "height": height,
    }


def _build_chart_regions() -> Dict[str, Dict[str, int]]:
    regions = {
        "chart_60m": _apply_inset(CHART_60M_REGION),
        "chart_15m": _apply_inset(CHART_15M_REGION),
        "chart_5m": _apply_inset(CHART_5M_REGION),
        "chart_1m": _apply_inset(CHART_1M_REGION),
    }
    log_message(
        f"子图裁剪参数: inset=({CROP_INSET_X}, {CROP_INSET_Y}), regions={regions}"
    )
    return regions


def _ensure_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def capture_region(
    region: Dict[str, int],
    name: str,
    window_image: Optional[Image.Image] = None,
    window_rect: Optional[Dict[str, int]] = None,
) -> str:
    _ensure_dir(SCREENSHOT_DIR)
    output_path = SCREENSHOT_DIR / f"{name}_{_timestamp()}.png"
    if window_image is not None and window_rect is not None:
        crop_box = (
            region["left"],
            region["top"],
            region["left"] + region["width"],
            region["top"] + region["height"],
        )
        image = window_image.crop(crop_box)
        image.save(output_path)
        log_message(
            f"区域截图保存完成: {output_path} | region={region} | relative_box={crop_box} | window_rect={window_rect}"
        )
        return str(output_path)

    with mss.mss() as sct:
        monitor = {
            "left": region["left"],
            "top": region["top"],
            "width": region["width"],
            "height": region["height"],
        }
        shot = sct.grab(monitor)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        image.save(output_path)
    log_message(f"区域截图保存完成: {output_path} | region={region} | screen_monitor={region}")
    return str(output_path)


def capture_all_regions() -> List[str]:
    """一次性截图全部关键区域。"""
    focus_trading_window()
    hwnd, title = _find_trading_window()
    window_image: Optional[Image.Image] = None
    window_rect: Optional[Dict[str, int]] = None
    chart_grid_image: Optional[Image.Image] = None
    chart_grid_rect: Optional[Dict[str, int]] = None
    if hwnd is not None:
        try:
            initial_window_rect = _get_window_rect(hwnd)
            log_message(f"点击进入行情前窗口矩形: {initial_window_rect}")
            _click_into_trading_window(hwnd)
            window_rect = _wait_for_window_stable(hwnd)
            window_full_path, window_image, window_rect = _capture_window_full(hwnd, title, window_rect)
            log_message(f"用于校准的完整窗口截图路径: {window_full_path}")
            log_message(f"完整窗口矩形: {window_rect}")
            log_message(
                f"CHART_GRID_REGION 调整前后: before={PREV_CHART_GRID_REGION}, after={CHART_GRID_REGION}"
            )
            log_message(
                f"ORDER_BOOK_REGION 调整前后: before={PREV_ORDER_BOOK_REGION}, after={ORDER_BOOK_REGION}"
            )
            chart_grid_image, chart_grid_rect = _crop_chart_grid(window_image, window_rect)
            log_message(f"chart_grid 已检测到并裁剪完成: {chart_grid_rect is not None}")
            log_message(f"order_book 区域已准备: {ORDER_BOOK_REGION}")
        except Exception as exc:  # noqa: BLE001
            log_message(f"保存完整窗口截图失败，继续按区域截图: {exc}")
    paths: List[str] = []
    if chart_grid_image is not None and chart_grid_rect is not None:
        split_regions = _build_chart_regions()
        for name in ["chart_60m", "chart_15m", "chart_5m", "chart_1m"]:
            region = split_regions[name]
            log_message(f"{name} region: {region}")
            paths.append(capture_region(region, name, window_image=chart_grid_image, window_rect=chart_grid_rect))
    else:
        split_regions = _build_chart_regions()
        for name in ["chart_60m", "chart_15m", "chart_5m", "chart_1m"]:
            region = split_regions[name]
            log_message(f"{name} region: {region}")
            paths.append(capture_region(region, name, window_image=chart_grid_image, window_rect=chart_grid_rect))

    order_book_region = REGION_MAP["order_book"]
    log_message(f"order_book region: {order_book_region}")
    paths.append(capture_region(order_book_region, "order_book", window_image=window_image, window_rect=window_rect))

    status_15m_right = "仍存在右侧过紧" if CHART_15M_REGION["width"] <= PREV_CHART_15M_REGION["width"] else "右侧已放松"
    status_1m_right = "仍存在右侧过紧" if CHART_1M_REGION["width"] <= PREV_CHART_1M_REGION["width"] else "右侧已放松"
    status_5m_cross = "仍存在右侧过紧或串图风险" if CHART_5M_REGION["width"] >= PREV_CHART_5M_REGION["width"] else "已收敛串图风险"
    status_bottom_tight = "底部指标区仍可能偏紧" if CHART_15M_REGION["height"] <= PREV_CHART_15M_REGION["height"] else "底部指标区已放松"
    log_message(
        f"问题检查: 15m={status_15m_right}, 1m={status_1m_right}, 5m={status_5m_cross}, bottom={status_bottom_tight}"
    )
    log_message("screenshot config frozen for chart regions")
    log_message("only order_book optional tuning allowed")
    log_message(f"最终裁剪参数: CHART_GRID_REGION={CHART_GRID_REGION}, ORDER_BOOK_REGION={ORDER_BOOK_REGION}, CHART_60M_REGION={CHART_60M_REGION}, CHART_15M_REGION={CHART_15M_REGION}, CHART_5M_REGION={CHART_5M_REGION}, CHART_1M_REGION={CHART_1M_REGION}")
    return paths


if __name__ == "__main__":
    print("开始测试截图模块...")
    for item in capture_all_regions():
        print(item)
    print("截图模块测试完成。")
