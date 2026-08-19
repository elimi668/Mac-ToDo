"""TaskDialog unit tests: deadline clear behavior."""
from __future__ import annotations

import unittest
from datetime import date, datetime

from PySide6.QtWidgets import QApplication

from app.database.database import dispose_db, init_db
from app.database.repository import NO_CHANGE, TaskRepository
from app.models.task import Task
from app.ui.components.task_dialog import TaskDialog


class TaskDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        import tempfile
        from pathlib import Path

        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "test.db"
        init_db(f"sqlite:///{db_path}")
        self.repo = TaskRepository()

    def tearDown(self) -> None:
        dispose_db()
        self._tmp.cleanup()

    def _open_dialog_with_deadline(self, deadline: date | None) -> TaskDialog:
        task = self.repo.create("测试任务", deadline=deadline)
        dialog = TaskDialog(task)
        return dialog

    def test_load_task_without_deadline_returns_no_change(self) -> None:
        dialog = self._open_dialog_with_deadline(None)
        _, _cat, _pri, deadline = dialog.result_data
        self.assertIs(deadline, NO_CHANGE)

    def test_load_task_with_deadline_preserves_it(self) -> None:
        d = date(2026, 8, 15)
        dialog = self._open_dialog_with_deadline(d)
        _, _cat, _pri, deadline = dialog.result_data
        assert isinstance(deadline, datetime)
        self.assertEqual(deadline.date(), d)

    def test_clear_deadline_via_button(self) -> None:
        dialog = self._open_dialog_with_deadline(date(2026, 7, 15))
        dialog._btn_clear_date.click()
        self._app.processEvents()
        _, _cat, _pri, deadline = dialog.result_data
        self.assertIsNone(deadline)

    def test_result_data_after_clearing_then_setting_new_date(self) -> None:
        dialog = self._open_dialog_with_deadline(date(2026, 7, 15))
        dialog._btn_clear_date.click()
        self._app.processEvents()
        new_dt = datetime(2026, 9, 1, 10, 30, 0)
        dialog._date_edit.setDateTime(
            datetime(new_dt.year, new_dt.month, new_dt.day, new_dt.hour, new_dt.minute, new_dt.second)
        )
        _, _cat, _pri, deadline = dialog.result_data
        assert isinstance(deadline, datetime)
        self.assertEqual(deadline.date(), date(2026, 9, 1))


if __name__ == "__main__":
    unittest.main()
