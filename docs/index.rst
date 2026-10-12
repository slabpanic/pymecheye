pymecheye
=========

Python bindings for Mech-Eye area-scan 3D cameras, built with nanobind and the
Mech-Eye C++ SDK. Installation compiles the native extension for the current
CPython version and threading ABI. NumPy is the only Python runtime dependency.

Install the distribution as ``pymecheye`` and import ``mecheye``. SDK capture and
parameter operations sit alongside camera lifecycle helpers, aligned NumPy
capture, and metadata dictionaries. The API reference is generated from the
installed binding and the Python docstrings.

.. toctree::
   :maxdepth: 2

   installation
   usage
   api/index
   development

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

