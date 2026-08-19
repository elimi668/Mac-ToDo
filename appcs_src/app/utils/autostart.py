"""开机启动管理（Windows 注册表）。"""
from __future__ import annotations

import sys
from pathlib import Path

_IS_WINDOWS = sys.platform == "win32"


def _registry_key() -> str:
    return r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_enabled() -> bool:
    if not _IS_WINDOWS:
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _registry_key(), 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, "MacTodo")
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable() -> bool:
    if not _IS_WINDOWS:
        return False
    try:
        import winreg

        exe = Path(sys.executable).resolve()
        if exe.name.lower() in ("python.exe", "pythonw.exe"):
            target = f'"{exe}" -m app.main'
        else:
            target = f'"{exe}"'

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _registry_key(), 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "MacTodo", 0, winreg.REG_SZ, target)
        return True
    except OSError:
        return False


def disable() -> bool:
    if not _IS_WINDOWS:
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _registry_key(), 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, "MacTodo")
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


def toggle() -> bool:
    if is_enabled():
        disable()
        return False
    else:
        enable()
        return True
