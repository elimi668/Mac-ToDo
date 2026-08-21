"""DailyReportService unit tests."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.database.database import dispose_db, init_db
from app.services.daily_report_service import DailyReportService


class DailyReportServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / 'test.db'
        init_db(f'sqlite:///{db_path}')
        self.svc = DailyReportService()

    def tearDown(self) -> None:
        dispose_db()
        self._tmp.cleanup()

    def test_get_today_created_empty(self) -> None:
        result = self.svc.get_today_created()
        self.assertEqual(result, [])

    def test_get_today_completed_empty(self) -> None:
        result = self.svc.get_today_completed()
        self.assertEqual(result, [])

    def test_get_today_completed_with_task(self) -> None:
        task = self.svc._repo.create('完成测试', category='工作', priority=1)
        self.svc._repo.set_completed(task.id, True)
        result = self.svc.get_today_completed()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, '完成测试')

    def test_generate_empty(self) -> None:
        report = self.svc.generate()
        today_str = datetime.now(tz=timezone.utc).date().strftime('%Y-%m-%d')
        self.assertIn(today_str, report)
        self.assertIn('创建: 0 项', report)
        self.assertIn('完成: 0 项', report)
        self.assertIn('未完成: 0 项', report)
        self.assertIn('暂无完成任务', report)
        self.assertIn('暂无未完成任务', report)

    def test_generate_with_completed_tasks(self) -> None:
        task = self.svc._repo.create('已完成任务', category='工作', priority=1)
        self.svc._repo.set_completed(task.id, True)
        report = self.svc.generate()
        self.assertIn('[x] 已完成任务', report)
        self.assertIn('完成: 1 项', report)

    def test_generate_with_incomplete_tasks(self) -> None:
        self.svc._repo.create('待办任务', category='学习', priority=2)
        report = self.svc.generate()
        self.assertIn('[ ] 待办任务', report)
        self.assertIn('未完成: 1 项', report)

    def test_generate_mixed(self) -> None:
        done = self.svc._repo.create('做完的', category='工作', priority=1)
        self.svc._repo.create('没做的', category='生活', priority=3)
        self.svc._repo.set_completed(done.id, True)
        report = self.svc.generate()
        self.assertIn('[x] 做完的', report)
        self.assertIn('[ ] 没做的', report)
        self.assertIn('创建: 2 项', report)
        self.assertIn('完成: 1 项', report)
        self.assertIn('未完成: 1 项', report)

    def test_generate_sections_present(self) -> None:
        report = self.svc.generate()
        self.assertIn('# ', report)
        self.assertIn('## ', report)


if __name__ == '__main__':
    unittest.main()
