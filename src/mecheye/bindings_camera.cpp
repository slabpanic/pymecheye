#include "area_scan_3d_camera/PointCloudTransformation.h"
#include "bindings.h"

CameraState::CameraState() {
    camera = sdk_call([] {
        auto camera = std::make_unique<eye::Camera>();
        SdkExecutor::instance().track_resource(camera.get(), [pointer = camera.get()] {
            std::unique_ptr<eye::Camera> camera(pointer);
            camera->disconnect();
        });
        return camera;
    });
}
CameraState::~CameraState() {
    auto *owned = camera.release();
    sdk_dispose([owned] { SdkExecutor::instance().release_resource(owned); });
}
NativeCamera::NativeCamera() : state(std::make_shared<CameraState>()) {}
NativeCamera::NativeCamera(const NativeCamera &other) : state(other.state) {}

void bind_camera(nb::module_ &m) {
    auto c = nb::class_<NativeCamera>(m, "Camera")
                 .def(nb::init<>())
                 .def(nb::init<const NativeCamera &>());
    c.def_static(
        "discover_cameras",
        [](unsigned timeout) {
            return sdk_call([&] { return eye::Camera::discoverCameras(timeout); });
        },
        nb::arg("timeoutMs") = 5000);
    c.def(
        "connect",
        [](NativeCamera &s, const std::string &ip, unsigned timeout) {
            return sdk_call([&] {
                auto status = s.state->camera->connect(ip, timeout);
                if (status.isOK())
                    s.state->connected = true;
                ++s.state->generation;
                return status;
            });
        },
        nb::arg("ipAddress"), nb::arg("timeoutMs") = 5000);
    c.def(
        "connect",
        [](NativeCamera &s, const eye::CameraInfo &info, unsigned timeout) {
            return sdk_call([&] {
                auto status = s.state->camera->connect(info, timeout);
                if (status.isOK())
                    s.state->connected = true;
                ++s.state->generation;
                return status;
            });
        },
        nb::arg("info"), nb::arg("timeoutMs") = 5000);
    c.def("disconnect", [](NativeCamera &s) {
        sdk_call([&] {
            s.state->camera->disconnect();
            s.state->connected = false;
            ++s.state->generation;
        });
    });
    c.def("connected",
          [](const NativeCamera &s) { return sdk_call([&] { return s.state->connected; }); });
    c.def("set_heartbeat_interval", [](NativeCamera &s, unsigned interval) {
        return sdk_call([&] { return s.state->camera->setHeartbeatInterval(interval); });
    });
    c.def("get_point_cloud_unit", [](NativeCamera &s) {
        return sdk_call([&] {
            eye::CoordinateUnit unit{};
            auto status = s.state->camera->getPointCloudUnit(unit);
            return std::make_pair(status, int(unit));
        });
    });
    c.def("set_point_cloud_unit", [](NativeCamera &s, int unit) {
        return sdk_call([&] {
            return s.state->camera->setPointCloudUnit(static_cast<eye::CoordinateUnit>(unit));
        });
    });
    c.def("save_virtual_device_file", [](NativeCamera &s, const std::string &path) {
        return sdk_call([&] { return s.state->camera->saveVirtualDeviceFile(path); });
    });
    c.def("current_user_set",
          [](NativeCamera &s) { return UserSetHandle{s.state, s.state->generation}; });
    c.def("user_set_manager", [](NativeCamera &s) {
        ManagerHandle h;
        h.state = s.state;
        h.generation = s.state->generation;
        return h;
    });
    c.def("poll_events", [](NativeCamera &s) {
        std::vector<std::pair<eye::EventData, eye::CameraEvent::Payload>> result;
        std::lock_guard<std::mutex> lock(s.state->events_mutex);
        while (!s.state->events.empty()) {
            result.push_back(std::move(s.state->events.front()));
            s.state->events.pop_front();
        }
        return result;
    });

    c.def("get_camera_info", [](NativeCamera &s, eye::CameraInfo &out) {
        return sdk_call([&] { return s.state->camera->getCameraInfo(out); });
    });
    c.def("get_camera_status", [](NativeCamera &s, eye::CameraStatus &out) {
        return sdk_call([&] { return s.state->camera->getCameraStatus(out); });
    });
    c.def("get_camera_resolutions", [](NativeCamera &s, eye::CameraResolutions &out) {
        return sdk_call([&] { return s.state->camera->getCameraResolutions(out); });
    });
    c.def("get_camera_intrinsics", [](NativeCamera &s, eye::CameraIntrinsics &out) {
        return sdk_call([&] { return s.state->camera->getCameraIntrinsics(out); });
    });
    c.def(
        "capture_2d",
        [](NativeCamera &s, NativeFrame<eye::Frame2D> &out, unsigned timeout) {
            return sdk_call([&] { return s.state->camera->capture2D(*out.value, timeout); });
        },
        nb::arg("frame"), nb::arg("timeoutMs") = 5000);
    c.def(
        "capture_depth_source_2d",
        [](NativeCamera &s, NativeFrame<eye::Frame2D> &out, unsigned timeout) {
            return sdk_call(
                [&] { return s.state->camera->captureDepthSource2D(*out.value, timeout); });
        },
        nb::arg("frame"), nb::arg("timeoutMs") = 5000);
    c.def(
        "capture_3d",
        [](NativeCamera &s, NativeFrame<eye::Frame3D> &out, unsigned timeout) {
            return sdk_call([&] { return s.state->camera->capture3D(*out.value, timeout); });
        },
        nb::arg("frame"), nb::arg("timeoutMs") = 5000);
    c.def(
        "capture_3d_with_normal",
        [](NativeCamera &s, NativeFrame<eye::Frame3D> &out, unsigned timeout) {
            return sdk_call(
                [&] { return s.state->camera->capture3DWithNormal(*out.value, timeout); });
        },
        nb::arg("frame"), nb::arg("timeoutMs") = 10000);
    c.def(
        "capture_2d_and_3d",
        [](NativeCamera &s, NativeFrame<eye::Frame2DAnd3D> &out, unsigned timeout) {
            return sdk_call([&] { return s.state->camera->capture2DAnd3D(*out.value, timeout); });
        },
        nb::arg("frame"), nb::arg("timeoutMs") = 10000);
    c.def(
        "capture_depth_source_2d_and_3d",
        [](NativeCamera &s, NativeFrame<eye::Frame2DAnd3D> &out, unsigned timeout) {
            return sdk_call(
                [&] { return s.state->camera->captureDepthSource2DAnd3D(*out.value, timeout); });
        },
        nb::arg("frame"), nb::arg("timeoutMs") = 10000);
    c.def(
        "capture_2d_and_3d_with_normal",
        [](NativeCamera &s, NativeFrame<eye::Frame2DAnd3D> &out, unsigned timeout) {
            return sdk_call(
                [&] { return s.state->camera->capture2DAnd3DWithNormal(*out.value, timeout); });
        },
        nb::arg("frame"), nb::arg("timeoutMs") = 15000);

    m.attr("Camera_discover_cameras") = c.attr("discover_cameras");
    c.def(
        "capture_stereo_2d",
        [](NativeCamera &s, NativeFrame<eye::Frame2D> &left, NativeFrame<eye::Frame2D> &right,
           bool rectified, unsigned timeout) {
            return sdk_call([&] {
                return s.state->camera->captureStereo2D(*left.value, *right.value, rectified,
                                                        timeout);
            });
        },
        nb::arg("left"), nb::arg("right"), nb::arg("isRectified") = false,
        nb::arg("timeoutMs") = 5000);
    m.def("get_transformation_params", [](NativeCamera &s) {
        return sdk_call([&] { return eye::getTransformationParams(*s.state->camera); });
    });
    m.def("get_supported_events", [](NativeCamera &s) {
        return sdk_call([&] {
            std::vector<eye::CameraEvent::EventInfo> result;
            auto status = eye::CameraEvent::getSupportedEvents(*s.state->camera, result);
            return std::make_pair(status, result);
        });
    });
    m.def("register_event", [](NativeCamera &s, uint16_t event) {
        auto state = std::weak_ptr<CameraState>(s.state);
        return sdk_call([&] {
            return eye::CameraEvent::registerCameraEventCallback(
                *s.state->camera, event,
                [state](const eye::EventData *event_data, const void *payload) {
                    if (!event_data)
                        return;
                    if (auto owner = state.lock()) {
                        auto data = *event_data;
                        eye::CameraEvent::Payload copy;
                        if (payload) {
                            for (const auto &source :
                                 *static_cast<const eye::CameraEvent::Payload *>(payload)) {
                                eye::CameraEvent::PayloadMember item{};
                                item.name = source.name;
                                item.type = source.type;
                                using Type = eye::CameraEvent::PayloadMember::Type;
                                switch (source.type) {
                                case Type::_UInt32:
                                    item.value.uint32Value = source.value.uint32Value;
                                    break;
                                case Type::_Int32:
                                    item.value.int32Value = source.value.int32Value;
                                    break;
                                case Type::_Int64:
                                    item.value.int64Value = source.value.int64Value;
                                    break;
                                case Type::_Float:
                                    item.value.floatValue = source.value.floatValue;
                                    break;
                                case Type::_Double:
                                    item.value.doubleValue = source.value.doubleValue;
                                    break;
                                case Type::_Bool:
                                    item.value.boolValue = source.value.boolValue;
                                    break;
                                case Type::_String:
                                    item.value.stringValue = source.value.stringValue;
                                    break;
                                }
                                copy.push_back(std::move(item));
                            }
                        }
                        std::lock_guard<std::mutex> lock(owner->events_mutex);
                        owner->events.emplace_back(std::move(data), std::move(copy));
                    }
                });
        });
    });
    m.def("unregister_event", [](NativeCamera &s, uint16_t event) {
        return sdk_call([&] {
            return eye::CameraEvent::unregisterCameraEventCallback(*s.state->camera, event);
        });
    });
    auto h = nb::class_<eye::HandEyeCalibration>(m, "HandEyeCalibration").def(nb::init<>());
    h.def("initialize_calibration", [](eye::HandEyeCalibration &h, NativeCamera &s, int mode,
                                       int board) {
        return sdk_call([&] {
            return h.initializeCalibration(
                *s.state->camera, static_cast<eye::HandEyeCalibration::CameraMountingMode>(mode),
                static_cast<eye::HandEyeCalibration::CalibrationBoardModel>(board));
        });
    });
    h.def(
        "add_pose_and_detect",
        [](eye::HandEyeCalibration &h, NativeCamera &s,
           const eye::HandEyeCalibration::Transformation &pose, eye::Color2DImage &image,
           unsigned timeout) {
            return sdk_call(
                [&] { return h.addPoseAndDetect(*s.state->camera, pose, image, timeout); });
        },
        nb::arg("camera"), nb::arg("poseData"), nb::arg("color2DImage"),
        nb::arg("timeoutMs") = 10000);
    h.def("calculate_extrinsics", [](eye::HandEyeCalibration &h, NativeCamera &s,
                                     eye::HandEyeCalibration::Transformation &out) {
        return sdk_call([&] { return h.calculateExtrinsics(*s.state->camera, out); });
    });
    h.def(
        "test_recognition",
        [](eye::HandEyeCalibration &h, NativeCamera &s, eye::Color2DImage &image,
           unsigned timeout) {
            return sdk_call([&] { return h.testRecognition(*s.state->camera, image, timeout); });
        },
        nb::arg("camera"), nb::arg("testResult"), nb::arg("timeoutMs") = 20000);
    h.def(
        "extract_current_image_first_corner",
        [](eye::HandEyeCalibration &h, NativeCamera &s, eye::PointXYZ &corner, unsigned timeout) {
            return sdk_call([&] {
                return h.extractCurrentImageFirstCorner(*s.state->camera, corner, timeout);
            });
        },
        nb::arg("camera"), nb::arg("corner"), nb::arg("timeoutMs") = 20000);
}
