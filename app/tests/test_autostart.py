"""autostart.py 单元测试。跨平台：Linux 用 desktop 文件，macOS 用 LaunchAgents，Windows 用注册表。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.utils import autostart


def _reload_autostart(platform_name: str) -> None:
    """重新加载 autostart 模块，模拟指定平台。"""
    import importlib
    with patch("platform.system", return_value=platform_name):
        importlib.reload(autostart)


class AutostartTest(unittest.TestCase):
    """测试跨平台开机自启模块。"""

    def setUp(self) -> None:
        """每个测试前重新加载模块，确保使用当前平台行为。"""
        _reload_autostart(sys.platform)

    # ---------- 辅助函数 ----------

    def test_slugify_app_name(self) -> None:
        """_slugify_app_name 返回小写连字符格式的应用名。"""
        result = autostart._slugify_app_name()
        self.assertEqual(result, "todomate")
        self.assertIsInstance(result, str)

    def test_desktop_file_path_linux(self) -> None:
        """Linux 下 desktop 文件路径正确。"""
        path = autostart._desktop_file_path()
        expected = Path.home() / ".config" / "autostart" / f"{autostart._slugify_app_name()}.desktop"
        self.assertEqual(path, expected)

    def test_plist_path_macos(self) -> None:
        """macOS 下 plist 文件路径正确。"""
        path = autostart._plist_path()
        expected = Path.home() / "Library" / "LaunchAgents" / f"com.{autostart._slugify_app_name()}.plist"
        self.assertEqual(path, expected)

    # ---------- Linux ----------

    def test_is_enabled_linux_false_when_no_file(self) -> None:
        """Linux 下无 desktop 文件时 is_enabled 返回 False。"""
        _reload_autostart("Linux")
        with patch.object(autostart, "_desktop_file_path") as mock_path:
            mock_path.return_value = Path(tempfile.mktemp())
            self.assertFalse(autostart.is_enabled())

    def test_is_enabled_linux_true_when_file_exists(self) -> None:
        """Linux 下有 desktop 文件时 is_enabled 返回 True。"""
        _reload_autostart("Linux")
        with tempfile.NamedTemporaryFile(suffix=".desktop", delete=False) as f:
            tmp_path = Path(f.name)
        try:
            with patch.object(autostart, "_desktop_file_path", return_value=tmp_path):
                self.assertTrue(autostart.is_enabled())
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_enable_creates_desktop_file(self) -> None:
        """Linux 下 enable 创建 ~/.config/autostart/Todomate.desktop。"""
        _reload_autostart("Linux")
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".config" / "autostart"
            config_dir.mkdir(parents=True)
            desktop_path = config_dir / f"{autostart._slugify_app_name()}.desktop"
            with patch.object(autostart, "_desktop_file_path", return_value=desktop_path):
                result = autostart.enable()
                self.assertTrue(result)
                self.assertTrue(desktop_path.exists())
                content = desktop_path.read_text()
                self.assertIn("[Desktop Entry]", content)
                self.assertIn("Type=Application", content)
                self.assertIn(f"Name={autostart._slugify_app_name()}", content)
                self.assertIn("Exec=", content)

    def test_disable_removes_desktop_file(self) -> None:
        """Linux 下 disable 删除 desktop 文件。"""
        _reload_autostart("Linux")
        with tempfile.NamedTemporaryFile(suffix=".desktop", delete=False) as f:
            tmp_path = Path(f.name)
        try:
            with patch.object(autostart, "_desktop_file_path", return_value=tmp_path):
                result = autostart.disable()
                self.assertTrue(result)
                self.assertFalse(tmp_path.exists())
        finally:
            tmp_path.unlink(missing_ok=True)

    # ---------- macOS ----------

    def test_is_enabled_macos_false_when_no_plist(self) -> None:
        """macOS 下无 plist 文件时 is_enabled 返回 False。"""
        _reload_autostart("Darwin")
        with patch.object(autostart, "_plist_path") as mock_path:
            mock_path.return_value = Path(tempfile.mktemp())
            self.assertFalse(autostart.is_enabled())

    def test_is_enabled_macos_true_when_plist_exists(self) -> None:
        """macOS 下有 plist 文件时 is_enabled 返回 True。"""
        _reload_autostart("Darwin")
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            tmp_path = Path(f.name)
        try:
            with patch.object(autostart, "_plist_path", return_value=tmp_path):
                self.assertTrue(autostart.is_enabled())
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_enable_creates_plist(self) -> None:
        """macOS 下 enable 创建 ~/Library/LaunchAgents/com.todomate.plist。"""
        _reload_autostart("Darwin")
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir) / "Library" / "LaunchAgents"
            agents_dir.mkdir(parents=True)
            plist_path = agents_dir / f"com.{autostart._slugify_app_name()}.plist"
            with patch.object(autostart, "_plist_path", return_value=plist_path):
                result = autostart.enable()
                self.assertTrue(result)
                self.assertTrue(plist_path.exists())
                content = plist_path.read_text()
                self.assertIn("<?xml version", content)
                self.assertIn("<plist version", content)
                self.assertIn("<key>Label</key>", content)
                self.assertIn("<key>ProgramArguments</key>", content)
                self.assertIn("<key>RunAtLoad</key>", content)
                self.assertIn("<key>KeepAlive</key>", content)

    def test_disable_removes_plist(self) -> None:
        """macOS 下 disable 删除 plist 文件。"""
        _reload_autostart("Darwin")
        with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
            tmp_path = Path(f.name)
        try:
            with patch.object(autostart, "_plist_path", return_value=tmp_path):
                result = autostart.disable()
                self.assertTrue(result)
                self.assertFalse(tmp_path.exists())
        finally:
            tmp_path.unlink(missing_ok=True)

    # ---------- Windows ----------

    def test_is_enabled_windows_false_when_no_registry_entry(self) -> None:
        """Windows 下无注册表项时 is_enabled 返回 False。"""
        _reload_autostart("Windows")
        # 创建 mock winreg 模块
        mock_winreg = MagicMock()
        mock_winreg.HKEY_CURRENT_USER = MagicMock()
        mock_winreg.KEY_READ = MagicMock()
        mock_winreg.QueryValueEx = MagicMock(side_effect=FileNotFoundError)
        mock_winreg.CloseKey = MagicMock()
        with patch.dict(sys.modules, {"winreg": mock_winreg}):
            self.assertFalse(autostart.is_enabled())

    def test_enable_creates_registry_entry(self) -> None:
        """Windows 下 enable 写入注册表。"""
        _reload_autostart("Windows")
        mock_winreg = MagicMock()
        mock_winreg.HKEY_CURRENT_USER = MagicMock()
        mock_winreg.KEY_SET_VALUE = MagicMock()
        mock_winreg.REG_SZ = MagicMock()
        mock_key = MagicMock()
        mock_key.__enter__ = MagicMock(return_value=mock_key)
        mock_key.__exit__ = MagicMock(return_value=False)
        mock_winreg.OpenKey = MagicMock(return_value=mock_key)
        mock_winreg.SetValueEx = MagicMock()
        with patch.dict(sys.modules, {"winreg": mock_winreg}):
            result = autostart.enable()
            self.assertTrue(result)
            mock_winreg.SetValueEx.assert_called_once()

    def test_disable_removes_registry_entry(self) -> None:
        """Windows 下 disable 删除注册表项。"""
        _reload_autostart("Windows")
        mock_winreg = MagicMock()
        mock_winreg.HKEY_CURRENT_USER = MagicMock()
        mock_winreg.KEY_SET_VALUE = MagicMock()
        mock_key = MagicMock()
        mock_key.__enter__ = MagicMock(return_value=mock_key)
        mock_key.__exit__ = MagicMock(return_value=False)
        mock_winreg.OpenKey = MagicMock(return_value=mock_key)
        mock_winreg.DeleteValue = MagicMock()
        with patch.dict(sys.modules, {"winreg": mock_winreg}):
            result = autostart.disable()
            self.assertTrue(result)
            mock_winreg.DeleteValue.assert_called_once()

    # ---------- toggle ----------

    def test_toggle_calls_enable_when_disabled(self) -> None:
        """未启用时 toggle 调用 enable 并返回其结果。"""
        with patch.object(autostart, "is_enabled", return_value=False), patch.object(autostart, "enable", return_value=True) as mock_enable:
            result = autostart.toggle()
            self.assertTrue(result)
            mock_enable.assert_called_once()

    def test_toggle_calls_disable_when_enabled(self) -> None:
        """已启用时 toggle 调用 disable 并返回其结果。"""
        with patch.object(autostart, "is_enabled", return_value=True), patch.object(autostart, "disable", return_value=False) as mock_disable:
            result = autostart.toggle()
            self.assertFalse(result)
            mock_disable.assert_called_once()

    # ---------- 异常处理 ----------

    def test_enable_returns_false_on_oserror(self) -> None:
        """enable 在 OSError 时返回 False。"""
        with patch.object(autostart, "_desktop_file_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/path/file.desktop")
            with patch.object(Path, "mkdir", side_effect=OSError):
                result = autostart.enable()
                self.assertFalse(result)

    def test_disable_returns_false_on_oserror(self) -> None:
        """disable 在 OSError 时返回 False。"""
        with patch.object(autostart, "_desktop_file_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/path/file.desktop")
            with patch.object(Path, "unlink", side_effect=OSError):
                result = autostart.disable()
                self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
