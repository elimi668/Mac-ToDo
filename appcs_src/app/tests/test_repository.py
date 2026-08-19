"""TaskRepository unit tests. Uses temporary file SQLite, non-interfering."""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.database.database import dispose_db, init_db
from app.database.repository import NO_CHANGE, TaskRepository


class TaskRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "test.db"
        init_db(f"sqlite:///{db_path}")
        self.repo = TaskRepository()

    def tearDown(self) -> None:
        # Release engine handle so Windows can delete temp file
        dispose_db()
        self._tmp.cleanup()

    # ---------- Create ----------
    def test_create_returns_task_with_defaults(self) -> None:
        task = self.repo.create("写周报")
        self.assertEqual(task.title, "写周报")
        self.assertEqual(task.category, "生活")
        self.assertEqual(task.priority, 2)
        self.assertFalse(task.completed)
        self.assertIsNone(task.deadline)
        self.assertIsNone(task.completed_time)
        self.assertIsNotNone(task.created_time)
        self.assertIsNotNone(task.id)

    def test_create_strips_title(self) -> None:
        task = self.repo.create("  带空格 ")
        self.assertEqual(task.title, "带空格")

    def test_create_empty_title_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.repo.create("   ")

    def test_create_invalid_priority_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.repo.create("x", priority=4)

    # ---------- Read ----------
    def test_get_by_id(self) -> None:
        created = self.repo.create("学习", category="学习", priority=1)
        fetched = self.repo.get_by_id(created.id)
        assert fetched is not None
        self.assertEqual(fetched.title, "学习")

    def test_get_by_id_missing_returns_none(self) -> None:
        self.assertIsNone(self.repo.get_by_id(9999))

    def test_list_all_orders_incomplete_first(self) -> None:
        t1 = self.repo.create("a")
        self.repo.set_completed(t1.id, True)
        t2 = self.repo.create("b")
        tasks = self.repo.list_all()
        self.assertEqual(tasks[0].id, t2.id)
        self.assertEqual(tasks[1].id, t1.id)

    def test_filter_by_category_and_priority(self) -> None:
        self.repo.create("a", category="工作", priority=1)
        self.repo.create("b", category="工作", priority=2)
        self.repo.create("c", category="学习", priority=1)

        work = self.repo.filter_tasks(category="工作")
        self.assertEqual(len(work), 2)
        high = self.repo.filter_tasks(priority=1)
        self.assertEqual(len(high), 2)
        work_high = self.repo.filter_tasks(category="工作", priority=1)
        self.assertEqual(len(work_high), 1)

    def test_filter_by_completed(self) -> None:
        t1 = self.repo.create("a")
        t2 = self.repo.create("b")
        self.repo.set_completed(t1.id, True)
        done = self.repo.filter_tasks(completed=True)
        self.assertEqual(len(done), 1)
        self.assertEqual(done[0].id, t1.id)
        todo = self.repo.filter_tasks(completed=False)
        self.assertEqual(len(todo), 1)
        self.assertEqual(todo[0].id, t2.id)

    # ---------- Update ----------
    def test_update_fields(self) -> None:
        task = self.repo.create("原标题", category="生活", priority=3)
        updated = self.repo.update(
            task.id,
            title="新标题",
            category="工作",
            priority=1,
            deadline=date(2026, 7, 20),
        )
        assert updated is not None
        self.assertEqual(updated.title, "新标题")
        self.assertEqual(updated.category, "工作")
        self.assertEqual(updated.priority, 1)
        self.assertEqual(updated.deadline.date(), date(2026, 7, 20))

    def test_update_only_provided_fields(self) -> None:
        task = self.repo.create("t", category="学习", priority=2)
        updated = self.repo.update(task.id, priority=1)
        assert updated is not None
        self.assertEqual(updated.priority, 1)
        self.assertEqual(updated.category, "学习")
        self.assertEqual(updated.title, "t")

    def test_update_deadline_no_change_keeps_value(self) -> None:
        d = date(2026, 7, 15)
        task = self.repo.create("t", deadline=d)
        updated = self.repo.update(task.id, title="改名")
        assert updated is not None
        self.assertEqual(updated.deadline.date(), d)

    def test_update_deadline_none_clears_value(self) -> None:
        task = self.repo.create("t", deadline=date(2026, 7, 15))
        updated = self.repo.update(task.id, deadline=None)
        assert updated is not None
        self.assertIsNone(updated.deadline)

    def test_update_missing_returns_none(self) -> None:
        self.assertIsNone(self.repo.update(9999, title="x"))

    def test_update_empty_title_raises(self) -> None:
        task = self.repo.create("t")
        with self.assertRaises(ValueError):
            self.repo.update(task.id, title="   ")

    # ---------- Completion ----------
    def test_set_completed_records_time(self) -> None:
        task = self.repo.create("t")
        updated = self.repo.set_completed(task.id, True)
        assert updated is not None
        self.assertTrue(updated.completed)
        self.assertIsNotNone(updated.completed_time)

    def test_set_uncompleted_clears_time(self) -> None:
        task = self.repo.create("t")
        self.repo.set_completed(task.id, True)
        updated = self.repo.set_completed(task.id, False)
        assert updated is not None
        self.assertFalse(updated.completed)
        self.assertIsNone(updated.completed_time)

    # ---------- Delete ----------
    def test_delete(self) -> None:
        task = self.repo.create("t")
        self.assertTrue(self.repo.delete(task.id))
        self.assertIsNone(self.repo.get_by_id(task.id))

    def test_delete_missing_returns_false(self) -> None:
        self.assertFalse(self.repo.delete(9999))

    def test_delete_twice_returns_false(self) -> None:
        task = self.repo.create("t")
        self.assertTrue(self.repo.delete(task.id))
        self.assertFalse(self.repo.delete(task.id))

    # ---------- Search ----------
    def test_filter_by_search_text(self) -> None:
        self.repo.create("写周报", category="工作", priority=1)
        self.repo.create("学习Python", category="学习", priority=2)
        self.repo.create("买咖啡", category="生活", priority=3)

        results = self.repo.filter_tasks(search_text="周报")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "写周报")

    def test_filter_by_search_text_no_match(self) -> None:
        self.repo.create("写周报")
        results = self.repo.filter_tasks(search_text="不存在的任务")
        self.assertEqual(len(results), 0)

    def test_filter_by_search_text_with_category(self) -> None:
        self.repo.create("写周报", category="工作")
        self.repo.create("学习Python", category="学习")
        self.repo.create("学习Java", category="学习")

        results = self.repo.filter_tasks(category="学习", search_text="学习")
        self.assertEqual(len(results), 2)

        results = self.repo.filter_tasks(category="工作", search_text="学习")
        self.assertEqual(len(results), 0)

    def test_filter_by_search_text_with_priority(self) -> None:
        self.repo.create("重要任务", priority=1)
        self.repo.create("普通任务", priority=2)

        results = self.repo.filter_tasks(priority=1, search_text="任务")
        self.assertEqual(len(results), 1)

    def test_filter_by_search_text_empty_returns_all(self) -> None:
        self.repo.create("任务A")
        self.repo.create("任务B")
        results = self.repo.filter_tasks(search_text="")
        self.assertEqual(len(results), 2)

    def test_list_all_with_search_text(self) -> None:
        self.repo.create("写周报")
        self.repo.create("学习Python")
        results = self.repo.list_all(search_text="Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "学习Python")


if __name__ == "__main__":
    unittest.main()
