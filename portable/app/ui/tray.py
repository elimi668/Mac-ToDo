"""系统托盘图标管理。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from app import config
from app.utils import autostart


class TrayManager:
    """托盘图标：双击显示窗口，右键菜单。"""

    def __init__(self, window: QWidget) -> None:
        self._window = window
        self._tray = QSystemTrayIcon(self._make_icon(), window)
        self._tray.setToolTip(config.TRAY_TOOLTIP)
        self._tray.activated.connect(self._on_activated)
        self._build_menu()

    def _make_icon(self) -> QIcon:
        """使用自定义图标或回退到绘制图标。"""
        icon_path = config.ICONS_DIR / "app_icon.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if not pixmap.isNull():
                return QIcon(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # 回退：绘制默认图标
        pm = QPixmap(64, 64)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor("#007AFF"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(4, 4, 56, 56, 14, 14)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, config.TRAY_ICON_TEXT)
        p.end()
        return QIcon(pm)

    def _build_menu(self) -> None:
        menu = QMenu()

        act_show = QAction("显示窗口", menu)
        act_show.triggered.connect(self._window.show)
        menu.addAction(act_show)

        act_hide = QAction("隐藏窗口", menu)
        act_hide.triggered.connect(self._window.hide)
        menu.addAction(act_hide)

        menu.addSeparator()

        self._act_autostart = QAction("开机启动", menu)
        self._act_autostart.setCheckable(True)
        self._act_autostart.setChecked(autostart.is_enabled())
        self._act_autostart.triggered.connect(self._toggle_autostart)
        menu.addAction(self._act_autostart)

        act_backup = QAction("立即备份", menu)
        act_backup.triggered.connect(self._backup_now)
        menu.addAction(act_backup)

        act_report = QAction("生成日报", menu)
        act_report.triggered.connect(self._generate_daily_report)
        menu.addAction(act_report)

        menu.addSeparator()

        act_quit = QAction("退出", menu)
        act_quit.triggered.connect(self._window.close)
        act_quit.triggered.connect(QApplication.quit)
        menu.addAction(act_quit)

        self._tray.setContextMenu(menu)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()

    def _toggle_autostart(self) -> None:
        autostart.toggle()

    def _backup_now(self) -> None:
        from app.utils.backup import backup_db
        backup_db()

    def _generate_daily_report(self) -> None:
        """生成日报并展示预览窗口。"""
        from app.database.repository import TaskRepository
        from app.services.daily_report_service import DailyReportService
        from app.ui.components.report_dialog import ReportDialog

        repo = TaskRepository()
        service = DailyReportService(repo)
        report = service.generate()

        cb = QApplication.clipboard()
        cb.setText(report)

        dialog = ReportDialog(report, self._window)
        dialog.exec()

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    @property
    def tray_icon(self) -> QSystemTrayIcon:
        """供 ReminderService 访问。"""
        return self._tray
