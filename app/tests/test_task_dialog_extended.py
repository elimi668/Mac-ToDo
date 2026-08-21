"""TaskDialog 单元测试。验证 deadline 语义和表单数据返回。"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone

from PySide6.QtWidgets import QApplication

from app.models.task import Task

_qapp: QApplication | None = None


def get_qapp() -> QApplication:
    global _qapp
    if _qapp is None:
        _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


def _make_task(title: str = "测试任务", **overrides) -> Task:
    from app.models.task import Task

    kwargs = {
        "id": 1,
        "title": title,
        "category": "生活",
        "priority": 2,
        "deadline": None,
        "created_time": datetime.now(tz=timezone.utc),
        "completed": False,
        "reminded": False,
        "completed_time": None,
        **overrides,
    }
    task = Task(**kwargs)
    task.id = kwargs["id"]
    return task


class TaskDialogDeadlineTest(unittest.TestCase):
    """验证截止日期字段的语义（NO_CHANGE / None / datetime）。"""

    def setUp(self) -> None:
        self.app = get_qapp()
        from app.ui.components.task_dialog import TaskDialog

        self.dialog = TaskDialog(_make_task(id=1, title="有截止日期", deadline=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)))

    def tearDown(self) -> None:
        self.dialog.deleteLater()

    def test_deadline_not_touched_returns_no_change(self) -> None:
        """不修改日期时，deadline 应为 NO_CHANGE。"""
        from app.database.repository import NO_CHANGE

        # 不调用任何日期操作，直接检查
        self.assertFalse(self.dialog._deadline_was_touched)
        result = self.dialog.result_data
        self.assertIs(result[3], NO_CHANGE)

    def test_clear_deadline_sets_none(self) -> None:
        """点击清除按钮后，deadline 应为 None。"""

        self.dialog._on_clear_date()
        result = self.dialog.result_data
        self.assertEqual(result[3], None)  # 清除 → None

    def test_modify_deadline_sets_datetime(self) -> None:
        """手动修改日期后，deadline 应为 datetime 对象。"""
        from datetime import datetime as dt

        self.dialog._on_clear_date()       # 先清除
        self.dialog._on_date_changed()     # 再设为有效日期
        result = self.dialog.result_data
        self.assertIsInstance(result[3], dt)


class TaskDialogValueTest(unittest.TestCase):
    """验证标题、分类、优先级返回值。"""

    def setUp(self) -> None:
        self.app = get_qapp()
        from app.ui.components.task_dialog import TaskDialog

        self.dialog = TaskDialog(_make_task(id=2, title="初始标题", category="工作", priority=1))

    def tearDown(self) -> None:
        self.dialog.deleteLater()

    def test_result_title_is_stripped(self) -> None:
        self.dialog._title_edit.setText("  带空格的标题  ")
        result = self.dialog.result_data
        self.assertEqual(result[0], "带空格的标题")

    def test_result_category(self) -> None:

        self.dialog._category_combo.setCurrentIndex(0)  # 工作
        result = self.dialog.result_data
        self.assertEqual(result[1], "工作")

        self.dialog._category_combo.setCurrentIndex(1)  # 学习
        result = self.dialog.result_data
        self.assertEqual(result[1], "学习")

    def test_result_priority(self) -> None:
        self.dialog._priority_combo.setCurrentIndex(0)  # 高
        result = self.dialog.result_data
        self.assertEqual(result[2], 1)

        self.dialog._priority_combo.setCurrentIndex(1)  # 中
        result = self.dialog.result_data
        self.assertEqual(result[2], 2)

        self.dialog._priority_combo.setCurrentIndex(2)  # 低
        result = self.dialog.result_data
        self.assertEqual(result[2], 3)


if __name__ == "__main__":
    unittest.main()
