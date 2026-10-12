"""NumPy utilities for area-scan camera images."""

from __future__ import annotations

import numpy as np

from .area_scan_3d_camera import *
from .shared import *

__all__ = ["image_to_gray"]


def image_to_gray(image_data: np.ndarray) -> np.ndarray:
    """Copy a grayscale/BGR/BGRA image into an independent grayscale array, ignoring alpha.

    uint8 and uint16 use 15-bit integer BT.601 coefficients; float32 uses floating-point coefficients.
    The caller owns the input and must prevent concurrent writes or resizing during this call.
    """
    image = np.array(image_data, copy=True, order="C")
    if image.ndim == 2:
        return image
    if image.ndim != 3 or image.shape[2] not in {3, 4}:
        raise ValueError(f"Unsupported image data shape: {image.shape}")
    if image.dtype in {np.dtype("uint8"), np.dtype("uint16")}:
        bgr = image[..., :3].astype(np.uint32)
        weighted = bgr @ np.array([3735, 19235, 9798], dtype=np.uint32)
        return ((weighted + 16384) >> 15).astype(image.dtype)
    if image.dtype == np.dtype("float32"):
        return image[..., :3] @ np.array([0.114, 0.587, 0.299], dtype=np.float32)
    raise TypeError("Color images must be uint8, uint16, or float32 arrays")


def print_camera_info(camera_info):
    """Print information explicitly requested by the caller."""
    from .shared import ip_assignment_method_to_string

    fields = {
        "Model": camera_info.model,
        "Device name": camera_info.device_name,
        "Serial number": camera_info.serial_number,
        "IP address": camera_info.ip_address,
        "Subnet mask": camera_info.subnet_mask,
        "IP address assignment method": ip_assignment_method_to_string(
            camera_info.ip_assignment_method
        ),
        "Hardware version": "V" + camera_info.hardware_version.to_string(),
        "Firmware version": "V" + camera_info.firmware_version.to_string(),
        "Support status": "Supported" if camera_info.supported else "Unsupported",
    }
    if not camera_info.last_supported_version.is_empty():
        fields["Last supported version"] = (
            "V" + camera_info.last_supported_version.to_string()
        )
    for label, value in fields.items():
        print(f"{label}: {value}")


def print_camera_status(camera_status):
    """Explicitly print CPU and projector temperatures in degrees Celsius."""
    print(f"CPU: {camera_status.temperature.cpu_temperature:.1f} °C")
    print(f"Projector: {camera_status.temperature.projector_temperature:.1f} °C")


def print_camera_resolution(camera_resolution):
    """Explicitly print texture and depth image dimensions in pixels."""
    for name in ("texture", "depth"):
        size = getattr(camera_resolution, name)
        print(f"{name}: width={size.width}, height={size.height}")


def print_camera_matrix(title, camera_matrix):
    """Explicitly print title and the 3-by-3 intrinsic camera matrix."""
    print(f"{title}:")
    for row in (
        [camera_matrix.fx, 0, camera_matrix.cx],
        [0, camera_matrix.fy, camera_matrix.cy],
        [0, 0, 1],
    ):
        print(f"    {row}")


def print_camera_dist_coeffs(title, dist_coeffs):
    """Explicitly print title and k1, k2, p1, p2, k3 distortion coefficients."""
    print(
        f"{title}: "
        + ", ".join(
            f"{key}: {getattr(dist_coeffs, key)}"
            for key in ("k1", "k2", "p1", "p2", "k3")
        )
    )


def print_transform(title, transformation):
    """Explicitly print title, rotation matrix, and translation in millimeters."""
    print(f"{title} rotation:")
    for row in transformation.rotation:
        print(f"    {list(row)}")
    print(f"Translation (mm): {list(transformation.translation)}")


def print_camera_intrinsics(intrinsics):
    """Explicitly print both camera calibrations and their depth-to-texture transform."""
    for name in ("texture", "depth"):
        camera = getattr(intrinsics, name)
        print_camera_matrix(f"{name} camera matrix", camera.camera_matrix)
        print_camera_dist_coeffs(
            f"{name} distortion coefficients", camera.camera_distortion
        )
    print_transform("Depth to texture", intrinsics.depth_to_texture)


def _available_cameras():
    from .area_scan_3d_camera import Camera

    infos = Camera.discover_cameras()
    for index, info in enumerate(infos):
        print(f"Camera index: {index}")
        print_camera_info(info)
    return infos


def find_and_connect(camera):
    """Interactively select a discovered camera; return whether connection succeeded."""
    from .shared import show_error

    infos = _available_cameras()
    if not infos:
        return False
    while True:
        index = input("Camera index: ")
        if index.isdigit() and int(index) < len(infos):
            status = camera.connect(infos[int(index)])
            show_error(status)
            return status.is_ok()


def find_and_connect_multi_camera():
    """Interactively select cameras, ending with c; return connected Camera objects."""
    from .area_scan_3d_camera import Camera
    from .shared import show_error

    infos = _available_cameras()
    if not infos:
        return []
    indices = set()
    while True:
        index = input("Camera index (c to finish): ")
        if index == "c":
            break
        if index.isdigit() and int(index) < len(infos):
            indices.add(int(index))
    cameras = []
    for index in sorted(indices):
        camera = Camera()
        status = camera.connect(infos[index])
        if status.is_ok():
            cameras.append(camera)
        else:
            show_error(status)
    return cameras


def confirm_capture_3d():
    """Ask whether 3D capture should proceed; return a boolean."""
    while True:
        answer = input("Capture 3D data? (y/n): ")
        if answer.lower() in {"y", "n"}:
            return answer.lower() == "y"


__all__ = [
    "image_to_gray",
    "print_camera_info",
    "print_camera_status",
    "print_camera_resolution",
    "print_camera_matrix",
    "print_camera_dist_coeffs",
    "print_transform",
    "print_camera_intrinsics",
    "find_and_connect",
    "find_and_connect_multi_camera",
    "confirm_capture_3d",
]

from .area_scan_3d_camera import __all__ as _camera_exports
from .shared import __all__ as _shared_exports

__all__ = list(dict.fromkeys(__all__ + _camera_exports + _shared_exports))
