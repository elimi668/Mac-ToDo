"""筛选行组件：类型/等级/日期三个下拉框，横向排列。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from app import config


class FilterRow(QWidget):
    """顶部筛选行。"""

    filter_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("FilterRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)

        # 类型筛选
        cat_label = QLabel("类型:", self)
        cat_label.setStyleSheet("color: #86868B; font-size: 12px;")
        layout.addWidget(cat_label)

        self._cat_combo = QComboBox(self)
        self._cat_combo.setObjectName("FilterCombo")
        self._cat_combo.addItems(["全部"] + config.CATEGORIES[1:])
        self._cat_combo.currentTextChanged.connect(self._emit)
        layout.addWidget(self._cat_combo)

        # 等级筛选
        pri_label = QLabel("等级:", self)
        pri_label.setStyleSheet("color: #86868B; font-size: 12px;")
        layout.addWidget(pri_label)

        self._pri_combo = QComboBox(self)
        self._pri_combo.setObjectName("FilterCombo")
        self._pri_combo.addItems([label for label, _ in config.PRIORITY_FILTERS])
        self._pri_combo.currentTextChanged.connect(self._emit)
        layout.addWidget(self._pri_combo)

        # 日期筛选
        date_label = QLabel("日期:", self)
        date_label.setStyleSheet("color: #86868B; font-size: 12px;")
        layout.addWidget(date_label)

        self._date_combo = QComboBox(self)
        self._date_combo.setObjectName("FilterCombo")
        self._date_combo.addItems(["全部", "今天", "明天", "本周", "已过期"])
        self._date_combo.currentTextChanged.connect(self._emit)
        layout.addWidget(self._date_combo)

        layout.addStretch(1)

    def _emit(self) -> None:
        self.filter_changed.emit()

    @property
    def selected_category(self) -> str | None:
        idx = self._cat_combo.currentIndex()
        if idx == 0 or idx <= 0:
            return None
        return config.CATEGORIES[idx]

    @property
    def selected_priority(self) -> int | None:
        idx = self._pri_combo.currentIndex()
        if idx <= 0:
            return None
        return config.PRIORITY_FILTERS[idx][1]

    @property
    def selected_date_filter(self) -> str:
        return self._date_combo.currentText()
