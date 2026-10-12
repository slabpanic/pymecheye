"""Serialize SDK object access and adapt native values to the public Python API."""

from __future__ import annotations

from functools import wraps
import operator
import threading

import numpy as np

from . import _native

_backend = _native.sdk
_api_lock = threading.RLock()
_types: dict[type, type] = {}


def _unwrap(value):
    if isinstance(value, Proxy):
        return value._read_native()
    if isinstance(value, FixedArray):
        return value._read()
    if isinstance(value, (list, tuple)):
        return [_unwrap(item) for item in value]
    if isinstance(value, dict):
        return {key: _unwrap(item) for key, item in value.items()}
    return value


def _wrap(value, owner=None):
    cls = _types.get(type(value))
    if cls is not None:
        result = object.__new__(cls)
        object.__setattr__(result, "_native", value)
        object.__setattr__(result, "_owner", owner)
        object.__setattr__(result, "_generation", 0)
        return result
    if isinstance(value, tuple):
        return tuple(_wrap(item, owner) for item in value)
    if isinstance(value, list):
        return [_wrap(item, owner) for item in value]
    if isinstance(value, dict):
        return {key: _wrap(item, owner) for key, item in value.items()}
    return value


def register(cls):
    native_type = getattr(_backend, cls._native_name)
    _types[native_type] = cls
    return cls


def call(obj, method, *args, sequence=None):
    with _api_lock:
        result = getattr(obj._read_native(), method)(*[_unwrap(arg) for arg in args])
        result = _wrap(result, obj)
        if sequence is list:
            return list(result)
        return result


def function(name, *args):
    with _api_lock:
        return _wrap(getattr(_backend, name)(*[_unwrap(arg) for arg in args]))


class Ownership:
    """Keep the SDK wrapper's ownership attribute while Python manages native lifetimes."""

    @property
    def thisown(self):
        """Retained ownership flag; Python continues to manage native object lifetimes."""
        return getattr(self, "_thisown", True)

    @thisown.setter
    def thisown(self, value):
        self._thisown = bool(value)


class Proxy(Ownership):
    """Retain native ownership and lock field access, including nested pixel references."""

    _native_name = ""
    _fields: tuple[str, ...] = ()

    def __init__(self, *args):
        with _api_lock:
            object.__setattr__(
                self,
                "_native",
                getattr(_backend, self._native_name)(*[_unwrap(arg) for arg in args]),
            )
            object.__setattr__(self, "_owner", None)
            object.__setattr__(self, "_generation", 0)

    def _read_native(self):
        if "_snapshot_fields" in self.__dict__:
            with self._snapshot_lock:
                result = getattr(_backend, self._native_name)()
                for name, value in self._snapshot_fields.items():
                    setattr(result, name, _unwrap(value))
                return result
        element = self.__dict__.get("_element")
        if element is None:
            return self._native
        array, index, generation, path = element
        if generation != array._generation:
            raise ReferenceError("The pixel reference expired after resize or release")
        value = array._native.element(index)
        for field in path:
            value = getattr(value, field)
        return value

    def _get_field(self, name):
        if "_snapshot_fields" in self.__dict__:
            with self._snapshot_lock:
                return self._snapshot_fields[name]
        with _api_lock:
            value = getattr(self._read_native(), name)
            if name in {"rotation", "translation"}:
                from .area_scan_3d_camera import doubleArray3, doubleMatrix3

                cls = doubleMatrix3 if name == "rotation" else doubleArray3
                result = object.__new__(cls)
                FixedArray.__init__(result, self, name)
                return result
            result = _wrap(value, self)
            if isinstance(result, Proxy) and "_element" in self.__dict__:
                array, index, generation, path = self._element
                object.__setattr__(
                    result, "_element", (array, index, generation, path + (name,))
                )
            return result

    def _set_field(self, name, value):
        if "_snapshot_fields" in self.__dict__:
            with self._snapshot_lock:
                native = self._read_native()
                setattr(native, name, _unwrap(value))
                self._snapshot_fields[name] = _snapshot(_wrap(getattr(native, name)))
                return
        with _api_lock:
            if "_element" not in self.__dict__:
                setattr(self._native, name, _unwrap(value))
                return
            array, index, generation, path = self._element
            if generation != array._generation:
                raise ReferenceError(
                    "The pixel reference expired after resize or release"
                )
            root = array._native.element(index)
            target = root
            for field in path:
                target = getattr(target, field)
            setattr(target, name, _unwrap(value))
            array._native.set_element(index, root)

    @property
    def thisown(self):
        """Ownership is managed by Python and cannot detach the native resource."""
        return True

    @thisown.setter
    def thisown(self, value):
        pass


_VALUE_DOCS = {
    "ErrorStatus": "Result of an SDK operation. Zero error_code means success; nonzero codes carry an error_description. Use is_ok() before reading output arguments.",
    "Size": "Integer width and height of an image or region, in pixels.",
    "SizeF": "Floating-point width and height reported by the SDK.",
    "ROI": "Rectangular image region in pixels: upper-left X/Y coordinates, width, and height.",
    "ProfileROI": "Shared floating-point region description with an X-axis center, width, and height. This value type does not provide profiler capture operations.",
    "PointXYZ": "Three floating-point coordinates in the point cloud's selected SDK unit.",
    "RangeFloat": "Mutable floating-point minimum and maximum bounds.",
    "RangeInt": "Mutable integer minimum and maximum bounds.",
    "RangeDouble": "Mutable double-precision minimum and maximum bounds.",
    "FrameTransformation": "Rigid transformation with a 3-by-3 rotation and three-element translation. Translation uses the same unit as the transformed coordinates; rotation helpers accept degrees.",
    "Transformation": "Camera transformation containing a 3-by-3 rotation and three-element translation.",
    "CameraIntrinsics": "Calibration for the texture and depth cameras, including the depth-to-texture rigid transformation.",
    "CameraInfo": "Discovered or connected camera metadata, including identity, network settings, versions, and support information.",
    "DeviceTemperature": "CPU and projector temperature measurements in degrees Celsius.",
    "CameraStatus": "Camera status containing a DeviceTemperature measurement.",
    "CameraMatrix": "Pinhole calibration with focal lengths fx/fy and principal point cx/cy, in pixels.",
    "CameraDistortion": "Camera distortion coefficients in k1, k2, p1, p2, k3 order.",
    "Intrinsics2DCamera": "CameraMatrix and CameraDistortion for one 2D camera.",
    "CameraResolutions": "Texture and depth image sizes, in pixels.",
    "Gray": "A grayscale pixel with one unsigned 8-bit intensity.",
    "ColorBGR": "A color pixel with unsigned 8-bit blue, green, and red channels.",
    "PointZ": "A per-pixel depth value in the selected SDK coordinate unit.",
    "NormalVector": "Surface-normal X/Y/Z components and curvature.",
    "PointXYZWithNormals": "A PointXYZ coordinate and its NormalVector.",
    "PointXYZBGR": "XYZ coordinates and unsigned 8-bit BGR/alpha channels, with packed rgb access.",
    "PointXYZBGRWithNormals": "A PointXYZBGR coordinate/color value and its NormalVector.",
    "EventData": "Copied event metadata: identifier, name, SDK timestamp, and capture frame identifier.",
    "EventInfo": "The name and identifier of a supported camera event.",
    "PayloadMember": "Named event payload with a ``Type_*`` discriminator and a MemberValue. Read the union field matching type.",
    "MemberValue": "Event payload union. Read only the numeric, boolean, or string field selected by PayloadMember.type.",
    "HandEyeTransformation": "Translation and quaternion in x, y, z, q_w, q_x, q_y, q_z order. Robot-pose translations use millimeters; calibrated extrinsic translations use meters.",
}
_FIELD_DOCS = {
    "error_code": "SDK integer error code; zero indicates success.",
    "error_description": "SDK explanation of the operation result.",
    "width": "Width in the unit described by this value type.",
    "height": "Height in the unit described by this value type.",
    "upper_left_x": "Horizontal pixel coordinate of the region's upper-left corner.",
    "upper_left_y": "Vertical pixel coordinate of the region's upper-left corner.",
    "x_axis_center": "Region center along the SDK X axis.",
    "min": "Lower bound of the range.",
    "max": "Upper bound of the range.",
    "x": "X coordinate or translation in this value type's unit.",
    "y": "Y coordinate or translation in this value type's unit.",
    "z": "Z coordinate or depth in this value type's unit.",
    "rotation": "Mutable 3-by-3 rotation matrix accessed with row and column indices.",
    "translation": "Mutable three-element translation vector.",
    "texture": "Texture-camera calibration or image size, depending on the owning type.",
    "depth": "Depth-camera calibration or image size, depending on the owning type.",
    "depth_to_texture": "Rigid transformation from depth-camera to texture-camera coordinates.",
    "model": "Camera model identifier.",
    "device_name": "User-assigned camera name.",
    "serial_number": "Device serial number.",
    "platform": "SDK ``Platform_*`` hardware platform value.",
    "hardware_version": "Hardware Version value.",
    "firmware_version": "Firmware Version value.",
    "ip_address": "Camera IP address.",
    "subnet_mask": "Camera IPv4 subnet mask.",
    "ip_assignment_method": "SDK ``IpAssignmentMethod_*`` value.",
    "port": "Device communication port.",
    "supported": "Whether the SDK reports this camera version as supported.",
    "last_supported_version": "Last supported SDK Version reported for the device.",
    "cpu_temperature": "CPU temperature in degrees Celsius.",
    "projector_temperature": "Projector temperature in degrees Celsius.",
    "temperature": "DeviceTemperature measurement.",
    "fx": "Horizontal focal length in pixels.",
    "fy": "Vertical focal length in pixels.",
    "cx": "Horizontal principal-point coordinate in pixels.",
    "cy": "Vertical principal-point coordinate in pixels.",
    "k1": "First radial distortion coefficient.",
    "k2": "Second radial distortion coefficient.",
    "k3": "Third radial distortion coefficient.",
    "p1": "First tangential distortion coefficient.",
    "p2": "Second tangential distortion coefficient.",
    "camera_distortion": "CameraDistortion coefficients.",
    "camera_matrix": "CameraMatrix intrinsic parameters.",
    "gray": "Unsigned 8-bit grayscale intensity.",
    "b": "Unsigned 8-bit blue channel.",
    "g": "Unsigned 8-bit green channel.",
    "r": "Unsigned 8-bit red channel.",
    "a": "Unsigned 8-bit alpha channel.",
    "rgb": "Packed SDK color representation.",
    "curvature": "Curvature reported by the SDK normal estimator.",
    "point": "Nested PointXYZ coordinate.",
    "normal": "Nested NormalVector.",
    "color_point": "Nested PointXYZBGR coordinate and color.",
    "event_id": "SDK event identifier.",
    "event_name": "SDK event name.",
    "timestamp": "SDK event occurrence timestamp.",
    "frame_id": "Capture frame identifier associated with this event.",
    "name": "Payload member name.",
    "type": "PayloadMember.``Type_*`` discriminator.",
    "value": "MemberValue payload union.",
    "uint_32value": "Unsigned 32-bit payload value; use when type is Type__UInt32.",
    "int_32value": "Signed 32-bit payload value; use when type is Type__Int32.",
    "int_64value": "Signed 64-bit payload value; use when type is Type__Int64.",
    "float_value": "Single-precision payload value; use when type is Type__Float.",
    "double_value": "Double-precision payload value; use when type is Type__Double.",
    "bool_value": "Boolean payload value; use when type is Type__Bool.",
    "string_value": "String payload value; use when type is Type__String.",
    "q_w": "Quaternion scalar component.",
    "q_x": "Quaternion X component.",
    "q_y": "Quaternion Y component.",
    "q_z": "Quaternion Z component.",
}
_ARRAY_DOCS = {
    "GrayScale2DImage": (
        "Organized grayscale image.",
        {"data": "Return an owned uint8 array with shape (height, width)."},
    ),
    "Color2DImage": (
        "Organized BGR color image.",
        {"data": "Return an owned uint8 BGR array with shape (height, width, 3)."},
    ),
    "DepthMap": (
        "Organized SDK depth grid.",
        {"data": "Return an owned float32 Z array with shape (height, width)."},
    ),
    "UntexturedPointCloud": (
        "Organized XYZ point cloud in the selected SDK coordinate unit.",
        {"data": "Return an owned float32 XYZ array with shape (height, width, 3)."},
    ),
    "UntexturedPointCloudWithNormals": (
        "Organized XYZ point cloud with surface normals.",
        {
            "data": "Return an owned float32 array with shape (height, width, 7), in x, y, z, normal-x, normal-y, normal-z, curvature order."
        },
    ),
    "TexturedPointCloud": (
        "Organized XYZ point cloud with BGR texture.",
        {
            "vertices": "Return an owned float32 XYZ array with shape (height, width, 3).",
            "colors": "Return an owned uint8 BGR array with shape (height, width, 3).",
        },
    ),
    "TexturedPointCloudWithNormals": (
        "Organized XYZ point cloud with BGR texture and surface normals.",
        {
            "vertices": "Return an owned float32 XYZ array with shape (height, width, 3).",
            "colors": "Return an owned uint8 BGR array with shape (height, width, 3).",
            "normals": "Return an owned float32 array with shape (height, width, 4), containing normal X/Y/Z and curvature.",
        },
    ),
}


def value_type(name, fields, module):
    """Generate a documented mutable SDK value class and its field properties."""
    namespace = {
        "_native_name": name,
        "_fields": tuple(fields),
        "__module__": module,
        "__doc__": _VALUE_DOCS[name]
        + "\n\nField access is serialized; nested values retain native ownership.",
    }
    for field in fields:
        namespace[field] = property(
            lambda self, field=field: self._get_field(field),
            lambda self, value, field=field: self._set_field(field, value),
            doc=_FIELD_DOCS[field],
        )
    return register(type(name, (Proxy,), namespace))


class FixedArray(Ownership):
    """Provide mutable, bounds-checked views of small transformation matrices."""

    def __init__(self, parent=None, field=None, row=None, matrix=False):
        self._parent = parent
        self._field = field
        self._row = row
        self._local = [[0.0] * 3 for _ in range(3)] if matrix else [0.0] * 3

    def _read(self):
        with _api_lock:
            value = (
                self._local
                if self._parent is None
                else getattr(self._parent._read_native(), self._field)
            )
            return value if self._row is None else value[self._row]

    def __len__(self):
        return 3

    def __getitem__(self, index):
        index = operator.index(index)
        if not 0 <= index < 3:
            raise IndexError("Index must be between 0 and 2")
        with _api_lock:
            result = self._read()[index]
            if isinstance(result, list):
                from .area_scan_3d_camera import doubleArray3

                row = object.__new__(doubleArray3)
                if self._parent is None:
                    FixedArray.__init__(row)
                    row._local = result
                else:
                    FixedArray.__init__(row, self._parent, self._field, index)
                return row
            return result

    def __setitem__(self, index, value):
        index = operator.index(index)
        if not 0 <= index < 3:
            raise IndexError("Index must be between 0 and 2")
        with _api_lock:
            if self._parent is None:
                self._local[index] = _unwrap(value)
                return
            snapshot = getattr(self._parent._read_native(), self._field)
            target = snapshot if self._row is None else snapshot[self._row]
            target[index] = _unwrap(value)
            self._parent._set_field(self._field, snapshot)

    @property
    def data(self):
        """Return the mutable three-element view; assign exactly three elements or rows."""
        return self

    @data.setter
    def data(self, value):
        with _api_lock:
            values = list(_unwrap(value))
            if len(values) != 3:
                raise ValueError("Expected three elements")
            for index, item in enumerate(values):
                self[index] = item


class Array2D(Proxy):
    """Own SDK data and return independent NumPy copies, with the documented layouts."""

    def width(self):
        """Return the grid width in pixels."""
        return call(self, "width")

    def height(self):
        """Return the grid height in pixels."""
        return call(self, "height")

    def is_empty(self):
        """Return whether the grid has no elements."""
        return call(self, "is_empty")

    def resize(self, width, height):
        """Resize the grid to width by height pixels.

        Existing pixel references expire if the dimensions change. NumPy copies remain
        valid independently of the grid.
        """
        with _api_lock:
            old = (self.width(), self.height())
            result = call(self, "resize", width, height)
            if old != (self.width(), self.height()):
                self._generation += 1
            return result

    def release(self):
        """Release native grid storage and invalidate existing pixel references."""
        with _api_lock:
            call(self, "release")
            self._generation += 1

    def clone(self):
        """Return an independent SDK grid with a deep copy of the stored values."""
        return call(self, "clone")

    def at(self, row, col):
        """Return a mutable pixel reference at row and col.

        :raises IndexError: A coordinate is outside the grid.
        :raises ReferenceError: Later access follows a resize or release that expired the reference.
        """
        with _api_lock:
            row, col = operator.index(row), operator.index(col)
            if not 0 <= row < self.height() or not 0 <= col < self.width():
                raise IndexError("Invalid pixel coordinates")
            return self[row * self.width() + col]

    def __getitem__(self, index):
        index = operator.index(index)
        with _api_lock:
            if not 0 <= index < self.width() * self.height():
                raise IndexError("Invalid pixel index")
            result = _wrap(self._native.element(index), self)
            object.__setattr__(result, "_element", (self, index, self._generation, ()))
            return result

    def _array(self, name):
        with _api_lock:
            if self.is_empty():
                return np.zeros(1)
            return call(self, name)


def array_type(name, accessors, module):
    """Generate a documented grid class with independently owned NumPy accessors."""
    summary, docs = _ARRAY_DOCS[name]
    namespace = {
        "_native_name": name,
        "__module__": module,
        "__doc__": summary
        + "\n\nNumPy accessors copy data; empty accessors return a float64 zero array of shape (1,).\nPixel references expire after a size-changing resize or release.",
    }
    for accessor in accessors:
        namespace[accessor] = lambda self, accessor=accessor: self._array(accessor)
        namespace[accessor].__doc__ = (
            docs[accessor]
            + "\n\nAn empty grid returns a float64 zero array of shape (1,)."
        )
    return register(type(name, (Array2D,), namespace))


def _snapshot(value):
    """Copy event values into Python-owned fields that do not wait for SDK operations."""
    if isinstance(value, Proxy):
        fields = {
            name: _snapshot(_wrap(getattr(value._native, name), value))
            for name in value._fields
        }
        object.__setattr__(value, "_snapshot_fields", fields)
        object.__setattr__(value, "_snapshot_lock", threading.RLock())
        return value
    if isinstance(value, tuple):
        return tuple(_snapshot(item) for item in value)
    if isinstance(value, list):
        return [_snapshot(item) for item in value]
    return value
