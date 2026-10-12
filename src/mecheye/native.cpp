// Mech-Eye C++ SDK bindings, compiled for the current CPython and threading ABI.
#include "bindings.h"

std::recursive_mutex sdk_mutex;

std::string sdk_version() {
    return sdk_call([] { return eye::getApiVersionInfo(); });
}

NB_MODULE(_native, m) {
    m.doc() = "Regular CPython bindings for Mech-Eye area-scan cameras";
    auto error = nb::exception<NativeError>(m, "NativeError", PyExc_RuntimeError);
    nb::exception<ConnectionError>(m, "ConnectionError", error.ptr());
    nb::exception<CaptureError>(m, "CaptureError", error.ptr());
    nb::exception<ConfigurationError>(m, "ConfigurationError", error.ptr());
    nb::exception<PointCloudError>(m, "PointCloudError", error.ptr());
    m.attr("python_version") = nb::make_tuple(PY_MAJOR_VERSION, PY_MINOR_VERSION);
#if defined(NB_FREE_THREADED)
    m.attr("free_threaded") = true;
#else
    m.attr("free_threaded") = false;
#endif
    bind_sdk(m.def_submodule("sdk"));
    m.def("sdk_version", &sdk_version);
}
