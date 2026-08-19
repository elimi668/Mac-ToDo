"""全局配置常量。集中管理窗口尺寸、颜色、字体等。"""
from __future__ import annotations

from pathlib import Path

# ---------- 路径 ----------
APP_ROOT: Path = Path(__file__).resolve().parent
RESOURCES_DIR: Path = APP_ROOT / "resources"
ICONS_DIR: Path = RESOURCES_DIR / "icons"
STYLES_DIR: Path = RESOURCES_DIR / "styles"
STYLES_FILE: Path = APP_ROOT / "ui" / "styles.qss"

# ---------- 窗口 ----------
APP_NAME: str = "Mac Todo"
WINDOW_WIDTH: int = 560
WINDOW_HEIGHT: int = 680
WINDOW_RADIUS: int = 12
TITLEBAR_HEIGHT: int = 44
SHADOW_BLUR: int = 30
SHADOW_MARGIN: int = 20
CONTENT_PADDING: int = 20
CARD_SPACING: int = 10

# ---------- 颜色 ----------
COLOR_BG: str = "#F5F5F7"
COLOR_CARD: str = "#FFFFFF"
COLOR_PRIMARY: str = "#007AFF"
COLOR_TEXT: str = "#1D1D1F"
COLOR_TEXT_SECONDARY: str = "#86868B"
COLOR_SIDEBAR: str = "#EFEFF2"
COLOR_PRIORITY_HIGH: str = "#FF3B30"
COLOR_PRIORITY_MEDIUM: str = "#FF9500"
COLOR_PRIORITY_LOW: str = "#34C759"

# ---------- 字体 ----------
FONT_FAMILY: str = "Segoe UI Variable, SF Pro Text, PingFang SC, Microsoft YaHei UI, sans-serif"

# ---------- 分类 ----------
CATEGORIES: list[str] = ["全部", "工作", "学习", "生活"]
PRIORITY_FILTERS: list[tuple[str, int | None]] = [("全部", None), ("高", 1), ("中", 2), ("低", 3)]

# ---------- 托盘 ----------
TRAY_TOOLTIP: str = "Mac Todo"
TRAY_ICON_TEXT: str = "T"

# ---------- 备份 ----------
BACKUP_DIR: Path = APP_ROOT / "data" / "backup"
BACKUP_INTERVAL_HOURS: float = 24.0

# ---------- 快捷键 ----------
SHORTCUT_NEW: str = "Ctrl+N"
SHORTCUT_QUIT: str = "Ctrl+Q"
SHORTCUT_FOCUS_INPUT: str = "Ctrl+L"

# ---------- 窗口缩放 ----------
WINDOW_MIN_WIDTH: int = 480
WINDOW_MAX_WIDTH: int = 700