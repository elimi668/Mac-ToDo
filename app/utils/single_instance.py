"""单实例检查：确保同一时间只运行一个进程。

跨平台方案：
- Linux / macOS : 用 /tmp 下的锁文件 + fcntl 文件锁，进程退出后锁自动释放
- Windows      : 用 named mutex（Kernel Object），进程退出后系统自动释放

用法：
    import sys
    from app.utils.single_instance import SingleInstance
    if not SingleInstance(app_name="TodoMate").try_lock():
        print("程序已在运行", file=sys.stderr)
        sys.exit(0)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Self


class SingleInstance:
    """单实例互斥锁。"""

    _instance: SingleInstance | None = None

    def __init__(self, app_name: str = "TodoMate") -> None:
        self._app_name = app_name
        self._lock_file: Path | None = None
        self._lock_fd: int | None = None
        self._mutex = None  # Windows named mutex handle
        self._is_single = False

    def try_lock(self) -> bool:
        """尝试获取单实例锁，返回 True 表示成功（唯一实例）。"""
        if self._is_windows():
            return self._acquire_windows()
        else:
            return self._acquire_posix()

    def unlock(self) -> None:
        """释放锁。"""
        if self._is_windows():
            self._release_windows()
        else:
            self._release_posix()

    # -------- POSIX (Linux / macOS) --------

    def _acquire_posix(self) -> bool:
        lock_dir = Path("/tmp")
        lock_dir.mkdir(parents=True, exist_ok=True)
        self._lock_file = lock_dir / f".{self._app_name}_single.lock"

        try:
            self._lock_fd = os.open(
                str(self._lock_file),
                os.O_CREAT | os.O_RDWR,
                0o600,
            )
        except OSError:
            return False

        try:
            import fcntl

            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # 写入 PID 方便排查
            self._lock_file.write_text(str(os.getpid()), encoding="utf-8")
            self._is_single = True
            return True
        except OSError:
            # 锁已被占用，说明已有实例在运行
            os.close(self._lock_fd)
            self._lock_fd = None
            return False

    def _release_posix(self) -> None:
        if self._lock_fd is not None:
            try:
                import fcntl
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(self._lock_fd)
            except OSError:
                pass
            self._lock_fd = None
        if self._lock_file is not None:
            try:
                self._lock_file.unlink(missing_ok=True)
            except OSError:
                pass
            self._lock_file = None

    # -------- Windows --------

    def _acquire_windows(self) -> bool:
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # CREATE_NEW_MUTEX = 4，仅创建不存在的；若已存在则错误码为 ERROR_ALREADY_EXISTS
            ERROR_ALREADY_EXISTS = 183

            mutex_name = f"Global\\{self._app_name}_single_instance"
            self._mutex = kernel32.CreateMutexW(None, True, mutex_name)  # type: ignore[attr-defined]
            last_error = kernel32.GetLastError()  # type: ignore[attr-defined]

            if last_error == ERROR_ALREADY_EXISTS:
                # 已有实例持有该 mutex
                kernel32.CloseHandle(self._mutex)  # type: ignore[attr-defined]
                self._mutex = None
                return False
            # 成功获得唯一所有权
            self._is_single = True
            return True
        except OSError:
            return False

    def _release_windows(self) -> None:
        if self._mutex is not None:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.ReleaseMutex(self._mutex)  # type: ignore[attr-defined]
                kernel32.CloseHandle(self._mutex)  # type: ignore[attr-defined]
            except OSError:
                pass
            self._mutex = None

    @staticmethod
    def _is_windows() -> bool:
        return sys.platform == "win32"

    def __enter__(self) -> Self:
        if not self.try_lock():
            raise RuntimeError(f"检测到 {self._app_name} 已经在运行，不允许重复启动。")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[override]
        self.unlock()
