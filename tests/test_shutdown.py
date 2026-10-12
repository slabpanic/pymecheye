"""Check native cleanup at process exit while SDK objects remain alive."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class ProcessShutdownTests(unittest.TestCase):
    def test_sdk_objects_and_cycles_do_not_abort_or_hang_at_exit(self):
        script = textwrap.dedent("""
            import gc
            from mecheye import area_scan_3d_camera as a

            retained = [(a.Camera(), a.Frame2DAnd3D()) for _ in range(64)]
            for camera, frame in retained:
                camera.cycle = camera
                camera.current_user_set()
                camera.capture_2d(a.Frame2D(), 1)
            gc.disable()
            """)
        for attempt in range(3):
            with self.subTest(attempt=attempt):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", script],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=dict(os.environ, PYTHONFAULTHANDLER="1"),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test_full_suite_exits_without_native_abort(self):
        # Run the SDK/mocking interactions in a child so teardown failures are observable.
        # Exclude this module to avoid recursively spawning the shutdown tests.
        modules = [
            "test_camera",
            "test_containers",
            "test_convenience",
            "test_loader",
            "test_sdk",
            "test_utils",
        ]
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", *modules],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            timeout=30,
            env=dict(os.environ, PYTHONFAULTHANDLER="1"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Bad file descriptor", result.stderr)
