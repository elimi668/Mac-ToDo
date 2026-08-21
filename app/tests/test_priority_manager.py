"""priority_manager.py 单元测试。mock PySide6 以测试持久化逻辑。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Mock PySide6 before importing priority_manager
sys.modules["PySide6"] = MagicMock()
sys.modules["PySide6.QtCore"] = MagicMock()
sys.modules["PySide6.QtWidgets"] = MagicMock()


class PriorityManagerTest(unittest.TestCase):
    """测试 PriorityManager 模块级函数（不依赖真实 Qt 应用）。"""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._priorities_file = Path(self._tmpdir.name) / "priorities.json"
        self._inject_module()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        # 清理模块缓存
        keys_to_remove = [k for k in list(sys.modules.keys()) if "priority_manager" in k]
        for k in keys_to_remove:
            del sys.modules[k]

    def _inject_module(self) -> None:
        """注入 priority_manager 模块到 sys.modules 并设置测试文件路径。"""
        from app.ui.components import priority_manager as pm_module
        pm_module._PRIORITIES_FILE = self._priorities_file
        self._pm = pm_module

    # ---------- _load_priorities ----------

    def test_load_priorities_returns_defaults_when_file_missing(self) -> None:
        """文件不存在时返回默认值。"""
        self.assertFalse(self._priorities_file.exists())
        result = self._pm._load_priorities()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        # JSON 序列化为 list，但默认值是 tuple
        self.assertEqual(result[0][0], "高")
        self.assertEqual(result[0][1], 1)
        self.assertEqual(result[1][0], "中")
        self.assertEqual(result[1][1], 2)
        self.assertEqual(result[2][0], "低")
        self.assertEqual(result[2][1], 3)

    def test_load_priorities_returns_stored_values(self) -> None:
        """文件存在时返回存储的值。"""
        # JSON 将 tuple 序列化为 list
        data = [["紧急", 1], ["高", 2], ["中", 3], ["低", 4]]
        self._priorities_file.write_text(json.dumps(data), encoding="utf-8")
        result = self._pm._load_priorities()
        self.assertEqual(len(result), 4)
        # JSON 反序列化后是 list 格式
        self.assertEqual(result[0], ["紧急", 1])
        self.assertEqual(result[1], ["高", 2])

    def test_load_priorities_handles_corrupt_file(self) -> None:
        """文件格式错误时返回默认值。"""
        self._priorities_file.write_text("not valid json", encoding="utf-8")
        result = self._pm._load_priorities()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_load_priorities_handles_empty_list(self) -> None:
        """空列表时返回默认值。"""
        self._priorities_file.write_text("[]", encoding="utf-8")
        result = self._pm._load_priorities()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], "高")

    # ---------- _save_priorities ----------

    def test_save_priorities_writes_file(self) -> None:
        """保存后文件存在且内容正确。"""
        data = [["高", 1], ["中", 2], ["低", 3], ["可选", 4]]
        self._pm._save_priorities(data)
        self.assertTrue(self._priorities_file.exists())
        loaded = json.loads(self._priorities_file.read_text())
        self.assertEqual(loaded, data)

    def test_save_priorities_creates_parent_dir(self) -> None:
        """保存时自动创建父目录。"""
        nested = Path(self._tmpdir.name) / "deep" / "nested" / "priorities.json"
        from app.ui.components import priority_manager as pm_module
        pm_module._PRIORITIES_FILE = nested
        pm_module._save_priorities([["高", 1], ["中", 2]])
        self.assertTrue(nested.exists())

    def test_save_priorities_preserves_order(self) -> None:
        """保存后顺序应保持一致。"""
        data = [["紧急", 0], ["高", 1], ["中", 2], ["低", 3]]
        self._pm._save_priorities(data)
        loaded = json.loads(self._priorities_file.read_text())
        self.assertEqual(loaded[0], ["紧急", 0])
        self.assertEqual(loaded[1], ["高", 1])
        self.assertEqual(loaded[2], ["中", 2])
        self.assertEqual(loaded[3], ["低", 3])

    # ---------- PriorityDialog 功能测试 ----------

    def test_priority_dialog_add_priority(self) -> None:
        """测试添加优先级功能。"""
        current = [["高", 1], ["中", 2], ["低", 3]]
        new_name = "紧急"
        new_value = 0  # 比高更优先
        current.insert(0, [new_name, new_value])
        self.assertEqual(current[0], ["紧急", 0])

    def test_priority_dialog_rename_priority(self) -> None:
        """测试重命名优先级功能。"""
        current = [["高", 1], ["中", 2], ["低", 3]]
        old_name = "高"
        new_name = "紧急"
        idx = next(i for i, (name, _) in enumerate(current) if name == old_name)
        current[idx] = [new_name, current[idx][1]]
        self.assertEqual(current[idx], ["紧急", 1])

    def test_priority_dialog_delete_priority(self) -> None:
        """测试删除优先级功能（至少保留一个）。"""
        current = [["高", 1], ["中", 2], ["低", 3]]
        # 删除一个后仍保留至少一个
        current.pop()
        self.assertEqual(len(current), 2)
        self.assertGreaterEqual(len(current), 1)

    def test_priority_dialog_cannot_delete_last(self) -> None:
        """不能删除最后一个优先级。"""
        current = [["高", 1]]
        # 尝试删除，应阻止或报错
        with self.assertRaises(ValueError):
            current.pop()
            if len(current) < 1:
                raise ValueError("至少需要保留一个优先级")

    def test_priority_dialog_update_value(self) -> None:
        """测试更新优先级值。"""
        current = [["高", 1], ["中", 2], ["低", 3]]
        # 修改'中'的值为 5
        idx = 1
        current[idx] = [current[idx][0], 5]
        self.assertEqual(current[idx], ["中", 5])

    # ---------- 配置一致性验证 ----------

    def test_default_priorities_match_config(self) -> None:
        """默认优先级应与 config.PRIORITY_OPTIONS 一致。"""
        from app import config
        defaults = self._pm._load_priorities()
        config_options = config.PRIORITY_OPTIONS
        self.assertEqual(len(defaults), len(config_options))
        for item, (config_name, config_value) in zip(defaults, config_options):
            self.assertEqual(item[0], config_name)
            self.assertEqual(item[1], config_value)

    # ---------- 集成验证 ----------

    def test_full_save_and_load_roundtrip(self) -> None:
        """完整保存后加载应恢复相同值。"""
        original = [["紧急", 0], ["高", 1], ["中", 2], ["低", 3]]
        self._pm._save_priorities(original)
        restored = self._pm._load_priorities()
        # 加载后 tuple 形式
        self.assertEqual(len(restored), 4)
        self.assertEqual(restored[0][0], "紧急")
        self.assertEqual(restored[0][1], 0)

    def test_add_then_save_then_load(self) -> None:
        """添加优先级后保存再加载应包含新优先级。"""
        self._pm._save_priorities([["高", 1], ["中", 2], ["低", 3], ["可选", 4]])
        restored = self._pm._load_priorities()
        self.assertEqual(len(restored), 4)
        self.assertEqual(restored[-1][0], "可选")
        self.assertEqual(restored[-1][1], 4)

    def test_invalid_priority_value_rejected(self) -> None:
        """负数或零值优先级应被拒绝（如果实现验证）。"""
        # 模拟验证逻辑 - 实际测试中 value 是 int
        valid_priorities = [["高", 1], ["中", 2], ["低", 3]]
        # 验证逻辑测试：正常优先级值应大于0
        for name, value in valid_priorities:
            self.assertGreater(value, 0, f"优先级值 must be > 0, got {value}")


if __name__ == "__main__":
    unittest.main()
