"""Reject inherited SDK objects without waiting for vanished forked threads."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from mecheye import _compat, area_scan_3d_camera as a


class ProcessTests(unittest.TestCase):
    def test_process_checks_precede_inherited_python_locks_and_snapshots(self):
        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        event = _compat._snapshot(a.EventData())
        with patch.object(
            _compat.os, "getpid", return_value=_compat._import_process + 1
        ):
            for operation in (
                lambda: a.Camera(),
                lambda: camera.current_user_set(),
                lambda: camera.disconnect(),
                lambda: camera.pop_callback_errors(),
                lambda: event.frame_id,
                lambda: setattr(event, "frame_id", 1),
                lambda: _compat._unwrap(event),
            ):
                with self.assertRaisesRegex(RuntimeError, "spawn or forkserver"):
                    operation()

    @unittest.skipUnless(hasattr(os, "fork"), "fork is unavailable on this platform")
    def test_fork_rejects_public_and_native_sdk_calls_without_hanging(self):
        script = textwrap.dedent("""
            import os
            from mecheye import _native, area_scan_3d_camera as a
            camera = a.Camera()
            pid = os.fork()
            if pid == 0:
                try:
                    for operation in (lambda: a.Frame2D(), lambda: camera.connected,
                                      lambda: _native.sdk.Frame2D()):
                        try:
                            operation()
                        except RuntimeError as error:
                            assert "spawn or forkserver" in str(error)
                        else:
                            raise AssertionError("forked SDK operation was accepted")
                    os._exit(0)
                except BaseException:
                    os._exit(1)
            _, status = os.waitpid(pid, 0)
            assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, status
            camera.disconnect()
        """)
        result = subprocess.run(
            [sys.executable, "-B", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(hasattr(os, "fork"), "fork is unavailable on this platform")
    def test_fork_rejects_calls_even_when_another_parent_thread_holds_api_lock(self):
        script = textwrap.dedent("""
            import os
            import threading
            from mecheye import area_scan_3d_camera as a
            from mecheye._compat import _api_lock
            camera = a.Camera()
            entered, release = threading.Event(), threading.Event()
            def hold():
                with _api_lock:
                    entered.set()
                    release.wait(5)
            worker = threading.Thread(target=hold)
            worker.start()
            assert entered.wait(2)
            pid = os.fork()
            if pid == 0:
                try:
                    camera.capture_2d(a.Frame2D(), 1)
                except RuntimeError as error:
                    os._exit(0 if "spawn or forkserver" in str(error) else 1)
                os._exit(1)
            _, status = os.waitpid(pid, 0)
            release.set()
            worker.join(2)
            camera.disconnect()
            assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, status
        """)
        result = subprocess.run(
            [sys.executable, "-B", "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_spawn_and_forkserver_create_independent_sdk_workers(self):
        script = textwrap.dedent("""
            import multiprocessing as mp
            from mecheye import area_scan_3d_camera as a
            def capture_types(queue):
                camera = a.Camera()
                frame = a.Frame2DAnd3D()
                result = (frame.frame_2d().is_empty(), frame.frame_3d().is_empty())
                camera.disconnect()
                queue.put(result)
            if __name__ == "__main__":
                camera = a.Camera()
                for method in ("spawn", "forkserver"):
                    if method not in mp.get_all_start_methods():
                        continue
                    if method == "forkserver":
                        # Keep the SDK out of the server before it forks workers.
                        mp.set_forkserver_preload([])
                    context = mp.get_context(method)
                    queue = context.Queue()
                    worker = context.Process(target=capture_types, args=(queue,))
                    worker.start()
                    assert queue.get(timeout=5) == (True, True)
                    worker.join(5)
                    assert worker.exitcode == 0, worker.exitcode
                    queue.close()
                    queue.join_thread()
                camera.disconnect()
        """)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "process_check.py"
            path.write_text(script)
            result = subprocess.run(
                [sys.executable, "-B", str(path)],
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
