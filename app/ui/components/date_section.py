"""日期分组标题：显示完整日期 + 相对标注。如"2026-07-10 今天"。"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from PySide6.QtWidgets import QLabel, QWidget


class DateSection(QLabel):
    """日期分组标题。"""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("DateSection")

    @staticmethod
    def from_date(d: date, parent: QWidget | None = None) -> DateSection:
        """根据日期生成标题，自动附加相对标注。"""
        today = datetime.now(tz=timezone.utc).date()
        label = str(d)
        if d == today:
            label += " 今天"
        elif d == today + timedelta(days=1):
            label += " 明天"
        elif d == today - timedelta(days=1):
            label += " 昨天"
        elif d < today:
            label += " 已过期"
        return DateSection(label, parent)
