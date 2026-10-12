#pragma once
#include "area_scan_3d_camera/CameraEvent.h"
#include "area_scan_3d_camera/HandEyeCalibration.h"
#include "sdk_executor.h"
#include <nanobind/stl/map.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/tuple.h>

// Frame objects contain opaque SDK implementations; keep construction and destruction on the
// worker.
template <typename T> struct NativeFrame {
    std::shared_ptr<T> value;
    NativeFrame() { initialize(nullptr); }
    explicit NativeFrame(const T &other) { initialize(&other); }
    NativeFrame(const NativeFrame &other) { initialize(other.value.get()); }

  private:
    void initialize(const T *other) {
        auto construct = [other] {
            std::lock_guard<std::recursive_mutex> lock(sdk_mutex);
            return std::shared_ptr<T>(other ? new T(*other) : new T(),
                                      [](T *frame) { sdk_dispose([frame] { delete frame; }); });
        };
        value = SdkExecutor::instance().on_worker() ? call_sdk(construct) : sdk_call(construct);
    }
};

struct CameraState {
    std::unique_ptr<eye::Camera> camera;
    bool connected = false;
    size_t generation = 0;
    std::mutex events_mutex;
    std::deque<std::pair<eye::EventData, eye::CameraEvent::Payload>> events;
    CameraState();
    ~CameraState();
};

struct NativeCamera {
    std::shared_ptr<CameraState> state;
    NativeCamera();
    NativeCamera(const NativeCamera &other);
};

struct UserSetHandle {
    std::shared_ptr<CameraState> state;
    size_t generation;
};
struct ManagerHandle : UserSetHandle {};
struct ParameterHandle : UserSetHandle {
    std::string parameter_name;
};

inline eye::ErrorStatus invalid_device() {
    return {eye::ErrorStatus::MMIND_STATUS_INVALID_DEVICE,
            "Invalid device. Please use connect() to connect to a Mech-Eye Industrial 3D Camera."};
}
inline eye::ErrorStatus invalid_parameter() {
    return {eye::ErrorStatus::MMIND_STATUS_PARAMETER_ERROR,
            "Parameter is unavailable or has a different type"};
}
inline bool valid_handle(const UserSetHandle &handle) {
    return handle.state->connected && handle.generation == handle.state->generation;
}

void bind_values(nb::module_ &m);
void bind_arrays(nb::module_ &m);
void bind_frames(nb::module_ &m);
void bind_parameters(nb::module_ &m);
void bind_camera(nb::module_ &m);
void bind_descriptors(nb::module_ &m);
inline void bind_sdk(nb::module_ m) {
    bind_values(m);
    bind_arrays(m);
    bind_frames(m);
    bind_parameters(m);
    bind_camera(m);
    bind_descriptors(m);
}
