"""ReminderService 单元测试。"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from PySide6.QtCore import QTimerEvent
from PySide6.QtWidgets import QApplication

from app.database.database import dispose_db, init_db
from app.database.repository import TaskRepository
from app.services.reminder_service import ReminderService


class ReminderServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "test.db"
        init_db("sqlite:///{}".format(db_path))
        self.repo = TaskRepository()

    def tearDown(self) -> None:
        dispose_db()
        self._tmp.cleanup()

    def _make_service(self, visible=True):
        mock_tray = MagicMock()
        mock_parent = MagicMock()
        mock_parent.isVisible.return_value = visible
        return ReminderService(self.repo, mock_tray, mock_parent)

    def test_due_task_triggers_reminder(self):
        today = date.today()
        t = self.repo.create("到期任务", deadline=datetime.now() + timedelta(minutes=5))
        svc = self._make_service()
        svc._check()
        refetched = self.repo.get_by_id(t.id)
        self.assertTrue(refetched.reminded)

    def test_future_task_not_triggered(self):
        future = date.today() + timedelta(days=30)
        t = self.repo.create("远处的任务", deadline=future)
        svc = self._make_service()
        svc._check()
        refetched = self.repo.get_by_id(t.id)
        self.assertFalse(refetched.reminded)

    def test_completed_task_not_triggered(self):
        today = date.today()
        t = self.repo.create("已完成的任务", deadline=today)
        self.repo.set_completed(t.id, True)
        svc = self._make_service()
        svc._check()
        refetched = self.repo.get_by_id(t.id)
        self.assertFalse(refetched.reminded)

    def test_already_reminded_not_triggered(self):
        today = date.today()
        t = self.repo.create("已提醒的任务", deadline=today)
        self.repo.mark_reminded(t.id)
        svc = self._make_service()
        svc._check()
        svc._tray.showMessage.assert_not_called()

    def test_only_remind_once(self):
        today = date.today()
        t = self.repo.create("只提醒一次", deadline=datetime.now() + timedelta(minutes=5))
        svc = self._make_service()
        svc._check()
        svc._check()
        refetched = self.repo.get_by_id(t.id)
        self.assertTrue(refetched.reminded)
        svc._tray.showMessage.assert_called_once()


if __name__ == "__main__":
    unittest.main()