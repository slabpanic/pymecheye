Installation
============

Requirements
------------

* Linux or Windows on x86_64.
* CPython 3.10 or newer; free-threaded CPython 3.13 or newer is supported.
* The separately installed Mech-Eye C++ SDK 2.6.0.
* A C++17 toolchain: GCC/Clang on Linux, or MSVC x64 on Windows.

The SDK is available from the `Mech-Mind download center
<https://downloads.mech-mind.com/?tab=tab-sdk>`_. SDK files are not included in
the Python distribution. The Python extension uses the regular CPython ABI,
so it is rebuilt for each Python minor version and threading ABI.

Select the SDK
--------------

``MECHEYE_SDK_ROOT`` overrides the platform default. It must be an absolute
directory containing ``include`` and the runtime/import library directories.

.. list-table::
   :header-rows: 1

   * - Platform
     - Default SDK root
     - Runtime
   * - Linux
     - ``/opt/mech-mind/mech-eye-sdk``
     - ``lib/libMechEyeApi.so``
   * - Windows
     - ``C:/Mech-Mind/Mech-Eye SDK-2.6.0/API``
     - ``dll/MechEyeApi.dll`` and ``lib/MechEyeApi.lib``

For example, on Linux:

.. code-block:: bash

   export MECHEYE_SDK_ROOT=/absolute/path/to/mech-eye-sdk
   uv add --no-binary-package pymecheye pymecheye

Or with pip:

.. code-block:: bash

   python -m pip install --no-binary=pymecheye pymecheye

Before a public source release is available, install from a local checkout:

.. code-block:: bash

   uv add /absolute/path/to/pymecheye

On Windows, set the variable in PowerShell before installing:

.. code-block:: powershell

   $env:MECHEYE_SDK_ROOT = "C:/Mech-Mind/Mech-Eye SDK-2.6.0/API"
   uv add --no-binary-package pymecheye pymecheye

Runtime validation
------------------

Importing the package checks the platform, Python ABI, and exact SDK runtime
SHA-256 recorded at compilation. A different runtime is rejected with
``ImportError``. After changing the SDK, rebuild and restart the interpreter:

.. code-block:: bash

   uv cache clean pymecheye
   uv sync --reinstall-package pymecheye

Importing the package and constructing a camera do not connect to a device.

