"""Business logic layer: wraps Repository, provides grouping and filtering. UI only calls Service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.database.repository import NO_CHANGE, TaskRepository
from app.models.task import Task


class TaskService:
    """Task business service."""

    def __init__(self, repo: TaskRepository | None = None) -> None:
        self._repo = repo or TaskRepository()

    def create_task(
        self,
        title: str,
        category: str = "生活",
        priority: int = 2,
        deadline: datetime | None = None,
    ) -> Task:
        return self._repo.create(title, category, priority, deadline)

    def get_task(self, task_id: int) -> Task | None:
        return self._repo.get_by_id(task_id)

    def list_all(self, search_text: str | None = None) -> list[Task]:
        return self._repo.list_all(search_text)

    def filter_tasks(
        self,
        category: str | None = None,
        priority: int | None = None,
        completed: bool | None = None,
        search_text: str | None = None,
    ) -> list[Task]:
        return self._repo.filter_tasks(category, priority, completed, search_text)

    def group_by_date(self, tasks: list[Task]) -> dict[str, list[Task]]:
        """Group by: past due / today / tomorrow / future / no date."""
        today = datetime.now(tz=timezone.utc).date()
        tomorrow = today + timedelta(days=1)
        buckets: dict[str, list[Task]] = {
            "已过期": [],
            "今天": [],
            "明天": [],
            "未来": [],
            "无日期": [],
        }
        for t in tasks:
            if t.deadline is None:
                buckets["无日期"].append(t)
            elif t.deadline.date() < today:
                buckets["已过期"].append(t)
            elif t.deadline.date() == today:
                buckets["今天"].append(t)
            elif t.deadline.date() == tomorrow:
                buckets["明天"].append(t)
            else:
                buckets["未来"].append(t)
        return buckets

    def update_task(
        self,
        task_id: int,
        title: object = NO_CHANGE,
        category: object = NO_CHANGE,
        priority: object = NO_CHANGE,
        deadline: object = NO_CHANGE,
    ) -> Task | None:
        # Omitted args default to NO_CHANGE; explicit None clears; date/value sets.
        # Repo treats None as "skip" for title/category/priority, "clear" for deadline.
        return self._repo.update(
            task_id,
            None if title is NO_CHANGE else title,
            None if category is NO_CHANGE else category,
            None if priority is NO_CHANGE else priority,
            deadline,
        )

    def set_completed(self, task_id: int, completed: bool) -> Task | None:
        return self._repo.set_completed(task_id, completed)

    def delete_task(self, task_id: int) -> bool:
        return self._repo.delete(task_id)

    def batch_set_completed(self, task_ids: list[int], completed: bool) -> int:
        """批量完成/取消完成，返回实际更新的行数。"""
        return self._repo.batch_set_completed(task_ids, completed)

    def batch_toggle_tasks(self, task_ids: list[int]) -> int:
        """批量切换完成状态（完成↔取消完成），返回实际更新的行数。"""
        return self._repo.batch_toggle_tasks(task_ids)

    def batch_delete(self, task_ids: list[int]) -> int:
        """批量删除，返回实际删除的行数。"""
        return self._repo.batch_delete(task_ids)

    def get_grouped_filtered(
        self,
        category: str | None = None,
        priority: int | None = None,
        date_filter: str | None = None,
        search_text: str | None = None,
    ) -> dict[str, list[Task]]:
        """Filter by category/priority/search, group by date, then apply date_filter.

        date_filter values: "全部"(default) / "今天" / "明天" / "本周" / "已过期"
        """
        tasks = self._repo.filter_tasks(category=category, priority=priority, search_text=search_text)
        grouped = self.group_by_date(tasks)

        if date_filter is None or date_filter == "全部":
            return grouped

        today = datetime.now(tz=timezone.utc).date()
        filtered: dict[str, list[Task]] = {k: [] for k in grouped}

        if date_filter == "今天":
            filtered["今天"] = [t for t in grouped.get("今天", []) if t.deadline is not None]
        elif date_filter == "明天":
            filtered["明天"] = [t for t in grouped.get("明天", []) if t.deadline is not None]
        elif date_filter == "本周":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            for bucket in grouped:
                filtered[bucket] = [
                    t for t in grouped[bucket]
                    if t.deadline is not None and week_start <= t.deadline.date() <= week_end
                ]
        elif date_filter == "已过期":
            filtered["已过期"] = [t for t in grouped.get("已过期", []) if t.deadline is not None]

        return filtered



