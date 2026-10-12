"""Validate SDK selection, binary identity, and build records without loading fixtures."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from mecheye import _sdk as sdk


def runtime_bytes(target):
    header = bytearray(64)
    if target == "linux":
        header[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<HH", header, 16, 3, 62)
        return bytes(header)
    header[:2] = b"MZ"
    struct.pack_into("<I", header, 60, 64)
    pe = bytearray(26)
    pe[:4] = b"PE\0\0"
    struct.pack_into("<H", pe, 4, 0x8664)
    struct.pack_into("<H", pe, 22, 0x2000)
    struct.pack_into("<H", pe, 24, 0x20B)
    return bytes(header + pe)


class SdkValidationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()

    def test_explicit_sdk_root_resolves_and_never_falls_back(self):
        with patch.dict(os.environ, {"MECHEYE_SDK_ROOT": str(self.root)}):
            self.assertEqual(sdk.sdk_root(), self.root)
        for value in ("relative/sdk", str(self.root / "missing")):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"MECHEYE_SDK_ROOT": value}):
                    with self.assertRaises(ImportError):
                        sdk.sdk_root()
        file = self.root / "file"
        file.touch()
        with patch.dict(os.environ, {"MECHEYE_SDK_ROOT": str(file)}):
            with self.assertRaisesRegex(ImportError, "not a directory"):
                sdk.sdk_root()

    def test_unset_and_empty_override_use_platform_default(self):
        with patch.dict(sdk._DEFAULT_SDK_ROOTS, {sys.platform: str(self.root)}):
            with patch.dict(os.environ):
                os.environ.pop("MECHEYE_SDK_ROOT", None)
                self.assertEqual(sdk.sdk_root(), self.root)
                os.environ["MECHEYE_SDK_ROOT"] = ""
                self.assertEqual(sdk.sdk_root(), self.root)

    def test_sdk_file_rejects_missing_files_directories_and_path_escape(self):
        file = self.root / "runtime"
        file.write_bytes(b"sdk")
        self.assertEqual(sdk.sdk_file(self.root, "runtime"), file)
        for relative in ("missing", ".", "../"):
            with self.subTest(relative=relative):
                with self.assertRaises(ImportError):
                    sdk.sdk_file(self.root, relative)

    def test_sdk_file_rejects_symlink_outside_root(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "runtime"
            target.write_bytes(b"sdk")
            try:
                (self.root / "runtime").symlink_to(target)
            except OSError as exc:
                self.skipTest(f"Symlink creation is unavailable: {exc}")
            with self.assertRaisesRegex(ImportError, "outside"):
                sdk.sdk_file(self.root, "runtime")

    def test_binary_validation_accepts_elf_and_pe_and_rejects_wrong_abi(self):
        for target in ("linux", "win32"):
            valid = runtime_bytes(target)
            file = self.root / target
            file.write_bytes(valid)
            sdk.validate_runtime(file, target)
            corruptions = [b"", valid[:32], b"text instead of a library"]
            altered = bytearray(valid)
            if target == "linux":
                altered[4] = 1
            else:
                struct.pack_into("<H", altered, 68, 0x14C)
            corruptions.append(bytes(altered))
            altered = bytearray(valid)
            if target == "linux":
                struct.pack_into("<H", altered, 16, 2)
            else:
                struct.pack_into("<H", altered, 86, 0)
            corruptions.append(bytes(altered))
            for index, contents in enumerate(corruptions):
                with self.subTest(target=target, corruption=index):
                    file.write_bytes(contents)
                    with self.assertRaises(ImportError):
                        sdk.validate_runtime(file, target)
        with self.assertRaises(ImportError):
            sdk.validate_runtime(self.root / "missing", "linux")

    def test_hash_matches_known_digest_and_reports_unreadable_file(self):
        file = self.root / "payload"
        payload = b"Mech-Eye SDK\n" * 100000
        file.write_bytes(payload)
        self.assertEqual(sdk.file_sha256(file), hashlib.sha256(payload).hexdigest())
        with self.assertRaisesRegex(ImportError, "Unable to hash"):
            sdk.file_sha256(self.root / "missing")

    def test_platform_validation_rejects_unsupported_targets(self):
        cases = [
            ("darwin", "x86_64", 2**63 - 1, "cpython", (3, 14), False),
            ("linux", "aarch64", 2**63 - 1, "cpython", (3, 14), False),
            ("linux", "x86_64", 2**31 - 1, "cpython", (3, 14), False),
            ("linux", "x86_64", 2**63 - 1, "pypy", (3, 10), False),
            ("linux", "x86_64", 2**63 - 1, "cpython", (3, 9), False),
            ("linux", "x86_64", 2**63 - 1, "cpython", (3, 12), True),
        ]
        for target, machine, maxsize, implementation, version, threaded in cases:
            with self.subTest(target=target, machine=machine, version=version):
                fake_sys = SimpleNamespace(
                    platform=target,
                    maxsize=maxsize,
                    implementation=SimpleNamespace(name=implementation),
                    version_info=version,
                )
                with (
                    patch.object(sdk, "sys", fake_sys),
                    patch.object(sdk.platform, "machine", return_value=machine),
                    patch.object(
                        sdk.sysconfig, "get_config_var", return_value=threaded
                    ),
                ):
                    with self.assertRaises(ImportError):
                        sdk.validate_platform()

    def test_build_record_tracks_headers_and_runtime_without_absolute_paths(self):
        relative = (
            "dll/MechEyeApi.dll" if sys.platform == "win32" else "lib/libMechEyeApi.so"
        )
        runtime = self.root / relative
        runtime.parent.mkdir()
        runtime.write_bytes(runtime_bytes(sys.platform))
        headers = [
            "include/area_scan_3d_camera/Camera.h",
            "include/area_scan_3d_camera/Mapping2DToDepth.h",
            "include/Version.h",
            "include/Extra.h",
            "include/profiler/Excluded.h",
        ]
        if sys.platform == "win32":
            headers.append("lib/MechEyeApi.lib")
        for relative in headers:
            file = self.root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(relative.encode())
        output = self.root / "runtime.json"
        with patch.dict(os.environ, {"MECHEYE_SDK_ROOT": str(self.root)}):
            sdk.write_build_record(output, sys.platform)
            with self.assertRaisesRegex(ImportError, "cross-compiling"):
                sdk.write_build_record(output, "darwin")
        record = json.loads(output.read_text())
        self.assertEqual(record["schema_version"], 2)
        self.assertEqual(record["python_soabi"], sdk.sysconfig.get_config_var("SOABI"))
        self.assertEqual(record["sha256"], sdk.file_sha256(runtime))
        self.assertIn("include/Extra.h", record["build_inputs"])
        self.assertNotIn("include/profiler/Excluded.h", record["build_inputs"])
        self.assertNotIn(str(self.root), output.read_text())
        get_config_var = sdk.sysconfig.get_config_var
        with (
            patch.dict(os.environ, {"MECHEYE_SDK_ROOT": str(self.root)}),
            patch.object(
                sdk.sysconfig,
                "get_config_var",
                side_effect=lambda name: (
                    None if name == "SOABI" else get_config_var(name)
                ),
            ),
        ):
            sdk.write_build_record(output, sys.platform)
        self.assertIsNone(json.loads(output.read_text())["python_soabi"])

    def test_unknown_sdk_platform_and_runtime_target_are_rejected(self):
        with (
            patch.dict(os.environ, {"MECHEYE_SDK_ROOT": ""}),
            patch.object(sdk, "sys", SimpleNamespace(platform="darwin")),
        ):
            with self.assertRaisesRegex(ImportError, "requires Linux/Windows"):
                sdk.sdk_root()
        runtime = self.root / "runtime"
        runtime.write_bytes(runtime_bytes("linux"))
        with self.assertRaisesRegex(ImportError, "not a darwin"):
            sdk.validate_runtime(runtime, "darwin")

    def test_windows_build_record_requires_import_library_and_excludes_profiler(self):
        runtime = self.root / "dll/MechEyeApi.dll"
        runtime.parent.mkdir()
        runtime.write_bytes(runtime_bytes("win32"))
        for relative in (
            "include/area_scan_3d_camera/Camera.h",
            "include/area_scan_3d_camera/Mapping2DToDepth.h",
            "include/Version.h",
            "include/profiler/Excluded.h",
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())
        fake_sys = SimpleNamespace(
            platform="win32",
            maxsize=sys.maxsize,
            implementation=sys.implementation,
            version_info=sys.version_info,
        )
        output = self.root / "runtime.json"
        with (
            patch.object(sdk, "sys", fake_sys),
            patch.dict(os.environ, {"MECHEYE_SDK_ROOT": str(self.root)}),
        ):
            with self.assertRaisesRegex(ImportError, "MechEyeApi.lib"):
                sdk.write_build_record(output, "win32")
            self.assertFalse(output.exists())
            library = self.root / "lib/MechEyeApi.lib"
            library.parent.mkdir()
            library.write_bytes(b"import library")
            sdk.write_build_record(output, "win32")
        record = json.loads(output.read_text())
        self.assertEqual(record["platform"], "win32")
        self.assertEqual(record["runtime"], "MechEyeApi.dll")
        self.assertEqual(
            record["build_inputs"]["lib/MechEyeApi.lib"], sdk.file_sha256(library)
        )
        self.assertNotIn("include/profiler/Excluded.h", record["build_inputs"])
