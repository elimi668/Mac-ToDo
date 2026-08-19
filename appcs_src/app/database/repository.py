"""TaskRepository: encapsulates Task CRUD and common queries. Short transactions, each operation gets an independent session."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.database import get_session
from app.models.task import Task


class _NoChangeType:
    """Sentinel singleton: distinguish 'don't update deadline' from 'pass None to clear deadline'."""
    _instance: "_NoChangeType | None" = None

    def __new__(cls) -> "_NoChangeType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<no-change>"


NO_CHANGE = _NoChangeType()
"""Pass to TaskRepository.update(deadline=...) to mean 'don't modify deadline'.
Pass a date to set a new value; pass None to clear."""


class TaskRepository:
    """Task data access layer."""

    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        # Allow test injection; default uses module-level SessionLocal
        self._session_factory = session_factory

    def _get_session(self) -> Session:
        if self._session_factory is not None:
            return self._session_factory()
        return get_session()

    # ---------- Create ----------
    def create(
        self,
        title: str,
        category: str = "生活",
        priority: int = 2,
        deadline: datetime | None = None,
    ) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("任务标题不能为空")
        if priority not in (1, 2, 3):
            raise ValueError("priority 必须为 1/2/3")

        task = Task(
            title=title,
            category=category,
            priority=priority,
            deadline=deadline,
        )
        with self._get_session() as session:
            session.add(task)
            session.commit()
            session.refresh(task)
        return task

    # ---------- Read ----------
    def get_by_id(self, task_id: int) -> Task | None:
        with self._get_session() as session:
            return session.get(Task, task_id)

    def list_all(self, search_text: str | None = None) -> list[Task]:
        """Incomplete first; within same status, sort by deadline ascending, created time descending."""
        with self._get_session() as session:
            stmt = select(Task).order_by(
                Task.completed.asc(),
                Task.deadline.asc().nulls_last(),
                Task.created_time.desc(),
            )
            if search_text:
                stmt = stmt.where(Task.title.like(f"%{search_text}%"))
            return list(session.scalars(stmt))

    def filter_tasks(
        self,
        category: str | None = None,
        priority: int | None = None,
        completed: bool | None = None,
        search_text: str | None = None,
    ) -> list[Task]:
        """Combined filter. Pass None to skip filtering on that dimension."""
        with self._get_session() as session:
            stmt = select(Task).order_by(
                Task.completed.asc(),
                Task.deadline.asc().nulls_last(),
                Task.created_time.desc(),
            )
            if category is not None:
                stmt = stmt.where(Task.category == category)
            if priority is not None:
                stmt = stmt.where(Task.priority == priority)
            if completed is not None:
                stmt = stmt.where(Task.completed == completed)
            if search_text:
                stmt = stmt.where(Task.title.like(f"%{search_text}%"))
            return list(session.scalars(stmt))

    # ---------- Update ----------
    def update(
        self,
        task_id: int,
        title: str | None = None,
        category: str | None = None,
        priority: int | None = None,
        deadline: object = NO_CHANGE,
    ) -> Task | None:
        """Update task fields. Only update non-None parameters.
        deadline uses sentinel: don't pass = no change, pass date = set, pass None = clear."""
        if priority is not None and priority not in (1, 2, 3):
            raise ValueError("priority 必须为 1/2/3")

        with self._get_session() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None

            if title is not None:
                title = title.strip()
                if not title:
                    raise ValueError("任务标题不能为空")
                task.title = title
            if category is not None:
                task.category = category
            if priority is not None:
                task.priority = priority
            if deadline is not NO_CHANGE:
                task.deadline = deadline  # type: ignore[assignment]
            session.commit()
            session.refresh(task)
            return task

    def set_completed(self, task_id: int, completed: bool) -> Task | None:
        """Toggle completed state, record/clear completion time."""
        with self._get_session() as session:
            task = session.get(Task, task_id)
            if task is None:
                return None
            task.completed = completed
            task.completed_time = datetime.now() if completed else None
            session.commit()
            session.refresh(task)
            return task

    # ---------- Delete ----------
    def delete(self, task_id: int) -> bool:
        """Delete a task. Returns whether a row was actually deleted."""
        with self._get_session() as session:
            task = session.get(Task, task_id)
            if task is None:
                return False
            session.delete(task)
            session.commit()
            return True


    # ---------- Reminder ----------
    def list_due_reminders(self, now: datetime, lead_minutes: int = 15) -> list[Task]:
        """Query tasks that need deadline reminders.
        Conditions: incomplete + not reminded + deadline between now and now+lead_minutes."""
        from datetime import timedelta

        end = now + timedelta(minutes=lead_minutes)
        with self._get_session() as session:
            stmt = select(Task).where(
                Task.completed == False,
                Task.reminded == False,
                Task.deadline.is_not(None),
                Task.deadline >= now,
                Task.deadline <= end,
            ).order_by(Task.deadline.asc(), Task.created_time.desc())
            return list(session.scalars(stmt))

    def mark_reminded(self, task_id: int) -> None:
        """Mark specified task as already reminded."""
        with self._get_session() as session:
            task = session.get(Task, task_id)
            if task is not None:
                task.reminded = True
                session.commit()

    # ---------- Daily/Weekly Report ----------
    def list_by_date_range(self, start: datetime, end: datetime) -> list[Task]:
        """Query tasks with deadline in [start, end] range (inclusive)."""
        with self._get_session() as session:
            stmt = select(Task).where(
                Task.deadline.is_not(None),
                Task.deadline >= start,
                Task.deadline <= end,
            ).order_by(Task.deadline.asc(), Task.created_time.desc())
            return list(session.scalars(stmt))

    def list_completed_in_range(self, start: datetime, end: datetime) -> list[Task]:
        """Query tasks completed in [start, end] range."""
        with self._get_session() as session:
            stmt = select(Task).where(
                Task.completed == True,
                Task.completed_time.is_not(None),
                Task.completed_time >= start,
                Task.completed_time <= end,
            ).order_by(Task.completed_time.desc())
            return list(session.scalars(stmt))

    def list_created_in_range(self, start: datetime, end: datetime) -> list[Task]:
        """Query tasks created in [start, end] range."""
        with self._get_session() as session:
            stmt = select(Task).where(
                Task.created_time >= start,
                Task.created_time <= end,
            ).order_by(Task.created_time.desc())
            return list(session.scalars(stmt))

    # ---------- Database Migration ----------
    @staticmethod
    def migrate() -> None:
        """Check and auto-add new columns (priority, etc.)."""
        from app.database.database import DB_FILE, _engine
        import sqlalchemy as sa

        if _engine is None:
            return
        try:
            with _engine.connect() as conn:
                inspector = sa.inspect(_engine)
                columns = {c["name"] for c in inspector.get_columns("tasks")}
                if "reminded" not in columns:
                    conn.execute(sa.text("ALTER TABLE tasks ADD COLUMN reminded BOOLEAN DEFAULT 0"))
                    conn.commit()
        except Exception:
            pass  # Table may not exist yet, ignore
