"""截止提醒服务。动态计算检查间隔：以最近截止日期为准，避免固定轮询的浪费和延迟。"""
from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QWidget

from app.database.repository import TaskRepository


class ReminderService:
    """截止提醒服务，采用动态调度替代固定 60 秒轮询。"""

    # 最小检查间隔（秒），避免无 deadline 任务时过于频繁
    _MIN_CHECK_INTERVAL_S = 30
    # 最大检查间隔（秒），确保不会遗漏即将到期的任务
    _MAX_CHECK_INTERVAL_S = 60

    def __init__(
        self,
        repo: TaskRepository,
        tray: QSystemTrayIcon,
        parent: QWidget,
        lead_minutes: int = 15,
    ) -> None:
        self._repo = repo
        self._tray = tray
        self._parent = parent
        self._lead_minutes = lead_minutes
        self._flashing = False
        self._flash_timer: QTimer | None = None
        self._restore_icon: QIcon | None = None

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._check)
        self._schedule_next()

    def _schedule_next(self, delay_seconds: int | None = None) -> None:
        """安排下一次检查。delay_seconds 为秒数；None 时自动计算。"""
        if delay_seconds is None:
            delay_seconds = self._compute_next_delay()
        ms = max(delay_seconds * 1000, 1000)  # 至少 1 秒
        self._timer.start(ms)

    def _compute_next_delay(self) -> int:
        """根据最近未提醒任务的截止时间和当前时间，计算下次检查间隔（秒）。"""
        now = datetime.now()
        tasks = self._repo.list_due_reminders(now, lead_minutes=self._lead_minutes)
        if tasks:
            # 有任务即将到期，立即检查
            return 0
        # 找所有未提醒任务的最近截止日期
        nearest = self._find_nearest_deadline(now)
        if nearest is not None:
            seconds_until = (nearest - now).total_seconds()
            # 在 lead_minutes 窗口之前，按剩余时间的一半调度（上限 MAX）
            return min(max(int(seconds_until / 2), self._MIN_CHECK_INTERVAL_S), self._MAX_CHECK_INTERVAL_S)
        # 没有截止日期的任务，用最大间隔
        return self._MAX_CHECK_INTERVAL_S

    def _find_nearest_deadline(self, now: datetime) -> datetime | None:
        """找到最近的一个未提醒的截止日期。"""
        from sqlalchemy import select
        from app.models.task import Task

        with self._repo._get_session() as session:
            stmt = (
                select(Task.deadline)
                .where(
                    Task.completed == False,
                    Task.reminded == False,
                    Task.deadline.is_not(None),
                    Task.deadline > now,
                )
                .order_by(Task.deadline.asc())
                .limit(1)
            )
            result = session.scalar(stmt)
            return result  # type: ignore[return-value]

    def _check(self) -> None:
        now = datetime.now()
        tasks = self._repo.list_due_reminders(now, lead_minutes=self._lead_minutes)
        print(f"[Reminder] check time: {now.isoformat()}, found: {len(tasks)} due tasks")
        for t in tasks:
            dl = t.deadline.isoformat() if t.deadline else "None"
            print(f"[Reminder]   task id={t.id} title={t.title!r} deadline={dl}")
        if not tasks:
            self._stop_flash()
            self._schedule_next()
            return

        for task in tasks:
            if task.deadline is None:
                continue
            print(f"[Reminder] notify: id={task.id} title={task.title!r}")
            self._notify(task)
            self._repo.mark_reminded(task.id)

        # 检查完一批后，安排下一次
        self._schedule_next()

    def _notify(self, task: object) -> None:
        title = "任务即将到期"
        msg = f'"{task.title}" 将在 {task.deadline} 截止'  # type: ignore[attr-defined]

        if self._parent.isVisible():
            self._tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 5000)
        else:
            self._tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 5000)
            self._start_flash()

    def _start_flash(self) -> None:
        if self._flashing:
            return
        self._flashing = True
        self._restore_icon = self._tray.icon()
        self._flash_timer = QTimer()
        self._flash_timer.timeout.connect(self._flash_tick)
        self._flash_timer.start(800)

    def _flash_tick(self) -> None:
        if self._tray.icon().isNull():
            return
        if self._flash_timer.property("on") is True:
            self._tray.setIcon(QIcon())
            self._flash_timer.setProperty("on", False)
        else:
            self._tray.setIcon(self._restore_icon)
            self._flash_timer.setProperty("on", True)

    def _stop_flash(self) -> None:
        if self._flashing and self._restore_icon is not None:
            self._tray.setIcon(self._restore_icon)
        self._flashing = False
        if self._flash_timer is not None:
            self._flash_timer.stop()
            self._flash_timer = None
