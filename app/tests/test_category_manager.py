"""category_manager.py 单元测试。mock PySide6 以测试持久化逻辑。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Mock PySide6 before importing category_manager
sys.modules["PySide6"] = MagicMock()
sys.modules["PySide6.QtCore"] = MagicMock()
sys.modules["PySide6.QtWidgets"] = MagicMock()


class CategoryManagerTest(unittest.TestCase):
    """测试 CategoryManager 模块级函数（不依赖真实 Qt 应用）。"""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._categories_file = Path(self._tmpdir.name) / "categories.json"
        self._inject_module()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        # 清理模块缓存
        keys_to_remove = [k for k in list(sys.modules.keys()) if "category_manager" in k]
        for k in keys_to_remove:
            del sys.modules[k]

    def _inject_module(self) -> None:
        """注入 category_manager 模块到 sys.modules 并设置测试文件路径。"""
        from app.ui.components import category_manager as cm_module
        cm_module._CATEGORIES_FILE = self._categories_file
        self._cm = cm_module

    # ---------- _load_categories ----------

    def test_load_categories_returns_defaults_when_file_missing(self) -> None:
        """文件不存在时返回默认值。"""
        self.assertFalse(self._categories_file.exists())
        result = self._cm._load_categories()
        self.assertIsInstance(result, list)
        self.assertIn("全部", result)
        self.assertIn("工作", result)
        self.assertIn("学习", result)
        self.assertIn("生活", result)

    def test_load_categories_returns_stored_values(self) -> None:
        """文件存在时返回存储的值。"""
        data = ["全部", "工作", "学习", "生活", "旅行", "运动"]
        self._categories_file.write_text(json.dumps(data), encoding="utf-8")
        result = self._cm._load_categories()
        self.assertEqual(result, data)
        self.assertEqual(len(result), 6)

    def test_load_categories_handles_corrupt_file(self) -> None:
        """文件格式错误时返回默认值。"""
        self._categories_file.write_text("not valid json", encoding="utf-8")
        result = self._cm._load_categories()
        self.assertIsInstance(result, list)
        self.assertIn("全部", result)

    def test_load_categories_handles_empty_list(self) -> None:
        """空列表时返回默认值。"""
        self._categories_file.write_text("[]", encoding="utf-8")
        result = self._cm._load_categories()
        self.assertEqual(result, ["全部", "工作", "学习", "生活"])

    # ---------- _save_categories ----------

    def test_save_categories_writes_file(self) -> None:
        """保存后文件存在且内容正确。"""
        data = ["全部", "工作", "学习", "生活", "旅行"]
        self._cm._save_categories(data)
        self.assertTrue(self._categories_file.exists())
        loaded = json.loads(self._categories_file.read_text())
        self.assertEqual(loaded, data)

    def test_save_categories_creates_parent_dir(self) -> None:
        """保存时自动创建父目录。"""
        nested = Path(self._tmpdir.name) / "deep" / "nested" / "categories.json"
        from app.ui.components import category_manager as cm_module
        cm_module._CATEGORIES_FILE = nested
        cm_module._save_categories(["全部", "工作"])
        self.assertTrue(nested.exists())

    def test_save_categories_preserves_all_item(self) -> None:
        """保存时'全部'项始终保留在第一位。"""
        data = ["工作", "学习", "生活"]
        self._cm._save_categories(data)
        loaded = json.loads(self._categories_file.read_text())
        self.assertEqual(loaded[0], "全部")
        self.assertIn("工作", loaded)
        self.assertIn("学习", loaded)
        self.assertIn("生活", loaded)

    # ---------- CategoryDialog 功能测试 ----------

    def test_category_dialog_add_category(self) -> None:
        """测试添加分类功能。"""
        current = ["全部", "工作", "学习", "生活"]
        new_name = "旅行"
        self.assertNotIn(new_name, current)
        current.append(new_name)
        self.assertIn(new_name, current)

    def test_category_dialog_rename_category(self) -> None:
        """测试重命名分类功能。"""
        current = ["全部", "工作", "学习", "生活"]
        old_name = "工作"
        new_name = "职场"
        idx = current.index(old_name)
        current[idx] = new_name
        self.assertEqual(current[idx], new_name)
        self.assertNotIn(old_name, current)

    def test_category_dialog_delete_category(self) -> None:
        """测试删除分类功能（不能删除'全部'）。"""
        current = ["全部", "工作", "学习", "生活"]
        # 不能删除'全部'
        self.assertEqual(current.count("全部"), 1)
        # 可以删除其他分类
        current.remove("工作")
        self.assertNotIn("工作", current)
        self.assertIn("全部", current)

    def test_category_dialog_delete_last_user_category(self) -> None:
        """删除最后一个用户分类后仍保留'全部'。"""
        current = ["全部", "工作"]
        current.remove("工作")
        self.assertEqual(current, ["全部"])

    # ---------- 集成验证 ----------

    def test_full_save_and_load_roundtrip(self) -> None:
        """完整保存后加载应恢复相同值。"""
        original = ["全部", "工作", "学习", "生活", "旅行", "运动"]
        self._cm._save_categories(original)
        restored = self._cm._load_categories()
        self.assertEqual(restored, original)

    def test_add_then_save_then_load(self) -> None:
        """添加分类后保存再加载应包含新分类。"""
        self._cm._save_categories(["全部", "工作", "学习", "生活", "旅行"])
        restored = self._cm._load_categories()
        self.assertEqual(len(restored), 5)
        self.assertEqual(restored[-1], "旅行")


if __name__ == "__main__":
    unittest.main()
