"""搜索框组件：带图标的搜索输入框，实时触发搜索信号。"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget


class SearchBar(QWidget):
    """顶部搜索框。输入变化实时触发 search_changed(text) 信号。"""

    search_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SearchBar")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        icon = QLabel("搜索", self)
        icon.setStyleSheet("font-size: 13px; color: #86868B;")
        layout.addWidget(icon)

        self._edit = QLineEdit(self)
        self._edit.setObjectName("SearchEdit")
        self._edit.setPlaceholderText("搜索任务...")
        self._edit.setClearButtonEnabled(True)
        self._edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._edit, stretch=1)

    def _on_text_changed(self, text: str) -> None:
        self.search_changed.emit(text.strip())

    @property
    def search_text(self) -> str:
        return self._edit.text().strip()

    def set_search_text(self, text: str) -> None:
        self._edit.setText(text)

    def clear(self) -> None:
        self._edit.clear()
