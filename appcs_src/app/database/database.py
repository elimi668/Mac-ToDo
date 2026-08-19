"""数据库初始化：engine / SessionLocal / init_db / dispose_db。"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config

DB_DIR = config.APP_ROOT / "data"
DB_FILE = DB_DIR / "todo.db"


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


# 模块级单例；调用 init_db() 后赋值。未初始化时为 None。
_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def init_db(db_url: str | None = None) -> None:
    """初始化数据库。默认使用本地文件 app/data/todo.db；测试可传入临时文件 URL。"""
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

    # 幂等迁移：已有库添加新字段
    from app.database.repository import TaskRepository
    TaskRepository.migrate()


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
