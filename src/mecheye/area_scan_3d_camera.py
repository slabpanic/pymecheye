"""Mech-Eye area-scan camera bindings and NumPy capture utilities."""

from __future__ import annotations
from collections import deque
from types import SimpleNamespace
import threading
import time
import weakref
import numpy as np
from . import shared
from ._compat import (
    Proxy,
    FixedArray,
    _api_lock,
    _backend,
    _unwrap,
    _wrap,
    call,
    function,
    register,
    value_type,
    array_type,
    _snapshot,
    Ownership,
)
from ._containers import SwigPyIterator, vector_type
from .shared import (
    ErrorStatus,
    MechEyeConnectionError,
    MechEyeCaptureError,
    MechEyePointCloudError,
    MechEyeConfigurationError,
)

ColorTypeOf2DCamera_Monochrome = 0
ColorTypeOf2DCamera_Color = 1
ColorTypeOf2DCamera_Undefined = 2
Transformation = value_type("Transformation", ["rotation", "translation"], __name__)
FrameTransformation = value_type(
    "FrameTransformation", ["rotation", "translation"], __name__
)
CameraIntrinsics = value_type(
    "CameraIntrinsics", ["texture", "depth", "depth_to_texture"], __name__
)
CameraInfo = value_type(
    "CameraInfo",
    [
        "model",
        "device_name",
        "serial_number",
        "platform",
        "hardware_version",
        "firmware_version",
        "ip_address",
        "subnet_mask",
        "ip_assignment_method",
        "port",
        "supported",
        "last_supported_version",
    ],
    __name__,
)
DeviceTemperature = value_type(
    "DeviceTemperature", ["cpu_temperature", "projector_temperature"], __name__
)
CameraStatus = value_type("CameraStatus", ["temperature"], __name__)
CameraMatrix = value_type("CameraMatrix", ["fx", "fy", "cx", "cy"], __name__)
CameraDistortion = value_type(
    "CameraDistortion", ["k1", "k2", "p1", "p2", "k3"], __name__
)
Intrinsics2DCamera = value_type(
    "Intrinsics2DCamera", ["camera_distortion", "camera_matrix"], __name__
)
CameraResolutions = value_type("CameraResolutions", ["texture", "depth"], __name__)
Gray = value_type("Gray", ["gray"], __name__)
ColorBGR = value_type("ColorBGR", ["b", "g", "r"], __name__)
PointZ = value_type("PointZ", ["z"], __name__)
NormalVector = value_type("NormalVector", ["x", "y", "z", "curvature"], __name__)
PointXYZWithNormals = value_type("PointXYZWithNormals", ["point", "normal"], __name__)
PointXYZBGR = value_type(
    "PointXYZBGR", ["x", "y", "z", "b", "g", "r", "a", "rgb"], __name__
)
PointXYZBGRWithNormals = value_type(
    "PointXYZBGRWithNormals", ["color_point", "normal"], __name__
)
EventData = value_type(
    "EventData", ["event_id", "event_name", "timestamp", "frame_id"], __name__
)
EventInfo = value_type("EventInfo", ["event_name", "event_id"], __name__)
PayloadMember = value_type("PayloadMember", ["name", "type", "value"], __name__)
MemberValue = value_type(
    "MemberValue",
    [
        "uint_32value",
        "int_32value",
        "int_64value",
        "float_value",
        "double_value",
        "bool_value",
        "string_value",
    ],
    __name__,
)
HandEyeTransformation = value_type(
    "HandEyeTransformation", ["x", "y", "z", "q_w", "q_x", "q_y", "q_z"], __name__
)


def _rotate(self, theta, axis):
    """Compose a rotation by theta degrees around an SDK FrameTransformation axis."""
    return call(self, "rotate", theta, axis)


def _translate(self, translateX, translateY, translateZ):
    """Set the translation in the same coordinate unit as the point cloud."""
    return call(self, "translate", translateX, translateY, translateZ)


def _is_valid(self):
    """Return whether the transform differs from identity according to the SDK.

    This checks for a custom reference frame, not rotation orthonormality."""
    return call(self, "is_valid")


def _pose_to_string(self):
    """Return comma-separated x, y, z, q_w, q_x, q_y, q_z values."""
    return call(self, "to_string")


FrameTransformation.__rotate__ = _rotate
FrameTransformation.__translate__ = _translate
FrameTransformation.__is__valid__ = _is_valid
HandEyeTransformation.to_string = _pose_to_string

for _index, _name in enumerate(
    ["_UInt32", "_Int32", "_Int64", "_Float", "_Double", "_Bool", "_String"]
):
    setattr(PayloadMember, "Type_" + _name, _index)


class doubleArray3(FixedArray):
    """Mutable three-element double array."""

    def __init__(self):
        super().__init__()


class doubleMatrix3(FixedArray):
    """Mutable three-by-three double matrix."""

    def __init__(self):
        super().__init__(matrix=True)


def camera_intrinsics_to_wrapped(wrappedIntrinsics, intrinsics):
    """Copy intrinsics into the supplied wrappedIntrinsics output; return None."""
    return function("copy_intrinsics", wrappedIntrinsics, intrinsics)


def wrapped_to_camera_intrinsics(intrinsics, wrappedIntrinsics):
    """Copy wrappedIntrinsics into the supplied intrinsics output; return None."""
    return function("copy_intrinsics", intrinsics, wrappedIntrinsics)


def wrapped_to_frame_transformation(frameTransformation, wrappedFrameTransformation):
    """Copy wrappedFrameTransformation into frameTransformation; return None."""
    return function(
        "copy_frame_transformation", frameTransformation, wrappedFrameTransformation
    )


def frame_transformation_towrapped(frameTransformation, wrappedFrameTransformation):
    """Copy frameTransformation into wrappedFrameTransformation; return None."""
    return function(
        "copy_frame_transformation", wrappedFrameTransformation, frameTransformation
    )


GrayScale2DImage = array_type("GrayScale2DImage", ["data"], __name__)
Color2DImage = array_type("Color2DImage", ["data"], __name__)
DepthMap = array_type("DepthMap", ["data"], __name__)
UntexturedPointCloud = array_type("UntexturedPointCloud", ["data"], __name__)
UntexturedPointCloudWithNormals = array_type(
    "UntexturedPointCloudWithNormals", ["data"], __name__
)
TexturedPointCloud = array_type("TexturedPointCloud", ["vertices", "colors"], __name__)
TexturedPointCloudWithNormals = array_type(
    "TexturedPointCloudWithNormals", ["vertices", "colors", "normals"], __name__
)


class Frame2D(Proxy):
    """SDK Frame2D object, serialized for regular and free-threaded Python."""

    _native_name = "Frame2D"

    def image_size(self):
        """Return the frame's image Size in pixels."""
        return call(self, "image_size")

    def is_empty(self):
        """Return whether the SDK reports that the frame has no data."""
        return call(self, "is_empty")

    def color_type(self):
        """Return the ColorTypeOf2DCamera value for the captured image."""
        return call(self, "color_type")

    def frame_id(self):
        """Return the SDK capture frame identifier."""
        return call(self, "frame_id")

    def clear(self):
        """Release the data held by this frame."""
        return call(self, "clear")

    def get_gray_scale_image(self):
        """Return the frame's GrayScale2DImage container; data() copies pixels to NumPy."""
        return call(self, "get_gray_scale_image")

    def get_color_image(self):
        """Return the frame's Color2DImage container; data() copies BGR pixels to NumPy."""
        return call(self, "get_color_image")


register(Frame2D)


class Frame3D(Proxy):
    """SDK Frame3D object, serialized for regular and free-threaded Python."""

    _native_name = "Frame3D"

    def image_size(self):
        """Return the frame's image Size in pixels."""
        return call(self, "image_size")

    def frame_id(self):
        """Return the SDK capture frame identifier."""
        return call(self, "frame_id")

    def is_empty(self):
        """Return whether the SDK reports that the frame has no data."""
        return call(self, "is_empty")

    def clear(self):
        """Release the data held by this frame."""
        return call(self, "clear")

    def get_untextured_point_cloud(self):
        """Return the frame's organized UntexturedPointCloud in the selected SDK unit."""
        return call(self, "get_untextured_point_cloud")

    def get_untextured_point_cloud_with_normals(self):
        """Return the organized UntexturedPointCloudWithNormals container."""
        return call(self, "get_untextured_point_cloud_with_normals")

    def get_depth_map(self):
        """Return the frame's DepthMap container with per-pixel Z coordinates."""
        return call(self, "get_depth_map")

    def get_orthogonal_depth_map(self):
        """Return ``[depth_map, x_scale, y_scale, x_offset, y_offset]``.

        The SDK supplies an orthogonal depth grid and its scale and offset values.
        """
        return call(self, "get_orthogonal_depth_map", sequence=list)

    def save_untextured_point_cloud(self, fileFormat, fileName, isOrganized=False):
        """Export this frame's point cloud with the SDK.

        :param fileFormat: A FileFormat_PLY, FileFormat_PCD, or FileFormat_CSV value.
        :param fileName: Destination filename.
        :param isOrganized: Preserve the image grid when the format supports it.
        :return: ErrorStatus; file errors are returned rather than printed.
        """
        return call(
            self, "save_untextured_point_cloud", fileFormat, fileName, isOrganized
        )

    def save_untextured_point_cloud_with_normals(
        self, fileFormat, fileName, isOrganized=False
    ):
        """Export this frame's point cloud with the SDK.

        :param fileFormat: A FileFormat_PLY, FileFormat_PCD, or FileFormat_CSV value.
        :param fileName: Destination filename.
        :param isOrganized: Preserve the image grid when the format supports it.
        :return: ErrorStatus; file errors are returned rather than printed.
        """
        return call(
            self,
            "save_untextured_point_cloud_with_normals",
            fileFormat,
            fileName,
            isOrganized,
        )

    @staticmethod
    def save_point_cloud(*args):
        """Export an explicit point-cloud container without capturing a frame.

        Arguments are ``(pointCloud, fileFormat, fileName, isOrganized=False,
        pointCloudUnit=CoordinateUnit_Millimeter)``. Pass the matching cloud type,
        including normals when using save_point_cloud_with_normals().
        :return: ErrorStatus from the SDK file writer.
        """
        with _api_lock:
            return _wrap(
                _backend.Frame3D.save_point_cloud(*[_unwrap(value) for value in args])
            )

    @staticmethod
    def save_point_cloud_with_normals(*args):
        """Export an explicit point-cloud container without capturing a frame.

        Arguments are ``(pointCloud, fileFormat, fileName, isOrganized=False,
        pointCloudUnit=CoordinateUnit_Millimeter)``. Pass the matching cloud type,
        including normals when using save_point_cloud_with_normals().
        :return: ErrorStatus from the SDK file writer.
        """
        with _api_lock:
            return _wrap(
                _backend.Frame3D.save_point_cloud_with_normals(
                    *[_unwrap(value) for value in args]
                )
            )


register(Frame3D)


class Frame2DAnd3D(Proxy):
    """SDK Frame2DAnd3D object, serialized for regular and free-threaded Python."""

    _native_name = "Frame2DAnd3D"

    def frame_2d(self):
        """Return the combined frame's Frame2D component."""
        return call(self, "frame_2d")

    def frame_3d(self):
        """Return the combined frame's Frame3D component."""
        return call(self, "frame_3d")

    def clear(self):
        """Release the data held by this frame."""
        return call(self, "clear")

    def get_textured_point_cloud(self):
        """Return the organized TexturedPointCloud container with XYZ and BGR data."""
        return call(self, "get_textured_point_cloud")

    def get_textured_point_cloud_with_normals(self):
        """Return the organized TexturedPointCloudWithNormals container."""
        return call(self, "get_textured_point_cloud_with_normals")

    def save_textured_point_cloud(self, fileFormat, fileName, isOrganized=False):
        """Export this frame's point cloud with the SDK.

        :param fileFormat: A FileFormat_PLY, FileFormat_PCD, or FileFormat_CSV value.
        :param fileName: Destination filename.
        :param isOrganized: Preserve the image grid when the format supports it.
        :return: ErrorStatus; file errors are returned rather than printed.
        """
        return call(
            self, "save_textured_point_cloud", fileFormat, fileName, isOrganized
        )

    def save_textured_point_cloud_with_normals(
        self, fileFormat, fileName, isOrganized=False
    ):
        """Export this frame's point cloud with the SDK.

        :param fileFormat: A FileFormat_PLY, FileFormat_PCD, or FileFormat_CSV value.
        :param fileName: Destination filename.
        :param isOrganized: Preserve the image grid when the format supports it.
        :return: ErrorStatus; file errors are returned rather than printed.
        """
        return call(
            self,
            "save_textured_point_cloud_with_normals",
            fileFormat,
            fileName,
            isOrganized,
        )

    @staticmethod
    def save_point_cloud(*args):
        """Export an explicit point-cloud container without capturing a frame.

        Arguments are ``(pointCloud, fileFormat, fileName, isOrganized=False,
        pointCloudUnit=CoordinateUnit_Millimeter)``. Pass the matching cloud type,
        including normals when using save_point_cloud_with_normals().
        :return: ErrorStatus from the SDK file writer.
        """
        with _api_lock:
            return _wrap(
                _backend.Frame2DAnd3D.save_point_cloud(
                    *[_unwrap(value) for value in args]
                )
            )

    @staticmethod
    def save_point_cloud_with_normals(*args):
        """Export an explicit point-cloud container without capturing a frame.

        Arguments are ``(pointCloud, fileFormat, fileName, isOrganized=False,
        pointCloudUnit=CoordinateUnit_Millimeter)``. Pass the matching cloud type,
        including normals when using save_point_cloud_with_normals().
        :return: ErrorStatus from the SDK file writer.
        """
        with _api_lock:
            return _wrap(
                _backend.Frame2DAnd3D.save_point_cloud_with_normals(
                    *[_unwrap(value) for value in args]
                )
            )


register(Frame2DAnd3D)


class HandEyeCalibration(Proxy):
    """SDK HandEyeCalibration object, serialized for regular and free-threaded Python."""

    _native_name = "HandEyeCalibration"

    def initialize_calibration(self, camera, mountingMode, boardModel):
        """Initialize calibration for a connected camera, mounting mode, and board model.

        Use the CameraMountingMode_* and CalibrationBoardModel_* class constants.
        :return: ErrorStatus.
        """
        return call(self, "initialize_calibration", camera, mountingMode, boardModel)

    def add_pose_and_detect(self, camera, poseData, color2DImage, timeoutMs=10000):
        """Record a robot pose, capture an image, and detect the calibration board.

        ``poseData`` is a HandEyeTransformation with translation in millimeters; ``color2DImage`` is an output
        Color2DImage. ``timeoutMs`` is measured in milliseconds.
        :return: ErrorStatus.
        """
        return call(
            self, "add_pose_and_detect", camera, poseData, color2DImage, timeoutMs
        )

    def calculate_extrinsics(self, camera, cameraToBase):
        """Fill cameraToBase with the calibrated HandEyeTransformation.

        The output depends on the mounting mode chosen at initialization.
        Its translation values use meters.
        :return: ErrorStatus.
        """
        return call(self, "calculate_extrinsics", camera, cameraToBase)

    def test_recognition(self, camera, testResult, timeoutMs=20000):
        """Capture and annotate board recognition in the output Color2DImage.

        ``timeoutMs`` is measured in milliseconds.
        :return: ErrorStatus.
        """
        return call(self, "test_recognition", camera, testResult, timeoutMs)

    def extract_current_image_first_corner(self, camera, corner, timeoutMs=20000):
        """Fill corner with the first detected board corner as a PointXYZ.

        ``timeoutMs`` is measured in milliseconds.
        :return: ErrorStatus.
        """
        return call(
            self, "extract_current_image_first_corner", camera, corner, timeoutMs
        )


register(HandEyeCalibration)
HandEyeCalibration.CameraMountingMode_EyeInHand = 0
HandEyeCalibration.CameraMountingMode_EyeToHand = 1
HandEyeCalibration.CalibrationBoardModel_BDB_5 = 0
HandEyeCalibration.CalibrationBoardModel_BDB_6 = 1
HandEyeCalibration.CalibrationBoardModel_BDB_7 = 2
HandEyeCalibration.CalibrationBoardModel_OCB_5 = 3
HandEyeCalibration.CalibrationBoardModel_OCB_10 = 4
HandEyeCalibration.CalibrationBoardModel_OCB_15 = 5
HandEyeCalibration.CalibrationBoardModel_OCB_20 = 6
HandEyeCalibration.CalibrationBoardModel_CGB_20 = 7
HandEyeCalibration.CalibrationBoardModel_CGB_35 = 8
HandEyeCalibration.CalibrationBoardModel_CGB_50 = 9
VectorCameraInfo = vector_type("VectorCameraInfo", CameraInfo, __name__)
EventInfos = vector_type("EventInfos", EventInfo, __name__)
Payload = vector_type("Payload", PayloadMember, __name__)


def get_point_cloud_after_mapping(*args):
    """Map a depth grid into the supplied output point cloud with SDK intrinsics.

    Accepted arguments are ``(depth, mask, intrinsics, cloud)`` for an
    UntexturedPointCloud, or ``(depth, mask, color, intrinsics, cloud)`` for a
    TexturedPointCloud. Nonzero grayscale mask pixels select depth samples.
    :return: ErrorStatus; the cloud is an output argument.
    """
    return function("get_point_cloud_after_mapping", *args)


def transform_point_cloud(coordinateTransformation, originalPointCloud):
    """Return a transformed point-cloud container without changing the input.

    ``coordinateTransformation`` is a FrameTransformation. Translation uses the
    same coordinate unit as the cloud. Pass the matching cloud type, including
    color or normals when required by this function.
    """
    return function(
        "transform_point_cloud", coordinateTransformation, originalPointCloud
    )


def transform_point_cloud_with_normals(coordinateTransformation, originalPointCloud):
    """Return a transformed point-cloud container without changing the input.

    ``coordinateTransformation`` is a FrameTransformation. Translation uses the
    same coordinate unit as the cloud. Pass the matching cloud type, including
    color or normals when required by this function.
    """
    return function(
        "transform_point_cloud_with_normals",
        coordinateTransformation,
        originalPointCloud,
    )


def transform_textured_point_cloud(
    coordinateTransformation, originalTexturedPointCloud
):
    """Return a transformed point-cloud container without changing the input.

    ``coordinateTransformation`` is a FrameTransformation. Translation uses the
    same coordinate unit as the cloud. Pass the matching cloud type, including
    color or normals when required by this function.
    """
    return function(
        "transform_textured_point_cloud",
        coordinateTransformation,
        originalTexturedPointCloud,
    )


def transform_textured_point_cloud_with_normals(
    coordinateTransformation, originalTexturedPointCloud
):
    """Return a transformed point-cloud container without changing the input.

    ``coordinateTransformation`` is a FrameTransformation. Translation uses the
    same coordinate unit as the cloud. Pass the matching cloud type, including
    color or normals when required by this function.
    """
    return function(
        "transform_textured_point_cloud_with_normals",
        coordinateTransformation,
        originalTexturedPointCloud,
    )


def get_transformation_params(camera):
    """Return the SDK Transformation for a connected camera."""
    return function("get_transformation_params", camera)


def _require(status, exception, message):
    if not status.is_ok():
        raise exception(
            f"{message}: {status.error_description} (code={status.error_code})"
        )


class _EventContext:
    """Share event registration across Camera copies without retaining their wrappers."""

    def __init__(self):
        self.callbacks = {}
        self.errors = deque()
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.thread = None
        self.owners = []


class Camera(Proxy):
    """Camera connection, SDK operations, and NumPy capture conveniences.

    ``Camera()`` requires explicit connect(). ``Camera(ip)`` remembers an IP and
    connects on context entry or first convenience capture/configuration.
    ``Camera(other_camera)`` shares the native connection and callback registry.
    Construction does not connect. Use a context manager or disconnect() to
    release a connection; close() is the same operation.

    SDK methods return ErrorStatus and never retry implicitly. Convenience
    methods raise the MechEyeError subclasses from mecheye.shared on failure.
    SDK access is serialized across camera instances; user code must synchronize
    writes to returned NumPy arrays and to its own callback state.
    """

    _native_name = "Camera"

    def __init__(self, *args):
        ip = args[0] if len(args) == 1 and isinstance(args[0], str) else None
        source = args[0] if len(args) == 1 and isinstance(args[0], Camera) else None
        super().__init__(*(() if ip is not None else args))
        self._ip = source.ip if source is not None else ip
        self._event_context = (
            source._event_context if source is not None else _EventContext()
        )
        self._callbacks = self._event_context.callbacks
        self._callback_errors = self._event_context.errors
        self._callback_lock = self._event_context.lock
        self._event_stop = self._event_context.stop
        with self._callback_lock:
            self._event_context.owners.append(weakref.ref(self))

    @staticmethod
    def discover_cameras(timeoutMs=5000):
        """Discover cameras on reachable interfaces without connecting.

        :param timeoutMs: Discovery timeout in milliseconds.
        :return: A VectorCameraInfo containing discovered device information.
        """
        return VectorCameraInfo(function("Camera_discover_cameras", timeoutMs))

    def connect(self, *args):
        """Connect using an IP address or CameraInfo and an optional timeout.

        Accepted forms are ``connect(ip)`` and ``connect(info)``, with an optional
        second positional ``timeoutMs`` argument (default 5000 milliseconds).
        The IP is remembered after a successful connection. No retries are performed.

        :return: ErrorStatus; inspect is_ok() before using the connection.
        """
        with _api_lock:
            result = call(self, "connect", *args)
            if result.is_ok() and args:
                self._ip = (
                    args[0].ip_address if isinstance(args[0], CameraInfo) else args[0]
                )
            return result

    def disconnect(self):
        """Disconnect and stop this connection's callback registrations.

        Camera copies share the connection, so disconnecting one also affects the others.
        This method can be called repeatedly.

        :return: None.
        """
        with _api_lock:
            result = call(self, "disconnect")
            with self._callback_lock:
                self._callbacks.clear()
                self._event_stop.set()
            return result

    close = disconnect

    @property
    def connected(self):
        """Whether the shared native camera connection is currently active."""
        return call(self, "connected")

    @property
    def ip(self):
        """The optional or last successfully connected IP address, or None."""
        with _api_lock:
            return self._ip

    def _ensure_connected(self):
        if self.connected:
            return
        if self._ip is None:
            raise MechEyeConnectionError(
                "The camera is not connected; call connect(ip) first"
            )
        _require(
            self.connect(self._ip), MechEyeConnectionError, "Camera connection failed"
        )

    def __enter__(self):
        with _api_lock:
            self._ensure_connected()
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    @property
    def device_info(self):
        """Read device metadata into a new Python dictionary.

        Includes model, device name, serial number, SDK and firmware versions,
        IP address, subnet mask, assignment method, port, and support information.

        :raises mecheye.shared.MechEyeConnectionError: The SDK cannot read the device information.
        """
        with _api_lock:
            info = CameraInfo()
            _require(
                self.get_camera_info(info),
                MechEyeConnectionError,
                "Failed to read device information",
            )
            return {
                "device_type": "mecheye",
                "model": info.model,
                "device_name": info.device_name,
                "serial_number": info.serial_number,
                "firmware_version": info.firmware_version.to_string(),
                "hardware_version": info.hardware_version.to_string(),
                "sdk_version": shared.get_api_version_info(),
                "ip": info.ip_address,
                "platform": f"Platform{chr(65 + info.platform)}",
                "subnet_mask": info.subnet_mask,
                "ip_assignment_method": shared.ip_assignment_method_to_string(
                    info.ip_assignment_method
                ),
                "port": info.port,
                "supported": info.supported,
                "last_supported_version": info.last_supported_version.to_string(),
            }

    @property
    def camera_parameters(self):
        """Read camera matrices, distortion coefficients, and depth-to-texture transform.

        The returned dictionary contains ``depth`` and ``texture`` dictionaries with
        flat 3-by-3 ``intrinsic_matrix`` values and five distortion coefficients.
        ``T_texture_camera_depth_camera_matrix_mm`` is a 4-by-4 nested list.

        :raises mecheye.shared.MechEyeConnectionError: The SDK cannot read the intrinsics.
        """
        with _api_lock:
            intrinsics = CameraIntrinsics()
            _require(
                self.get_camera_intrinsics(intrinsics),
                MechEyeConnectionError,
                "Failed to read camera intrinsics",
            )

            def metadata(camera):
                m, d = (camera.camera_matrix, camera.camera_distortion)
                return {
                    "intrinsic_matrix": [m.fx, 0, m.cx, 0, m.fy, m.cy, 0, 0, 1],
                    "distortion_k1_k2_p1_p2_k3": [d.k1, d.k2, d.p1, d.p2, d.k3],
                }

            t = intrinsics.depth_to_texture
            matrix = [
                [t.rotation[row][col] for col in range(3)] + [t.translation[row]]
                for row in range(3)
            ]
            matrix.append([0, 0, 0, 1])
            return {
                "depth": metadata(intrinsics.depth),
                "texture": metadata(intrinsics.texture),
                "T_texture_camera_depth_camera_matrix_mm": matrix,
            }

    def configure_depth_source_2d_exposure(self, mode):
        """Set and verify the depth-source 2D exposure mode.

        :param mode: Either ``"timed"`` or ``"flash"``.
        :return: The requested mode after successful device readback.
        :raises ValueError: The mode is not supported.
        :raises mecheye.shared.MechEyeConnectionError: The camera cannot be connected.
        :raises mecheye.shared.MechEyeConfigurationError: Configuration or readback fails.
        """
        if mode not in {"timed", "flash"}:
            raise ValueError("mode must be timed or flash")
        with _api_lock:
            self._ensure_connected()
            user_set = self.current_user_set()
            name = Scanning2DDepthSourceExposureMode.name
            desired = "Timed" if mode == "timed" else "Flash"
            _require(
                user_set.set_enum_value(name, desired),
                MechEyeConfigurationError,
                "Failed to configure exposure",
            )
            status, actual = user_set.get_enum_value_string(name)
            _require(status, MechEyeConfigurationError, "Failed to read exposure mode")
            if actual != desired:
                raise MechEyeConfigurationError(
                    "Depth-source exposure mode readback mismatch"
                )
            return mode

    def capture_points(self, timeoutMs=10000):
        """Capture aligned grayscale and organized XYZ arrays in millimeters.

        Uses depth-source 2D and 3D capture, camera intrinsics, and SDK mapping.
        The camera model must support depth-source 2D capture. An optional constructor
        IP enables lazy connection; SDK capture errors are not retried.

        :param timeoutMs: Capture timeout in milliseconds.
        :return: ``(image, points)`` with owned NumPy buffers. ``image`` has shape
            ``(height, width)`` and dtype ``uint8``; ``points`` has shape
            ``(height, width, 3)`` and dtype ``float64``. All-zero SDK points become
            NaN triplets; non-finite coordinate components become NaN.
        :raises mecheye.shared.MechEyeConnectionError: Connection is unavailable.
        :raises mecheye.shared.MechEyeCaptureError: Capture, frame validation, or intrinsics fail.
        :raises mecheye.shared.MechEyePointCloudError: Mapping fails or produces an invalid grid.
        :raises mecheye.shared.MechEyeConfigurationError: Restoring the previous cloud unit fails.

        The previous cloud unit is restored after capture or mapping succeeds or fails.
        If restoration itself fails, that configuration error is raised.
        """
        from .area_scan_3d_camera_utils import image_to_gray

        with _api_lock:
            self._ensure_connected()
            status, previous = self.get_point_cloud_unit()
            _require(status, MechEyeCaptureError, "Failed to read point cloud unit")
            if previous != shared.CoordinateUnit_Millimeter:
                _require(
                    self.set_point_cloud_unit(shared.CoordinateUnit_Millimeter),
                    MechEyeCaptureError,
                    "Failed to set millimeter units",
                )
            try:
                frame = Frame2DAnd3D()
                _require(
                    self.capture_depth_source_2d_and_3d(frame, timeoutMs),
                    MechEyeCaptureError,
                    "Depth-source 2D and 3D capture failed",
                )
                frame2d, frame3d = (frame.frame_2d(), frame.frame_3d())
                if frame2d.is_empty() or frame3d.is_empty():
                    raise MechEyeCaptureError("The captured frame is empty")
                depth = frame3d.get_depth_map()
                if depth.is_empty():
                    raise MechEyeCaptureError("The depth map is empty")
                image = (
                    frame2d.get_gray_scale_image().data()
                    if frame2d.color_type() == ColorTypeOf2DCamera_Monochrome
                    else frame2d.get_color_image().data()
                )
                if image.shape[:2] != (depth.height(), depth.width()):
                    raise MechEyeCaptureError(
                        "The depth-source image does not match the depth grid"
                    )
                intrinsics = CameraIntrinsics()
                _require(
                    self.get_camera_intrinsics(intrinsics),
                    MechEyeCaptureError,
                    "Failed to read camera intrinsics",
                )
                mask = GrayScale2DImage()
                mask.resize(depth.width(), depth.height())
                call(mask, "fill_gray", 255)
                cloud = UntexturedPointCloud()
                _require(
                    get_point_cloud_after_mapping(depth, mask, intrinsics, cloud),
                    MechEyePointCloudError,
                    "Point cloud mapping failed",
                )
                if (
                    cloud.is_empty()
                    or (cloud.height(), cloud.width()) != image.shape[:2]
                ):
                    raise MechEyePointCloudError(
                        "The point cloud does not match the depth-source image grid"
                    )
                return (image_to_gray(image), call(cloud, "normalized_points"))
            finally:
                if previous != shared.CoordinateUnit_Millimeter:
                    _require(
                        self.set_point_cloud_unit(previous),
                        MechEyeConfigurationError,
                        "Failed to restore point cloud unit",
                    )

    def pop_callback_errors(self):
        """Return and clear pending callback exceptions in registration context order.

        Camera copies share the error queue. Exceptions are retained without printing.
        :return: A new list of exceptions.
        """
        with self._callback_lock:
            errors = list(self._callback_errors)
            self._callback_errors.clear()
            return errors

    def set_heartbeat_interval(self, timeIntervalMs):
        """Set the SDK heartbeat interval in milliseconds; return ErrorStatus."""
        return call(self, "set_heartbeat_interval", timeIntervalMs)

    def get_camera_info(self, info):
        """Fill the supplied CameraInfo with device metadata; return ErrorStatus."""
        return call(self, "get_camera_info", info)

    def get_camera_status(self, status):
        """Fill the supplied CameraStatus with temperatures; return ErrorStatus."""
        return call(self, "get_camera_status", status)

    def get_camera_resolutions(self, resolutions):
        """Fill the supplied CameraResolutions with image sizes; return ErrorStatus."""
        return call(self, "get_camera_resolutions", resolutions)

    def current_user_set(self):
        """Return a handle to the current device UserSet.

        Read and write operations on the handle report SDK status values. Obtain a new
        handle after reconnecting or changing the selected configuration.
        """
        return call(self, "current_user_set")

    def user_set_manager(self):
        """Return the connection's UserSetManager for selecting and persisting user sets."""
        return call(self, "user_set_manager")

    def capture_3d(self, frame3D, timeoutMs=5000):
        """Capture a 3D frame into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        """
        return call(self, "capture_3d", frame3D, timeoutMs)

    def capture_3d_with_normal(self, frame3D, timeoutMs=10000):
        """Capture a 3D frame with normals into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        """
        return call(self, "capture_3d_with_normal", frame3D, timeoutMs)

    def capture_2d(self, frame2D, timeoutMs=5000):
        """Capture a 2D frame into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        """
        return call(self, "capture_2d", frame2D, timeoutMs)

    def capture_depth_source_2d(self, frame2D, timeoutMs=5000):
        """Capture the depth-source 2D frame into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        """
        return call(self, "capture_depth_source_2d", frame2D, timeoutMs)

    def capture_2d_and_3d(self, frame2DAnd3D, timeoutMs=10000):
        """Capture a combined texture 2D and 3D frame into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        """
        return call(self, "capture_2d_and_3d", frame2DAnd3D, timeoutMs)

    def capture_depth_source_2d_and_3d(self, frame2DAnd3D, timeoutMs=10000):
        """Capture a combined depth-source 2D and 3D frame into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        """
        return call(self, "capture_depth_source_2d_and_3d", frame2DAnd3D, timeoutMs)

    def capture_2d_and_3d_with_normal(self, frame2DAnd3D, timeoutMs=15000):
        """Capture a combined 2D and 3D frame with normals into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        """
        return call(self, "capture_2d_and_3d_with_normal", frame2DAnd3D, timeoutMs)

    def capture_stereo_2d(self, left, right, isRectified=False, timeoutMs=5000):
        """Capture left and right stereo 2D frames into the supplied output container.

        ``timeoutMs`` is measured in milliseconds. The camera must already be connected;
        this SDK operation does not initiate a connection or retry a failure.
        :return: ErrorStatus; only read output data after is_ok() succeeds.
        :param isRectified: Whether the SDK should rectify the stereo images.
        """
        return call(self, "capture_stereo_2d", left, right, isRectified, timeoutMs)

    def set_point_cloud_unit(self, unit):
        """Set CoordinateUnit_Millimeter or CoordinateUnit_Meter; return ErrorStatus."""
        return call(self, "set_point_cloud_unit", unit)

    def save_virtual_device_file(self, fileName):
        """Save a virtual-device file at fileName through the SDK; return ErrorStatus."""
        return call(self, "save_virtual_device_file", fileName)

    def get_camera_intrinsics(self, wrappedIntrinsics):
        """Fill the supplied CameraIntrinsics with calibration values; return ErrorStatus."""
        return call(self, "get_camera_intrinsics", wrappedIntrinsics)

    def get_point_cloud_unit(self):
        """Return ``[status, unit]`` for the SDK's current CoordinateUnit selection."""
        return call(self, "get_point_cloud_unit", sequence=list)


register(Camera)
cvar = SimpleNamespace()
for _name, _metadata in _backend.descriptors.items():
    _namespace = {
        "__module__": __name__,
        "thisown": Ownership.thisown,
        "__doc__": f"Descriptor for the {_metadata['name']} camera parameter.\n\nUse name with UserSet getters/setters. Constants describe the SDK type, enum\nentries, units, and nominal limits; check device-specific availability before use.",
    }
    for _key, _value in _metadata.items():
        if _key == "range":

            def _range(value=_value):
                """Return an independent copy of the descriptor's nominal range."""
                with _api_lock:
                    return _wrap(_backend.clone_value(value))

            _namespace[_key] = staticmethod(_range)
        elif _key in {"step", "max_size"}:
            _method = lambda value=_value: value
            _method.__doc__ = (
                "Return the nominal increment."
                if _key == "step"
                else "Return the nominal maximum number of array elements."
            )
            _namespace[_key] = staticmethod(_method)
        else:
            _namespace[_key] = _value
            setattr(cvar, f"{_name}_{_key}", _value)
    globals()[_name] = type(_name, (), _namespace)


class EventCallbackBase(Ownership):
    """Override run(), process_event(), or process_event_with_payload() to receive events."""

    def run(self, event):
        """Override to handle an event identifier from the four-argument registration form."""
        pass

    def process_event(self, eventData):
        """Override to receive a copied EventData value on the dispatch thread."""
        pass

    def process_event_with_payload(self, eventData, extraPayload):
        """Override to receive copied EventData and Payload values on the dispatch thread.

        When overridden, this method takes precedence over process_event(). Values
        remain readable while a capture is running; synchronize your own shared state.
        """
        pass

    def __disown__(self):
        return self


def _dispatch_events(owner_ref, stop):
    """Run callbacks outside SDK calls, retaining only a live shared-connection wrapper."""
    while not stop.wait(0.01):
        owner = owner_ref()
        if owner is None:
            return
        if isinstance(owner, Camera):
            camera = owner
            context = owner._event_context
        else:
            context = owner
            with context.lock:
                live = []
                camera = None
                for ref in context.owners:
                    candidate = ref()
                    if candidate is not None:
                        live.append(ref)
                        if camera is None:
                            camera = candidate
                context.owners[:] = live
                candidate = None
            if camera is None:
                return
        try:
            pending = _snapshot(_wrap(camera._native.poll_events()))
            with context.lock:
                registrations = tuple(context.callbacks.items())
            for data, payload in pending:
                for event, (callback, legacy) in registrations:
                    if event not in {CameraEvent.CAMERA_EVENT_ALL, data.event_id}:
                        continue
                    try:
                        if legacy:
                            callback.run(data.event_id)
                        elif (
                            type(callback).process_event_with_payload
                            is not EventCallbackBase.process_event_with_payload
                        ):
                            snapshot_payload = list.__new__(Payload)
                            list.__init__(snapshot_payload, payload)
                            snapshot_payload._capacity = len(payload)
                            snapshot_payload._event_lock = threading.RLock()
                            callback.process_event_with_payload(data, snapshot_payload)
                        else:
                            callback.process_event(data)
                    except BaseException as exc:
                        with context.lock:
                            context.errors.append(exc)
        except BaseException as exc:
            with context.lock:
                context.errors.append(exc)
        finally:
            del camera, context, owner


class CameraEvent(Ownership):
    """Manage SDK event registration and dispatch Python callbacks safely."""

    CAMERA_EVENT_NONE = 0
    CAMERA_EVENT_DISCONNECTED = 1
    CAMERA_EVENT_EXPOSURE_END = 36878
    CAMERA_EVENT_ALL = 65535

    @staticmethod
    def get_supported_events(camera, eventInfos):
        """Fill eventInfos with supported EventInfo values; return ErrorStatus."""
        with _api_lock:
            status, infos = function("get_supported_events", camera)
            eventInfos[:] = infos
            return status

    def register_camera_event_callback(self, *args):
        """Register a callback for a connected camera and event identifier.

        Use ``(camera, event, callback)`` with EventCallbackBase.process_event() or
        process_event_with_payload(). The four-argument form
        ``(camera, callback, user, event)`` calls run(event_id); user is accepted
        but is not forwarded. CAMERA_EVENT_ALL subscribes to all events.

        Event values are copied before Python dispatch. Callback exceptions are
        retained by Camera.pop_callback_errors(). SDK calls in callbacks wait for
        other SDK calls to finish.
        :return: ErrorStatus.
        :raises TypeError: The argument count or camera type is invalid.
        """
        if len(args) == 3:
            camera, event, callback = args
            legacy = False
        elif len(args) == 4:
            camera, callback, user, event = args
            legacy = True
        else:
            raise TypeError(
                "Expected camera, event, callback or camera, callback, user, events"
            )
        if not isinstance(camera, Camera):
            raise TypeError("Expected Camera")
        if not isinstance(callback, EventCallbackBase):
            return ErrorStatus(
                ErrorStatus.MMIND_STATUS_INVALID_CALLBACKFUNC,
                "Expected EventCallbackBase",
            )
        with _api_lock:
            status = function("register_event", camera, event)
            if status.is_ok():
                with camera._callback_lock:
                    camera._callbacks[event] = (callback, legacy)
                    camera._event_stop.clear()
                context = camera._event_context
                if context.thread is None or not context.thread.is_alive():
                    context.thread = threading.Thread(
                        target=_dispatch_events,
                        args=(weakref.ref(context), context.stop),
                        name="MechEye events",
                        daemon=True,
                    )
                    context.thread.start()
            return status

    def unregister_camera_event_callback(self, camera, event):
        """Unregister an event, or all events with CAMERA_EVENT_ALL; return ErrorStatus."""
        with _api_lock:
            status = function("unregister_event", camera, event)
            if status.is_ok():
                with camera._callback_lock:
                    if event == self.CAMERA_EVENT_ALL:
                        camera._callbacks.clear()
                    else:
                        camera._callbacks.pop(event, None)
                    if not camera._callbacks:
                        camera._event_stop.set()
            return status


__all__ = [
    name
    for name in globals()
    if not name.startswith("_")
    and name
    not in {
        "deque",
        "SimpleNamespace",
        "threading",
        "time",
        "weakref",
        "np",
        "Proxy",
        "Ownership",
        "FixedArray",
        "call",
        "function",
        "register",
        "value_type",
        "array_type",
        "vector_type",
    }
]
