"""Validate and load the Mech-Eye C++ SDK binding built for the current CPython ABI."""

from __future__ import annotations

import ctypes
import importlib.util
import json
import os
import sys
import sysconfig
import threading
from pathlib import Path
from typing import Any

from ._sdk import file_sha256, runtime_path, sdk_root, validate_platform

_MECHEYE_RUNTIME_HANDLE: Any | None = None
_MECHEYE_DLL_DIRECTORY_HANDLE: Any | None = None
_MECHEYE_RUNTIME_PATH: Path | None = None
_MECHEYE_LOAD_LOCK = threading.Lock()


def _load_native_sdk() -> None:
    """Preload the external runtime matching the binding's recorded build inputs."""
    global _MECHEYE_RUNTIME_HANDLE, _MECHEYE_DLL_DIRECTORY_HANDLE, _MECHEYE_RUNTIME_PATH
    validate_platform()

    spec = importlib.util.find_spec(f"{__name__}._native")
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    if spec is None or spec.origin is None:
        raise ImportError(
            "MechEye native binding is not built; run uv sync in the consuming project"
        )
    extension = Path(spec.origin)
    if not extension.is_file():
        raise ImportError(
            f"MechEye compiled extension is missing: {extension}; reinstall the local dependency"
        )
    if not suffix or extension.name != f"_native{suffix}":
        raise ImportError(
            "MechEye extension ABI mismatch; reinstall this local dependency with the current interpreter"
        )
    runtime_dir = extension.parent / "_runtime"
    manifest_path = runtime_dir / "runtime.json"
    runtime = runtime_path(sdk_root())
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        runtime_name = (
            "MechEyeApi.dll" if sys.platform == "win32" else "libMechEyeApi.so"
        )
        if (
            manifest["schema_version"] != 2
            or manifest["platform"] != sys.platform
            or manifest["architecture"] != "x86_64"
            or manifest["python_soabi"] != sysconfig.get_config_var("SOABI")
            or manifest["runtime"] != runtime_name
        ):
            raise ImportError(
                "MechEye build metadata does not match the current platform or Python ABI"
            )
        digest = file_sha256(runtime)
        if digest != manifest["sha256"]:
            raise ImportError(
                "MechEye external SDK runtime SHA-256 does not match the build record; run uv cache clean pymecheye, then uv sync --reinstall-package pymecheye, and restart Python"
            )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ImportError(
            f"MechEye build record is missing or corrupted: {manifest_path}"
        ) from exc

    with _MECHEYE_LOAD_LOCK:
        if _MECHEYE_RUNTIME_PATH == runtime:
            return
        if _MECHEYE_RUNTIME_HANDLE is not None:
            raise ImportError(
                "MechEye has already loaded a different SDK runtime; restart the process"
            )
        dll_directory: Any | None = None
        try:
            if sys.platform == "win32":
                dll_directory = os.add_dll_directory(str(runtime.parent))
                handle = ctypes.WinDLL(str(runtime))
            else:
                handle = ctypes.CDLL(str(runtime), mode=ctypes.RTLD_GLOBAL)
        except OSError as exc:
            if dll_directory is not None:
                dll_directory.close()
            raise ImportError(
                f"Failed to load the MechEye C++ SDK runtime {runtime}: {exc}"
            ) from exc
        _MECHEYE_RUNTIME_HANDLE = handle
        _MECHEYE_DLL_DIRECTORY_HANDLE = dll_directory
        _MECHEYE_RUNTIME_PATH = runtime


_load_native_sdk()

from . import _native  # noqa: E402

if tuple(_native.python_version) != sys.version_info[:2]:
    raise ImportError(
        "MechEye native binding CPython minor version mismatch; rerun uv sync --reinstall-package pymecheye"
    )
if bool(_native.free_threaded) != bool(sysconfig.get_config_var("Py_GIL_DISABLED")):
    raise ImportError(
        "MechEye native binding threading ABI mismatch; reinstall the local dependency with the current interpreter"
    )

from .area_scan_3d_camera import Camera  # noqa: E402
from .area_scan_3d_camera_utils import image_to_gray  # noqa: E402
from .shared import (  # noqa: E402
    MechEyeCaptureError,
    MechEyeConfigurationError,
    MechEyeConnectionError,
    MechEyeError,
    MechEyePointCloudError,
)

__all__ = [
    "Camera",
    "MechEyeCaptureError",
    "MechEyeConfigurationError",
    "MechEyeConnectionError",
    "MechEyeError",
    "MechEyePointCloudError",
    "image_to_gray",
]
