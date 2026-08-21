"""FilterRow 单元测试。验证筛选值返回正确性。"""
from __future__ import annotations

import sys
import unittest

from PySide6.QtWidgets import QApplication

_qapp: QApplication | None = None


def get_qapp() -> QApplication:
    global _qapp
    if _qapp is None:
        _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


class FilterRowTest(unittest.TestCase):
    """FilterRow 组件行为测试。"""

    def setUp(self) -> None:
        self.app = get_qapp()
        from app.ui.components.filter_row import FilterRow

        self.filter_row = FilterRow()

    def tearDown(self) -> None:
        self.filter_row.deleteLater()

    def test_selected_category_all_returns_none(self) -> None:
        """默认"全部"应返回 None。"""
        self.assertIsNone(self.filter_row.selected_category)

    def test_selected_category_by_index(self) -> None:
        from app import config

        self.filter_row._cat_combo.setCurrentIndex(1)  # 工作
        self.assertEqual(self.filter_row.selected_category, config.CATEGORIES[1])

        self.filter_row._cat_combo.setCurrentIndex(2)  # 学习
        self.assertEqual(self.filter_row.selected_category, config.CATEGORIES[2])

        self.filter_row._cat_combo.setCurrentIndex(3)  # 生活
        self.assertEqual(self.filter_row.selected_category, config.CATEGORIES[3])

    def test_selected_priority_all_returns_none(self) -> None:
        """默认"全部"应返回 None。"""
        self.assertIsNone(self.filter_row.selected_priority)

    def test_selected_priority_by_index(self) -> None:

        self.filter_row._pri_combo.setCurrentIndex(1)  # 高
        self.assertEqual(self.filter_row.selected_priority, 1)

        self.filter_row._pri_combo.setCurrentIndex(2)  # 中
        self.assertEqual(self.filter_row.selected_priority, 2)

        self.filter_row._pri_combo.setCurrentIndex(3)  # 低
        self.assertEqual(self.filter_row.selected_priority, 3)

    def test_selected_date_filter(self) -> None:
        self.filter_row._date_combo.setCurrentIndex(1)
        self.assertEqual(self.filter_row.selected_date_filter, "今天")

        self.filter_row._date_combo.setCurrentIndex(2)
        self.assertEqual(self.filter_row.selected_date_filter, "明天")

        self.filter_row._date_combo.setCurrentIndex(3)
        self.assertEqual(self.filter_row.selected_date_filter, "本周")

        self.filter_row._date_combo.setCurrentIndex(4)
        self.assertEqual(self.filter_row.selected_date_filter, "已过期")


if __name__ == "__main__":
    unittest.main()
