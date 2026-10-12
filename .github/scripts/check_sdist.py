"""Reject local environments, build outputs, and links in a source distribution."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import tarfile


def check_sdist(archive: Path) -> None:
    """Validate archive members and the source files required for an SDK build."""
    required = {
        "pyproject.toml",
        "CMakeLists.txt",
        "cmake/MechEyeSdk.cmake",
        "src/mecheye/native.cpp",
        "src/mecheye/sdk_executor.h",
        "src/mecheye/_sdk.py",
        "src/mecheye/licenses/nanobind/LICENSE",
        "src/mecheye/licenses/robin-map/LICENSE",
        "README.md",
        "README.zh-CN.md",
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "tests/api_surface.json",
        "docs/conf.py",
        "docs/_ext/check_translations.py",
        "docs/_templates/language-switcher.html",
        "docs/locale/zh_CN/LC_MESSAGES/api.po",
        "docs/locale/zh_CN/LC_MESSAGES/development.po",
        "docs/locale/zh_CN/LC_MESSAGES/index.po",
        "docs/locale/zh_CN/LC_MESSAGES/installation.po",
        "docs/locale/zh_CN/LC_MESSAGES/usage.po",
    }
    forbidden = {".venv", "venv", "__pycache__", "build", "dist", ".git", ".uv-cache"}
    with tarfile.open(archive, "r:gz") as stream:
        members = stream.getmembers()
        roots = {PurePosixPath(member.name).parts[0] for member in members}
        if len(roots) != 1:
            raise ValueError("Source distribution must have one top-level directory")
        paths = set()
        for member in members:
            path = PurePosixPath(member.name)
            relative = PurePosixPath(*path.parts[1:])
            if (
                path.is_absolute()
                or ".." in path.parts
                or not (member.isfile() or member.isdir())
                or forbidden.intersection(relative.parts)
                or relative.is_relative_to("src/sdk")
                or relative.is_relative_to("docs/_build")
                or relative.is_relative_to("docs/api/_generated")
                or relative.suffix.lower()
                in {".so", ".dll", ".pyd", ".pyc", ".gcda", ".gcno", ".mo", ".pot"}
            ):
                raise ValueError(
                    f"Unexpected source-distribution member: {member.name}"
                )
            if member.isfile():
                paths.add(str(relative))
        missing = required - paths
        if missing:
            raise ValueError(
                f"Source distribution is missing required files: {sorted(missing)}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path)
    for archive in parser.parse_args().archives:
        check_sdist(archive)
