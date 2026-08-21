"""设置对话框：备份间隔、提醒提前量、开机自启、主题切换。配置持久化到 data/settings.json。"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.services.theme_service import ThemeService
from app.utils import autostart

_SETTINGS_FILE: Path = config.APP_ROOT / "data" / "settings.json"


def _load_settings() -> dict:
    """加载持久化设置，缺失时返回默认值。"""
    if _SETTINGS_FILE.exists():
        try:
            with open(_SETTINGS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "backup_interval_hours": config.BACKUP_INTERVAL_HOURS,
        "reminder_lead_minutes": 15,
        "autostart": False,
        "theme": "light",
    }


def _save_settings(data: dict) -> None:
    """将设置持久化到 settings.json。"""
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class SettingsDialog(QDialog):
    """应用设置对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumWidth(380)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self._settings = _load_settings()
        self._theme_service = ThemeService(parent) if parent else None

        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── 备份间隔 ──────────────────────────────────────────────────
        self._spin_backup = self._make_spinbox(
            min_val=1, max_val=168, default=int(self._settings.get("backup_interval_hours", 24)),
        )
        self._add_setting_row(
            layout,
            label="备份间隔（小时）",
            hint="距上次备份超过此时间后自动备份",
            widget=self._spin_backup,
        )

        # ── 提醒提前量 ──────────────────────────────────────────────────
        self._spin_reminder = self._make_spinbox(
            min_val=1, max_val=1440, default=int(self._settings.get("reminder_lead_minutes", 15)),
        )
        self._add_setting_row(
            layout,
            label="提醒提前量（分钟）",
            hint="截止前多少分钟发送提醒",
            widget=self._spin_reminder,
        )

        # ── 分割线 ──────────────────────────────────────────────────────
        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("Separator")
        layout.addWidget(sep)

        # ── 开机自启 ────────────────────────────────────────────────────
        auto_layout = QHBoxLayout()
        auto_label = QLabel("开机自启", self)
        auto_label.setObjectName("SettingsLabel")
        auto_layout.addWidget(auto_label)
        auto_layout.addStretch(1)
        self._chk_autostart = QCheckBox(self)
        self._chk_autostart.setObjectName("SettingsCheckbox")
        self._chk_autostart.setChecked(bool(self._settings.get("autostart", False)))
        self._chk_autostart.stateChanged.connect(self._on_autostart_toggled)
        auto_layout.addWidget(self._chk_autostart)
        layout.addLayout(auto_layout)

        # ── 分割线 ──────────────────────────────────────────────────────
        sep2 = QFrame(self)
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("Separator")
        layout.addWidget(sep2)

        # ── 主题切换 ────────────────────────────────────────────────────
        theme_layout = QHBoxLayout()
        theme_label = QLabel("主题", self)
        theme_label.setObjectName("SettingsLabel")
        theme_layout.addWidget(theme_label)
        theme_layout.addStretch(1)
        self._btn_theme = QPushButton(
            self._theme_service.theme_icon_text() if self._theme_service else "☀️", self
        )
        self._btn_theme.setObjectName("SettingsThemeButton")
        self._btn_theme.setCursor(Qt.PointingHandCursor)
        self._btn_theme.setFixedSize(40, 32)
        self._btn_theme.clicked.connect(self._on_toggle_theme)
        theme_layout.addWidget(self._btn_theme)
        layout.addLayout(theme_layout)

        layout.addStretch(1)

        # ── 分类/优先级管理 ──────────────────────────────────────────────
        mgr_layout = QHBoxLayout()
        mgr_label = QLabel("数据管理", self)
        mgr_label.setObjectName("SettingsLabel")
        mgr_layout.addWidget(mgr_label)
        mgr_layout.addStretch(1)

        self._btn_manage_categories = QPushButton("管理分类", self)
        self._btn_manage_categories.setObjectName("SettingsButton")
        self._btn_manage_categories.setCursor(Qt.PointingHandCursor)
        self._btn_manage_categories.clicked.connect(self._on_manage_categories)
        mgr_layout.addWidget(self._btn_manage_categories)

        self._btn_manage_priorities = QPushButton("管理优先级", self)
        self._btn_manage_priorities.setObjectName("SettingsButton")
        self._btn_manage_priorities.setCursor(Qt.PointingHandCursor)
        self._btn_manage_priorities.clicked.connect(self._on_manage_priorities)
        mgr_layout.addWidget(self._btn_manage_priorities)

        layout.addLayout(mgr_layout)

        # ── 按钮 ────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_setting_row(
        self,
        parent_layout: QVBoxLayout,
        *,
        label: str,
        hint: str,
        widget: QWidget,
    ) -> None:
        """添加一行设置项：标签 + 说明文字 + 控件。"""
        row = QHBoxLayout()
        row.setSpacing(12)

        left = QVBoxLayout()
        lbl = QLabel(label, self)
        lbl.setObjectName("SettingsLabel")
        left.addWidget(lbl)
        hint_lbl = QLabel(hint, self)
        hint_lbl.setObjectName("SettingsHint")
        hint_lbl.setStyleSheet("color: #86868B; font-size: 11px;")
        left.addWidget(hint_lbl)
        left.addStretch(1)
        row.addLayout(left, stretch=1)
        row.addWidget(widget)

        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("Separator")

        full = QVBoxLayout()
        full.addLayout(row)
        full.addWidget(sep)
        parent_layout.addLayout(full)

    @staticmethod
    def _make_spinbox(*, min_val: int, max_val: int, default: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setObjectName("FilterCombo")
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setFixedWidth(80)
        return spin

    def _on_toggle_theme(self) -> None:
        if self._theme_service is None:
            return
        new_theme = self._theme_service.toggle()
        self._btn_theme.setText(self._theme_service.theme_icon_text())
        self._settings["theme"] = new_theme

    def _on_autostart_toggled(self, state: int) -> None:
        """开机自启开关变化时立即应用。"""
        enabled = state == Qt.CheckState.Checked.value
        autostart.toggle() if enabled else autostart.disable()
        self._settings["autostart"] = autostart.is_enabled()

    def _on_accept(self) -> None:
        self._settings["backup_interval_hours"] = self._spin_backup.value()
        self._settings["reminder_lead_minutes"] = self._spin_reminder.value()
        self._settings["autostart"] = self._chk_autostart.isChecked()
        _save_settings(self._settings)
        self.accept()

    def _on_manage_categories(self) -> None:
        """打开分类管理对话框。"""
        from app.ui.components.category_manager import CategoryManagerDialog

        dialog = CategoryManagerDialog(self)
        dialog.exec()

    def _on_manage_priorities(self) -> None:
        """打开优先级管理对话框。"""
        from app.ui.components.priority_manager import PriorityManagerDialog

        dialog = PriorityManagerDialog(self)
        dialog.exec()
