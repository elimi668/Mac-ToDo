"""快速输入栏：两行布局。第一行标题+添加，第二行类型/等级/日期。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_CATEGORIES = ["工作", "学习", "生活"]
_PRIORITIES = [("中", 2), ("高", 1), ("低", 3)]


class TaskInputBar(QWidget):
    task_added = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TaskInputBar")
        self._pending: tuple[str, str, int, date | None] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        # 第一行：标题 + 添加
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(8)

        self._title_edit = QLineEdit(self)
        self._title_edit.setObjectName("QuickInputEdit")
        self._title_edit.setPlaceholderText("输入任务内容...")
        self._title_edit.setClearButtonEnabled(True)
        self._title_edit.returnPressed.connect(self._on_add)
        row1.addWidget(self._title_edit, stretch=1)

        self._add_btn = QPushButton("添加", self)
        self._add_btn.setObjectName("AddButton")
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add)
        row1.addWidget(self._add_btn)

        outer.addLayout(row1)

        # 第二行：类型 / 等级 / 日期
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(8)

        cat_label = QLabel("类型:", self)
        cat_label.setStyleSheet("color: #86868B; font-size: 12px;")
        row2.addWidget(cat_label)

        self._category_combo = QComboBox(self)
        self._category_combo.setObjectName("FilterCombo")
        self._category_combo.addItems(_CATEGORIES)
        row2.addWidget(self._category_combo)

        pri_label = QLabel("等级:", self)
        pri_label.setStyleSheet("color: #86868B; font-size: 12px;")
        row2.addWidget(pri_label)

        self._priority_combo = QComboBox(self)
        self._priority_combo.setObjectName("FilterCombo")
        for label, _val in _PRIORITIES:
            self._priority_combo.addItem(label)
        row2.addWidget(self._priority_combo)

        date_label = QLabel("截止:", self)
        date_label.setStyleSheet("color: #86868B; font-size: 12px;")
        row2.addWidget(date_label)

        self._date_edit = QDateTimeEdit(self)
        self._date_edit.setObjectName("FilterCombo")
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDateTime(QDateTime.currentDateTime())
        self._date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._date_edit.setSpecialValueText("无日期")
        self._date_edit.setMinimumDate(QDate(2000, 1, 1))
        row2.addWidget(self._date_edit)

        row2.addStretch(1)
        outer.addLayout(row2)

        # 错误提示
        self._error_label = QLabel(self)
        self._error_label.setObjectName("ErrorLabel")
        self._error_label.hide()
        outer.addWidget(self._error_label)

    def _on_add(self) -> None:
        title = self._title_edit.text().strip()
        if not title:
            self._show_error("任务标题不能为空")
            return
        category = self._category_combo.currentText()
        priority = _PRIORITIES[self._priority_combo.currentIndex()][1]
        qdt = self._date_edit.dateTime()
        deadline: datetime | None = qdt.toPython()
        self._clear_error()
        self._pending = (title, category, priority, deadline)
        self._title_edit.clear()
        self.task_added.emit()
    def _show_error(self, msg: str) -> None:
        self._error_label.setText(msg)
        self._error_label.show()

    def _clear_error(self) -> None:
        self._error_label.hide()
        self._error_label.clear()

    @property
    def pending_input(self) -> tuple[str, str, int, datetime | None] | None:
        return self._pending
