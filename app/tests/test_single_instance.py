"""SingleInstance unit tests. Verifies lock acquisition, blocking, and unlock behavior."""
from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path


class SingleInstanceBasicTest(unittest.TestCase):
    """Tests for the posix (Linux/macOS) single-instance locking mechanism."""

    def test_first_instance_acquires_lock(self) -> None:
        """The first instance to call try_lock() should succeed."""
        from app.utils.single_instance import SingleInstance
        inst = SingleInstance(app_name="TestAppAcquire")
        self.assertTrue(inst.try_lock(), "First instance should acquire lock")
        inst.unlock()

    def test_second_instance_blocked(self) -> None:
        """A second instance started while the first holds the lock should be blocked."""
        from app.utils.single_instance import SingleInstance

        inst1 = SingleInstance(app_name="TestAppBlocked")
        self.assertTrue(inst1.try_lock(), "First should acquire")

        inst2 = SingleInstance(app_name="TestAppBlocked")
        self.assertFalse(inst2.try_lock(), "Second should be blocked")
        # inst2 never acquired, so no unlock needed

        inst1.unlock()

    def test_unlock_releases_for_third(self) -> None:
        """After unlock, a new instance should be able to acquire."""
        from app.utils.single_instance import SingleInstance

        inst1 = SingleInstance(app_name="TestAppRelease")
        inst1.try_lock()
        inst1.unlock()

        inst2 = SingleInstance(app_name="TestAppRelease")
        self.assertTrue(inst2.try_lock(), "Should acquire after unlock")
        inst2.unlock()

    def test_lock_file_contains_pid(self) -> None:
        """After acquiring lock, the lock file should contain the process PID."""
        from app.utils.single_instance import SingleInstance

        inst = SingleInstance(app_name="TestAppPid")
        inst.try_lock()
        # Lock file is at /tmp/.{app_name}_single.lock
        lock_file = Path("/tmp") / f".{inst._app_name}_single.lock"
        if lock_file.exists():
            pid_in_file = lock_file.read_text().strip()
            self.assertEqual(pid_in_file, str(os.getpid()))
        inst.unlock()

    def test_cross_process_blocking(self) -> None:
        """Verify that two separate processes are correctly blocked from both acquiring."""
        holder_code = '''
import sys, time
sys.path.insert(0, "/root/deepseek/Mac-ToDo")
from app.utils.single_instance import SingleInstance
si = SingleInstance(app_name="TodoMate_cross_proc")
assert si.try_lock(), "Holder should acquire"
time.sleep(0.6)
si.unlock()
print("HOLDER_RELEASED")
'''
        proc = subprocess.Popen([sys.executable, "-c", holder_code])
        time.sleep(0.3)  # let holder acquire lock

        from app.utils.single_instance import SingleInstance
        inst = SingleInstance(app_name="TodoMate_cross_proc")
        locked = inst.try_lock()
        self.assertFalse(locked, "Second process should be blocked")

        proc.wait(timeout=5)
        self.assertEqual(proc.returncode, 0)

    def test_context_manager_normal_exit(self) -> None:
        """Using `with` when lock is available should not raise."""
        from app.utils.single_instance import SingleInstance
        with SingleInstance(app_name="TestAppCtx") as si:
            self.assertTrue(si._is_single)
        # After exit, lock released — another can acquire
        inst2 = SingleInstance(app_name="TestAppCtx")
        self.assertTrue(inst2.try_lock())
        inst2.unlock()

    def test_context_manager_raises_on_duplicate(self) -> None:
        """Using `with` when lock is held by another process should raise RuntimeError."""
        holder_code = '''
import sys, time
sys.path.insert(0, "/root/deepseek/Mac-ToDo")
from app.utils.single_instance import SingleInstance
si = SingleInstance(app_name="TodoMate_ctx_test")
si.try_lock()
time.sleep(0.5)
si.unlock()
'''
        proc = subprocess.Popen([sys.executable, "-c", holder_code])
        time.sleep(0.2)  # let holder acquire

        from app.utils.single_instance import SingleInstance
        with self.assertRaises(RuntimeError), SingleInstance(app_name="TodoMate_ctx_test"):
                pass  # should never reach here

        proc.wait(timeout=5)

    def test_different_app_names_independent(self) -> None:
        """Two instances of different app names should not block each other."""
        from app.utils.single_instance import SingleInstance

        inst1 = SingleInstance(app_name="AppA_unique")
        inst2 = SingleInstance(app_name="AppB_unique")
        self.assertTrue(inst1.try_lock(), "AppA should acquire")
        self.assertTrue(inst2.try_lock(), "AppB should also acquire independently")
        inst1.unlock()
        inst2.unlock()


if __name__ == "__main__":
    unittest.main()
