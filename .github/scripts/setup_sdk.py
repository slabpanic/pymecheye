"""Download and unpack the pinned external C++ SDK on GitHub-hosted runners."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

# Source: https://downloads.mech-mind.com/?tab=tab-sdk (SDK 2.6.0).
ARCHIVES = {
    "linux": (
        "https://CDN-OBJ.azureedge.net/community/community_downloads/community_downloads/"
        "Mech-Eye_API_2.6.0_amd64.zip?se=4764-05-14T12%3A35%3A05Z&sp=r&sv=2023-11-03"
        "&sr=b&sig=NUoccE1KG13iE5hARFTT5AAsScwfb4BPlNGQDYki17I%3D",
        "75b6e21521c4f2b75897d19449d74ac53c983b9fcaecc3dbe471da7e5a9246e0",
        ".deb",
    ),
    "win32": (
        "https://CDN-OBJ.azureedge.net/community/community_downloads/community_downloads/"
        "Mech-Eye%20SDK%20Installer%202.6.0.zip?se=4764-05-14T12%3A35%3A41Z&sp=r"
        "&sv=2023-11-03&sr=b&sig=IeeM20pY/M293KewR/BoP0AXayqKnQhzqrjfvzOjTcI%3D",
        "fc510202fdfae5110a201759f25ee893a8fdf77eb33eda1fcc770c4191870ebf",
        ".exe",
    ),
}


def download(url: str, path: Path) -> None:
    for attempt in range(3):
        try:
            with (
                urllib.request.urlopen(url, timeout=60) as response,
                path.open("wb") as output,
            ):
                shutil.copyfileobj(response, output)
            return
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2)


def unpack_windows(installer: Path, destination: Path) -> None:
    # WiX 3 is included in the windows-2022 image. Extract the bundle, then create
    # an administrative MSI image without installing drivers or the viewer.
    candidates = sorted(
        Path(os.environ["ProgramFiles(x86)"]).glob("WiX Toolset*/bin/dark.exe")
    )
    if not candidates:
        raise RuntimeError("WiX 3 dark.exe is required to extract the SDK bundle")
    payload = destination / "bundle"
    subprocess.run(
        [
            str(candidates[-1]),
            "-nologo",
            "-x",
            str(payload),
            str(installer),
            str(destination / "bundle.wxs"),
        ],
        check=True,
    )
    packages = [
        p
        for p in payload.rglob("config")
        if p.is_file() and p.read_bytes()[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    ]
    if len(packages) != 1:
        raise RuntimeError("Expected one SDK MSI in the extracted bundle")
    package = packages[0].with_name("SDK.msi")
    shutil.copy2(packages[0], package)
    subprocess.run(
        [
            "msiexec.exe",
            "/a",
            str(package),
            "/qn",
            f"TARGETDIR={destination / 'payload'}",
            f"INSTALLDIRVARIABLE={destination / 'payload'}",
            "/L*v",
            str(destination / "msi.log"),
        ],
        check=True,
    )


def setup(destination: Path, archive: Path | None = None) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    url, expected, suffix = ARCHIVES[sys.platform]
    if archive is None:
        archive = destination / "sdk.zip"
        download(url, archive)
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise RuntimeError("SDK archive SHA-256 mismatch")
    with zipfile.ZipFile(archive) as package:
        members = [name for name in package.namelist() if name.endswith(suffix)]
        if len(members) != 1:
            raise RuntimeError("Expected one SDK installer in the archive")
        installer = Path(package.extract(members[0], destination))
    if sys.platform == "linux":
        subprocess.run(
            ["dpkg-deb", "--extract", str(installer), str(destination / "payload")],
            check=True,
        )
        root = destination / "payload/opt/mech-mind/mech-eye-sdk"
    else:
        unpack_windows(installer, destination)
        roots = [
            p.parents[2]
            for p in (destination / "payload").rglob("Camera.h")
            if p.parent.name == "area_scan_3d_camera"
        ]
        if len(roots) != 1:
            raise RuntimeError("Expected one SDK API directory in the MSI image")
        root = roots[0]
    required = ["include/area_scan_3d_camera/Camera.h", "include/Version.h"]
    required += (
        ["lib/libMechEyeApi.so"]
        if sys.platform == "linux"
        else ["dll/MechEyeApi.dll", "lib/MechEyeApi.lib"]
    )
    for relative in required:
        if not (root / relative).is_file():
            raise RuntimeError(f"SDK extraction is missing {relative}")
    return root.resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    root = setup(args.destination.resolve(), args.archive)
    if env_file := os.environ.get("GITHUB_ENV"):
        with Path(env_file).open("a", encoding="utf-8") as output:
            output.write(f"MECHEYE_SDK_ROOT={root}\n")
    print(f"MECHEYE_SDK_ROOT={root}")
