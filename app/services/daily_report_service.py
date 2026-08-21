"""日报服务：查询当天任务数据并生成 Markdown 格式文本。"""
from __future__ import annotations

from datetime import datetime, timezone

from app.database.repository import TaskRepository
from app.models.task import Task


class DailyReportService:
    """生成当日任务日报。"""

    def __init__(self, repo: TaskRepository | None = None) -> None:
        self._repo = repo or TaskRepository()

    def _today_start(self) -> datetime:
        return datetime.combine(datetime.now(tz=timezone.utc).date(), datetime.min.time())

    def _today_end(self) -> datetime:
        return datetime.combine(datetime.now(tz=timezone.utc).date(), datetime.max.time())

    def get_today_created(self) -> list[Task]:
        """获取当天创建的任务列表。"""
        return self._repo.list_created_in_range(
            self._today_start(), self._today_end()
        )

    def get_today_completed(self) -> list[Task]:
        """获取当天完成的任务列表。"""
        return self._repo.list_completed_in_range(
            self._today_start(), self._today_end()
        )

    def generate(self) -> str:
        """生成今日 Markdown 日报文本。

        Returns:
            格式化后的 Markdown 字符串。
        """
        created = self.get_today_created()
        completed = self.get_today_completed()

        completed_titles = [t.title for t in completed]
        incomplete_titles = [
            t.title for t in created if t.title not in completed_titles
        ]

        lines: list[str] = []
        today_str = datetime.now(tz=timezone.utc).date().strftime("%Y-%m-%d")
        lines.append(f"# 📋 任务日报 · {today_str}")
        lines.append("")
        lines.append(f"- 创建: {len(created)} 项")
        lines.append(f"- 完成: {len(completed)} 项")
        lines.append(f"- 未完成: {len(incomplete_titles)} 项")
        lines.append("")

        # 已完成
        lines.append("## ✅ 已完成")
        lines.append("")
        if completed:
            for t in completed:
                lines.append(f"- [x] {t.title}")
        else:
            lines.append("_暂无完成任务_")
        lines.append("")

        # 未完成
        lines.append("## ⏳ 未完成")
        lines.append("")
        if incomplete_titles:
            for title in incomplete_titles:
                lines.append(f"- [ ] {title}")
        else:
            lines.append("_暂无未完成任务_")
        lines.append("")

        return "\n".join(lines)

