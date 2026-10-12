#include "bindings.h"

void bind_values(nb::module_ &m) {
    auto c_ErrorStatus = nb::class_<eye::ErrorStatus>(m, "ErrorStatus").def(nb::init<>());
    c_ErrorStatus.def_rw("error_code", &eye::ErrorStatus::errorCode);
    c_ErrorStatus.def_rw("error_description", &eye::ErrorStatus::errorDescription);
    auto c_Size = nb::class_<eye::Size>(m, "Size").def(nb::init<>());
    c_Size.def_rw("width", &eye::Size::width);
    c_Size.def_rw("height", &eye::Size::height);
    auto c_SizeF = nb::class_<eye::SizeF>(m, "SizeF").def(nb::init<>());
    c_SizeF.def_rw("width", &eye::SizeF::width);
    c_SizeF.def_rw("height", &eye::SizeF::height);
    auto c_ROI = nb::class_<eye::ROI>(m, "ROI").def(nb::init<>());
    c_ROI.def_rw("upper_left_x", &eye::ROI::upperLeftX);
    c_ROI.def_rw("upper_left_y", &eye::ROI::upperLeftY);
    c_ROI.def_rw("width", &eye::ROI::width);
    c_ROI.def_rw("height", &eye::ROI::height);
    auto c_ProfileROI = nb::class_<eye::ProfileROI>(m, "ProfileROI").def(nb::init<>());
    c_ProfileROI.def_rw("x_axis_center", &eye::ProfileROI::xAxisCenter);
    c_ProfileROI.def_rw("width", &eye::ProfileROI::width);
    c_ProfileROI.def_rw("height", &eye::ProfileROI::height);
    auto c_PointXYZ = nb::class_<eye::PointXYZ>(m, "PointXYZ").def(nb::init<>());
    c_PointXYZ.def_rw("x", &eye::PointXYZ::x);
    c_PointXYZ.def_rw("y", &eye::PointXYZ::y);
    c_PointXYZ.def_rw("z", &eye::PointXYZ::z);
    auto c_Gray = nb::class_<eye::Gray>(m, "Gray").def(nb::init<>());
    c_Gray.def_rw("gray", &eye::Gray::gray);
    auto c_ColorBGR = nb::class_<eye::ColorBGR>(m, "ColorBGR").def(nb::init<>());
    c_ColorBGR.def_rw("b", &eye::ColorBGR::b);
    c_ColorBGR.def_rw("g", &eye::ColorBGR::g);
    c_ColorBGR.def_rw("r", &eye::ColorBGR::r);
    auto c_PointZ = nb::class_<eye::PointZ>(m, "PointZ").def(nb::init<>());
    c_PointZ.def_rw("z", &eye::PointZ::z);
    auto c_NormalVector = nb::class_<eye::NormalVector>(m, "NormalVector").def(nb::init<>());
    c_NormalVector.def_rw("x", &eye::NormalVector::x);
    c_NormalVector.def_rw("y", &eye::NormalVector::y);
    c_NormalVector.def_rw("z", &eye::NormalVector::z);
    c_NormalVector.def_rw("curvature", &eye::NormalVector::curvature);
    auto c_PointXYZWithNormals =
        nb::class_<eye::PointXYZWithNormals>(m, "PointXYZWithNormals").def(nb::init<>());
    c_PointXYZWithNormals.def_rw("point", &eye::PointXYZWithNormals::point);
    c_PointXYZWithNormals.def_rw("normal", &eye::PointXYZWithNormals::normal);
    auto c_PointXYZBGR = nb::class_<eye::PointXYZBGR>(m, "PointXYZBGR").def(nb::init<>());
    c_PointXYZBGR.def_rw("x", &eye::PointXYZBGR::x);
    c_PointXYZBGR.def_rw("y", &eye::PointXYZBGR::y);
    c_PointXYZBGR.def_rw("z", &eye::PointXYZBGR::z);
    c_PointXYZBGR.def_rw("b", &eye::PointXYZBGR::b);
    c_PointXYZBGR.def_rw("g", &eye::PointXYZBGR::g);
    c_PointXYZBGR.def_rw("r", &eye::PointXYZBGR::r);
    c_PointXYZBGR.def_rw("a", &eye::PointXYZBGR::a);
    c_PointXYZBGR.def_rw("rgb", &eye::PointXYZBGR::rgb);
    auto c_PointXYZBGRWithNormals =
        nb::class_<eye::PointXYZBGRWithNormals>(m, "PointXYZBGRWithNormals").def(nb::init<>());
    c_PointXYZBGRWithNormals.def_rw("color_point", &eye::PointXYZBGRWithNormals::colorPoint);
    c_PointXYZBGRWithNormals.def_rw("normal", &eye::PointXYZBGRWithNormals::normal);
    auto c_CameraInfo = nb::class_<eye::CameraInfo>(m, "CameraInfo").def(nb::init<>());
    c_CameraInfo.def_rw("model", &eye::CameraInfo::model);
    c_CameraInfo.def_rw("device_name", &eye::CameraInfo::deviceName);
    c_CameraInfo.def_rw("serial_number", &eye::CameraInfo::serialNumber);
    c_CameraInfo.def_rw("hardware_version", &eye::CameraInfo::hardwareVersion);
    c_CameraInfo.def_rw("firmware_version", &eye::CameraInfo::firmwareVersion);
    c_CameraInfo.def_rw("ip_address", &eye::CameraInfo::ipAddress);
    c_CameraInfo.def_rw("subnet_mask", &eye::CameraInfo::subnetMask);
    c_CameraInfo.def_rw("port", &eye::CameraInfo::port);
    c_CameraInfo.def_rw("supported", &eye::CameraInfo::supported);
    c_CameraInfo.def_rw("last_supported_version", &eye::CameraInfo::lastSupportedVersion);
    auto c_DeviceTemperature =
        nb::class_<eye::DeviceTemperature>(m, "DeviceTemperature").def(nb::init<>());
    c_DeviceTemperature.def_rw("cpu_temperature", &eye::DeviceTemperature::cpuTemperature);
    c_DeviceTemperature.def_rw("projector_temperature",
                               &eye::DeviceTemperature::projectorTemperature);
    auto c_CameraStatus = nb::class_<eye::CameraStatus>(m, "CameraStatus").def(nb::init<>());
    c_CameraStatus.def_rw("temperature", &eye::CameraStatus::temperature);
    auto c_CameraMatrix = nb::class_<eye::CameraMatrix>(m, "CameraMatrix").def(nb::init<>());
    c_CameraMatrix.def_rw("fx", &eye::CameraMatrix::fx);
    c_CameraMatrix.def_rw("fy", &eye::CameraMatrix::fy);
    c_CameraMatrix.def_rw("cx", &eye::CameraMatrix::cx);
    c_CameraMatrix.def_rw("cy", &eye::CameraMatrix::cy);
    auto c_CameraDistortion =
        nb::class_<eye::CameraDistortion>(m, "CameraDistortion").def(nb::init<>());
    c_CameraDistortion.def_rw("k1", &eye::CameraDistortion::k1);
    c_CameraDistortion.def_rw("k2", &eye::CameraDistortion::k2);
    c_CameraDistortion.def_rw("p1", &eye::CameraDistortion::p1);
    c_CameraDistortion.def_rw("p2", &eye::CameraDistortion::p2);
    c_CameraDistortion.def_rw("k3", &eye::CameraDistortion::k3);
    auto c_Intrinsics2DCamera =
        nb::class_<eye::Intrinsics2DCamera>(m, "Intrinsics2DCamera").def(nb::init<>());
    c_Intrinsics2DCamera.def_rw("camera_matrix", &eye::Intrinsics2DCamera::cameraMatrix);
    c_Intrinsics2DCamera.def_rw("camera_distortion", &eye::Intrinsics2DCamera::cameraDistortion);
    auto c_CameraResolutions =
        nb::class_<eye::CameraResolutions>(m, "CameraResolutions").def(nb::init<>());
    c_CameraResolutions.def_rw("texture", &eye::CameraResolutions::texture);
    c_CameraResolutions.def_rw("depth", &eye::CameraResolutions::depth);
    auto c_CameraIntrinsics =
        nb::class_<eye::CameraIntrinsics>(m, "CameraIntrinsics").def(nb::init<>());
    c_CameraIntrinsics.def_rw("texture", &eye::CameraIntrinsics::texture);
    c_CameraIntrinsics.def_rw("depth", &eye::CameraIntrinsics::depth);
    c_CameraIntrinsics.def_rw("depth_to_texture", &eye::CameraIntrinsics::depthToTexture);
    auto c_EventData = nb::class_<eye::EventData>(m, "EventData").def(nb::init<>());
    c_EventData.def_rw("event_id", &eye::EventData::eventId);
    c_EventData.def_rw("event_name", &eye::EventData::eventName);
    c_EventData.def_rw("timestamp", &eye::EventData::timestamp);
    c_EventData.def_rw("frame_id", &eye::EventData::frameId);
    auto c_EventInfo = nb::class_<eye::CameraEvent::EventInfo>(m, "EventInfo").def(nb::init<>());
    c_EventInfo.def_rw("event_name", &eye::CameraEvent::EventInfo::eventName);
    c_EventInfo.def_rw("event_id", &eye::CameraEvent::EventInfo::eventId);
    auto c_MemberValue = nb::class_<eye::CameraEvent::PayloadMember::MemberValue>(m, "MemberValue")
                             .def(nb::init<>());
    c_MemberValue.def_rw("uint_32value",
                         &eye::CameraEvent::PayloadMember::MemberValue::uint32Value);
    c_MemberValue.def_rw("int_32value", &eye::CameraEvent::PayloadMember::MemberValue::int32Value);
    c_MemberValue.def_rw("int_64value", &eye::CameraEvent::PayloadMember::MemberValue::int64Value);
    c_MemberValue.def_rw("float_value", &eye::CameraEvent::PayloadMember::MemberValue::floatValue);
    c_MemberValue.def_rw("double_value",
                         &eye::CameraEvent::PayloadMember::MemberValue::doubleValue);
    c_MemberValue.def_rw("bool_value", &eye::CameraEvent::PayloadMember::MemberValue::boolValue);
    c_MemberValue.def_rw("string_value",
                         &eye::CameraEvent::PayloadMember::MemberValue::stringValue);
    auto c_PayloadMember =
        nb::class_<eye::CameraEvent::PayloadMember>(m, "PayloadMember").def(nb::init<>());
    c_PayloadMember.def_rw("name", &eye::CameraEvent::PayloadMember::name);
    c_PayloadMember.def_rw("value", &eye::CameraEvent::PayloadMember::value);
    auto c_HandEyeTransformation =
        nb::class_<eye::HandEyeCalibration::Transformation>(m, "HandEyeTransformation")
            .def(nb::init<>());
    c_HandEyeTransformation.def_rw("x", &eye::HandEyeCalibration::Transformation::x);
    c_HandEyeTransformation.def_rw("y", &eye::HandEyeCalibration::Transformation::y);
    c_HandEyeTransformation.def_rw("z", &eye::HandEyeCalibration::Transformation::z);
    c_HandEyeTransformation.def_rw("q_w", &eye::HandEyeCalibration::Transformation::qW);
    c_HandEyeTransformation.def_rw("q_x", &eye::HandEyeCalibration::Transformation::qX);
    c_HandEyeTransformation.def_rw("q_y", &eye::HandEyeCalibration::Transformation::qY);
    c_HandEyeTransformation.def_rw("q_z", &eye::HandEyeCalibration::Transformation::qZ);
    nb::class_<eye::Range<int>>(m, "RangeInt")
        .def(nb::init<>())
        .def(nb::init<int, int>())
        .def_rw("min", &eye::Range<int>::min)
        .def_rw("max", &eye::Range<int>::max);
    nb::class_<eye::Range<float>>(m, "RangeFloat")
        .def(nb::init<>())
        .def(nb::init<float, float>())
        .def_rw("min", &eye::Range<float>::min)
        .def_rw("max", &eye::Range<float>::max);
    nb::class_<eye::Range<double>>(m, "RangeDouble")
        .def(nb::init<>())
        .def(nb::init<double, double>())
        .def_rw("min", &eye::Range<double>::min)
        .def_rw("max", &eye::Range<double>::max);

    c_Size.def(nb::init<size_t, size_t>());
    c_SizeF.def(nb::init<double, double>());
    c_ROI.def(nb::init<unsigned, unsigned, size_t, size_t>());
    c_ProfileROI.def(nb::init<double, double, double>());
    c_ErrorStatus.def("is_ok", &eye::ErrorStatus::isOK)
        .def("__init__", [](eye::ErrorStatus *p, int code, const std::string &message) {
            new (p) eye::ErrorStatus(static_cast<eye::ErrorStatus::ErrorCode>(code), message);
        });
    c_ErrorStatus.def_prop_rw(
        "error_code", [](const eye::ErrorStatus &s) { return int(s.errorCode); },
        [](eye::ErrorStatus &s, int v) {
            s.errorCode = static_cast<eye::ErrorStatus::ErrorCode>(v);
        });
    c_CameraInfo
        .def_prop_rw(
            "platform", [](const eye::CameraInfo &s) { return int(s.platform); },
            [](eye::CameraInfo &s, int v) { s.platform = static_cast<decltype(s.platform)>(v); })
        .def_prop_rw(
            "ip_assignment_method",
            [](const eye::CameraInfo &s) { return int(s.ipAssignmentMethod); },
            [](eye::CameraInfo &s, int v) {
                s.ipAssignmentMethod = static_cast<eye::IpAssignmentMethod>(v);
            });
    c_PayloadMember.def_prop_rw(
        "type", [](const eye::CameraEvent::PayloadMember &s) { return int(s.type); },
        [](eye::CameraEvent::PayloadMember &s, int v) {
            s.type = static_cast<eye::CameraEvent::PayloadMember::Type>(v);
        });
    c_PointXYZBGR.def(nb::init<float, float, float>())
        .def(nb::init<uint8_t, uint8_t, uint8_t, uint8_t>())
        .def(nb::init<float, float, float, uint8_t, uint8_t, uint8_t>())
        .def(nb::init<float, float, float, uint8_t, uint8_t, uint8_t, uint8_t>())
        .def(nb::init<const eye::PointXYZBGR &>());
    c_EventInfo.def(nb::init<const std::string &, uint16_t>());
    c_HandEyeTransformation.def(nb::init<double, double, double, double, double, double, double>())
        .def("to_string", &eye::HandEyeCalibration::Transformation::toString);
    nb::class_<eye::Version>(m, "Version")
        .def(nb::init<>())
        .def(nb::init<int, int, int>())
        .def(nb::init<const std::string &>())
        .def("to_string", &eye::Version::toString)
        .def("from_string", &eye::Version::fromString)
        .def("is_empty", &eye::Version::isEmpty)
        .def("__eq__", &eye::Version::operator==)
        .def("__ne__", &eye::Version::operator!=)
        .def("__ge__", &eye::Version::operator>=)
        .def("__lt__", &eye::Version::operator<)
        .def("__le__", &eye::Version::operator<=);

    auto c_Transformation = nb::class_<eye::Transformation>(m, "Transformation").def(nb::init<>());
    c_Transformation.def_prop_rw(
        "rotation",
        [](const eye::Transformation &s) {
            std::vector<std::vector<double>> v(3, std::vector<double>(3));
            for (size_t i = 0; i < 3; i++)
                for (size_t j = 0; j < 3; j++)
                    v[i][j] = s.rotation[i][j];
            return v;
        },
        [](eye::Transformation &s, const std::vector<std::vector<double>> &v) {
            if (v.size() != 3)
                throw nb::value_error("Expected three elements");
            for (size_t i = 0; i < 3; i++) {
                if (v[i].size() != 3)
                    throw nb::value_error("Expected a 3x3 matrix");
            }
            for (size_t i = 0; i < 3; i++)
                for (size_t j = 0; j < 3; j++)
                    s.rotation[i][j] = v[i][j];
        });
    c_Transformation.def_prop_rw(
        "translation",
        [](const eye::Transformation &s) {
            return std::vector<double>(s.translation, s.translation + 3);
        },
        [](eye::Transformation &s, const std::vector<double> &v) {
            if (v.size() != 3)
                throw nb::value_error("Expected three elements");
            for (size_t i = 0; i < 3; i++)
                s.translation[i] = v[i];
        });
    auto c_FrameTransformation =
        nb::class_<eye::FrameTransformation>(m, "FrameTransformation").def(nb::init<>());
    c_FrameTransformation.def_prop_rw(
        "rotation",
        [](const eye::FrameTransformation &s) {
            std::vector<std::vector<double>> v(3, std::vector<double>(3));
            for (size_t i = 0; i < 3; i++)
                for (size_t j = 0; j < 3; j++)
                    v[i][j] = s.rotation[i][j];
            return v;
        },
        [](eye::FrameTransformation &s, const std::vector<std::vector<double>> &v) {
            if (v.size() != 3)
                throw nb::value_error("Expected three elements");
            for (size_t i = 0; i < 3; i++) {
                if (v[i].size() != 3)
                    throw nb::value_error("Expected a 3x3 matrix");
            }
            for (size_t i = 0; i < 3; i++)
                for (size_t j = 0; j < 3; j++)
                    s.rotation[i][j] = v[i][j];
        });
    c_FrameTransformation.def_prop_rw(
        "translation",
        [](const eye::FrameTransformation &s) {
            return std::vector<double>(s.translation, s.translation + 3);
        },
        [](eye::FrameTransformation &s, const std::vector<double> &v) {
            if (v.size() != 3)
                throw nb::value_error("Expected three elements");
            for (size_t i = 0; i < 3; i++)
                s.translation[i] = v[i];
        });

    c_FrameTransformation.def(nb::init<double, double, double, double, double, double>())
        .def(nb::init<const eye::FrameTransformation &>())
        .def("rotate",
             [](eye::FrameTransformation &s, double theta, int axis) {
                 s.rotate(theta, static_cast<eye::FrameTransformation::Axis>(axis));
             })
        .def("translate", &eye::FrameTransformation::translate)
        .def("is_valid", &eye::FrameTransformation::isValid);
    m.def("clone_value", [](const eye::ErrorStatus &value) { return eye::ErrorStatus(value); });
    m.def("clone_value", [](const eye::Size &value) { return eye::Size(value); });
    m.def("clone_value", [](const eye::SizeF &value) { return eye::SizeF(value); });
    m.def("clone_value", [](const eye::ROI &value) { return eye::ROI(value); });
    m.def("clone_value", [](const eye::ProfileROI &value) { return eye::ProfileROI(value); });
    m.def("clone_value", [](const eye::PointXYZ &value) { return eye::PointXYZ(value); });
    m.def("clone_value", [](const eye::Gray &value) { return eye::Gray(value); });
    m.def("clone_value", [](const eye::ColorBGR &value) { return eye::ColorBGR(value); });
    m.def("clone_value", [](const eye::PointZ &value) { return eye::PointZ(value); });
    m.def("clone_value", [](const eye::NormalVector &value) { return eye::NormalVector(value); });
    m.def("clone_value",
          [](const eye::PointXYZWithNormals &value) { return eye::PointXYZWithNormals(value); });
    m.def("clone_value", [](const eye::PointXYZBGR &value) { return eye::PointXYZBGR(value); });
    m.def("clone_value", [](const eye::PointXYZBGRWithNormals &value) {
        return eye::PointXYZBGRWithNormals(value);
    });
    m.def("clone_value", [](const eye::CameraInfo &value) { return eye::CameraInfo(value); });
    m.def("clone_value",
          [](const eye::DeviceTemperature &value) { return eye::DeviceTemperature(value); });
    m.def("clone_value", [](const eye::CameraStatus &value) { return eye::CameraStatus(value); });
    m.def("clone_value", [](const eye::CameraMatrix &value) { return eye::CameraMatrix(value); });
    m.def("clone_value",
          [](const eye::CameraDistortion &value) { return eye::CameraDistortion(value); });
    m.def("clone_value",
          [](const eye::Intrinsics2DCamera &value) { return eye::Intrinsics2DCamera(value); });
    m.def("clone_value",
          [](const eye::CameraResolutions &value) { return eye::CameraResolutions(value); });
    m.def("clone_value",
          [](const eye::CameraIntrinsics &value) { return eye::CameraIntrinsics(value); });
    m.def("clone_value",
          [](const eye::Transformation &value) { return eye::Transformation(value); });
    m.def("clone_value",
          [](const eye::FrameTransformation &value) { return eye::FrameTransformation(value); });
    m.def("clone_value", [](const eye::Version &value) { return eye::Version(value); });
    m.def("clone_value", [](const eye::Range<int> &value) { return value; });
    m.def("clone_value", [](const eye::Range<float> &value) { return value; });
    m.def("clone_value", [](const eye::Range<double> &value) { return value; });
    m.def("clone_value", [](const eye::EventData &value) { return value; });
    m.def("clone_value", [](const eye::CameraEvent::EventInfo &value) { return value; });
    m.def("clone_value", [](const eye::CameraEvent::PayloadMember &value) { return value; });
    m.def("clone_value",
          [](const eye::CameraEvent::PayloadMember::MemberValue &value) { return value; });
    m.def("clone_value",
          [](const eye::HandEyeCalibration::Transformation &value) { return value; });
    m.def("copy_intrinsics",
          [](eye::CameraIntrinsics &out, const eye::CameraIntrinsics &in) { out = in; });
    m.def("copy_frame_transformation",
          [](eye::FrameTransformation &out, const eye::FrameTransformation &in) { out = in; });
    c_Size.def("__eq__", [](eye::Size &s, const eye::Size &other) { return s == other; });
    c_SizeF.def("__eq__", [](eye::SizeF &s, const eye::SizeF &other) { return s == other; });
    c_ROI.def("__eq__", [](eye::ROI &s, const eye::ROI &other) { return s == other; });
    c_ProfileROI.def("__eq__",
                     [](eye::ProfileROI &s, const eye::ProfileROI &other) { return s == other; });
}
