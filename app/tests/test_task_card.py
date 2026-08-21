"""TaskCard 单元测试。验证信号发射、完成状态切换、右键菜单及焦点高亮样式。"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from app.models.task import Task

# 必须在全局创建 QApplication 实例（每个测试类只能有一个）
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
    # SQLAlchemy ORM 需要 session 才能正常运作 id；这里直接手动设置
    task.id = kwargs["id"]
    return task


class TaskCardSignalTest(unittest.TestCase):
    """验证 TaskCard 信号正确发射。"""

    def setUp(self) -> None:
        self.app = get_qapp()
        from app.ui.task_card import TaskCard

        self.task = _make_task(id=42, title="信号测试任务")
        self.card = TaskCard(self.task)

    def tearDown(self) -> None:
        self.card.deleteLater()

    def test_toggled_signal_emits_id_and_state(self) -> None:
        """勾选复选框应发射 toggled(task_id, checked) 信号。"""
        emitted: list[tuple[int, bool]] = []
        self.card.toggled.connect(lambda tid, state: emitted.append((tid, state)))
        self.card._on_toggled(True)
        self.assertEqual(emitted, [(42, True)])

    def test_edit_requested_signal(self) -> None:
        """右键菜单"编辑"应发射 edit_requested(task_id) 信号。"""
        emitted: list[int] = []
        self.card.edit_requested.connect(lambda tid: emitted.append(tid))
        self.card._show_context_menu(MagicMock())
        self.assertIn(2, emitted)  # edit_requested 在菜单关闭前发射

    def test_delete_requested_signal(self) -> None:
        """右键菜单"删除"应发射 delete_requested(task_id) 信号。"""
        emitted: list[int] = []
        self.card.delete_requested.connect(lambda tid: emitted.append(tid))
        self.card._show_context_menu(MagicMock())
        self.assertIn(2, emitted)


class TaskCardSubtitleTest(unittest.TestCase):
    """验证任务副标题格式。"""

    def setUp(self) -> None:
        self.app = get_qapp()
        from app.ui.task_card import TaskCard

        self.card = TaskCard(_make_task(id=1, title="测试标题"))

    def tearDown(self) -> None:
        self.card.deleteLater()

    def test_subtitle_with_category_and_priority(self) -> None:
        parts = self.card._build_subtitle(self.card._task)
        self.assertIn("生活", parts)
        self.assertIn("中", parts)

    def test_subtitle_with_deadline(self) -> None:
        from datetime import datetime

        task = _make_task(
            id=2,
            deadline=datetime(2026, 8, 15, 14, 30, tzinfo=timezone.utc),
        )
        subtitle = self.card._build_subtitle(task)
        self.assertIn("08-15 14:30", subtitle)

    def test_subtitle_no_deadline(self) -> None:
        task = _make_task(id=3, deadline=None)
        subtitle = self.card._build_subtitle(task)
        self.assertNotIn("-", subtitle.split(" · ")[-1] if " · " in subtitle else subtitle)


class TaskCardFocusStyleTest(unittest.TestCase):
    """验证焦点高亮属性设置（无需显示窗口）。"""

    def setUp(self) -> None:
        self.app = get_qapp()
        from app.ui.task_card import TaskCard

        self.card = TaskCard(_make_task(id=10, title="焦点测试"))

    def tearDown(self) -> None:
        self.card.deleteLater()

    def test_focus_property_set_and_unset(self) -> None:
        self.card.setProperty("focused", True)
        self.assertTrue(self.card.property("focused"))
        self.card.setProperty("focused", False)
        self.assertFalse(self.card.property("focused"))


if __name__ == "__main__":
    unittest.main()
