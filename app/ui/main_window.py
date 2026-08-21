"""Main window: borderless + rounded corners + shadow + draggable + traffic lights + vertical three-section layout."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QKeySequence, QMouseEvent, QShortcut
from PySide6.QtWidgets import (
    QApplication,
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
from app.ui.components.date_section import DateSection
from app.ui.components.filter_row import FilterRow
from app.ui.components.search_bar import SearchBar
from app.ui.components.task_dialog import TaskDialog
from app.ui.components.task_input_bar import TaskInputBar
from app.ui.task_card import TaskCard

_bucket_order = ("已过期", "今天", "明天", "未来", "无日期")


class MainWindow(QWidget):
    def __init__(self, service: TaskService | None = None) -> None:
        super().__init__()
        self._drag_offset: QPoint | None = None
        self._service = service or TaskService()
        self._theme_service = ThemeService(self)
        # 键盘导航：当前焦点卡片（None 表示无焦点）
        self._focus_task_id: int | None = None
        # 批量选择：上次点击的卡片 id，用于 Shift+Click 范围选择
        self._last_click_task_id: int | None = None
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
        self._build_selection_bar()
        return body

    def _setup_shortcuts(self) -> None:
        """配置快捷键。导航键在输入框无焦点时生效；编辑键通过 keyPressEvent 分发。"""
        sc_focus = QShortcut(QKeySequence(config.SHORTCUT_FOCUS_INPUT), self)
        sc_focus.activated.connect(self._focus_input)
        sc_new = QShortcut(QKeySequence(config.SHORTCUT_NEW), self)
        sc_new.activated.connect(self._focus_input)
        sc_quit = QShortcut(QKeySequence(config.SHORTCUT_QUIT), self)
        sc_quit.activated.connect(lambda: __import__("PySide6.QtWidgets").QtWidgets.QApplication.quit())

        # 键盘导航：仅当输入框无焦点时触发
        if self._input_bar._title_edit is not None:
            sc_up = QShortcut(QKeySequence("Up"), self)
            sc_up.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc_up.activated.connect(self._go_up)

            sc_down = QShortcut(QKeySequence("Down"), self)
            sc_down.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc_down.activated.connect(self._go_down)

            sc_enter = QShortcut(QKeySequence("Return"), self)
            sc_enter.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc_enter.activated.connect(self._on_keyboard_enter)

            sc_delete = QShortcut(QKeySequence("Delete"), self)
            sc_delete.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc_delete.activated.connect(self._on_keyboard_delete)

            sc_copy = QShortcut(QKeySequence(QKeySequence.Copy), self)
            sc_copy.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc_copy.activated.connect(self._on_keyboard_copy)

    def _focus_input(self) -> None:
        self._input_bar._title_edit.setFocus()
        self._input_bar._title_edit.selectAll()

    # ── 键盘导航 ──────────────────────────────────────────────────────────────

    def _input_has_focus(self) -> bool:
        """判断输入框是否当前拥有焦点（此时不应响应列表键盘操作）。"""
        widget = __import__("PySide6.QtWidgets").QtWidgets.QApplication.focusWidget()
        if widget is None:
            return False
        # 检查是否为输入框或其子控件
        return widget is self._input_bar._title_edit or widget.parent() is self._input_bar

    def _highlight_focused_card(self, task_id: int | None) -> None:
        """清除旧焦点高亮，为新焦点卡片添加样式。"""
        old_card = self._task_cards.get(self._focus_task_id)
        if old_card is not None:
            old_card.setProperty("focused", False)
            old_card.style().unpolish(old_card)
            old_card.style().polish(old_card)
        self._focus_task_id = task_id
        new_card = self._task_cards.get(task_id) if task_id is not None else None
        if new_card is not None:
            new_card.setProperty("focused", True)
            new_card.style().unpolish(new_card)
            new_card.style().polish(new_card)
            # 滚动到可视区域（对齐顶部）
            self._task_scroll.verticalScrollBar().setValue(
                new_card.y() - self._task_scroll.verticalScrollBar().height() // 3
            )

    def _card_list(self) -> list[int]:
        """返回当前列表中按顺序排列的所有 task_id。"""
        return list(self._task_cards.keys())

    def _go_up(self) -> None:
        if self._input_has_focus():
            return
        cards = self._card_list()
        if not cards:
            return
        if self._focus_task_id is None:
            self._highlight_focused_card(cards[-1])  # 跳到最后一个
        else:
            idx = cards.index(self._focus_task_id)
            self._highlight_focused_card(cards[(idx - 1) % len(cards)])

    def _go_down(self) -> None:
        if self._input_has_focus():
            return
        cards = self._card_list()
        if not cards:
            return
        if self._focus_task_id is None:
            self._highlight_focused_card(cards[0])  # 跳到第一个
        else:
            idx = cards.index(self._focus_task_id)
            self._highlight_focused_card(cards[(idx + 1) % len(cards)])

    def _on_keyboard_enter(self) -> None:
        """Enter：完成/取消完成当前焦点卡片。"""
        if self._input_has_focus() or self._focus_task_id is None:
            return
        task = self._service.get_task(self._focus_task_id)
        if task is None:
            return
        self._service.set_completed(self._focus_task_id, not task.completed)
        self._refresh_tasks()
        # 刷新后尝试重新聚焦同一卡片（如果还在列表里）
        if self._focus_task_id in self._task_cards:
            self._highlight_focused_card(self._focus_task_id)
        else:
            self._highlight_focused_card(None)

    def _on_keyboard_delete(self) -> None:
        """Delete：删除当前焦点卡片（二次确认）。"""
        if self._input_has_focus() or self._focus_task_id is None:
            return
        task = self._service.get_task(self._focus_task_id)
        if task is None:
            return
        dialog = ConfirmDialog(
            title="删除任务",
            message=f'确定要删除任务"{task.title}"吗？此操作不可撤销。',
            parent=self,
        )
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            self._service.delete_task(self._focus_task_id)
            self._refresh_tasks()
        self._highlight_focused_card(None)

    def _on_keyboard_copy(self) -> None:
        """Ctrl+C：复制当前焦点卡片的标题到剪贴板。"""
        if self._input_has_focus() or self._focus_task_id is None:
            return
        task = self._service.get_task(self._focus_task_id)
        if task is None:
            return
        cb = QApplication.clipboard()
        cb.setText(task.title)

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
        # 新增任务后自动聚焦到最新添加的任务
        self._highlight_focused_card(None)

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
                card.selected.connect(self._on_card_selected)
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

        # 如果焦点任务已被删除，清除焦点
        if self._focus_task_id is not None and self._focus_task_id not in self._task_cards:
            self._highlight_focused_card(None)

    def _on_card_selected(self, task_id: int, selected: bool) -> None:
        """处理卡片选中/取消选中事件。"""
        if selected:
            self._last_click_task_id = task_id
        self._update_selection_bar()

    def keyPressEvent(self, event) -> None:
        """处理不在 QShortcut 范围内的按键（如小键盘 Enter）。"""
        if self._input_has_focus():
            super().keyPressEvent(event)
            return
        key = event.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self._on_keyboard_enter()
            event.accept()
            return
        if key == Qt.Key_Delete:
            self._on_keyboard_delete()
            event.accept()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._in_titlebar(event.position().toPoint()):
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        # 点击任务区域清除旧焦点高亮（交由鼠标事件重绘新焦点）
        if self._focus_task_id is not None:
            old_card = self._task_cards.get(self._focus_task_id)
            if old_card is not None:
                old_card.setProperty("focused", False)
                old_card.style().unpolish(old_card)
                old_card.style().polish(old_card)
            self._focus_task_id = None
        # 点击非卡片区域时清除批量选择
        if not any(isinstance(item.widget(), TaskCard) for item in (
            self._task_layout.itemAt(i) for i in range(self._task_layout.count())
        ) if item is not None):
            self._clear_selection()
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

    def _build_selection_bar(self) -> None:
        """底部选中操作栏：显示已选数量，提供批量完成/删除按钮。"""
        self._selection_bar = QFrame(self._root)
        self._selection_bar.setObjectName("SelectionBar")
        self._selection_bar.setFixedHeight(40)
        self._selection_bar.setVisible(False)
        sel_layout = QHBoxLayout(self._selection_bar)
        sel_layout.setContentsMargins(16, 0, 16, 0)
        sel_layout.setSpacing(12)

        self._sel_count_label = QLabel("已选择 0 项", self._selection_bar)
        self._sel_count_label.setObjectName("SelectionCount")
        sel_layout.addWidget(self._sel_count_label)

        sel_layout.addStretch(1)

        btn_toggle = QPushButton("批量完成", self._selection_bar)
        btn_toggle.setObjectName("BatchButton")
        btn_toggle.setCursor(Qt.PointingHandCursor)
        btn_toggle.clicked.connect(self._on_batch_complete)
        sel_layout.addWidget(btn_toggle)

        btn_delete = QPushButton("删除", self._selection_bar)
        btn_delete.setObjectName("BatchButtonDelete")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.clicked.connect(self._on_batch_delete)
        sel_layout.addWidget(btn_delete)

        btn_clear = QPushButton("×", self._selection_bar)
        btn_clear.setObjectName("BatchButtonClear")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setFixedSize(28, 28)
        btn_clear.clicked.connect(self._clear_selection)
        sel_layout.addWidget(btn_clear)

        # 将选择栏插入 body 布局末尾
        body = self._body
        body_layout = body.layout()
        body_layout.addWidget(self._selection_bar)

    def _update_selection_bar(self) -> None:
        selected_ids = [tid for tid, card in self._task_cards.items() if card.is_selected]
        if selected_ids:
            self._sel_count_label.setText(f"已选择 {len(selected_ids)} 项")
            self._selection_bar.setVisible(True)
        else:
            self._selection_bar.setVisible(False)

    def _clear_selection(self) -> None:
        for card in self._task_cards.values():
            if card.is_selected:
                card._selected = False
                card._update_select_style()
        self._update_selection_bar()

    def _on_batch_complete(self) -> None:
        selected_ids = [tid for tid, card in self._task_cards.items() if card.is_selected]
        if not selected_ids:
            return
        self._service.batch_toggle_tasks(selected_ids)
        self._clear_selection()
        self._refresh_tasks()

    def _on_batch_delete(self) -> None:
        selected_ids = [tid for tid, card in self._task_cards.items() if card.is_selected]
        if not selected_ids:
            return
        titles = ", ".join(
            self._service.get_task(tid).title for tid in selected_ids if self._service.get_task(tid) is not None
        )
        dialog = ConfirmDialog(
            title="批量删除",
            message=f'确定要删除选中的 {len(selected_ids)} 个任务吗？此操作不可撤销。\n\n{titles}',
            parent=self,
        )
        if dialog.exec() == ConfirmDialog.DialogCode.Accepted:
            self._service.batch_delete(selected_ids)
        self._clear_selection()
        self._refresh_tasks()
