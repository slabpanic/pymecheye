"""Capture one Mech-Eye grayscale image and organized point cloud, then print a data summary."""

from __future__ import annotations

import argparse
import ipaddress
import sys

import numpy as np

from mecheye.area_scan_3d_camera import Camera
from mecheye.shared import MechEyeError


def camera_ip(value: str) -> str:
    """Validate and return the camera IPv4 address."""
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid IP address: {value}") from exc
    if address.version != 4:
        raise argparse.ArgumentTypeError("The camera address must be an IPv4 address")
    return str(address)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Capture one frame from the Mech-Eye camera at the given IP and print an array summary",
    )
    parser.add_argument("ip", type=camera_ip, help="Camera IPv4 address")
    return parser.parse_args()


def main() -> int:
    """Connect, capture one frame, and print array shapes, dtypes, and the valid point count."""
    args = parse_args()
    try:
        with Camera(args.ip) as camera:
            gray, points_mm = camera.capture_points()
        valid_count = int(np.count_nonzero(np.isfinite(points_mm).all(axis=2)))
        print(
            f"Capture complete: grayscale image shape={gray.shape}, dtype={gray.dtype}; "
            f"point cloud shape={points_mm.shape}, dtype={points_mm.dtype}, "
            f"valid points={valid_count}, unit=mm."
        )
    except (MechEyeError, ValueError) as exc:
        print(f"Capture failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
