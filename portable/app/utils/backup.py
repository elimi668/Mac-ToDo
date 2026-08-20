"""数据备份：启动时备份 + 定时备份。"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app import config
from app.database.database import DB_FILE


def _ensure_backup_dir() -> Path:
    backup_dir = config.BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_db(db_file: Path | None = None) -> Path | None:
    """备份当前数据库文件。返回备份文件路径，失败返回 None。"""
    source = db_file or DB_FILE
    if not source.exists():
        return None
    try:
        backup_dir = _ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = backup_dir / f"todo_backup_{timestamp}.db"
        # 使用 sqlite3 在线备份 API 获取一致性快照，避免 shutil.copy2 在写入中复制不完整数据
        src_conn = sqlite3.connect(str(source))
        dst_conn = sqlite3.connect(str(dest))
        try:
            src_conn.backup(dst_conn)
        finally:
            src_conn.close()
            dst_conn.close()
        _cleanup_old_backups(backup_dir)
        return dest
    except (sqlite3.Error, OSError):
        return None


def backup_on_startup() -> Path | None:
    """启动时检查：若距上次备份超过阈值则备份。"""
    backup_dir = _ensure_backup_dir()
    latest = _get_latest_backup(backup_dir)
    if latest is not None:
        age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
        if age_hours < config.BACKUP_INTERVAL_HOURS:
            return None
    return backup_db()


def _get_latest_backup(backup_dir: Path) -> Path | None:
    backups = sorted(backup_dir.glob("todo_backup_*.db"))
    return backups[-1] if backups else None


def _cleanup_old_backups(backup_dir: Path, keep: int = 10) -> None:
    backups = sorted(backup_dir.glob("todo_backup_*.db"), reverse=True)
    for old in backups[keep:]:
        try:
            old.unlink()
        except OSError:
            pass
