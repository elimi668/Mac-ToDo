"""跨平台开机自启管理。Windows 用注册表，Linux 用 xdg-autostart，macOS 用 LaunchAgents。"""
from __future__ import annotations

import platform
import sys
from pathlib import Path

_SYSTEM = platform.system()  # "Windows" / "Linux" / "Darwin"


def _get_exe_path() -> Path:
    """获取可执行路径（开发环境取 python 路径并构造 -m app.main 命令）。"""
    exe = Path(sys.executable).resolve()
    return exe


def _slugify_app_name() -> str:
    from app import config
    return config.APP_NAME.replace(" ", "-").lower()


def is_enabled() -> bool:
    """检测开机自启是否已启用。"""
    if _SYSTEM == "Windows":
        return _win_is_enabled()
    if _SYSTEM == "Linux":
        return _desktop_file_path().exists()
    if _SYSTEM == "Darwin":
        return _plist_path().exists()
    return False


def enable() -> bool:
    """启用开机自启。"""
    try:
        if _SYSTEM == "Windows":
            return _win_enable()
        if _SYSTEM == "Linux":
            return _create_desktop_file()
        if _SYSTEM == "Darwin":
            return _create_plist()
    except OSError:
        pass
    return False


def disable() -> bool:
    """禁用开机自启。"""
    try:
        if _SYSTEM == "Windows":
            return _win_disable()
        if _SYSTEM == "Linux":
            _desktop_file_path().unlink(missing_ok=True)
            return True
        if _SYSTEM == "Darwin":
            _plist_path().unlink(missing_ok=True)
            return True
    except OSError:
        pass
    return False


def toggle() -> bool:
    """切换开机自启状态，返回新状态。"""
    if is_enabled():
        return disable()
    return enable()


# ---------- Windows ----------

def _win_is_enabled() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _slugify_app_name())
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def _win_enable() -> bool:
    try:
        import winreg
        exe = _get_exe_path()
        if exe.name.lower() in ("python.exe", "pythonw.exe"):
            target = f'"{exe}" -m app.main'
        else:
            target = f'"{exe}"'
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, _slugify_app_name(), 0, winreg.REG_SZ, target)
        return True
    except OSError:
        return False


def _win_disable() -> bool:
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, _slugify_app_name())
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


# ---------- Linux ----------

def _desktop_file_path() -> Path:
    return Path.home() / ".config" / "autostart" / f"{_slugify_app_name()}.desktop"


def _create_desktop_file() -> bool:
    try:
        desktop_dir = _desktop_file_path().parent
        desktop_dir.mkdir(parents=True, exist_ok=True)
        exe = _get_exe_path()
        icon = Path(__file__).resolve().parent.parent / "resources" / "icons" / "app_icon.png"
        icon_path = str(icon) if icon.exists() else ""
        content = (
            f"[Desktop Entry]\n"
            f"Type=Application\n"
            f"Exec={exe} -m app.main\n"
            f"Name={_slugify_app_name()}\n"
            f"Comment=TodoMate 任务管理助手\n"
            f"Hidden=false\n"
            f"NoDisplay=false\n"
            f"X-GNOME-Autostart-enabled=true\n"
            f"Terminal=false\n"
            f"Icon={icon_path}\n"
        )
        _desktop_file_path().write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


# ---------- macOS ----------

def _plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"com.{_slugify_app_name()}.plist"


def _create_plist() -> bool:
    try:
        plist_dir = _plist_path().parent
        plist_dir.mkdir(parents=True, exist_ok=True)
        exe = _get_exe_path()
        label = f"com.{_slugify_app_name()}.autostart"
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n'
            '<dict>\n'
            f'  <key>Label</key>\n'
            f'  <string>{label}</string>\n'
            '  <key>ProgramArguments</key>\n'
            '  <array>\n'
            f'    <string>{exe}</string>\n'
            f'    <string>-m</string>\n'
            f'    <string>app.main</string>\n'
            '  </array>\n'
            '  <key>RunAtLoad</key>\n'
            '  <true/>\n'
            '  <key>KeepAlive</key>\n'
            '  <false/>\n'
            '</dict>\n'
            '</plist>\n'
        )
        _plist_path().write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False
