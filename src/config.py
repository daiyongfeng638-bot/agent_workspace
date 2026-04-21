"""全局配置集中管理。"""

from __future__ import annotations

from pathlib import Path

# ===== 基础路径 =====
BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = LOG_DIR / "screenshots"
ANALYSIS_LOG_DIR = LOG_DIR / "analysis"
TRADE_LOG_DIR = LOG_DIR / "trades"

# ===== 调度配置 =====
SCREENSHOT_INTERVAL_MINUTES = 15
POSITION_CHECK_INTERVAL_SECONDS = 180
MAX_SINGLE_DIRECTION_LOTS = 30
COOLDOWN_AFTER_EXIT_MINUTES = 15
AUTO_FILL_ORDER = True
AUTO_SUBMIT_ORDER = False
CONFIDENCE_THRESHOLD = 75
DEFAULT_LOT_SIZE = 5

# ===== 固定截图区域占位 =====
# TODO: 以下坐标仅为示例值，表示“相对行情端窗口左上角”的偏移，请根据真实布局人工修正。
# 当前语义：左上=60m，右上=15m，左下=5m，右下=1m，最右=盘口。
# TODO: 以下坐标仍为示例值，表示“相对行情端窗口左上角”的偏移，请结合 window_full_*.png 校准。
# NOTE: 当前 chart 截图参数已冻结为稳定基线，后续不要再调整下列 chart 区域。
CHART_GRID_REGION = {"left": 2, "top": 66, "width": 1616, "height": 918}
# NOTE: 盘口区当前主要问题是宽度过窄；本轮仅做右侧信息补全，尽量不影响四宫格图表。
ORDER_BOOK_REGION = {"left": 1608, "top": 66, "width": 328, "height": 908}

# 四宫格在 chart_grid 内的裁剪内边距，避免截到相邻面板的指标尾部。
CROP_INSET_X = 2
CROP_INSET_Y = 2

# ===== 旧字段兼容映射 =====
# TODO: 仅用于兼容旧代码路径，后续请逐步迁移到新语义名称。
CHART_60M_REGION = {"left": 0, "top": 0, "width": 811, "height": 455}
# NOTE: 右侧边界紧贴盘口区，右向扩展只能做安全微调，避免跨面板串图。
CHART_15M_REGION = {"left": 813, "top": 0, "width": 807, "height": 473}
CHART_5M_REGION = {"left": 0, "top": 457, "width": 829, "height": 477}
CHART_1M_REGION = {"left": 813, "top": 457, "width": 809, "height": 479}
CHART_REGION = CHART_60M_REGION
ORDER_PANEL_REGION = ORDER_BOOK_REGION
POSITION_REGION = CHART_5M_REGION
PRICE_REGION = CHART_1M_REGION

# ===== 冻结基线说明 =====
CHART_REGIONS_FROZEN = True
ORDER_BOOK_ONLY_OPTIONAL_TUNING = True

# ===== 自动填单点击坐标占位 =====
# TODO: 以下位置仅为示例值，请根据真实交易软件按钮位置人工修正。
BUY_BUTTON_POS = (1130, 260)
SELL_BUTTON_POS = (1250, 260)
PRICE_INPUT_POS = (1125, 340)
LOT_INPUT_POS = (1125, 390)

# ===== 其他配置 =====
ENV_FILE = BASE_DIR / ".env"
TIMEZONE = "Asia/Shanghai"
