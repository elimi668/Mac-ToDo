"""TaskService unit tests."""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app.database.database import dispose_db, init_db
from app.services.task_service import TaskService


class TaskServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "test.db"
        init_db(f"sqlite:///{db_path}")
        self.svc = TaskService()

    def tearDown(self) -> None:
        dispose_db()
        self._tmp.cleanup()

    def test_create_and_list(self) -> None:
        t = self.svc.create_task("写周报", category="工作", priority=1)
        self.assertEqual(t.title, "写周报")
        tasks = self.svc.list_all()
        self.assertEqual(len(tasks), 1)

    def test_group_by_date(self) -> None:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        future = today + timedelta(days=5)
        past = today - timedelta(days=1)

        self.svc.create_task("过期", deadline=past)
        self.svc.create_task("今天", deadline=today)
        self.svc.create_task("明天", deadline=tomorrow)
        self.svc.create_task("未来", deadline=future)
        self.svc.create_task("无日期")

        grouped = self.svc.group_by_date(self.svc.list_all())
        self.assertEqual(len(grouped["已过期"]), 1)
        self.assertEqual(len(grouped["今天"]), 1)
        self.assertEqual(len(grouped["明天"]), 1)
        self.assertEqual(len(grouped["未来"]), 1)
        self.assertEqual(len(grouped["无日期"]), 1)

    def test_get_grouped_filtered(self) -> None:
        today = date.today()
        self.svc.create_task("a", category="工作", priority=1, deadline=today)
        self.svc.create_task("b", category="学习", priority=2, deadline=today)

        grouped = self.svc.get_grouped_filtered(category="工作")
        total = sum(len(v) for v in grouped.values())
        self.assertEqual(total, 1)

    def test_set_completed(self) -> None:
        t = self.svc.create_task("t")
        updated = self.svc.set_completed(t.id, True)
        assert updated is not None
        self.assertTrue(updated.completed)
        self.assertIsNotNone(updated.completed_time)

    def test_delete(self) -> None:
        t = self.svc.create_task("t")
        self.assertTrue(self.svc.delete_task(t.id))
        self.assertIsNone(self.svc.get_task(t.id))

    # ---------- Search ----------
    def test_filter_by_search_text(self) -> None:
        self.svc.create_task("写周报", category="工作", priority=1)
        self.svc.create_task("学习Python", category="学习", priority=2)

        results = self.svc.filter_tasks(search_text="周报")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "写周报")

    def test_filter_by_search_text_no_match(self) -> None:
        self.svc.create_task("写周报")
        results = self.svc.filter_tasks(search_text="不存在的")
        self.assertEqual(len(results), 0)

    def test_filter_by_search_text_with_category(self) -> None:
        self.svc.create_task("写周报", category="工作")
        self.svc.create_task("学习Python", category="学习")
        self.svc.create_task("学习Java", category="学习")

        results = self.svc.filter_tasks(category="学习", search_text="学习")
        self.assertEqual(len(results), 2)

    def test_get_grouped_filtered_with_search(self) -> None:
        self.svc.create_task("写周报", category="工作")
        self.svc.create_task("学习Python", category="学习")
        grouped = self.svc.get_grouped_filtered(search_text="Python")
        total = sum(len(v) for v in grouped.values())
        self.assertEqual(total, 1)

    # ---------- Update Task Deadline Semantics ----------
    def test_update_task_clear_deadline_via_service(self) -> None:
        task = self.svc.create_task("t", deadline=date(2026, 7, 15))
        updated = self.svc.update_task(task.id, deadline=None)
        assert updated is not None
        self.assertIsNone(updated.deadline)

    def test_update_task_keep_deadline_when_not_specified(self) -> None:
        from app.database.repository import NO_CHANGE

        d = date(2026, 7, 15)
        task = self.svc.create_task("t", deadline=d)
        updated = self.svc.update_task(task.id, title="改名", deadline=NO_CHANGE)
        assert updated is not None
        self.assertEqual(updated.deadline.date(), d)

    def test_update_task_set_new_deadline(self) -> None:
        task = self.svc.create_task("t")
        new_deadline = date(2026, 8, 1)
        updated = self.svc.update_task(task.id, deadline=new_deadline)
        assert updated is not None
        self.assertEqual(updated.deadline.date(), new_deadline)


if __name__ == "__main__":
    unittest.main()

