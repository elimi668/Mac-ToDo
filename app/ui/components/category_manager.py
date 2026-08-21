"""分类管理对话框：添加/删除/重命名分类，数据持久化到 data/categories.json。"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import config

_CATEGORIES_FILE: Path = config.APP_ROOT / "data" / "categories.json"
_DEFAULT_CATEGORIES: list[str] = ["全部", "工作", "学习", "生活"]


def _load_categories() -> list[str]:
    """加载持久化分类，缺失时返回默认值。"""
    if _CATEGORIES_FILE.exists():
        try:
            with open(_CATEGORIES_FILE, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return _DEFAULT_CATEGORIES.copy()


def _save_categories(categories: list[str]) -> None:
    """将分类持久化到 categories.json。确保'全部'始终在第一位。"""
    _CATEGORIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 确保"全部"在第一位
    if categories and categories[0] != "全部":
        categories = ["全部"] + [c for c in categories if c != "全部"]
    with open(_CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)


class CategoryManagerDialog(QDialog):
    """分类管理对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CategoryManagerDialog")
        self.setWindowTitle("管理分类")
        self.setModal(True)
        self.setMinimumWidth(320)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self._categories = _load_categories()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 分类列表
        self._list = QListWidget(self)
        self._list.setObjectName("CategoryList")
        for cat in self._categories:
            self._list.addItem(QListWidgetItem(cat))
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
        dialog.setWindowTitle("添加分类")
        layout = QVBoxLayout(dialog)
        edit = QLineEdit(dialog)
        edit.setPlaceholderText("输入分类名称...")
        layout.addWidget(edit)
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
            name = edit.text().strip()
            if name and name not in self._categories:
                self._categories.append(name)
                self._list.addItem(name)

    def _on_rename(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        old_name = item.text()
        if old_name == "全部":
            return
        from PySide6.QtWidgets import QDialog, QLineEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("重命名分类")
        layout = QVBoxLayout(dialog)
        edit = QLineEdit(dialog)
        edit.setText(old_name)
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
            if new_name and new_name != old_name and new_name not in self._categories:
                idx = self._categories.index(old_name)
                self._categories[idx] = new_name
                item.setText(new_name)

    def _on_delete(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        name = item.text()
        if name == "全部":
            return
        from app.ui.components.confirm_dialog import ConfirmDialog
        ok = ConfirmDialog(
            self,
            title="确认删除",
            message=f"确定要删除分类「{name}」吗？",
        )
        if ok.exec() == QDialog.DialogCode.Accepted:
            row = self._list.row(item)
            self._categories.remove(name)
            self._list.takeItem(row)

    def _on_accept(self) -> None:
        _save_categories(self._categories)
        self.accept()

    @property
    def categories(self) -> list[str]:
        return self._categories.copy()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dlg = CategoryManagerDialog()
    dlg.exec()
