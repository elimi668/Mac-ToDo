"""删除二次确认弹窗。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class ConfirmDialog(QDialog):
    """通用确认弹窗。"""

    def __init__(
        self,
        title: str = "确认",
        message: str = "确定要执行此操作吗？",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ConfirmDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(300)
        self._build_ui(message)

    def _build_ui(self, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        label = QLabel(message, self)
        label.setObjectName("ConfirmMessage")
        label.setWordWrap(True)
        layout.addWidget(label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Yes).setText("删除")
        buttons.button(QDialogButtonBox.StandardButton.No).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)