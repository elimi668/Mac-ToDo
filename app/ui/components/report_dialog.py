"""日报预览对话框。"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app import config


def _markdown_to_html(md: str) -> str:
    """简易 Markdown → HTML（仅覆盖日报常用语法）。"""
    html = md

    # 标题 # → <h1>, ## → <h2>
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)

    # 斜体 *text* → <em>text>
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # 列表项 - [x] / - [ ] → <li>
    html = re.sub(r"^[-*] \[x\] (.+)$", r'<li style="list-style-type: none;">&#10004; \1</li>', html, flags=re.MULTILINE)
    html = re.sub(r"^[-*] \[ \] (.+)$", r'<li style="list-style-type: none;">&#10068; \1</li>', html, flags=re.MULTILINE)

    # 空行保留
    html = re.sub(r"\n{2,}", "</p><p>", html)

    return f"<html><head><style>body{{font-family:{config.FONT_FAMILY};font-size:13px;line-height:1.6;}}h1{{font-size:16px;font-weight:bold;margin-top:12px;}}h2{{font-size:14px;font-weight:bold;margin-top:10px;}}</style></head><body>{html}</body></html>"


class ReportDialog(QDialog):
    """Markdown 日报预览对话框。"""

    def __init__(self, report_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ReportDialog")
        self.setWindowTitle("日报预览")
        self.setModal(True)
        self.setMinimumSize(560, 460)
        self.resize(620, 520)
        self.setMaximumSize(900, 700)
        self._report_text = report_text
        self._build_ui()

    def showEvent(self, event) -> None:
        """窗口显示时相对于父窗口居中。"""
        super().showEvent(event)
        parent = self.parent()
        if parent and hasattr(parent, "geometry"):
            parent_geom = parent.geometry()
            dialog_rect = self.frameGeometry()
            center_pos = parent_geom.center() - dialog_rect.center()
            self.move(center_pos)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # --- 标题区域 ---
        header = QWidget(self)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        today_str = datetime.now(tz=timezone.utc).date().strftime("%Y-%m-%d")
        title_label = QLabel(f"\U0001f4cb 任务日报 \u00b7 {today_str}", self)
        title_label.setObjectName("ReportTitle")
        font = title_label.font()
        font.setPointSizeF(20)
        font.setBold(True)
        title_label.setFont(font)

        subtitle_label = QLabel("支持复制与导出", self)
        subtitle_label.setObjectName("ReportSubtitle")
        sub_font = subtitle_label.font()
        sub_font.setPointSizeF(10)
        subtitle_label.setFont(sub_font)
        subtitle_label.setStyleSheet("color: palette(text); opacity: 0.55;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        root.addWidget(header)

        # --- Markdown 展示区域 ---
        scroll = QScrollArea(self)
        scroll.setObjectName("ReportScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QTextBrowser(scroll)
        content.setObjectName("ReportContent")
        content.setOpenExternalLinks(False)
        content.setHtml(_markdown_to_html(self._report_text))
        content.setFont(QFontDatabase.systemFont(QFontDatabase.GeneralFont))
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # --- 底部按钮 ---
        btn_box = QDialogButtonBox(self)

        btn_copy = QPushButton("复制到剪贴板", btn_box)
        btn_save = QPushButton("保存为 .md", btn_box)
        btn_close = QPushButton("关闭", btn_box)

        for btn in (btn_copy, btn_save, btn_close):
            btn.setFixedHeight(36)

        btn_copy.clicked.connect(self._copy_to_clipboard)
        btn_save.clicked.connect(self._save_as_md)
        btn_close.clicked.connect(self.close)

        hbox = QVBoxLayout()
        hbox.setSpacing(8)
        hbox.addWidget(btn_copy)
        hbox.addWidget(btn_save)
        hbox.addWidget(btn_close)
        hbox.addStretch(1)

        btn_box.setLayout(hbox)
        root.addWidget(btn_box)

    def _copy_to_clipboard(self) -> None:
        cb = QApplication.clipboard()
        cb.setText(self._report_text)

    def _save_as_md(self) -> None:
        today_str = datetime.now(tz=timezone.utc).date().strftime("%Y%m%d")
        default_name = f"日报_{config.APP_NAME}_{today_str}.md"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "保存日报",
            str(Path.home() / "Documents" / default_name),
            "Markdown (*.md);;All Files (*)",
        )
        if filepath:
            if not filepath.endswith(".md"):
                filepath += ".md"
            Path(filepath).write_text(self._report_text, encoding="utf-8")