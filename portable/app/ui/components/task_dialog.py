"""编辑任务弹窗：修改标题 / 分类 / 等级 / 截止日期。统一 Mac 风格。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, QDateTime, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.repository import NO_CHANGE
from app.models.task import Task

_CATEGORIES = ["工作", "学习", "生活"]
_PRIORITY_LABELS = [("高", 1), ("中", 2), ("低", 3)]
_PRIORITY_VALUES = {1: 0, 2: 1, 3: 2}  # priority -> combo index


class TaskDialog(QDialog):
    """编辑任务弹窗。"""

    def __init__(self, task: Task, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TaskDialog")
        self.setWindowTitle("编辑任务")
        self.setModal(True)
        self.setMinimumWidth(340)
        # Mac 风格：无边框 + 圆角
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self._task = task
        self._deadline_was_touched = task.deadline is not None
        self._deadline_was_cleared = False
        self._build_ui()
        self._load_task()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 标题输入
        self._title_edit = QLineEdit(self)
        self._title_edit.setObjectName("QuickInputEdit")
        layout.addWidget(self._title_edit)

        # 分类 + 等级 + 日期 横排
        row = QHBoxLayout()
        row.setSpacing(8)

        self._category_combo = QComboBox(self)
        self._category_combo.setObjectName("FilterCombo")
        self._category_combo.addItems(_CATEGORIES)
        row.addWidget(self._category_combo)

        self._priority_combo = QComboBox(self)
        self._priority_combo.setObjectName("FilterCombo")
        for label, _val in _PRIORITY_LABELS:
            self._priority_combo.addItem(label)
        row.addWidget(self._priority_combo)

        # 日期选择 + 清除按钮
        self._date_edit = QDateTimeEdit(self)
        self._date_edit.setObjectName("FilterCombo")
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._date_edit.setSpecialValueText("无日期")
        self._date_edit.setMinimumDate(QDate(2000, 1, 1))
        self._btn_clear_date = QPushButton("x", self)
        self._btn_clear_date.setFixedSize(24, 24)
        self._btn_clear_date.setCursor(Qt.PointingHandCursor)
        self._btn_clear_date.setToolTip("清除截止日期")
        self._btn_clear_date.setStyleSheet(
            "QPushButton { background: transparent; border: none; font-size: 14px; color: #999; }"
            "QPushButton:hover { color: #333; }"
        )
        self._btn_clear_date.clicked.connect(self._on_clear_date)
        self._date_edit.dateTimeChanged.connect(self._on_date_changed)
        self._date_row = QHBoxLayout()
        self._date_row.addWidget(self._date_edit, stretch=1)
        self._date_row.addWidget(self._btn_clear_date)
        row.addLayout(self._date_row)

        layout.addLayout(row)

        # 错误提示
        self._error_label = QLabel(self)
        self._error_label.setObjectName("ErrorLabel")
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_clear_date(self) -> None:
        self._date_edit.setDateTime(QDateTime())
        self._deadline_was_touched = True
        self._deadline_was_cleared = True

    def _on_date_changed(self) -> None:
        # User manually changed the date; reset cleared flag if they set a real date
        qd = self._date_edit.dateTime().date()
        if qd != self._date_edit.minimumDate():
            self._deadline_was_cleared = False

    def _load_task(self) -> None:
        self._title_edit.setText(self._task.title)
        # 分类
        idx = _CATEGORIES.index(self._task.category) if self._task.category in _CATEGORIES else 0
        self._category_combo.setCurrentIndex(idx)
        # 等级
        pidx = _PRIORITY_VALUES.get(self._task.priority, 1)
        self._priority_combo.setCurrentIndex(pidx)
        # 日期
        if self._task.deadline is not None:
            d = self._task.deadline
            self._date_edit.setDateTime(QDateTime(d.year, d.month, d.day, d.hour, d.minute, d.second))
        else:
            self._date_edit.setDateTime(QDateTime())

    def _on_accept(self) -> None:
        title = self._title_edit.text().strip()
        if not title:
            self._error_label.setText("任务标题不能为空")
            self._error_label.show()
            return
        self._error_label.hide()
        self.accept()

    @property
    def result_data(self) -> tuple[str, str, int, datetime | None | object]:
        """返回编辑后的数据：title, category, priority, deadline。
        deadline 为 NO_CHANGE 表示未修改，None 表示清除，datetime 表示新截止日期。
        """
        title = self._title_edit.text().strip()
        category = self._category_combo.currentText()
        priority = _PRIORITY_LABELS[self._priority_combo.currentIndex()][1]

        if not self._deadline_was_touched:
            deadline: datetime | None | object = NO_CHANGE
        elif self._deadline_was_cleared:
            deadline = None
        else:
            qdt = self._date_edit.dateTime()
            qd = qdt.date()
            if qd == self._date_edit.minimumDate():
                deadline = None
            else:
                deadline = qdt.toPython()

        return title, category, priority, deadline
