# pymecheye

[![CI](https://github.com/slabpanic/pymecheye/actions/workflows/ci.yml/badge.svg)](https://github.com/slabpanic/pymecheye/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/slabpanic/pymecheye/branch/main/graph/badge.svg)](https://codecov.io/gh/slabpanic/pymecheye)

[![文档](https://readthedocs.org/projects/pymecheye/badge/?version=latest)](https://pymecheye.readthedocs.io/zh-cn/latest/)

[English](README.md)

通过 [nanobind](https://nanobind.readthedocs.io/) 和厂商 C++ SDK 实现的高性能
Mech-Eye 面阵 3D 相机 Python 绑定。

pymecheye 不依赖厂商预编译的 Python SDK，而是在安装时为当前 CPython 版本和线程
ABI 编译轻量原生绑定，避免受厂商 Python 扩展版本限制。同时提供相机生命周期管理、
NumPy 数据采集、设备信息访问和错误处理等便利功能。Python 运行时只依赖 NumPy。

安装的发行包名是 **pymecheye**，导入包名仍为 **mecheye**：

```python
from mecheye.area_scan_3d_camera import Camera
```

面阵相机接口以 **mecheyeapi 2.6.0** 的公开 Python API 为源码兼容目标：
现有脚本保留 `mecheye` 导入和相机调用方式，安装依赖改为 `pymecheye`。
不包含激光轮廓仪接口。同一环境只安装一个提供 `mecheye` 导入包的发行包。

## 功能

- 使用轻量 nanobind 绑定在 C++ 中完成原生采集和点云转换。
- 阻塞 SDK 调用释放 Python 线程状态，相机状态和 SDK 调用使用显式锁，不依赖 GIL
  保证安全，支持常规与 free-threaded CPython；不同相机实例的 SDK 调用也会串行执行。
- 返回独立持有缓冲区的 NumPy 数组，再次采集或关闭相机不会使已有数组失效；
  点云保留与图像对应的有组织像素网格。
- 提供相机发现、连接、各种采集方式、帧容器、参数、配置集、点云处理和导出、
  事件及手眼标定接口，保留 SDK 的错误状态返回方式。
- 便利功能直接融入同一个 `Camera`，支持上下文管理和可选 IP 的延迟连接；
   SDK 方法不会隐式重试。
- 提供设备信息、相机内参、深度源 2D 曝光模式配置和 NumPy 灰度转换。

本项目面向高效原生数据采集，尚未提供与绑定对比的性能测量。
数组会复制到独立缓冲区，不直接暴露 SDK 帧内存。

## 环境要求

| 项目 | 支持范围 |
| --- | --- |
| 平台 | Linux、Windows，x86_64 |
| Python | CPython 3.10+；free-threaded CPython 3.13+ |
| 厂商 SDK | 单独安装的 Mech-Eye C++ SDK 2.6.0 |
| Linux 构建环境 | 支持 C++17 的 GCC 或 Clang；glibc、libstdc++、libgcc、libgomp |
| Windows 构建环境 | MSVC x64 C++17 工具链、Windows SDK、VC++ 2015-2022 x64 Redistributable |

扩展按 Python 次版本和线程 ABI 分别编译，并非一个二进制文件适用于所有 Python。
构建始终启用 nanobind 的 `FREE_THREADED` 选项，在 free-threaded 解释器上生效。
后续 Python 版本的兼容性取决于 nanobind、NumPy 和编译器支持。
暂不支持其他 SDK 版本、PyPy、ARM、macOS 或 MinGW。

## 安装

先安装厂商 C++ SDK。构建与运行时使用相同默认路径：

| 平台 | SDK 根目录 | 所需文件 |
| --- | --- | --- |
| Linux | `/opt/mech-mind/mech-eye-sdk/` | `include/`、`lib/libMechEyeApi.so` |
| Windows | `C:/Mech-Mind/Mech-Eye SDK-2.6.0/API/` | `include/`、`lib/MechEyeApi.lib`、`dll/MechEyeApi.dll` |

自定义安装位置通过环境变量 `MECHEYE_SDK_ROOT` 指定，必须使用绝对路径：

```bash
# Linux
export MECHEYE_SDK_ROOT=/absolute/path/to/mech-eye-sdk
```

```powershell
# Windows PowerShell
$env:MECHEYE_SDK_ROOT = 'C:\path\to\Mech-Eye SDK\API'
```

变量未设置或为空时使用当前平台默认路径；显式指定的路径无效时直接报错。
头文件、链接库和运行库必须来自同一 SDK 安装。运行库的 SHA-256 必须与编译时一致。

在使用本库的 uv 项目中执行：

```bash
uv add pymecheye
```

也可以直接从 Git 安装：

```bash
uv add git+https://github.com/slabpanic/pymecheye.git
```

uv 会记录依赖并在锁文件中固定 Git 提交。
可使用 `--tag` 指定已发布的标签，或通过 `--rev` 指定提交。

两种方式均采用普通安装。PyPI 只发布源码包时，uv 会自动解析构建依赖，
用引用项目的 Python 和本地 C++ SDK 编译扩展；Git 安装也会从源码构建。
厂商 C++ SDK 需要预先安装：uv 编译的是本项目的绑定，不是厂商 SDK 本身。
uv 可能复用此前编译的缓存 wheel。使用自定义 SDK 路径时，构建和运行应用时都应保留环境变量。
项目不会将厂商头文件、链接库或运行库复制到源码包或 wheel 中。

引用本地源码目录时，也使用普通安装：

```bash
uv add ../pymecheye
```

也可在源码目录使用 pip 安装：

```bash
python -m pip install .
```

源码修改需要重新构建、安装后才会生效。SDK 文件更新后，清理此前编译的包，
重新构建并重启 Python：

```bash
uv cache clean pymecheye
uv sync --reinstall-package pymecheye
```

在本仓库内使用 `uv sync` 和 `uv run` 时，增加 `--no-editable`，确保项目本身也采用
普通安装。Git 和 PyPI 依赖可能复用已编译的缓存 wheel，SDK 更新时清理包缓存可强制
重新从源码构建。不同 Python 次版本、线程 ABI 和平台需要各自兼容的环境与构建。

## API 兼容性

| 模块 | API |
| --- | --- |
| `mecheye.area_scan_3d_camera` | 相机、元数据、帧、图像和点云容器、参数描述符、映射、变换、事件及手眼标定 |
| `mecheye.shared` | ErrorStatus、公共数据类型、参数、配置集、版本与日志导出工具 |
| `mecheye.area_scan_3d_camera_utils` | 打印和交互式设备选择工具，以及 `image_to_gray()` |

方法保留原有签名和返回约定：`Camera.connect()` 返回 `ErrorStatus`；
采集写入调用方提供的帧并返回 `ErrorStatus`；标量参数读取返回 `[status, value]`，
结构化读取返回 `(status, value)`。SDK 错误码和说明原样传递，`disconnect()` 返回 `None`。

兼容范围是 2.6.0 的面阵公开 Python API，不包含激光轮廓仪或 SWIG 实现细节。
不提供直接 `this` 指针访问、其他 SWIG 扩展的指针互操作或 `__swig_destroy__`。
原生对象由 Python 管理生命周期；`thisown` 是兼容属性，不能转移原生内存所有权。
后续 SDK 版本新增的接口需要进一步适配。

## 接口示例

现有脚本保留以下调用方式：

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

图像和点云访问方法返回独立 NumPy 副本，保持类型和布局：XYZ 为 `float32`，
灰度和 BGR 为 `uint8`；纹理点云提供 `vertices()`、`colors()`，带法线的类型还提供
`normals()`。为保持兼容，空数据访问返回 `np.zeros(1)`。

`at()` 或索引返回的像素对象支持字段赋值。容器调整尺寸或释放后，已有像素引用会
抛出 `ReferenceError`，避免访问已释放内存。相机、帧、参数和像素操作使用显式锁；
SDK 对象的构造和销毁也在专用工作线程完成。

多进程推荐使用 `multiprocessing.get_context("spawn")`，在各子进程中创建 SDK
对象。若 fork 子进程继承了 `mecheye`，SDK 操作会在获取继承的锁之前抛出
`RuntimeError`。这类 fork 不受支持，厂商运行时在子进程退出时也可能中止进程。
使用 `forkserver` 时，应在启动服务进程之前调用
`multiprocessing.set_forkserver_preload([])`，避免服务进程预加载导入了 `mecheye`
的主模块。进程间传递独立 NumPy 数组，不传递 SDK 对象。

## 集成便利功能

NumPy 采集和上下文管理直接由 `Camera` 对象提供：

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

`Camera()` 使用显式连接流程。提供可选 IP 时，进入上下文或第一次调用便利采集、
配置方法时连接。导入包或构造相机不会连接设备，`close()` 是 `disconnect()` 的别名。

`capture_points()` 组合 `capture_depth_source_2d_and_3d()`、点云映射、灰度转换与
独立 NumPy 输出，返回 `uint8` 灰度图 `(h, w)` 和同网格上的 `float64` 有组织点云
`(h, w, 3)`。坐标单位为毫米，无效点为 `NaN`；成功或失败后均恢复调用前选定的
点云单位。SDK 要求这种采集使用带外置 2D 相机的型号。

`device_info` 与 `camera_parameters` 查询已连接相机并返回普通 Python 字典。
曝光配置接受 `"timed"` 或 `"flash"`，并返回从当前配置集读回的实际模式。
调用方需要自行同步对返回数组的并发写入和尺寸调整。

## 错误、事件与工具函数

SDK 方法返回 `ErrorStatus`。便利方法失败时抛出 `MechEyeConnectionError`、
`MechEyeConfigurationError`、`MechEyeCaptureError` 或 `MechEyePointCloudError`，
均继承 `MechEyeError`，可从 `mecheye.shared` 或包根目录导入。

继承 `EventCallbackBase` 并通过 `CameraEvent` 注册回调。
事件与负载先复制再交给 Python，采集期间回调仍能读取这些数据。
回调异常保留在 `camera.pop_callback_errors()` 中，不打印或丢弃。
回调中调用其他 SDK 操作时，会等待正在进行的 SDK 操作完成。

Python 层不添加自动日志。Linux 下在专用工作线程中关闭 SDK 标准输出，
不重定向宿主进程的输出流；厂商 SDK 仍可能生成诊断文件。
`show_error()` 与 `print_*()` 仅在调用方显式调用时打印，交互式工具也只在
显式调用时请求输入。

```python
from mecheye.area_scan_3d_camera_utils import image_to_gray

gray = image_to_gray(bgr_image)
```

该工具接受灰度、BGR 或 BGRA 数组，返回独立数组并忽略 alpha。
彩色输入支持 `uint8`、`uint16` 和 `float32`。

示例脚本只输出数组形状、类型和有效点数：

```bash
uv run --no-editable python examples/capture.py 192.168.1.100
```

该命令会连接相机，不打开 GUI。项目的 Python 依赖不包含 Pillow、OpenCV 或 Open3D。

## 文档

[中文文档](https://pymecheye.readthedocs.io/zh-cn/latest/)（[English](https://pymecheye.readthedocs.io/en/latest/)）包含安装说明、相机使用方式，
以及从实际绑定的 docstring 自动生成的 API 参考。安装 C++ SDK 后可在本地构建：

```bash
uv sync --locked --no-editable --group docs
uv run --no-sync sphinx-build -n -W --keep-going -b html -D language=zh_CN docs docs/_build/zh_CN
uv run --no-sync sphinx-build -n -W --keep-going -b html -D language=en docs docs/_build/en
```

打开 `docs/_build/zh_CN/index.html` 查看结果。构建会检查公开接口的 docstring，
并将警告和失效交叉引用视为错误。自动生成的 API 页面与 HTML 已加入 Git 忽略规则。
GitHub Actions 同样构建文档，并保存 HTML 预览产物。

[Read the Docs 配置](.readthedocs.yaml) 会下载并校验外部 SDK、编译绑定，
再使用锁定的文档依赖完成构建。首次启用需要在 Read the Docs 导入
`slabpanic/pymecheye`，将项目标识设为 `pymecheye`，授权其 GitHub App，
并使用 `main` 作为默认分支。之后推送会自动触发托管构建；激活 release tag 版本
可发布 stable 文档。中文版本需将同一仓库再次导入为 `pymecheye-zh-cn`，
语言选择简体中文，并在父项目的 Translations 设置中关联。构建会自动读取
`READTHEDOCS_LANGUAGE` 选择翻译。GitHub Actions 无需配置 Read the Docs Token。
在线地址会在项目导入且首次构建成功后可用，完整步骤见
[docs/development.rst](docs/development.rst)。

## 开发

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

格式、编译、导入和依赖检查不会连接相机。
单元测试使用原生 SDK 数据操作和模拟设备响应，无需相机或网络发现。
GitHub Actions 在 Linux 上测试 Python 3.10–3.14、3.13t、3.14t，在 Windows 上测试
Python 3.10、3.14、3.14t。free-threaded 测试检查导入绑定后 GIL 仍然禁用。
工作流从厂商下载 SDK 2.6.0，核对固定 SHA-256 后解包到仓库之外；Windows 使用
Runner 提供的 WiX 工具与 MSI 管理映像。CI 不执行真实相机采集。

本地运行 Python 分支覆盖率：

```bash
uv sync --locked --no-editable --group test
uv run --no-sync coverage run -m unittest discover -s tests
uv run --no-sync coverage report --fail-under=95
uv run --no-sync coverage xml
```

在 Linux 与 GCC 环境同时测量 C++ 绑定覆盖率：

```bash
uv sync --locked --no-editable --group test --group native-coverage \
  --no-build-isolation-package pymecheye --reinstall-package pymecheye \
  -Ccmake.define.MECHEYE_ENABLE_COVERAGE=ON -Cbuild-dir=build/coverage
uv run --no-sync coverage run -m unittest discover -s tests
uv run --no-sync gcovr --root . --filter 'src/mecheye/' --merge-lines \
  --xml-pretty --output coverage-native.xml --print-summary build/coverage
```

原生覆盖率仅统计本仓库的 C++ 代码，不包含厂商二进制或 nanobind 实现。
完成测量后使用 `uv sync --locked --no-editable --reinstall-package pymecheye` 恢复普通构建。
CI 要求 Python 覆盖率至少 95%、C++ 行覆盖率至少 80%，将两份 XML 报告保存为
工作流产物，并以独立 flag 上传到 Codecov。

在 [Codecov](https://app.codecov.io/gh/slabpanic/pymecheye) 中启用仓库并安装 GitHub App，
即可提供 PR 检查和评论。上传使用 [OIDC](https://github.com/codecov/codecov-action#using-oidc)，
无需配置 `CODECOV_TOKEN`。Fork PR 执行全部测试并生成报告，但不执行认证上传，
报告可从工作流产物下载。main 分支推送、仓库内部 PR 和手动运行会上传覆盖率。

## 源码发布

推送 `v0.1.0` 等版本 tag 会触发
[release.yml](https://github.com/slabpanic/pymecheye/blob/main/.github/workflows/release.yml)。
工作流检查 tag 与 `pyproject.toml` 中规范化的 `project.version` 是否一致，校验源码包和
PyPI 元数据，并运行完整 CI；全部通过后自动向 PyPI 上传 `.tar.gz`。发布工具单独安装，
构建源码包不需要 SDK。

首次启用需要完成以下配置：

1. 在 GitHub 仓库的 Settings → Environments 中创建名为 `pypi` 的环境。
2. 在 PyPI 账户的 Publishing 设置中添加待创建项目的 GitHub Trusted Publisher：
   项目名 `pymecheye`、所有者 `slabpanic`、仓库 `pymecheye`、workflow 文件名
   `release.yml`、环境名 `pypi`。如果 PyPI 项目已经存在，在该项目的 Publishing 设置中
   添加相同配置。

发布使用 OIDC，无需在 GitHub secrets 中配置 PyPI API Token。配置步骤见
[PyPI Trusted Publishing 文档](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)。

每次发布先更新 `project.version`，运行 `uv lock` 并提交发布改动，再推送匹配的 tag：

```bash
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

预发布版本也使用规范形式，例如 `0.2.0rc1` 对应 `v0.2.0rc1`。版本不匹配，或构建、元数据、
测试、覆盖率、文档检查失败时，不会上传。仅在本地创建 tag 不会触发发布；工作流不会自动
修改版本号。

本地构建源码包：

```bash
uv build --sdist --no-sources
```

上传生成的 `dist/pymecheye-<version>.tar.gz`。本地构建的 wheel 会记录构建机器上
SDK 运行库的精确哈希，适用于 SDK 匹配的环境，不应作为通用 PyPI 二进制发行包上传。
只发布源码包且没有可复用的已编译缓存时，`uv add pymecheye` 会使用安装者本机的 SDK
自动编译。如果索引中也提供了 wheel，使用者可以显式选择从源码安装：

```bash
uv add --no-binary-package pymecheye pymecheye
```

也可以在引用项目中持久配置：

```toml
[tool.uv]
no-binary-package = ["pymecheye"]
```

这些 uv 安装策略由引用项目配置，不会通过 pymecheye 的发行元数据强制传递给下游。

## 许可证

本项目自有代码与文档采用 [MIT 许可证](LICENSE)。
第三方代码保留原有条款，发行包包含 MIT 与 BSD 3-Clause 许可说明。

## 第三方说明

单独安装的 Mech-Eye SDK 受厂商协议约束。
编入扩展的 nanobind、robin-map 和 SDK 头文件代码的许可说明保留在
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与
[`src/mecheye/licenses/`](src/mecheye/licenses/) 中。
