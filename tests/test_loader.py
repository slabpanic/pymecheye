"""Validate runtime metadata failures before invoking the system library loader."""

import importlib.machinery
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import sysconfig
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import mecheye


class RuntimeLoaderTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.extension = self.root / (
            "_native" + sysconfig.get_config_var("EXT_SUFFIX")
        )
        self.extension.touch()
        self.runtime = self.root / (
            "MechEyeApi.dll" if sys.platform == "win32" else "libMechEyeApi.so"
        )
        self.runtime.touch()
        self.manifest = self.root / "_runtime/runtime.json"
        self.manifest.parent.mkdir()
        self.record = {
            "schema_version": 2,
            "platform": sys.platform,
            "architecture": "x86_64",
            "python_soabi": sysconfig.get_config_var("SOABI"),
            "runtime": self.runtime.name,
            "sha256": "expected-digest",
        }
        self.manifest.write_text(json.dumps(self.record))
        spec = importlib.machinery.ModuleSpec(
            "mecheye._native", loader=None, origin=str(self.extension)
        )
        patches = [
            patch.object(mecheye.importlib.util, "find_spec", return_value=spec),
            patch.object(mecheye, "validate_platform"),
            patch.object(mecheye, "sdk_root", return_value=self.root),
            patch.object(mecheye, "runtime_path", return_value=self.runtime),
            patch.object(mecheye, "file_sha256", return_value="expected-digest"),
            patch.object(mecheye, "_MECHEYE_RUNTIME_PATH", None),
            patch.object(mecheye, "_MECHEYE_RUNTIME_HANDLE", None),
            patch.object(mecheye, "_MECHEYE_DLL_DIRECTORY_HANDLE", None),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def test_missing_extension_and_wrong_suffix_are_rejected(self):
        with patch.object(mecheye.importlib.util, "find_spec", return_value=None):
            with self.assertRaisesRegex(ImportError, "not built"):
                mecheye._load_native_sdk()
        self.extension.unlink()
        with self.assertRaisesRegex(ImportError, "extension is missing"):
            mecheye._load_native_sdk()
        other = self.root / "_native.invalid"
        other.touch()
        spec = importlib.machinery.ModuleSpec(
            "mecheye._native", loader=None, origin=str(other)
        )
        with patch.object(mecheye.importlib.util, "find_spec", return_value=spec):
            with self.assertRaisesRegex(ImportError, "ABI mismatch"):
                mecheye._load_native_sdk()

    def test_manifest_missing_corrupted_or_incomplete_is_rejected(self):
        for content in ("invalid json", "{}", "null"):
            with self.subTest(content=content):
                self.manifest.write_text(content)
                with self.assertRaisesRegex(ImportError, "missing or corrupted"):
                    mecheye._load_native_sdk()
        self.manifest.unlink()
        with self.assertRaisesRegex(ImportError, "missing or corrupted"):
            mecheye._load_native_sdk()

    def test_each_platform_and_abi_field_must_match(self):
        for field in (
            "schema_version",
            "platform",
            "architecture",
            "python_soabi",
            "runtime",
        ):
            with self.subTest(field=field):
                record = dict(self.record, **{field: "mismatch"})
                self.manifest.write_text(json.dumps(record))
                with self.assertRaisesRegex(ImportError, "does not match"):
                    mecheye._load_native_sdk()

    def test_missing_sysconfig_soabi_is_supported_without_relaxing_extension_checks(
        self,
    ):
        get_config_var = mecheye.sysconfig.get_config_var
        record = dict(self.record, python_soabi=None)
        self.manifest.write_text(json.dumps(record))
        loader = "WinDLL" if sys.platform == "win32" else "CDLL"
        with (
            patch.object(
                mecheye.sysconfig,
                "get_config_var",
                side_effect=lambda name: (
                    None if name == "SOABI" else get_config_var(name)
                ),
            ),
            patch.object(mecheye.ctypes, loader) as load,
            patch.object(mecheye.os, "add_dll_directory", create=True),
        ):
            mecheye._load_native_sdk()
            load.assert_called_once()

    def test_runtime_checksum_mismatch_is_rejected(self):
        with patch.object(mecheye, "file_sha256", return_value="different-digest"):
            with self.assertRaisesRegex(ImportError, "SHA-256 does not match"):
                mecheye._load_native_sdk()

    def test_same_runtime_is_reused_and_switching_runtime_is_rejected(self):
        with patch.object(mecheye, "_MECHEYE_RUNTIME_PATH", self.runtime):
            mecheye._load_native_sdk()
        with patch.object(mecheye, "_MECHEYE_RUNTIME_HANDLE", object()):
            with self.assertRaisesRegex(ImportError, "different SDK runtime"):
                mecheye._load_native_sdk()

    def test_library_load_failure_closes_windows_search_handle(self):
        directory_handle = Mock()
        loader = "WinDLL" if sys.platform == "win32" else "CDLL"
        with (
            patch.object(
                mecheye.os,
                "add_dll_directory",
                return_value=directory_handle,
                create=True,
            ),
            patch.object(
                mecheye.ctypes, loader, side_effect=OSError("missing dependency")
            ),
        ):
            with self.assertRaisesRegex(ImportError, "missing dependency"):
                mecheye._load_native_sdk()
        if sys.platform == "win32":
            directory_handle.close.assert_called_once_with()
        else:
            directory_handle.close.assert_not_called()

    def test_concurrent_loads_keep_one_runtime_and_search_directory_alive(self):
        directory_handle = Mock()
        runtime_handle = object()
        loader = "WinDLL" if sys.platform == "win32" else "CDLL"
        with (
            patch.object(
                mecheye.os,
                "add_dll_directory",
                return_value=directory_handle,
                create=True,
            ) as add_directory,
            patch.object(mecheye.ctypes, loader, return_value=runtime_handle) as load,
            ThreadPoolExecutor(max_workers=8) as executor,
        ):
            list(executor.map(lambda _: mecheye._load_native_sdk(), range(20)))
            load.assert_called_once()
            self.assertIs(mecheye._MECHEYE_RUNTIME_HANDLE, runtime_handle)
            self.assertEqual(mecheye._MECHEYE_RUNTIME_PATH, self.runtime)
        if sys.platform == "win32":
            add_directory.assert_called_once_with(str(self.runtime.parent))
            self.assertIs(mecheye._MECHEYE_DLL_DIRECTORY_HANDLE, directory_handle)
        else:
            add_directory.assert_not_called()
        directory_handle.close.assert_not_called()

    def test_windows_loader_retains_directory_and_cleans_it_up_on_failure(self):
        record = dict(self.record, platform="win32", runtime="MechEyeApi.dll")
        self.manifest.write_text(json.dumps(record))
        directory, handle = Mock(), object()
        with (
            patch.object(mecheye, "sys", SimpleNamespace(platform="win32")),
            patch.object(
                mecheye.os, "add_dll_directory", return_value=directory, create=True
            ) as search,
            patch.object(
                mecheye.ctypes, "WinDLL", return_value=handle, create=True
            ) as loader,
        ):
            mecheye._load_native_sdk()
            search.assert_called_once_with(str(self.runtime.parent))
            loader.assert_called_once_with(str(self.runtime))
            self.assertIs(mecheye._MECHEYE_RUNTIME_HANDLE, handle)
            self.assertIs(mecheye._MECHEYE_DLL_DIRECTORY_HANDLE, directory)
            mecheye._load_native_sdk()
            loader.assert_called_once()
            directory.close.assert_not_called()
        with (
            patch.object(mecheye, "_MECHEYE_RUNTIME_PATH", None),
            patch.object(mecheye, "_MECHEYE_RUNTIME_HANDLE", None),
            patch.object(mecheye, "_MECHEYE_DLL_DIRECTORY_HANDLE", None),
            patch.object(mecheye, "sys", SimpleNamespace(platform="win32")),
            patch.object(
                mecheye.os, "add_dll_directory", return_value=directory, create=True
            ),
            patch.object(
                mecheye.ctypes,
                "WinDLL",
                side_effect=OSError("dependency unavailable"),
                create=True,
            ),
        ):
            with self.assertRaisesRegex(ImportError, "dependency unavailable"):
                mecheye._load_native_sdk()
            directory.close.assert_called_once_with()
            self.assertIsNone(mecheye._MECHEYE_RUNTIME_HANDLE)
            self.assertIsNone(mecheye._MECHEYE_DLL_DIRECTORY_HANDLE)

    def test_missing_spec_origin_or_extension_suffix_rejects_binding(self):
        with patch.object(
            mecheye.importlib.util,
            "find_spec",
            return_value=SimpleNamespace(origin=None),
        ):
            with self.assertRaisesRegex(ImportError, "not built"):
                mecheye._load_native_sdk()
        get_config_var = mecheye.sysconfig.get_config_var
        with patch.object(
            mecheye.sysconfig,
            "get_config_var",
            side_effect=lambda name: (
                None if name == "EXT_SUFFIX" else get_config_var(name)
            ),
        ):
            with self.assertRaisesRegex(ImportError, "ABI mismatch"):
                mecheye._load_native_sdk()
