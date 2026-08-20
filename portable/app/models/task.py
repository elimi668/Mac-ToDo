"""Task ORM 模型（SQLAlchemy 2.0 声明式）。字段命名与产品需求一致。"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Task(Base):
    """待办任务。"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="生活")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=2)  # 1=高 2=中 3=低
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reminded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_deadline", "deadline"),
        Index("idx_completed", "completed"),
        Index("idx_category", "category"),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} done={self.completed}>"
