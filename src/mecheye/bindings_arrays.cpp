#include "bindings.h"
#include <cstring>

template <typename Array, typename Element> auto bind_array(nb::module_ &m, const char *name) {
    return nb::class_<Array>(m, name)
        .def(nb::init<>())
        .def("width", &Array::width)
        .def("height", &Array::height)
        .def("is_empty", &Array::isEmpty)
        .def("release", &Array::release)
        .def("resize",
             [](Array &a, size_t width, size_t height) {
                 if (height &&
                     width > std::numeric_limits<size_t>::max() / height / sizeof(Element))
                     throw nb::value_error("Array dimensions overflow the native buffer size");
                 a.resize(width, height);
             })
        .def("clone", [](const Array &a) { return a.isEmpty() ? Array{} : a.clone(); })
        .def("element", [](const Array &a, size_t index) { return Element(a[index]); })
        .def("set_element", [](Array &a, size_t index, const Element &value) { a[index] = value; });
}

template <typename Array, typename Scalar> auto array_data(const Array &array, size_t channels) {
    const size_t count = array.width() * array.height();
    std::vector<Scalar> values(count * channels);
    if (count)
        std::memcpy(values.data(), array.data(), values.size() * sizeof(Scalar));
    if (channels == 1)
        return owned_array(std::move(values), {array.height(), array.width()});
    return owned_array(std::move(values), {array.height(), array.width(), channels});
}

template <typename Array, bool Normals> void textured_arrays(nb::class_<Array> &cls) {
    cls.def("vertices",
            [](const Array &a) {
                std::vector<float> v(a.width() * a.height() * 3);
                for (size_t i = 0; i < a.width() * a.height(); ++i) {
                    const auto &p = [&]() -> const eye::PointXYZBGR & {
                        if constexpr (Normals)
                            return a[i].colorPoint;
                        else
                            return a[i];
                    }();
                    v[3 * i] = p.x;
                    v[3 * i + 1] = p.y;
                    v[3 * i + 2] = p.z;
                }
                return owned_array(std::move(v), {a.height(), a.width(), 3});
            })
        .def("colors", [](const Array &a) {
            std::vector<uint8_t> v(a.width() * a.height() * 3);
            for (size_t i = 0; i < a.width() * a.height(); ++i) {
                const auto &p = [&]() -> const eye::PointXYZBGR & {
                    if constexpr (Normals)
                        return a[i].colorPoint;
                    else
                        return a[i];
                }();
                v[3 * i] = p.b;
                v[3 * i + 1] = p.g;
                v[3 * i + 2] = p.r;
            }
            return owned_array(std::move(v), {a.height(), a.width(), 3});
        });
    if constexpr (Normals)
        cls.def("normals", [](const Array &a) {
            std::vector<float> v(a.width() * a.height() * 4);
            for (size_t i = 0; i < a.width() * a.height(); ++i) {
                v[4 * i] = a[i].normal.x;
                v[4 * i + 1] = a[i].normal.y;
                v[4 * i + 2] = a[i].normal.z;
                v[4 * i + 3] = a[i].normal.curvature;
            }
            return owned_array(std::move(v), {a.height(), a.width(), 4});
        });
}

void bind_arrays(nb::module_ &m) {
    bind_array<eye::GrayScale2DImage, eye::Gray>(m, "GrayScale2DImage")
        .def("fill_gray",
             [](eye::GrayScale2DImage &a, uint8_t value) {
                 sdk_call([&] {
                     for (size_t i = 0; i < a.width() * a.height(); ++i)
                         a[i].gray = value;
                 });
             })
        .def("data", [](const eye::GrayScale2DImage &a) {
            return array_data<eye::GrayScale2DImage, uint8_t>(a, 1);
        });
    bind_array<eye::Color2DImage, eye::ColorBGR>(m, "Color2DImage")
        .def("data", [](const eye::Color2DImage &a) {
            return array_data<eye::Color2DImage, uint8_t>(a, 3);
        });
    bind_array<eye::DepthMap, eye::PointZ>(m, "DepthMap").def("data", [](const eye::DepthMap &a) {
        return array_data<eye::DepthMap, float>(a, 1);
    });
    bind_array<eye::UntexturedPointCloud, eye::PointXYZ>(m, "UntexturedPointCloud")
        .def("normalized_points",
             [](const eye::UntexturedPointCloud &a) {
                 auto values = sdk_call([&] {
                     std::vector<double> result(a.width() * a.height() * 3);
                     for (size_t i = 0; i < a.width() * a.height(); ++i) {
                         const auto &p = a[i];
                         const bool valid = !(p.x == 0 && p.y == 0 && p.z == 0);
                         result[3 * i] = valid && std::isfinite(p.x)
                                             ? p.x
                                             : std::numeric_limits<double>::quiet_NaN();
                         result[3 * i + 1] = valid && std::isfinite(p.y)
                                                 ? p.y
                                                 : std::numeric_limits<double>::quiet_NaN();
                         result[3 * i + 2] = valid && std::isfinite(p.z)
                                                 ? p.z
                                                 : std::numeric_limits<double>::quiet_NaN();
                     }
                     return result;
                 });
                 return owned_array(std::move(values), {a.height(), a.width(), 3});
             })
        .def("data", [](const eye::UntexturedPointCloud &a) {
            return array_data<eye::UntexturedPointCloud, float>(a, 3);
        });
    bind_array<eye::UntexturedPointCloudWithNormals, eye::PointXYZWithNormals>(
        m, "UntexturedPointCloudWithNormals")
        .def("data", [](const eye::UntexturedPointCloudWithNormals &a) {
            return array_data<eye::UntexturedPointCloudWithNormals, float>(a, 7);
        });
    auto t = bind_array<eye::TexturedPointCloud, eye::PointXYZBGR>(m, "TexturedPointCloud");
    textured_arrays<eye::TexturedPointCloud, false>(t);
    auto n = bind_array<eye::TexturedPointCloudWithNormals, eye::PointXYZBGRWithNormals>(
        m, "TexturedPointCloudWithNormals");
    textured_arrays<eye::TexturedPointCloudWithNormals, true>(n);
}
