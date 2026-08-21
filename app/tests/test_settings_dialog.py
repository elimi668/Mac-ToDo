"""settings_dialog.py 单元测试。mock PySide6 以测试持久化逻辑。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Mock PySide6 before importing settings_dialog
sys.modules["PySide6"] = MagicMock()
sys.modules["PySide6.QtCore"] = MagicMock()
sys.modules["PySide6.QtWidgets"] = MagicMock()


class SettingsDialogTest(unittest.TestCase):
    """测试 SettingsDialog 模块级函数（不依赖真实 Qt 应用）。"""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._settings_file = Path(self._tmpdir.name) / "settings.json"
        # 确保 settings_dialog 模块被导入并注入 mock
        self._inject_module()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        # 清理模块缓存
        keys_to_remove = [k for k in list(sys.modules.keys()) if "settings_dialog" in k]
        for k in keys_to_remove:
            del sys.modules[k]

    def _inject_module(self) -> None:
        """注入 settings_dialog 模块到 sys.modules 并设置测试文件路径。"""
        from app.ui.components import settings_dialog as sd_module
        sd_module._SETTINGS_FILE = self._settings_file
        self._sd = sd_module

    # ---------- _load_settings ----------

    def test_load_settings_returns_defaults_when_file_missing(self) -> None:
        """文件不存在时返回默认值。"""
        self.assertFalse(self._settings_file.exists())
        result = self._sd._load_settings()
        self.assertIsInstance(result, dict)
        self.assertIn("backup_interval_hours", result)
        self.assertIn("reminder_lead_minutes", result)
        self.assertIn("autostart", result)
        self.assertIn("theme", result)

    def test_load_settings_returns_stored_values(self) -> None:
        """文件存在时返回存储的值。"""
        data = {
            "backup_interval_hours": 12,
            "reminder_lead_minutes": 30,
            "autostart": True,
            "theme": "dark",
        }
        self._settings_file.write_text(json.dumps(data), encoding="utf-8")
        result = self._sd._load_settings()
        self.assertEqual(result["backup_interval_hours"], 12)
        self.assertEqual(result["reminder_lead_minutes"], 30)
        self.assertTrue(result["autostart"])
        self.assertEqual(result["theme"], "dark")

    def test_load_settings_handles_corrupt_file(self) -> None:
        """文件格式错误时返回默认值。"""
        self._settings_file.write_text("not valid json", encoding="utf-8")
        result = self._sd._load_settings()
        self.assertIsInstance(result, dict)

    # ---------- _save_settings ----------

    def test_save_settings_writes_file(self) -> None:
        """保存后文件存在且内容正确。"""
        data = {
            "backup_interval_hours": 24,
            "reminder_lead_minutes": 15,
            "autostart": False,
            "theme": "light",
        }
        self._sd._save_settings(data)
        self.assertTrue(self._settings_file.exists())
        loaded = json.loads(self._settings_file.read_text())
        self.assertEqual(loaded, data)

    def test_save_settings_creates_parent_dir(self) -> None:
        """保存时自动创建父目录。"""
        nested = Path(self._tmpdir.name) / "deep" / "nested" / "settings.json"
        from app.ui.components import settings_dialog as sd_module
        sd_module._SETTINGS_FILE = nested
        sd_module._save_settings({"test": True})
        self.assertTrue(nested.exists())

    # ---------- 集成验证 ----------

    def test_full_save_and_load_roundtrip(self) -> None:
        """完整保存后加载应恢复相同值。"""
        original = {
            "backup_interval_hours": 48,
            "reminder_lead_minutes": 10,
            "autostart": True,
            "theme": "dark",
        }
        self._sd._save_settings(original)
        restored = self._sd._load_settings()
        self.assertEqual(restored, original)


if __name__ == "__main__":
    unittest.main()
