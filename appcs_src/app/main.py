"""程序入口：延迟导入 UI、全局异常处理、托盘常驻、截止提醒。"""
from __future__ import annotations

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from app import config
from app.database.database import init_db
from app.database.repository import TaskRepository
from app.utils.backup import backup_on_startup


def _global_excepthook(exc_type, exc_value, exc_tb) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(msg, file=sys.stderr)
    QMessageBox.critical(None, "程序异常", "发生未捕获异常：\n\n{}".format(exc_value))


def main() -> int:
    sys.excepthook = _global_excepthook

    init_db()
    backup_on_startup()

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    qss_path = config.STYLES_FILE
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    from app.ui.main_window import MainWindow
    from app.ui.tray import TrayManager
    from app.services.reminder_service import ReminderService

    window = MainWindow()
    window.show()

    tray = TrayManager(window)
    tray.show()

    # 截止提醒（需要 tray 和 window）
    repo = TaskRepository()
    ReminderService(repo, tray.tray_icon, window)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())