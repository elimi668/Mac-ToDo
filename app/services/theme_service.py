"""主题服务：检测系统主题、持久化用户偏好、切换亮暗主题。"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import QWidget

from app import config

_THEME_FILE: Path = config.APP_ROOT / "data" / "theme.json"
_STYLES_DIR: Path = config.APP_ROOT / "styles"


class ThemeService:
    """管理主题检测、持久化和切换。"""

    def __init__(self, window: QWidget | None = None) -> None:
        self._window = window
        self._current_theme: str = self._load_persisted()

    # ---------- 持久化 ----------

    @staticmethod
    def _load_persisted() -> str:
        if _THEME_FILE.exists():
            try:
                with open(_THEME_FILE, encoding="utf-8") as f:
                    saved = json.load(f).get("theme")
                    if saved in ("light", "dark"):
                        return saved
            except (json.JSONDecodeError, OSError):
                pass
        return detect_system_theme()

    def _save(self, theme: str) -> None:
        _THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_THEME_FILE, "w", encoding="utf-8") as f:
            json.dump({"theme": theme}, f)
        self._current_theme = theme

    # ---------- 切换 ----------

    def toggle(self) -> str:
        """切换亮/暗主题并持久化，返回新主题名。"""
        new_theme = "dark" if self._current_theme == "light" else "light"
        self._save(new_theme)
        self._apply(new_theme)
        return new_theme

    def _apply(self, theme: str) -> None:
        """将指定主题的 QSS 加载到窗口。"""
        fp = _STYLES_DIR / f"{theme}.qss"
        if fp.exists() and self._window is not None:
            self._window.setStyleSheet(fp.read_text(encoding="utf-8"))

    # ---------- 查询 ----------

    @property
    def current_theme(self) -> str:
        return self._current_theme

    def theme_icon_text(self) -> str:
        """返回主题按钮的显示文本（☀️ 亮色 / 🌙 暗色）。"""
        return "\U0001f319" if self._current_theme == "light" else "\U0001f311"


def detect_system_theme() -> str:
    """检测系统级亮/暗色偏好。非 Windows 默认返回 light。"""
    import platform
    if platform.system() != "Windows":
        return "light"
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except OSError:
        return "light"
