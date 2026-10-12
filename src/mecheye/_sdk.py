"""Validate the external SDK and record the runtime used to compile the binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import struct
import sys
import sysconfig
from pathlib import Path

_DEFAULT_SDK_ROOTS: dict[str, str] = {
    "linux": "/opt/mech-mind/mech-eye-sdk",
    "win32": "C:/Mech-Mind/Mech-Eye SDK-2.6.0/API",
}


def validate_platform() -> None:
    """Reject unsupported operating systems, CPUs, and Python implementations."""
    if (
        sys.platform not in {"linux", "win32"}
        or platform.machine().lower() not in {"x86_64", "amd64"}
        or sys.maxsize <= 2**32
    ):
        raise ImportError(
            f"MechEye supports only Linux/Windows x86_64; current platform: {sys.platform}/{platform.machine()}"
        )
    if sys.implementation.name != "cpython" or sys.version_info < (3, 10):
        raise ImportError("MechEye requires CPython 3.10 or newer")
    if sysconfig.get_config_var("Py_GIL_DISABLED") and sys.version_info < (3, 13):
        raise ImportError("MechEye requires CPython 3.13+ for free-threaded builds")


def sdk_root() -> Path:
    """Use an environment override or the current platform's fixed SDK default."""
    value = os.environ.get("MECHEYE_SDK_ROOT") or _DEFAULT_SDK_ROOTS.get(sys.platform)
    if value is None:
        raise ImportError("MechEye requires Linux/Windows x86_64")
    root = Path(value)
    if not root.is_absolute():
        raise ImportError("MECHEYE_SDK_ROOT must be an absolute SDK directory")
    try:
        root = root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ImportError(
            f"MechEye SDK directory is unavailable: {root}; set MECHEYE_SDK_ROOT to a valid SDK directory"
        ) from exc
    if not root.is_dir():
        raise ImportError(f"MECHEYE_SDK_ROOT is not a directory: {root}")
    return root


def sdk_file(root: Path, relative: str) -> Path:
    """Require a regular SDK file whose resolved path stays inside the SDK root."""
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ImportError(
            f"Required MechEye SDK file is missing or outside MECHEYE_SDK_ROOT: {path}"
        ) from exc
    if not resolved.is_file():
        raise ImportError(f"Required MechEye SDK file is not a regular file: {path}")
    return resolved


def validate_runtime(path: Path, target_platform: str) -> None:
    """Check ELF/PE headers before asking the system loader to load the runtime."""
    try:
        with path.open("rb") as stream:
            header = stream.read(64)
            if target_platform == "linux":
                valid = (
                    len(header) == 64
                    and header[:6] == b"\x7fELF\x02\x01"
                    and struct.unpack_from("<HH", header, 16) == (3, 62)
                )
            elif target_platform == "win32":
                valid = False
                if len(header) == 64 and header[:2] == b"MZ":
                    stream.seek(struct.unpack_from("<I", header, 60)[0])
                    pe = stream.read(26)
                    valid = (
                        len(pe) == 26
                        and pe[:4] == b"PE\x00\x00"
                        and struct.unpack_from("<H", pe, 4)[0] == 0x8664
                        and bool(struct.unpack_from("<H", pe, 22)[0] & 0x2000)
                        and struct.unpack_from("<H", pe, 24)[0] == 0x20B
                    )
            else:
                valid = False
    except OSError as exc:
        raise ImportError(f"Unable to read MechEye SDK runtime: {path}") from exc
    if not valid:
        raise ImportError(
            f"MechEye SDK runtime is not a {target_platform} x86_64 shared library: {path}"
        )


def runtime_path(root: Path) -> Path:
    """Select and validate the current platform's external runtime."""
    relative = (
        "dll/MechEyeApi.dll" if sys.platform == "win32" else "lib/libMechEyeApi.so"
    )
    runtime = sdk_file(root, relative)
    validate_runtime(runtime, sys.platform)
    return runtime


def file_sha256(path: Path) -> str:
    """Hash an SDK file without loading its entire contents into memory."""
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError as exc:
        raise ImportError(f"Unable to hash MechEye SDK file: {path}") from exc


def write_build_record(output: Path, target_platform: str) -> None:
    """Validate build inputs and record SDK identity without redistributing it."""
    validate_platform()
    if target_platform != sys.platform:
        raise ImportError("MechEye does not support cross-compiling its Python binding")
    root = sdk_root()
    runtime = runtime_path(root)
    required = [
        "include/area_scan_3d_camera/Camera.h",
        "include/area_scan_3d_camera/Mapping2DToDepth.h",
        "include/Version.h",
    ]
    required.extend(
        str(path.relative_to(root).as_posix())
        for path in sorted((root / "include").rglob("*.h"))
        if "profiler" not in path.parts
        and str(path.relative_to(root).as_posix()) not in required
    )
    if sys.platform == "win32":
        required.append("lib/MechEyeApi.lib")
    inputs = {name: file_sha256(sdk_file(root, name)) for name in required}
    record = {
        "schema_version": 2,
        "platform": sys.platform,
        "architecture": "x86_64",
        # Windows CPython 3.10 has no SOABI; record the same value used by the loader.
        "python_soabi": sysconfig.get_config_var("SOABI"),
        "runtime": (
            "MechEyeApi.dll" if sys.platform == "win32" else "libMechEyeApi.so"
        ),
        "sha256": file_sha256(runtime),
        "build_inputs": inputs,
    }
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--platform", required=True)
    args = parser.parse_args()
    write_build_record(args.manifest, args.platform)
