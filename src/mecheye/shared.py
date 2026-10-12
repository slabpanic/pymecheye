"""Shared SDK types, status values, parameters, and user-set interfaces."""

from __future__ import annotations
import math
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
)
from ._containers import SwigPyIterator, MechEyeMapStringInt, vector_type

PI = math.pi
CoordinateUnit_Millimeter = 0
CoordinateUnit_Meter = 1
FileFormat_PLY = 0
FileFormat_PCD = 1
FileFormat_CSV = 2
IpAssignmentMethod_Unknown = 0
IpAssignmentMethod_DHCP = 4
IpAssignmentMethod_Static = 5
IpAssignmentMethod_LLA = 6
for _index, _letter in enumerate("ABCDEFGH"):
    globals()[f"Platform_PLATFORM_{_letter}"] = _index
ErrorStatus = value_type("ErrorStatus", ["error_code", "error_description"], __name__)
Size = value_type("Size", ["width", "height"], __name__)
SizeF = value_type("SizeF", ["width", "height"], __name__)
ROI = value_type("ROI", ["upper_left_x", "upper_left_y", "width", "height"], __name__)
ProfileROI = value_type("ProfileROI", ["x_axis_center", "width", "height"], __name__)
PointXYZ = value_type("PointXYZ", ["x", "y", "z"], __name__)
RangeFloat = value_type("RangeFloat", ["min", "max"], __name__)
RangeInt = value_type("RangeInt", ["min", "max"], __name__)
RangeDouble = value_type("RangeDouble", ["min", "max"], __name__)
FrameTransformation = value_type(
    "FrameTransformation", ["rotation", "translation"], __name__
)
ErrorStatus.is_ok = lambda self: call(self, "is_ok")
ErrorStatus.MMIND_STATUS_SUCCESS = 0
ErrorStatus.MMIND_STATUS_INVALID_DEVICE = -1
ErrorStatus.MMIND_STATUS_DEVICE_OFFLINE = -2
ErrorStatus.MMIND_STATUS_NO_SUPPORT_ERROR = -3
ErrorStatus.MMIND_STATUS_OUT_OF_RANGE_ERROR = -4
ErrorStatus.MMIND_STATUS_PARAMETER_ERROR = -5
ErrorStatus.MMIND_STATUS_NO_DATA_ERROR = -6
ErrorStatus.MMIND_STATUS_INVALID_INPUT_ERROR = -7
ErrorStatus.MMIND_STATUS_FILE_IO_ERROR = -8
ErrorStatus.MMIND_STATUS_TIMEOUT_ERROR = -9
ErrorStatus.MMIND_HANDEYE_CALIBRATION_EXECUTION_ERROR = -10
ErrorStatus.MMIND_STATUS_REPLY_WITH_ERROR = -11
ErrorStatus.MMIND_STATUS_ACQUISITION_TRIGGER_WAIT = -12
ErrorStatus.MMIND_STATUS_DEVICE_BUSY = -13
ErrorStatus.MMIND_STATUS_INVALID_CALLBACKFUNC = -14
ErrorStatus.MMIND_STATUS_RESPONSE_PARSE_ERROR = -15
ErrorStatus.MMIND_STATUS_PROFILE_POST_PROCESS_ERROR = -16
ErrorStatus.MMIND_STATUS_MESSAGE_CHANNEL_ERROR = -17
ErrorStatus.MMIND_STATUS_DUPLICATE_REGISTRATION = -18
ErrorStatus.MMIND_STATUS_MESSAGE_CHANNEL_OCCUPPIED = -19
ErrorStatus.MMIND_STATUS_BUFFER_FULL = -20
FrameTransformation.Axis_X = 0
FrameTransformation.Axis_Y = 1
FrameTransformation.Axis_Z = 2
FrameTransformation.rotate = lambda self, theta, rotationAxis: call(
    self, "rotate", theta, rotationAxis
)
FrameTransformation.translate = lambda self, x, y, z: call(self, "translate", x, y, z)
FrameTransformation.is_valid = lambda self: call(self, "is_valid")


class Version(Proxy):
    """Represent the SDK's version string and comparisons."""

    _native_name = "Version"

    def to_string(self):
        return call(self, "to_string")

    def from_string(self, version):
        return call(self, "from_string", version)

    def is_empty(self):
        return call(self, "is_empty")

    def __eq__(self, other):
        return (
            call(self, "__eq__", other)
            if isinstance(other, Version)
            else NotImplemented
        )

    def __ne__(self, other):
        return (
            call(self, "__ne__", other)
            if isinstance(other, Version)
            else NotImplemented
        )

    def __ge__(self, other):
        return (
            call(self, "__ge__", other)
            if isinstance(other, Version)
            else NotImplemented
        )

    def __lt__(self, other):
        return (
            call(self, "__lt__", other)
            if isinstance(other, Version)
            else NotImplemented
        )

    def __le__(self, other):
        return (
            call(self, "__le__", other)
            if isinstance(other, Version)
            else NotImplemented
        )


register(Version)


def ip_assignment_method_to_string(type):
    return {0: "Unknown", 4: "DHCP", 5: "Static", 6: "LLA"}.get(type, "")


def get_api_version_info():
    from . import _native

    return _native.sdk_version()


def export_logs(dstPath, coverIfExist):
    return function("export_logs", dstPath, coverIfExist)


def show_error(status, successMessage=""):
    """Explicitly display a status, as requested by the caller."""
    if status.is_ok():
        if successMessage:
            print(successMessage)
    else:
        print(
            f"Error Code : {status.error_code}, Error Description: {status.error_description}"
        )


class Parameter(Proxy):
    """A parameter handle owned by the camera's current user set."""

    _native_name = "Parameter"
    _kind = None

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")

    def name(self):
        return call(self, "name")

    def type(self):
        return call(self, "type")

    def description(self):
        return call(self, "description")

    def is_writable(self):
        return call(self, "is_writable")

    def is_readable(self):
        return call(self, "is_readable")

    @classmethod
    def convert_from_parameter(cls, param):
        if param is None:
            return None
        if not isinstance(param, Parameter):
            raise TypeError("Expected Parameter")
        with _api_lock:
            if param.type() != cls._kind:
                return None
            result = object.__new__(cls)
            result.__dict__.update(param.__dict__)
            return result


register(Parameter)
Parameter._Int = 0
Parameter._Float = 1
Parameter._Bool = 2
Parameter._Enum = 3
Parameter._Roi = 4
Parameter._Range = 5
Parameter._FloatArray = 6
Parameter._RoiArray = 7
Parameter._ProfileRoi = 8


class IntParameter(Parameter):
    """Typed int device parameter."""

    _kind = 0

    def get_value(self):
        return call(self, "get_int_value", sequence=list)

    def set_value(self, value):
        return call(self, "set_int_value", value)

    def get_min(self):
        return call(self, "int_get_min", sequence=list)

    def get_max(self):
        return call(self, "int_get_max", sequence=list)

    def get_step(self):
        return call(self, "int_get_step", sequence=list)

    def get_unit(self):
        return call(self, "int_get_unit", sequence=list)


class FloatParameter(Parameter):
    """Typed float device parameter."""

    _kind = 1

    def get_value(self):
        return call(self, "get_float_value", sequence=list)

    def set_value(self, value):
        return call(self, "set_float_value", value)

    def get_min(self):
        return call(self, "float_get_min", sequence=list)

    def get_max(self):
        return call(self, "float_get_max", sequence=list)

    def get_step(self):
        return call(self, "float_get_step", sequence=list)

    def get_unit(self):
        return call(self, "float_get_unit", sequence=list)


class BoolParameter(Parameter):
    """Typed bool device parameter."""

    _kind = 2

    def get_value(self):
        return call(self, "get_bool_value", sequence=list)

    def set_value(self, value):
        return call(self, "set_bool_value", value)


class EnumParameter(Parameter):
    """Typed enum device parameter."""

    _kind = 3

    def get_value(self):
        return call(self, "get_enum_value", sequence=list)

    def set_value(self, value):
        return call(self, "set_enum_value", value)

    def get_value_string(self):
        return call(self, "get_enum_value_string", sequence=list)

    def get_values(self):
        return call(self, "get_enum_values")


class RoiParameter(Parameter):
    """Typed roi device parameter."""

    _kind = 4

    def get_value(self):
        return call(self, "get_roi_value", sequence=None)

    def set_value(self, value):
        return call(self, "set_roi_value", value)

    def get_max_roi_size(self, maxSize):
        return call(self, "get_max_roi_size", maxSize)


class RangeParameter(Parameter):
    """Typed range device parameter."""

    _kind = 5

    def get_value(self):
        return call(self, "get_range_value", sequence=None)

    def set_value(self, value):
        return call(self, "set_range_value", value)

    def get_min(self):
        return call(self, "range_get_min", sequence=list)

    def get_max(self):
        return call(self, "range_get_max", sequence=list)

    def get_step(self):
        return call(self, "range_get_step", sequence=list)

    def get_unit(self):
        return call(self, "range_get_unit", sequence=list)


class FloatArrayParameter(Parameter):
    """Typed float array device parameter."""

    _kind = 6

    def get_value(self):
        return call(self, "get_float_array_value", sequence=None)

    def set_value(self, value):
        return call(self, "set_float_array_value", value)

    def get_min(self):
        return call(self, "float_array_get_min", sequence=list)

    def get_max(self):
        return call(self, "float_array_get_max", sequence=list)

    def get_step(self):
        return call(self, "float_array_get_step", sequence=list)

    def get_unit(self):
        return call(self, "float_array_get_unit", sequence=list)

    def get_max_array_size(self):
        return call(self, "get_max_array_size", sequence=list)


class RoiArrayParameter(Parameter):
    """Typed roi array device parameter."""

    _kind = 7

    def get_value(self):
        return call(self, "get_roi_array_value", sequence=None)


class ProfileRoiParameter(Parameter):
    """Typed profile roi device parameter."""

    _kind = 8

    def get_value(self):
        return call(self, "get_profile_roi_value", sequence=None)

    def set_value(self, value):
        return call(self, "set_profile_roi_value", value)

    def get_max_roi_size(self, maxSize):
        return call(self, "get_max_profile_roi_size", maxSize)

    def get_min_roi_size(self, minSize):
        return call(self, "get_min_profile_roi_size", minSize)


class UserSet(Proxy):
    """Read and write the camera's current device user set."""

    _native_name = "UserSet"

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")

    def __getitem__(self, parameterName):
        return self.get_parameter(parameterName)

    def get_name(self):
        return call(self, "get_name", sequence=list)

    def rename(self, newName):
        return call(self, "rename", newName, sequence=None)

    def get_available_parameter_names(self):
        return call(self, "get_available_parameter_names", sequence=None)

    def reset_all_parameters_to_default_values(self):
        return call(self, "reset_all_parameters_to_default_values", sequence=None)

    def save_all_parameters_to_device(self):
        return call(self, "save_all_parameters_to_device", sequence=None)

    def get_available_parameters(self):
        return call(self, "get_available_parameters", sequence=None)

    def get_parameter(self, parameterName):
        return call(self, "get_parameter", parameterName, sequence=None)

    def get_int_value(self, parameterName):
        return call(self, "get_int_value", parameterName, sequence=list)

    def set_int_value(self, parameterName, value):
        return call(self, "set_int_value", parameterName, value, sequence=None)

    def get_float_value(self, parameterName):
        return call(self, "get_float_value", parameterName, sequence=list)

    def set_float_value(self, parameterName, value):
        return call(self, "set_float_value", parameterName, value, sequence=None)

    def get_bool_value(self, parameterName):
        return call(self, "get_bool_value", parameterName, sequence=list)

    def set_bool_value(self, parameterName, value):
        return call(self, "set_bool_value", parameterName, value, sequence=None)

    def get_enum_value(self, parameterName):
        return call(self, "get_enum_value", parameterName, sequence=list)

    def get_enum_value_string(self, parameterName):
        return call(self, "get_enum_value_string", parameterName, sequence=list)

    def set_enum_value(self, parameterName, value):
        return call(self, "set_enum_value", parameterName, value, sequence=None)

    def get_roi_value(self, parameterName):
        return call(self, "get_roi_value", parameterName, sequence=None)

    def set_roi_value(self, parameterName, value):
        return call(self, "set_roi_value", parameterName, value, sequence=None)

    def get_profile_roi_value(self, parameterName):
        return call(self, "get_profile_roi_value", parameterName, sequence=None)

    def set_profile_roi_value(self, parameterName, value):
        return call(self, "set_profile_roi_value", parameterName, value, sequence=None)

    def get_roi_array_value(self, parameterName):
        return call(self, "get_roi_array_value", parameterName, sequence=None)

    def get_range_value(self, parameterName):
        return call(self, "get_range_value", parameterName, sequence=None)

    def set_range_value(self, parameterName, value):
        return call(self, "set_range_value", parameterName, value, sequence=None)

    def get_float_array_value(self, parameterName):
        return call(self, "get_float_array_value", parameterName, sequence=None)

    def set_float_array_value(self, parameterName, value):
        return call(self, "set_float_array_value", parameterName, value, sequence=None)


register(UserSet)


class UserSetManager(Proxy):
    """Select, persist, import, and export device user sets."""

    _native_name = "UserSetManager"

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")

    def current_user_set(self):
        return call(self, "current_user_set", sequence=None)

    def get_all_user_set_names(self):
        return call(self, "get_all_user_set_names", sequence=None)

    def select_user_set(self, userSetName):
        return call(self, "select_user_set", userSetName, sequence=None)

    def add_user_set(self, userSetName):
        return call(self, "add_user_set", userSetName, sequence=None)

    def delete_user_set(self, userSetName):
        return call(self, "delete_user_set", userSetName, sequence=None)

    def save_to_file(self, fileName):
        return call(self, "save_to_file", fileName, sequence=None)

    def load_from_file(self, fileName):
        return call(self, "load_from_file", fileName, sequence=None)


register(UserSetManager)


class VirtualUserSet(UserSet):
    """Shared read-only interface; no profiler implementation is included."""

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")


MechEyeVectorROI = vector_type("MechEyeVectorROI", ROI, __name__)
MechEyeVectorString = vector_type("MechEyeVectorString", str, __name__)
MechEyeVectorParameterPointer = vector_type(
    "MechEyeVectorParameterPointer", Parameter, __name__
)


from ._compat import Ownership


class WrappedDoubleList(list, Ownership):
    """Double sequence accepted by the SDK float-array adapters."""

    @property
    def values(self):
        return self

    @values.setter
    def values(self, values):
        self[:] = [float(value) for value in values]

    def push_back(self, value):
        self.append(float(value))


class MechEyeError(Exception):
    """Base class for all camera errors."""


class MechEyeConnectionError(MechEyeError):
    """Connection, device information retrieval, or resource release failed."""


class MechEyeCaptureError(MechEyeError):
    """Capture failed or frame data is invalid."""


class MechEyePointCloudError(MechEyeError):
    """Point cloud mapping failed."""


class MechEyeConfigurationError(MechEyeError):
    """Parameter configuration or readback failed."""


__all__ = [
    name
    for name in globals()
    if not name.startswith("_")
    and name
    not in {
        "math",
        "Proxy",
        "Ownership",
        "FixedArray",
        "call",
        "function",
        "register",
        "value_type",
        "vector_type",
    }
]
for _type in (Size, SizeF, ROI, ProfileROI):
    _type.__eq__ = lambda self, other: call(self, "__eq__", other)
