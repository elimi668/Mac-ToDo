"""程序入口：延迟导入 UI、全局异常处理、托盘常驻、截止提醒。"""
from __future__ import annotations

import sys
import traceback

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app import config
from app.database.database import init_db
from app.database.repository import TaskRepository
from app.utils.backup import backup_on_startup
from app.utils.single_instance import SingleInstance


def _global_excepthook(exc_type, exc_value, exc_tb) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(msg, file=sys.stderr)
    QMessageBox.critical(None, "程序异常", f"发生未捕获异常：\n\n{exc_value}")


def main() -> int:
    # ── 单实例检查 ───────────────────────────────────────────────────────────
    # 防止用户双击两次或从不同位置启动多个进程 / 窗口
    if not SingleInstance(app_name=config.APP_NAME).try_lock():
        QMessageBox.warning(
            None,
            "已在运行",
            f"「{config.APP_NAME}」已经在运行，请勿重复启动。",
        )
        return 0

    sys.excepthook = _global_excepthook

    init_db()
    backup_on_startup()

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # 设置应用图标（任务栏和窗口）
    icon_path = config.ICONS_DIR / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    qss_path = config.STYLES_FILE
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    from app.services.reminder_service import ReminderService
    from app.ui.main_window import MainWindow
    from app.ui.tray import TrayManager

    window = MainWindow()
    window.setWindowFlags(window.windowFlags() | Qt.CustomizeWindowHint)
    window.show()

    tray = TrayManager(window)
    tray.show()

    # 截止提醒（需要 tray 和 window）
    repo = TaskRepository()
    ReminderService(repo, tray.tray_icon, window)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())