"""批量操作单元测试：batch_set_completed / batch_toggle_tasks / batch_delete。"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.database.database import dispose_db, init_db
from app.services.task_service import TaskService


class BatchOperationsTest(unittest.TestCase):
    """批量操作测试套件。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "test.db"
        init_db(f"sqlite:///{db_path}")
        self.svc = TaskService()

    def tearDown(self) -> None:
        dispose_db()
        self._tmp.cleanup()

    def _create_tasks(self, count: int = 5) -> list[int]:
        """创建多个任务并返回它们的 ID 列表。"""
        ids = []
        for i in range(count):
            task = self.svc.create_task(f"任务 {i}", category="工作", priority=1)
            ids.append(task.id)
        return ids

    # ---------- batch_set_completed ----------

    def test_batch_set_completed_normal(self) -> None:
        """正常情况：批量标记为完成。"""
        ids = self._create_tasks(5)
        updated = self.svc.batch_set_completed(ids, True)
        self.assertEqual(updated, 5)
        for tid in ids:
            task = self.svc.get_task(tid)
            self.assertIsNotNone(task)
            self.assertTrue(task.completed)

    def test_batch_set_completed_empty_list(self) -> None:
        """空列表应返回 0。"""
        updated = self.svc.batch_set_completed([], True)
        self.assertEqual(updated, 0)

    def test_batch_set_completed_invalid_ids_ignored(self) -> None:
        """包含不存在的 task_id 时应忽略并返回实际更新数。"""
        ids = self._create_tasks(3)
        invalid_ids = [99999, 88888]
        all_ids = ids + invalid_ids
        updated = self.svc.batch_set_completed(all_ids, True)
        self.assertEqual(updated, 3)  # 只有 3 个有效 ID

    def test_batch_set_completed_toggle_back(self) -> None:
        """批量取消完成。"""
        ids = self._create_tasks(3)
        # 先全部完成
        self.svc.batch_set_completed(ids, True)
        # 再取消完成
        updated = self.svc.batch_set_completed(ids, False)
        self.assertEqual(updated, 3)
        for tid in ids:
            task = self.svc.get_task(tid)
            self.assertFalse(task.completed)

    # ---------- batch_toggle_tasks ----------

    def test_batch_toggle_tasks_normal(self) -> None:
        """正常情况：批量切换完成状态。"""
        ids = self._create_tasks(5)
        toggled = self.svc.batch_toggle_tasks(ids)
        self.assertEqual(toggled, 5)
        for tid in ids:
            task = self.svc.get_task(tid)
            self.assertTrue(task.completed)  # 从 False 切换到 True

    def test_batch_toggle_tasks_empty_list(self) -> None:
        """空列表应返回 0。"""
        toggled = self.svc.batch_toggle_tasks([])
        self.assertEqual(toggled, 0)

    def test_batch_toggle_tasks_invalid_ids_ignored(self) -> None:
        """包含不存在的 task_id 时应忽略。"""
        ids = self._create_tasks(2)
        all_ids = ids + [99999]
        toggled = self.svc.batch_toggle_tasks(all_ids)
        self.assertEqual(toggled, 2)

    def test_batch_toggle_tasks_toggle_back(self) -> None:
        """再次切换应恢复原始状态。"""
        ids = self._create_tasks(3)
        self.svc.batch_toggle_tasks(ids)  # 完成
        self.svc.batch_toggle_tasks(ids)  # 取消完成
        for tid in ids:
            task = self.svc.get_task(tid)
            self.assertFalse(task.completed)

    # ---------- batch_delete ----------

    def test_batch_delete_normal(self) -> None:
        """正常情况：批量删除。"""
        ids = self._create_tasks(5)
        deleted = self.svc.batch_delete(ids)
        self.assertEqual(deleted, 5)
        for tid in ids:
            self.assertIsNone(self.svc.get_task(tid))

    def test_batch_delete_empty_list(self) -> None:
        """空列表应返回 0。"""
        deleted = self.svc.batch_delete([])
        self.assertEqual(deleted, 0)

    def test_batch_delete_invalid_ids_ignored(self) -> None:
        """包含不存在的 task_id 时应忽略。"""
        ids = self._create_tasks(2)
        all_ids = ids + [99999, 88888]
        deleted = self.svc.batch_delete(all_ids)
        self.assertEqual(deleted, 2)

    def test_batch_delete_partial(self) -> None:
        """部分有效 ID 应只删除有效的。"""
        ids = self._create_tasks(3)
        partial_ids = ids[:2] + [99999]
        deleted = self.svc.batch_delete(partial_ids)
        self.assertEqual(deleted, 2)
        # 第 3 个任务应仍然存在
        self.assertIsNotNone(self.svc.get_task(ids[2]))


if __name__ == "__main__":
    unittest.main()
