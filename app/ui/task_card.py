"""任务卡片：展示 Task 模型。支持多选（Shift+Click）、右键菜单编辑/删除/完成。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.models.task import Task

# 从 config 读取优先级标签，与 TaskDialog 保持一致
_PRIORITY_LABEL: dict[int, str] = {val: label for label, val in config.PRIORITY_OPTIONS}
_PRIORITY_COLOR: dict[int, str] = {
    1: config.COLOR_PRIORITY_HIGH,
    2: config.COLOR_PRIORITY_MEDIUM,
    3: config.COLOR_PRIORITY_LOW,
}


class TaskCard(QFrame):
    toggled = Signal(int, bool)
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    selected = Signal(int, bool)  # task_id, is_selected

    def __init__(self, task: Task, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TaskCard")
        self._task = task
        self._selected = False
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self._check = QCheckBox(self)
        self._check.setObjectName("TaskCheckbox")
        self._check.setChecked(task.completed)
        self._check.toggled.connect(self._on_toggled)
        layout.addWidget(self._check, 0, Qt.AlignVCenter)

        center = QVBoxLayout()
        center.setSpacing(2)
        self._title = QLabel(task.title, self)
        self._title.setObjectName("TaskTitle")
        self._title.setText(self._format_title(task.title, task.completed))
        center.addWidget(self._title)
        self._sub_label = QLabel(self._build_subtitle(task), self)
        self._sub_label.setObjectName("TaskSubtitle")
        if task.completed:
            self._sub_label.setProperty("done", True)
        center.addWidget(self._sub_label)
        layout.addLayout(center, stretch=1)

        dot = QLabel(self)
        dot.setObjectName("PriorityDot")
        dot.setFixedSize(10, 10)
        color = _PRIORITY_COLOR.get(task.priority, config.COLOR_TEXT_SECONDARY)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        layout.addWidget(dot, 0, Qt.AlignVCenter)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """点击卡片切换选中状态；Shift 时切换到 range 选中。"""
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._select_range()
            else:
                self._toggle_select()
            event.accept()
            return
        super().mousePressEvent(event)

    def _toggle_select(self) -> None:
        self._selected = not self._selected
        self._update_select_style()
        self.selected.emit(self._task.id, self._selected)

    def _select_range(self) -> None:
        """Shift+Click：从 _last_click_task_id 到当前卡片之间的所有卡片同步选中。"""
        main_window = self._find_main_window()
        if main_window is None:
            self._toggle_select()
            return
        last_id = getattr(main_window, "_last_click_task_id", None)
        if last_id is None:
            self._toggle_select()
            return
        parent = self.parent()
        if parent is None:
            self._toggle_select()
            return
        # 在当前 parent 中收集所有 TaskCard（保留顺序）
        cards = [w for w in parent.children() if isinstance(w, TaskCard)]
        idx_last = next((i for i, c in enumerate(cards) if getattr(c, "_task_id", None) == last_id), None)
        idx_curr = next((i for i, c in enumerate(cards) if c is self), None)
        if idx_last is None or idx_curr is None:
            self._toggle_select()
            return
        lo, hi = min(idx_last, idx_curr), max(idx_last, idx_curr)
        for c in cards[lo: hi + 1]:
            c._selected = True
            c._update_select_style()
            c.selected.emit(c._task.id, True)

    def _find_main_window(self) -> QWidget | None:
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "_last_click_task_id"):
                return parent
            parent = parent.parent()
        return None

    def _update_select_style(self) -> None:
        bg = "rgba(0,122,255,0.08)" if self._selected else "transparent"
        self.setStyleSheet(
            f"QFrame#TaskCard {{ background-color: {bg}; border-radius: 8px; }}"
        )

    @property
    def is_selected(self) -> bool:
        return self._selected

    @staticmethod
    def _format_title(title: str, done: bool) -> str:
        """用 <s> 标签实现删除线（QSS 不支持 text-decoration）。"""
        return f"<s>{title}</s>" if done else title

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        if self._task.completed:
            act_toggle = menu.addAction("取消完成")
        else:
            act_toggle = menu.addAction("完成")
        act_toggle.triggered.connect(self._toggle_via_menu)
        menu.addSeparator()
        act_edit = menu.addAction("编辑")
        act_edit.triggered.connect(lambda: self.edit_requested.emit(self._task.id))
        menu.addSeparator()
        act_del = menu.addAction("删除")
        act_del.triggered.connect(lambda: self.delete_requested.emit(self._task.id))
        menu.exec(self.mapToGlobal(pos))

    def _toggle_via_menu(self) -> None:
        self.toggled.emit(self._task.id, not self._task.completed)

    def _on_toggled(self, checked: bool) -> None:
        self._title.setProperty("done", checked)
        self._title.setText(self._format_title(self._task.title, checked))
        self._sub_label.setProperty("done", checked)
        self._sub_label.style().unpolish(self._sub_label)
        self._sub_label.style().polish(self._sub_label)
        self.toggled.emit(self._task.id, checked)

    @staticmethod
    def _build_subtitle(task: Task) -> str:
        parts = [task.category, _PRIORITY_LABEL.get(task.priority, "")]
        if task.deadline is not None:
            parts.append(task.deadline.strftime("%m-%d %H:%M"))
        if task.completed:
            parts.append("已完成")
        return " · ".join(p for p in parts if p)
