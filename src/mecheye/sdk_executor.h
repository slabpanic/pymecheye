#pragma once
#include <cmath>
#include <condition_variable>
#include <deque>
#include <functional>
#include <future>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <stdexcept>
#include <string>
#include <thread>
#include <type_traits>
#include <utility>
#include <vector>
#if defined(__linux__)
#include <fcntl.h>
#include <sched.h>
#include <unistd.h>
#endif
#include "Version.h"
#include "area_scan_3d_camera/Camera.h"
#include "area_scan_3d_camera/Mapping2DToDepth.h"

namespace nb = nanobind;
namespace eye = mmind::eye;

// The SDK has no public logging switch and writes to standard streams or starts child processes.
// On Linux, the dedicated worker copies its file descriptor table and silences only that copy's
// stdout and stderr. Python and other native application threads retain the original table and
// their output. SDK background threads and child processes inherit the worker's isolated table.
class SdkExecutor {
  public:
    SdkExecutor(const SdkExecutor &) = delete;
    SdkExecutor &operator=(const SdkExecutor &) = delete;

    template <typename Function> std::invoke_result_t<Function> invoke(Function &&function) {
        if (std::this_thread::get_id() == worker_id_)
            return function();
        using Result = std::invoke_result_t<Function>;
        auto task =
            std::make_shared<std::packaged_task<Result()>>(std::forward<Function>(function));
        auto result = task->get_future();
        {
            std::lock_guard<std::mutex> lock(mutex_);
            tasks_.emplace_back([task] { (*task)(); });
        }
        condition_.notify_one();
        return result.get();
    }

    bool on_worker() const { return std::this_thread::get_id() == worker_id_; }

    void post(std::function<void()> task) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            tasks_.emplace_back(std::move(task));
        }
        condition_.notify_one();
    }

    static SdkExecutor &instance() {
        // Let the OS terminate this worker at process exit to avoid static destruction order
        // issues.
        static auto *executor = new SdkExecutor();
        return *executor;
    }

  private:
    SdkExecutor() {
        std::promise<void> ready;
        auto initialized = ready.get_future();
        worker_ = std::thread([this, ready = std::move(ready)]() mutable {
            try {
                worker_id_ = std::this_thread::get_id();
                isolate_output();
                ready.set_value();
            } catch (...) {
                ready.set_exception(std::current_exception());
                return;
            }
            for (;;) {
                std::function<void()> task;
                {
                    std::unique_lock<std::mutex> lock(mutex_);
                    condition_.wait(lock, [this] { return !tasks_.empty(); });
                    task = std::move(tasks_.front());
                    tasks_.pop_front();
                }
                task();
            }
        });
        try {
            initialized.get();
        } catch (...) {
            worker_.join();
            throw;
        }
        worker_.detach();
    }

    static void isolate_output() {
#if defined(__linux__)
        if (::unshare(CLONE_FILES) != 0)
            throw std::runtime_error("Failed to isolate the Mech-Eye SDK file descriptor table");
        const int null_fd = ::open("/dev/null", O_WRONLY | O_CLOEXEC);
        if (null_fd < 0)
            throw std::runtime_error("Failed to open /dev/null to silence Mech-Eye SDK logging");
        if (::dup2(null_fd, STDOUT_FILENO) < 0 || ::dup2(null_fd, STDERR_FILENO) < 0) {
            ::close(null_fd);
            throw std::runtime_error("Failed to silence Mech-Eye SDK standard stream logging");
        }
        ::close(null_fd);
#endif
    }

    std::mutex mutex_;
    std::condition_variable condition_;
    std::deque<std::function<void()>> tasks_;
    std::thread worker_;
    std::thread::id worker_id_;
};

// The SDK does not guarantee full global thread safety, so serialize all SDK entry points.
// Always lock the camera before the SDK and release both locks before restoring Python thread
// state.
extern std::recursive_mutex sdk_mutex;

template <typename Function> std::invoke_result_t<Function> call_sdk(Function &&function) {
    return SdkExecutor::instance().invoke(std::forward<Function>(function));
}

// SDK work runs on the isolated worker; Python objects are constructed only after it returns.
template <typename Function> std::invoke_result_t<Function> sdk_call(Function &&function) {
    nb::gil_scoped_release release;
    return call_sdk([&function] {
        std::lock_guard<std::recursive_mutex> lock(sdk_mutex);
        return function();
    });
}

struct NativeError : std::runtime_error {
    using std::runtime_error::runtime_error;
};
struct ConnectionError : NativeError {
    using NativeError::NativeError;
};
struct CaptureError : NativeError {
    using NativeError::NativeError;
};
struct ConfigurationError : NativeError {
    using NativeError::NativeError;
};
struct PointCloudError : NativeError {
    using NativeError::NativeError;
};

template <typename Error> void check(const eye::ErrorStatus &status, const char *context) {
    if (!status.isOK())
        throw Error(std::string(context) + ": " + status.errorDescription +
                    " (code=" + std::to_string(static_cast<int>(status.errorCode)) + ")");
}

// Arrays own independent buffers and remain valid after frame destruction, recapture, or
// disconnect.
template <typename T>
nb::ndarray<nb::numpy, T> owned_array(std::vector<T> &&values,
                                      std::initializer_list<size_t> shape) {
    auto storage = std::make_unique<std::vector<T>>(std::move(values));
    auto *pointer = storage.get();
    nb::capsule owner(pointer, [](void *p) noexcept { delete static_cast<std::vector<T> *>(p); });
    storage.release();
    return nb::ndarray<nb::numpy, T>(pointer->data(), shape, owner);
}

// SDK callback threads have no Python thread state and must never wait for their own shutdown.
// Dispose SDK objects on the worker; release Python state only when a caller is attached.
template <typename Function> void sdk_dispose(Function function) noexcept {
    try {
        auto cleanup = [function = std::move(function)]() mutable {
            std::lock_guard<std::recursive_mutex> lock(sdk_mutex);
            try {
                function();
            } catch (...) {
            }
        };
        auto &executor = SdkExecutor::instance();
        if (executor.on_worker()) {
            cleanup();
            return;
        }
#if PY_VERSION_HEX >= 0x030D0000
        auto *state = PyThreadState_GetUnchecked();
        const bool finalizing = Py_IsFinalizing();
#else
        auto *state = _PyThreadState_UncheckedGet();
        const bool finalizing = _Py_IsFinalizing();
#endif
        if (!state || finalizing) {
            executor.post(std::move(cleanup));
            return;
        }
        nb::gil_scoped_release release;
        executor.invoke(std::move(cleanup));
    } catch (...) {
    }
}
