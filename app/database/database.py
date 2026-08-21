"""数据库初始化：engine / SessionLocal / init_db / dispose_db。"""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config

# 使用用户目录存储数据，确保可写
if getattr(sys, 'frozen', False):
    # 打包后使用 AppData 目录
    DB_DIR = Path.home() / "AppData" / "Local" / "TodoMate" / "data"
else:
    DB_DIR = config.APP_ROOT / "data"
DB_FILE = DB_DIR / "todo.db"

# Alembic 配置文件路径（相对于项目根目录）
ALEMBIC_INI = Path(__file__).resolve().parent.parent.parent / "alembic.ini"


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


# 模块级单例；调用 init_db() 后赋值。未初始化时为 None。
_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def init_db(db_url: str | None = None) -> None:
    """初始化数据库。默认使用本地文件 app/data/todo.db；测试可传入临时文件 URL。

    迁移策略：
    - 临时数据库（测试）：仅执行 Base.metadata.create_all()，不运行 alembic
    - 生产数据库（文件路径）：先 create_all（幂等），再执行 alembic upgrade head
    """
    global _engine, SessionLocal

    # 若已有旧引擎，先释放（测试复用模块时避免句柄泄漏）
    if _engine is not None:
        _engine.dispose()

    if db_url is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{DB_FILE}"

    _engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False}, pool_pre_ping=True)

    # 启用 WAL 模式：提升并发读性能，确保备份时读取一致性快照
    @event.listens_for(_engine, "connect")
    def _set_wal_mode(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)

    # 确保模型已注册后再建表
    from app.models import task as _task  # noqa: F401

    Base.metadata.create_all(_engine)

    # 仅对文件路径数据库运行 alembic 迁移（测试用内存/临时数据库跳过）
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:///:memory:"):
        _run_alembic_upgrade()


def _run_alembic_upgrade() -> None:
    """运行 alembic upgrade head 以应用所有待处理迁移。"""
    try:
        from alembic.config import Config

        from alembic import command

        # 使用绝对路径，确保从任意工作目录均可正确加载
        alembic_cfg = Config(str(ALEMBIC_INI))
        command.upgrade(alembic_cfg, "head")
    except ImportError:
        # 无 alembic 时回退到原始 migrate() 逻辑
        from app.database.repository import TaskRepository
        TaskRepository.migrate()
    except Exception:
        # 迁移失败不阻断启动，仅打印警告
        import logging
        logging.getLogger(__name__).warning("Alembic migration failed, using current schema", exc_info=True)


def get_session() -> Session:
    """获取一个新的数据库会话。调用方负责关闭（建议用 with 语句）。"""
    if SessionLocal is None:
        init_db()
    assert SessionLocal is not None
    return SessionLocal()


def dispose_db() -> None:
    """释放当前引擎与连接池。测试清理临时文件前调用。"""
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        SessionLocal = None
