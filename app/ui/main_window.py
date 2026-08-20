"""Main window: borderless + rounded corners + shadow + draggable + traffic lights + vertical three-section layout."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QKeySequence, QMouseEvent, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# 窗口图标路径
WINDOW_ICON_PATH = Path(__file__).resolve().parent.parent / "resources" / "icons" / "app_icon.png"

from app import config
from app.services.task_service import TaskService
from app.services.theme_service import ThemeService
from app.ui.components.confirm_dialog import ConfirmDialog
from app.ui.components.filter_row import FilterRow
from app.ui.components.date_section import DateSection
from app.ui.components.task_dialog import TaskDialog
from app.ui.components.task_input_bar import TaskInputBar
from app.ui.components.search_bar import SearchBar
from app.ui.task_card import TaskCard

_bucket_order = ("已过期", "今天", "明天", "未来", "无日期")


class MainWindow(QWidget):
    def __init__(self, service: TaskService | None = None) -> None:
        super().__init__()
        self._drag_offset: QPoint | None = None
        self._service = service or TaskService()
        self._theme_service = ThemeService(self)
        self._setup_window()
        self._build_ui()
        # 增量更新：维护 task_id → TaskCard 映射，避免全量重建
        self._task_cards: dict[int, TaskCard] = {}
        self._refresh_tasks()
        self._update_theme_icon()

    def _toggle_theme(self) -> None:
        self._theme_service.toggle()
        self._update_theme_icon()

    def _update_theme_icon(self) -> None:
        self._btn_theme.setText(self._theme_service.theme_icon_text())

    def _setup_window(self) -> None:
        self.setWindowTitle(config.APP_NAME)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        if WINDOW_ICON_PATH.exists():
            self.setWindowIcon(WINDOW_ICON_PATH)
        margin = config.SHADOW_MARGIN
        self.resize(config.WINDOW_WIDTH + margin * 2, config.WINDOW_HEIGHT + margin * 2)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH + margin * 2, 400)
        self.setMaximumWidth(config.WINDOW_MAX_WIDTH + margin * 2)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        margin = config.SHADOW_MARGIN
        outer.setContentsMargins(margin, margin, margin, margin)
        self._root = QFrame(self)
        self._root.setObjectName("RootContainer")
        outer.addWidget(self._root)
        shadow = QGraphicsDropShadowEffect(self._root)
        shadow.setBlurRadius(config.SHADOW_BLUR)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self._root.setGraphicsEffect(shadow)
        root = QVBoxLayout(self._root)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_titlebar())
        root.addWidget(self._build_body(), stretch=1)

    def _build_titlebar(self) -> QWidget:
        bar = QWidget(self._root)
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(config.TITLEBAR_HEIGHT)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)
        btn_theme = QPushButton(bar)
        btn_theme.setObjectName("BtnTheme")
        btn_theme.setCursor(Qt.PointingHandCursor)
        btn_theme.setFixedSize(24, 24)
        btn_theme.setStyleSheet(
            "QPushButton#BtnTheme { background: transparent; border: none; font-size: 15px; }"
            "QPushButton#BtnTheme:hover { background-color: rgba(0,0,0,0.06); border-radius: 12px; }"
        )
        btn_theme.clicked.connect(self._toggle_theme)
        layout.addWidget(btn_theme, 0, Qt.AlignVCenter)
        self._btn_theme = btn_theme
        self._btn_close = QPushButton(bar)
        self._btn_close.setObjectName("BtnClose")
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.close)
        self._btn_min = QPushButton(bar)
        self._btn_min.setObjectName("BtnMinimize")
        self._btn_min.setCursor(Qt.PointingHandCursor)
        self._btn_min.clicked.connect(self.showMinimized)
        layout.addWidget(self._btn_close)
        layout.addWidget(self._btn_min)
        layout.addStretch(1)
        title = QLabel(config.APP_NAME, bar)
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)
        spacer = QWidget(bar)
        spacer.setFixedWidth(12 * 2 + 8)
        layout.addWidget(spacer)
        return bar

    def _build_body(self) -> QWidget:
        body = QWidget(self._root)
        body.setObjectName("Body")
        layout = QVBoxLayout(body)
        pad = config.CONTENT_PADDING
        layout.setContentsMargins(pad, pad, pad, pad)
        layout.setSpacing(10)

        # Section 1: Input
        add_label = QLabel("添加任务", body)
        add_label.setObjectName("SectionLabel")
        layout.addWidget(add_label)
        self._input_bar = TaskInputBar(body)
        self._input_bar.task_added.connect(self._on_task_added)
        layout.addWidget(self._input_bar)

        sep1 = QFrame(body)
        sep1.setFrameShape(QFrame.HLine)
        sep1.setObjectName("Separator")
        layout.addWidget(sep1)

        # Task management header
        mgmt_label = QLabel("任务管理", body)
        mgmt_label.setObjectName("SectionLabel")
        layout.addWidget(mgmt_label)

        # Section 2: Filter row
        self._filter_row = FilterRow(body)
        self._filter_row.filter_changed.connect(self._refresh_tasks)
        layout.addWidget(self._filter_row)

        # Section 3: Search bar
        self._search_bar = SearchBar(body)
        self._search_bar.search_changed.connect(self._refresh_tasks)
        layout.addWidget(self._search_bar)

        # Section 4: Task list
        self._task_scroll = QScrollArea(body)
        self._task_scroll.setObjectName("TaskScroll")
        self._task_scroll.setWidgetResizable(True)
        self._task_scroll.setFrameShape(QFrame.NoFrame)
        self._task_container = QWidget()
        self._task_container.setObjectName("TaskContainer")
        self._task_layout = QVBoxLayout(self._task_container)
        self._task_layout.setContentsMargins(0, 0, 0, 0)
        self._task_layout.setSpacing(config.CARD_SPACING)
        self._task_layout.addStretch(1)
        self._task_scroll.setWidget(self._task_container)
        layout.addWidget(self._task_scroll, stretch=1)

        self._setup_shortcuts()
        return body

    def _setup_shortcuts(self) -> None:
        sc_focus = QShortcut(QKeySequence(config.SHORTCUT_FOCUS_INPUT), self)
        sc_focus.activated.connect(self._focus_input)
        sc_new = QShortcut(QKeySequence(config.SHORTCUT_NEW), self)
        sc_new.activated.connect(self._focus_input)
        sc_quit = QShortcut(QKeySequence(config.SHORTCUT_QUIT), self)
        sc_quit.activated.connect(lambda: __import__("PySide6.QtWidgets").QtWidgets.QApplication.quit())

    def _focus_input(self) -> None:
        self._input_bar._title_edit.setFocus()
        self._input_bar._title_edit.selectAll()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()

    def _on_task_added(self) -> None:
        data = self._input_bar.pending_input
        if data is None:
            return
        title, category, priority, deadline = data
        try:
            self._service.create_task(title, category, priority, deadline)
        except ValueError as e:
            self._input_bar._show_error(str(e))
            return
        self._refresh_tasks()

    def _on_task_toggled(self, task_id: int, completed: bool) -> None:
        self._service.set_completed(task_id, completed)
        self._refresh_tasks()

    def _on_edit_requested(self, task_id: int) -> None:
        task = self._service.get_task(task_id)
        if task is None:
            return
        dialog = TaskDialog(task, self)
        if dialog.exec() == TaskDialog.DialogCode.Accepted:
            title, category, priority, deadline = dialog.result_data
            self._service.update_task(task_id, title=title, category=category, priority=priority, deadline=deadline)
            self._refresh_tasks()

    def _on_delete_requested(self, task_id: int) -> None:
        task = self._service.get_task(task_id)
        if task is None:
            return
        dialog = ConfirmDialog(title="删除任务", message=f'确定要删除任务"{task.title}"吗？此操作不可撤销。', parent=self)
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            self._service.delete_task(task_id)
            self._refresh_tasks()

    def _refresh_tasks(self) -> None:
        """增量刷新任务列表：复用已有 TaskCard，仅增删变更项。"""
        cat = self._filter_row.selected_category
        pri = self._filter_row.selected_priority
        date_filter = self._filter_row.selected_date_filter
        grouped = self._service.get_grouped_filtered(
            category=cat, priority=pri, date_filter=date_filter, search_text=self._search_bar.search_text
        )

        # 构建新的有序元素列表：(widget, task_id_or_None)
        new_items: list[tuple[QWidget, int | None]] = []
        for bucket_name in _bucket_order:
            bucket_tasks = grouped.get(bucket_name, [])
            if not bucket_tasks:
                continue
            if bucket_name == "无日期":
                new_items.append((DateSection("无日期", self._task_container), None))
            else:
                valid_dates = [t.deadline.date() for t in bucket_tasks if t.deadline is not None]
                header = (
                    DateSection.from_date(min(valid_dates), self._task_container)
                    if valid_dates
                    else DateSection(bucket_name, self._task_container)
                )
                new_items.append((header, None))
            for task in bucket_tasks:
                card = TaskCard(task, self._task_container)
                card._task_id = task.id  # type: ignore[attr-defined]
                card.toggled.connect(self._on_task_toggled)
                card.edit_requested.connect(self._on_edit_requested)
                card.delete_requested.connect(self._on_delete_requested)
                new_items.append((card, task.id))

        # 收集当前布局中所有 widget 及其 task_id
        current_items: list[tuple[QWidget, int | None]] = []
        for i in range(self._task_layout.count()):
            item = self._task_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            task_id: int | None = getattr(widget, "_task_id", None)
            current_items.append((widget, task_id))

        # 计算需要删除的旧 widget
        new_ids = {tid for _, tid in new_items if tid is not None}
        current_ids = {tid for _, tid in current_items if tid is not None}
        to_remove_ids = current_ids - new_ids

        # 移除不再需要的卡片（保留引用以便复 reparent）
        removed_cards: dict[int, TaskCard] = {}
        for widget, tid in current_items:
            if tid is not None and tid in to_remove_ids:
                if isinstance(widget, TaskCard):
                    removed_cards[tid] = widget
                self._task_layout.removeWidget(widget)
                widget.deleteLater()

        # 清空 stretch，保留 DateSection 和复用的 TaskCard
        while self._task_layout.count() > 0:
            self._task_layout.takeAt(0)

        # 重新按序添加
        self._task_cards = {}
        for widget, tid in new_items:
            if tid is not None:
                if tid in removed_cards:
                    # 复用旧卡片（已在 current layout 中 removeWidget，但对象还活着）
                    card = removed_cards[tid]
                    self._task_layout.addWidget(card)
                    self._task_cards[tid] = card
                else:
                    # 新建卡片已在 new_items 中创建，直接加入布局
                    self._task_layout.addWidget(widget)
                    self._task_cards[tid] = widget  # type: ignore[assignment]
            else:
                # DateSection 等无任务 ID 的控件
                self._task_layout.addWidget(widget)

        self._task_layout.addStretch(1)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._in_titlebar(event.position().toPoint()):
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _in_titlebar(self, pos: QPoint) -> bool:
        return pos.y() <= config.TITLEBAR_HEIGHT + config.SHADOW_MARGIN




