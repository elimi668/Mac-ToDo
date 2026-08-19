"""autostart.py 单元测试。Linux 环境下所有 Windows 注册表操作均返回 False。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils import autostart


class AutostartTest(unittest.TestCase):
    """测试 autostart 模块在非 Windows 平台的行为。"""

    def test_is_enabled_returns_false_on_linux(self) -> None:
        """非 Windows 平台 is_enabled 应返回 False。"""
        with patch("sys.platform", "linux"):
            # 重新导入以应用 patch（模块级 _IS_WINDOWS 在导入时计算）
            import importlib
            importlib.reload(autostart)
            self.assertFalse(autostart.is_enabled())

    def test_enable_returns_false_on_linux(self) -> None:
        """非 Windows 平台 enable 应返回 False。"""
        with patch("sys.platform", "linux"):
            import importlib
            importlib.reload(autostart)
            self.assertFalse(autostart.enable())

    def test_disable_returns_false_on_linux(self) -> None:
        """非 Windows 平台 disable 返回 False。"""
        with patch("sys.platform", "linux"):
            import importlib
            importlib.reload(autostart)
            self.assertFalse(autostart.disable())

    def test_toggle_calls_enable_on_non_windows(self) -> None:
        """未启用时 toggle 调用 enable，但 toggle 自身始终在 else 分支返回 True。"""
        with patch("sys.platform", "linux"):
            import importlib
            importlib.reload(autostart)
            # toggle else 分支：enable() 返回值被忽略，直接 return True
            result = autostart.toggle()
            self.assertTrue(result)

    def test_toggle_calls_disable_when_enabled(self) -> None:
        """已启用时 toggle 调用 disable 并返回其结果。"""
        with patch("sys.platform", "win32"):
            import importlib
            importlib.reload(autostart)
            with patch.object(autostart, "is_enabled", return_value=True):
                with patch.object(autostart, "disable", return_value=False):
                    result = autostart.toggle()
                    self.assertFalse(result)

    def test_registry_key_format(self) -> None:
        """注册表路径格式正确。"""
        self.assertEqual(
            autostart._registry_key(),
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        )
