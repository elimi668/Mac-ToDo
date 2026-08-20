"""Backup module unit tests. Uses temporary file SQLite, non-interfering."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.database.database import dispose_db, init_db
from app.database.repository import TaskRepository
from app.utils.backup import (
    _cleanup_old_backups,
    backup_db,
    backup_on_startup,
)


class BackupDbTest(unittest.TestCase):
    """Tests for backup_db()."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)
        self.backup_dir = self.tmp_dir / "backup"
        self.backup_dir.mkdir()

        # Create a test SQLite database with content
        self.db_path = self.tmp_dir / "test.db"
        init_db(f"sqlite:///{self.db_path}")
        TaskRepository().create("backup test task")
        dispose_db()

    def tearDown(self) -> None:
        dispose_db()
        self._tmp.cleanup()

    def test_backup_db_with_custom_path(self) -> None:
        """backup_db(db_file=...) creates a valid backup file."""
        with patch("app.config.BACKUP_DIR", self.backup_dir):
            result = backup_db(db_file=self.db_path)
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())
        self.assertEqual(result.suffix, ".db")
        self.assertTrue(result.name.startswith("todo_backup_"))

    def test_backup_db_valid_sqlite(self) -> None:
        """Backup file is a valid SQLite database with original data."""
        with patch("app.config.BACKUP_DIR", self.backup_dir):
            result = backup_db(db_file=self.db_path)
        conn = sqlite3.connect(str(result))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_backup_db_no_source_returns_none(self) -> None:
        """backup_db() returns None when source doesn't exist."""
        missing = self.tmp_dir / "nonexistent.db"
        with patch("app.config.BACKUP_DIR", self.backup_dir):
            result = backup_db(db_file=missing)
        self.assertIsNone(result)

    def test_backup_db_default_path(self) -> None:
        """backup_db() with no arg uses DB_FILE (patched)."""
        with patch("app.config.BACKUP_DIR", self.backup_dir), \
             patch("app.utils.backup.DB_FILE", self.db_path):
            result = backup_db()
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())


class BackupOnStartupTest(unittest.TestCase):
    """Tests for backup_on_startup()."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)
        self.backup_dir = self.tmp_dir / "backup"
        self.backup_dir.mkdir()

        self.db_path = self.tmp_dir / "test.db"
        init_db(f"sqlite:///{self.db_path}")
        TaskRepository().create("backup test task")
        dispose_db()

    def tearDown(self) -> None:
        dispose_db()
        self._tmp.cleanup()

    def test_backup_on_startup_no_backup_creates_one(self) -> None:
        """When no prior backup exists, backup_on_startup creates one."""
        with patch("app.config.BACKUP_DIR", self.backup_dir), \
             patch("app.utils.backup.DB_FILE", self.db_path):
            result = backup_on_startup()
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())

    def test_backup_on_startup_recent_backup_returns_none(self) -> None:
        """When a recent backup exists (<24h), backup_on_startup skips."""
        recent = self.backup_dir / "todo_backup_20260720_120000.db"
        recent.write_text("")
        with patch("app.config.BACKUP_DIR", self.backup_dir), \
             patch("app.utils.backup.DB_FILE", self.db_path):
            result = backup_on_startup()
        self.assertIsNone(result)


class CleanupTest(unittest.TestCase):
    """Tests for _cleanup_old_backups()."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_cleanup_removes_excess_backups(self) -> None:
        """Keeps at most `keep` backup files."""
        for i in range(15):
            (self.tmp_dir / f"todo_backup_20260720_{10000 + i}.db").write_text("")
        _cleanup_old_backups(self.tmp_dir, keep=10)
        remaining = list(self.tmp_dir.glob("todo_backup_*.db"))
        self.assertEqual(len(remaining), 10)

    def test_cleanup_keeps_all_when_under_limit(self) -> None:
        """Does not remove files when count <= keep."""
        for i in range(5):
            (self.tmp_dir / f"todo_backup_20260720_{10000 + i}.db").write_text("")
        _cleanup_old_backups(self.tmp_dir, keep=10)
        remaining = list(self.tmp_dir.glob("todo_backup_*.db"))
        self.assertEqual(len(remaining), 5)
