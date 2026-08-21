"""优先级管理对话框：添加/删除/重命名优先级，数据持久化到 data/priorities.json。"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import config

_PRIORITIES_FILE: Path = config.APP_ROOT / "data" / "priorities.json"
_DEFAULT_PRIORITIES: list[list] = [["高", 1], ["中", 2], ["低", 3]]


def _load_priorities() -> list[list]:
    """加载持久化优先级，缺失时返回默认值。"""
    if _PRIORITIES_FILE.exists():
        try:
            with open(_PRIORITIES_FILE, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    # JSON 将 tuple 序列化为 list，直接返回 list 即可
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return _DEFAULT_PRIORITIES.copy()


def _save_priorities(priorities: list[list]) -> None:
    """将优先级持久化到 priorities.json。"""
    _PRIORITIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_PRIORITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(priorities, f, ensure_ascii=False, indent=2)


class PriorityManagerDialog(QDialog):
    """优先级管理对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PriorityManagerDialog")
        self.setWindowTitle("管理优先级")
        self.setModal(True)
        self.setMinimumWidth(320)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self._priorities = _load_priorities()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 优先级列表
        self._list = QListWidget(self)
        self._list.setObjectName("PriorityList")
        for name, value in self._priorities:
            self._list.addItem(QListWidgetItem(f"{name} (值: {value})"))
        layout.addWidget(self._list)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._add_btn = QPushButton("添加", self)
        self._add_btn.setObjectName("SettingsButton")
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self._add_btn)

        self._rename_btn = QPushButton("重命名", self)
        self._rename_btn.setObjectName("SettingsButton")
        self._rename_btn.setCursor(Qt.PointingHandCursor)
        self._rename_btn.clicked.connect(self._on_rename)
        btn_layout.addWidget(self._rename_btn)

        self._delete_btn = QPushButton("删除", self)
        self._delete_btn.setObjectName("SettingsButton")
        self._delete_btn.setCursor(Qt.PointingHandCursor)
        self._delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self._delete_btn)

        btn_layout.addStretch(1)
        layout.addLayout(btn_layout)

        layout.addStretch(1)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_add(self) -> None:
        from PySide6.QtWidgets import QDialog, QLineEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("添加优先级")
        layout = QVBoxLayout(dialog)

        name_edit = QLineEdit(dialog)
        name_edit.setPlaceholderText("输入优先级名称...")
        layout.addWidget(QLabel("名称:", dialog))
        layout.addWidget(name_edit)

        value_edit = QLineEdit(dialog)
        value_edit.setPlaceholderText("输入优先级值（整数）...")
        layout.addWidget(QLabel("值:", dialog))
        layout.addWidget(value_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("添加")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            value_str = value_edit.text().strip()
            if name and value_str:
                try:
                    value = int(value_str)
                    if value > 0 and (name, value) not in self._priorities:
                        self._priorities.append((name, value))
                        self._list.addItem(QListWidgetItem(f"{name} (值: {value})"))
                except ValueError:
                    pass

    def _on_rename(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        text = item.text()
        # 解析 "名称 (值: X)" 格式
        if " (值:" in text:
            name = text.split(" (值:")[0]
        else:
            name = text
        if not name:
            return

        from PySide6.QtWidgets import QDialog, QLineEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("重命名优先级")
        layout = QVBoxLayout(dialog)
        edit = QLineEdit(dialog)
        edit.setText(name)
        layout.addWidget(edit)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("重命名")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = edit.text().strip()
            if new_name and new_name != name:
                idx = next((i for i, (n, _) in enumerate(self._priorities) if n == name), None)
                if idx is not None:
                    self._priorities[idx] = (new_name, self._priorities[idx][1])
                    item.setText(f"{new_name} (值: {self._priorities[idx][1]})")

    def _on_delete(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        if len(self._priorities) <= 1:
            return
        text = item.text()
        if " (值:" in text:
            name = text.split(" (值:")[0]
        else:
            name = text
        from app.ui.components.confirm_dialog import ConfirmDialog
        ok = ConfirmDialog(
            self,
            title="确认删除",
            message=f"确定要删除优先级「{name}」吗？",
        )
        if ok.exec() == QDialog.DialogCode.Accepted:
            row = self._list.row(item)
            self._priorities = [(n, v) for n, v in self._priorities if n != name]
            self._list.takeItem(row)

    def _on_accept(self) -> None:
        _save_priorities(self._priorities)
        self.accept()

    @property
    def priorities(self) -> list[tuple[str, int]]:
        return self._priorities.copy()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dlg = PriorityManagerDialog()
    dlg.exec()
