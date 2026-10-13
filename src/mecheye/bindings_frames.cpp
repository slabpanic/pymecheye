#include "Log.h"
#include "area_scan_3d_camera/PointCloudTransformation.h"
#include "bindings.h"
void bind_frames(nb::module_ &m) {
    auto c_Frame2D = nb::class_<NativeFrame<eye::Frame2D>>(m, "Frame2D")
                         .def(nb::init<>())
                         .def(nb::init<const NativeFrame<eye::Frame2D> &>());
    c_Frame2D.def("image_size", [](NativeFrame<eye::Frame2D> &s) {
        return sdk_call([&] { return s.value->imageSize(); });
    });
    c_Frame2D.def("is_empty", [](NativeFrame<eye::Frame2D> &s) {
        return sdk_call([&] { return s.value->isEmpty(); });
    });
    c_Frame2D.def("frame_id", [](NativeFrame<eye::Frame2D> &s) {
        return sdk_call([&] { return s.value->frameId(); });
    });
    c_Frame2D.def("clear", [](NativeFrame<eye::Frame2D> &s) {
        return sdk_call([&] { return s.value->clear(); });
    });
    c_Frame2D.def("get_gray_scale_image", [](NativeFrame<eye::Frame2D> &s) {
        return sdk_call([&] { return s.value->getGrayScaleImage(); });
    });
    c_Frame2D.def("get_color_image", [](NativeFrame<eye::Frame2D> &s) {
        return sdk_call([&] { return s.value->getColorImage(); });
    });
    c_Frame2D.def("color_type", [](NativeFrame<eye::Frame2D> &s) {
        return sdk_call([&] { return int(s.value->colorType()); });
    });
    auto c_Frame3D = nb::class_<NativeFrame<eye::Frame3D>>(m, "Frame3D")
                         .def(nb::init<>())
                         .def(nb::init<const NativeFrame<eye::Frame3D> &>());
    c_Frame3D.def("image_size", [](NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] { return s.value->imageSize(); });
    });
    c_Frame3D.def("is_empty", [](NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] { return s.value->isEmpty(); });
    });
    c_Frame3D.def("frame_id", [](NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] { return s.value->frameId(); });
    });
    c_Frame3D.def("clear", [](NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] { return s.value->clear(); });
    });
    c_Frame3D.def("get_untextured_point_cloud", [](NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] { return s.value->getUntexturedPointCloud(); });
    });
    c_Frame3D.def("get_untextured_point_cloud_with_normals", [](NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] { return s.value->getUntexturedPointCloudWithNormals(); });
    });
    c_Frame3D.def("get_depth_map", [](NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] { return s.value->getDepthMap(); });
    });
    c_Frame3D.def(
        "save_untextured_point_cloud",
        [](const NativeFrame<eye::Frame3D> &s, int format, const std::string &file,
           bool organized) {
            return sdk_call([&] {
                return s.value->saveUntexturedPointCloud(static_cast<eye::FileFormat>(format), file,
                                                         organized);
            });
        },
        nb::arg("fileFormat"), nb::arg("fileName"), nb::arg("isOrganized") = false);
    c_Frame3D.def_static(
        "save_point_cloud",
        [](const eye::UntexturedPointCloud &cloud, int format, const std::string &file,
           bool organized, int unit) {
            return sdk_call([&] {
                return eye::Frame3D::savePointCloud(cloud, static_cast<eye::FileFormat>(format),
                                                    file, organized,
                                                    static_cast<eye::CoordinateUnit>(unit));
            });
        },
        nb::arg("pointCloud"), nb::arg("fileFormat"), nb::arg("fileName"),
        nb::arg("isOrganized") = false, nb::arg("pointCloudUnit") = 0);
    c_Frame3D.def(
        "save_untextured_point_cloud_with_normals",
        [](const NativeFrame<eye::Frame3D> &s, int format, const std::string &file,
           bool organized) {
            return sdk_call([&] {
                return s.value->saveUntexturedPointCloudWithNormals(
                    static_cast<eye::FileFormat>(format), file, organized);
            });
        },
        nb::arg("fileFormat"), nb::arg("fileName"), nb::arg("isOrganized") = false);
    c_Frame3D.def_static(
        "save_point_cloud_with_normals",
        [](const eye::UntexturedPointCloudWithNormals &cloud, int format, const std::string &file,
           bool organized, int unit) {
            return sdk_call([&] {
                return eye::Frame3D::savePointCloudWithNormals(
                    cloud, static_cast<eye::FileFormat>(format), file, organized,
                    static_cast<eye::CoordinateUnit>(unit));
            });
        },
        nb::arg("pointCloud"), nb::arg("fileFormat"), nb::arg("fileName"),
        nb::arg("isOrganized") = false, nb::arg("pointCloudUnit") = 0);
    auto c_Frame2DAnd3D = nb::class_<NativeFrame<eye::Frame2DAnd3D>>(m, "Frame2DAnd3D")
                              .def(nb::init<>())
                              .def(nb::init<const NativeFrame<eye::Frame2DAnd3D> &>());
    c_Frame2DAnd3D.def("frame_2d", [](NativeFrame<eye::Frame2DAnd3D> &s) {
        return NativeFrame<eye::Frame2D>::from_sdk([&] { return s.value->frame2D(); });
    });
    c_Frame2DAnd3D.def("frame_3d", [](NativeFrame<eye::Frame2DAnd3D> &s) {
        return NativeFrame<eye::Frame3D>::from_sdk([&] { return s.value->frame3D(); });
    });
    c_Frame2DAnd3D.def("clear", [](NativeFrame<eye::Frame2DAnd3D> &s) {
        return sdk_call([&] { return s.value->clear(); });
    });
    c_Frame2DAnd3D.def("get_textured_point_cloud", [](NativeFrame<eye::Frame2DAnd3D> &s) {
        return sdk_call([&] { return s.value->getTexturedPointCloud(); });
    });
    c_Frame2DAnd3D.def(
        "get_textured_point_cloud_with_normals", [](NativeFrame<eye::Frame2DAnd3D> &s) {
            return sdk_call([&] { return s.value->getTexturedPointCloudWithNormals(); });
        });
    c_Frame2DAnd3D.def(
        "save_textured_point_cloud",
        [](const NativeFrame<eye::Frame2DAnd3D> &s, int format, const std::string &file,
           bool organized) {
            return sdk_call([&] {
                return s.value->saveTexturedPointCloud(static_cast<eye::FileFormat>(format), file,
                                                       organized);
            });
        },
        nb::arg("fileFormat"), nb::arg("fileName"), nb::arg("isOrganized") = false);
    c_Frame2DAnd3D.def_static(
        "save_point_cloud",
        [](const eye::TexturedPointCloud &cloud, int format, const std::string &file,
           bool organized, int unit) {
            return sdk_call([&] {
                return eye::Frame2DAnd3D::savePointCloud(
                    cloud, static_cast<eye::FileFormat>(format), file, organized,
                    static_cast<eye::CoordinateUnit>(unit));
            });
        },
        nb::arg("pointCloud"), nb::arg("fileFormat"), nb::arg("fileName"),
        nb::arg("isOrganized") = false, nb::arg("pointCloudUnit") = 0);
    c_Frame2DAnd3D.def(
        "save_textured_point_cloud_with_normals",
        [](const NativeFrame<eye::Frame2DAnd3D> &s, int format, const std::string &file,
           bool organized) {
            return sdk_call([&] {
                return s.value->saveTexturedPointCloudWithNormals(
                    static_cast<eye::FileFormat>(format), file, organized);
            });
        },
        nb::arg("fileFormat"), nb::arg("fileName"), nb::arg("isOrganized") = false);
    c_Frame2DAnd3D.def_static(
        "save_point_cloud_with_normals",
        [](const eye::TexturedPointCloudWithNormals &cloud, int format, const std::string &file,
           bool organized, int unit) {
            return sdk_call([&] {
                return eye::Frame2DAnd3D::savePointCloudWithNormals(
                    cloud, static_cast<eye::FileFormat>(format), file, organized,
                    static_cast<eye::CoordinateUnit>(unit));
            });
        },
        nb::arg("pointCloud"), nb::arg("fileFormat"), nb::arg("fileName"),
        nb::arg("isOrganized") = false, nb::arg("pointCloudUnit") = 0);

    c_Frame3D.def("get_orthogonal_depth_map", [](const NativeFrame<eye::Frame3D> &s) {
        return sdk_call([&] {
            double xs = 0, ys = 0, xo = 0, yo = 0;
            auto depth = s.value->getOrthogonalDepthMap(xs, ys, xo, yo);
            return std::make_tuple(depth, xs, ys, xo, yo);
        });
    });
    m.def("get_point_cloud_after_mapping",
          [](const eye::DepthMap &d, const eye::GrayScale2DImage &mask,
             const eye::CameraIntrinsics &i, eye::UntexturedPointCloud &cloud) {
              return sdk_call([&] { return eye::getPointCloudAfterMapping(d, mask, i, cloud); });
          });
    m.def("get_point_cloud_after_mapping", [](const eye::DepthMap &d,
                                              const eye::GrayScale2DImage &mask,
                                              const eye::Color2DImage &color,
                                              const eye::CameraIntrinsics &i,
                                              eye::TexturedPointCloud &cloud) {
        return sdk_call([&] { return eye::getPointCloudAfterMapping(d, mask, color, i, cloud); });
    });
    m.def("export_logs", [](const std::string &path, bool cover) {
        return sdk_call([&] { return eye::exportLogs(path, cover); });
    });

    m.def("transform_point_cloud",
          [](const eye::FrameTransformation &t, const eye::UntexturedPointCloud &p) {
              return sdk_call([&] { return eye::transformPointCloud(t, p); });
          });
    m.def("transform_point_cloud_with_normals",
          [](const eye::FrameTransformation &t, const eye::UntexturedPointCloud &p) {
              return sdk_call([&] { return eye::transformPointCloudWithNormals(t, p); });
          });
    m.def("transform_textured_point_cloud",
          [](const eye::FrameTransformation &t, const eye::TexturedPointCloud &p) {
              return sdk_call([&] { return eye::transformTexturedPointCloud(t, p); });
          });
    m.def("transform_textured_point_cloud_with_normals",
          [](const eye::FrameTransformation &t, const eye::TexturedPointCloud &p) {
              return sdk_call([&] { return eye::transformTexturedPointCloudWithNormals(t, p); });
          });
}
