# pymecheye

[![CI](https://github.com/slabpanic/pymecheye/actions/workflows/ci.yml/badge.svg)](https://github.com/slabpanic/pymecheye/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/slabpanic/pymecheye/branch/main/graph/badge.svg)](https://codecov.io/gh/slabpanic/pymecheye)

[![Documentation](https://readthedocs.org/projects/pymecheye/badge/?version=latest)](https://pymecheye.readthedocs.io/en/latest/)

[简体中文](https://github.com/slabpanic/pymecheye/blob/main/README.zh-CN.md)

High-performance Python bindings for Mech-Eye area-scan 3D cameras, built with
[nanobind](https://nanobind.readthedocs.io/) and the vendor C++ SDK.

pymecheye removes the dependency on vendor-precompiled Python SDKs: installation
compiles a thin native binding for your current CPython version and threading
ABI. It also provides convenient camera lifecycle management, NumPy capture,
metadata access, and error handling. NumPy is the only Python runtime dependency.

Install the distribution as **pymecheye** and keep importing **mecheye**:

```python
from mecheye.area_scan_3d_camera import Camera
```

The area-scan API targets source compatibility with **mecheyeapi 2.6.0**:
keep your existing `mecheye` imports and camera calls, and change the
installed distribution to `pymecheye`. Laser profiler interfaces are excluded.
Install only one distribution providing `mecheye` in each environment.

## Features

- Native C++ capture and point cloud conversion through a thin nanobind layer.
- Blocking SDK calls release Python thread state. Camera and SDK access use
  explicit locks, supporting regular and free-threaded CPython without relying
  on the GIL. SDK calls are serialized, including across camera instances.
- Independent NumPy arrays that remain valid after another capture or camera
  closure; point clouds preserve their organized pixel grid.
- Camera discovery, connections, capture variants, frame containers,
  parameters, user sets, point cloud processing and exports, events, and hand-eye
  calibration, preserving SDK status returns.
- NumPy capture and lifecycle conveniences on the same `Camera` object, including
  context management and optional-IP lazy connection. SDK methods never retry implicitly.
- Device information, camera intrinsics, depth-source 2D exposure configuration,
  and NumPy grayscale conversion.

The design targets efficient native data capture; it does not claim a measured
speedup over the vendor Python bindings. Arrays are copied into owned buffers rather
than exposing SDK frame memory.

## Requirements

| Requirement | Support |
| --- | --- |
| Platform | Linux or Windows, x86_64 |
| Python | CPython 3.10+; free-threaded CPython 3.13+ |
| Vendor SDK | Mech-Eye C++ SDK 2.6.0, installed separately |
| Linux build tools | C++17 GCC or Clang; glibc, libstdc++, libgcc, libgomp |
| Windows build tools | MSVC x64 C++17 toolchain, Windows SDK, VC++ 2015-2022 x64 Redistributable |

The extension is compiled for each Python minor version and threading ABI;
there is no single binary shared across Python versions. The nanobind
`FREE_THREADED` option is always enabled and takes effect on free-threaded
interpreters. Compatibility with future Python versions depends on nanobind,
NumPy, and compiler support. Other SDK versions, PyPy, ARM, macOS, and MinGW are
not currently supported.

## Installation

Install the vendor C++ SDK first. Build and runtime use these defaults:

| Platform | SDK root | Expected files |
| --- | --- | --- |
| Linux | `/opt/mech-mind/mech-eye-sdk/` | `include/`, `lib/libMechEyeApi.so` |
| Windows | `C:/Mech-Mind/Mech-Eye SDK-2.6.0/API/` | `include/`, `lib/MechEyeApi.lib`, `dll/MechEyeApi.dll` |

Set `MECHEYE_SDK_ROOT` to an absolute SDK directory to override the default:

```bash
# Linux
export MECHEYE_SDK_ROOT=/absolute/path/to/mech-eye-sdk
```

```powershell
# Windows PowerShell
$env:MECHEYE_SDK_ROOT = 'C:\path\to\Mech-Eye SDK\API'
```

An unset or empty variable selects the platform default. An invalid override
fails directly. Headers, link library, and runtime must come from the same SDK
installation. The runtime SHA-256 must match the one used to compile the binding.

Add it to your uv project:

```bash
uv add pymecheye
```

Or install directly from Git:

```bash
uv add git+https://github.com/slabpanic/pymecheye.git
```

uv records the dependency and resolves a Git commit in the lockfile. You can
select a released tag with `--tag` or a commit with `--rev`.

Both commands install a regular package. With source-only PyPI releases, uv
resolves the build dependencies and compiles the extension for the consuming
project's Python and local C++ SDK; Git installations also build from source.
The C++ SDK must already be installed: uv builds this binding, not the vendor SDK.
uv can reuse previously compiled wheels from its cache.
Keep any SDK environment override set for both building and running your
application. The package never copies vendor headers, import libraries, or
runtime binaries into its source archives or wheels.

For a local checkout, use a regular installation:

```bash
uv add ../pymecheye
```

Or install from inside the checkout with pip:

```bash
python -m pip install .
```

Source changes take effect after rebuilding and reinstalling. After changing SDK
files, clear the previously compiled package, rebuild, and restart Python:

```bash
uv cache clean pymecheye
uv sync --reinstall-package pymecheye
```

Inside this repository, add `--no-editable` to `uv sync` and `uv run` to keep the
project installed as a regular package. For Git and registry dependencies,
compiled wheels may be cached; clearing the package cache forces a source rebuild
when the SDK changes. Each Python minor version, threading ABI, and platform
requires its own compatible environment and build.

## API compatibility

| Module | API |
| --- | --- |
| `mecheye.area_scan_3d_camera` | Camera, metadata, frames, image/cloud containers, parameter descriptors, mapping, transformations, events, and hand-eye calibration |
| `mecheye.shared` | ErrorStatus, common data types, parameters, user sets, version and log-export utilities |
| `mecheye.area_scan_3d_camera_utils` | Print and interactive selection helpers, plus `image_to_gray()` |

SDK operations retain their signatures and return conventions. For example,
`Camera.connect()` returns `ErrorStatus`; captures fill the supplied frame and
return `ErrorStatus`; scalar parameter reads return `[status, value]`, while
structured reads return `(status, value)`. SDK error codes and descriptions pass
through unchanged. `disconnect()` returns `None`.

The compatibility target is the public Python area-scan API of version 2.6.0,
not laser profilers or SWIG implementation internals. Direct `this` pointer
access, foreign SWIG pointer interoperability, and `__swig_destroy__` are not
provided. Python manages native object lifetimes; `thisown` is a compatibility
attribute and cannot transfer ownership of native memory. Future SDK
versions may add interfaces that require further updates.

## Camera API example

Existing scripts can keep this calling pattern:

```python
from mecheye.area_scan_3d_camera import Camera, Frame3D

camera = Camera()
try:
    status = camera.connect("192.168.1.100")
    if not status.is_ok():
        raise RuntimeError(status.error_description)

    frame = Frame3D()
    status = camera.capture_3d(frame)
    if not status.is_ok():
        raise RuntimeError(status.error_description)

    points = frame.get_untextured_point_cloud().data()
finally:
    camera.disconnect()
```

Image and cloud accessors return independent NumPy copies with the
documented dtypes and layouts. XYZ values use `float32`; grayscale and BGR use
`uint8`. Textured clouds expose `vertices()` and `colors()`, with `normals()`
available on their normal-bearing variant. For compatibility, empty accessors
return `np.zeros(1)`.

Pixel objects returned by `at()` or indexing support field assignment. A pixel
reference becomes invalid after its container is resized or released, raising
`ReferenceError` instead of accessing freed memory. Camera, frame, parameter,
and pixel operations are serialized. SDK object construction and destruction
run on the dedicated worker.

For multiprocessing, prefer `multiprocessing.get_context("spawn")` and create
SDK objects inside each child process. SDK calls after a fork that inherits
`mecheye` raise `RuntimeError` before acquiring inherited locks. Such forks are
unsupported: the vendor runtime can also abort during child process shutdown. To use
`forkserver`, call `multiprocessing.set_forkserver_preload([])` before starting
the server, so it does not preload a main module that imports `mecheye`.
Exchange owned NumPy arrays between processes rather than SDK objects.

## Integrated conveniences

The `Camera` object provides NumPy capture and context management:

```python
from mecheye.area_scan_3d_camera import Camera

with Camera("192.168.1.100") as camera:
    camera.configure_depth_source_2d_exposure("flash")
    image, points_mm = camera.capture_points(timeoutMs=10000)
    device_info = camera.device_info
    camera_parameters = camera.camera_parameters

print(image.shape, image.dtype)
print(points_mm.shape, points_mm.dtype)
```

`Camera()` follows the explicit-connect SDK workflow. An optional IP connects on
context entry or first convenience capture/configuration. Importing the package
or constructing a camera does not connect. `close()` aliases `disconnect()`.

`capture_points()` composes `capture_depth_source_2d_and_3d()`, point cloud mapping,
grayscale conversion, and owned NumPy output. It returns a grayscale `uint8`
image `(h, w)` and an organized `float64` cloud `(h, w, 3)` on the same grid,
in millimeters with `NaN` invalid points. A previously selected point cloud unit
is restored on success and failure. This capture requires a camera model with
an external 2D camera, as specified by the SDK.

`device_info` and `camera_parameters` query the connected camera and return plain
Python dictionaries. Exposure configuration accepts `"timed"` or `"flash"` and
returns the mode read back from the current user set. Synchronize concurrent
writes or resizing of returned NumPy arrays in your application.

## Errors, events, and utilities

SDK methods return `ErrorStatus`. Convenience methods raise
`MechEyeConnectionError`, `MechEyeConfigurationError`, `MechEyeCaptureError`,
or `MechEyePointCloudError`, derived from `MechEyeError` and available from
`mecheye.shared` and the package root.

Override `EventCallbackBase` methods and register with `CameraEvent`, using the
camera API. Event data and payloads are copied before Python dispatch, so
callbacks can inspect them while a capture is still running. Callback exceptions
are retained and retrieved with `camera.pop_callback_errors()`; none are printed
or discarded. Callback code that calls another SDK operation waits for the
ongoing operation to finish.

No automatic Python logging is added. SDK standard-stream output on Linux is
silenced on the dedicated worker without redirecting the host process's streams.
The SDK may still create its own diagnostic files. `show_error()` and
`print_*()` helpers print only when explicitly called; interactive helpers ask
for input only when called.

```python
from mecheye.area_scan_3d_camera_utils import image_to_gray

gray = image_to_gray(bgr_image)
```

This utility accepts grayscale, BGR, and BGRA arrays and returns an independent
array, ignoring alpha. Color input supports `uint8`, `uint16`, and `float32`.

The capture example prints array shapes, dtypes, and valid point count:

```bash
uv run --no-editable python examples/capture.py 192.168.1.100
```

It connects to a camera and opens no GUI. Pillow, OpenCV, and Open3D are not Python
dependencies of this project.

## Documentation

Read the [English documentation](https://pymecheye.readthedocs.io/en/latest/) or
[简体中文文档](https://pymecheye.readthedocs.io/zh-cn/latest/) for setup,
camera workflows, and API reference pages generated from the installed binding's
docstrings. To build the same documentation locally with an installed C++ SDK:

```bash
uv sync --locked --no-editable --group docs
uv run --no-sync sphinx-build -n -W --keep-going -b html -D language=en docs docs/_build/en
uv run --no-sync sphinx-build -n -W --keep-going -b html -D language=zh_CN docs docs/_build/zh_CN
```

Open `docs/_build/en/index.html` or `docs/_build/zh_CN/index.html`. The build
checks public docstrings and treats warnings and broken cross-references as errors. Generated API pages and HTML are
ignored by Git. GitHub Actions also builds the documentation and saves an HTML
preview artifact.

The [Read the Docs configuration](.readthedocs.yaml) downloads and verifies the
external SDK, compiles the binding, and builds with the locked documentation
dependencies. To activate publishing, import `slabpanic/pymecheye` into Read the
Docs with the project slug `pymecheye`, authorize its GitHub App, and use `main`
as the default branch. Subsequent pushes trigger the hosted build automatically;
activate release-tag versions to publish stable documentation. Import the same
repository as `pymecheye-zh-cn` with Simplified Chinese selected, and add it under
the parent project's Translations settings to publish `/zh-cn/` documentation.
No Read the Docs token is needed in GitHub Actions. The hosted URL becomes available after the
project is imported and its first build succeeds. See
[docs/development.rst](docs/development.rst) for the complete setup.

## Development

```bash
uv sync --no-editable
uv lock --check
uv run --no-editable black --check src/mecheye/*.py examples/*.py tests/*.py
uv run --no-editable python -m compileall -q src/mecheye
uv run --no-editable python -c "import mecheye"
uv run --no-editable python -m unittest discover -s tests
uv pip check
uv build --sdist
```

The format, compile, import, and dependency checks do not connect to a camera.
The unit tests use native SDK data operations and simulated device responses;
no camera or network discovery is required. GitHub Actions builds the extension
on Linux with Python 3.10–3.14, 3.13t, and 3.14t, and on Windows with Python 3.10,
3.14, and 3.14t. Free-threaded tests verify that importing the binding keeps the
GIL disabled. The workflow downloads SDK 2.6.0 from the vendor, verifies pinned
SHA-256 checksums, and unpacks it outside the repository. Windows uses the runner's
WiX tools and an administrative MSI image; hardware captures are not part of CI.

To run Python branch coverage locally:

```bash
uv sync --locked --no-editable --group test
uv run --no-sync coverage run -m unittest discover -s tests
uv run --no-sync coverage report --fail-under=95
uv run --no-sync coverage xml
```

To also measure the C++ binding on Linux with GCC:

```bash
uv sync --locked --no-editable --group test --group native-coverage \
  --no-build-isolation-package pymecheye --reinstall-package pymecheye \
  -Ccmake.define.MECHEYE_ENABLE_COVERAGE=ON -Cbuild-dir=build/coverage
uv run --no-sync coverage run -m unittest discover -s tests
uv run --no-sync gcovr --root . --filter 'src/mecheye/' --merge-lines \
  --xml-pretty --output coverage-native.xml --print-summary build/coverage
```

Native coverage measures this repository's C++ code, excluding vendor binaries
and nanobind implementation code. Restore a regular build with
`uv sync --locked --no-editable --reinstall-package pymecheye` after profiling.
CI requires at least 95% Python coverage and 80% native line coverage, and retains
both XML reports as workflow artifacts. Codecov tracks Python and native reports with separate flags.

Enable this repository in [Codecov](https://app.codecov.io/gh/slabpanic/pymecheye)
and install its GitHub App to enable pull request checks and comments. Uploads
use [OIDC](https://github.com/codecov/codecov-action#using-oidc), so no
`CODECOV_TOKEN` secret is needed. Fork pull requests run all tests and generate
reports, but do not perform authenticated uploads; reports remain available in
the workflow artifacts. Uploads run for main-branch pushes, internal pull
requests, and manual workflow runs.

## Source releases

Pushing a version tag such as `v0.1.0` runs
[release.yml](https://github.com/slabpanic/pymecheye/blob/main/.github/workflows/release.yml).
The workflow requires the tag to match the normalized `project.version` in
`pyproject.toml`, validates the source archive and PyPI metadata, and runs the
complete CI workflow before uploading the `.tar.gz` to PyPI. Release tools are
installed separately, so building the source archive does not require the SDK.

To enable automatic publishing once:

1. Create a GitHub environment named `pypi` under the repository's Settings → Environments.
2. In your PyPI account's Publishing settings, add a pending GitHub Trusted Publisher
   with project name `pymecheye`, owner `slabpanic`, repository `pymecheye`, workflow
   filename `release.yml`, and environment `pypi`. For an existing PyPI project,
   add the same publisher in that project's Publishing settings.

The publisher uses OIDC; no PyPI API token is needed in GitHub secrets. See the
[PyPI Trusted Publishing guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

For each release, update `project.version`, run `uv lock`, commit the release
changes, then push the matching tag:

```bash
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

Use normalized versions for prereleases as well, for example `0.2.0rc1` with
`v0.2.0rc1`. A tag mismatch or failed build, metadata, test, coverage, or
documentation check prevents uploading. Existing tags do not trigger publication
until pushed; the version is never changed automatically by the workflow.

To build a source archive locally:

```bash
uv build --sdist --no-sources
```

Upload the resulting `dist/pymecheye-<version>.tar.gz`. Locally built wheels record
the builder's exact SDK runtime hash; they are intended for matching environments
and should not be uploaded as general-purpose PyPI releases. Publishing only the
source archive lets `uv add pymecheye` build with the recipient's installed SDK
when a compatible compiled package is not already cached. If an index also
offers wheels, consumers can explicitly request a source installation:

```bash
uv add --no-binary-package pymecheye pymecheye
```

For a persistent source-only preference, add this to the consuming project:

```toml
[tool.uv]
no-binary-package = ["pymecheye"]
```

Dependency-specific uv settings are configured by the consuming project; they
are not imposed through pymecheye's published package metadata.

## License

Project-owned code and documentation are licensed under the [MIT License](https://github.com/slabpanic/pymecheye/blob/main/LICENSE).
Third-party code retains its original terms; the distribution includes MIT and
BSD 3-Clause notices.

## Third-party notices

The independently installed Mech-Eye SDK remains subject to its vendor agreement.
Notices for nanobind, robin-map, and SDK header code compiled into the extension
are included in [THIRD_PARTY_NOTICES.md](https://github.com/slabpanic/pymecheye/blob/main/THIRD_PARTY_NOTICES.md) and
[`src/mecheye/licenses/`](https://github.com/slabpanic/pymecheye/tree/main/src/mecheye/licenses).
