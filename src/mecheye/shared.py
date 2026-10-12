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


def _status_is_ok(self):
    """Return True exactly when error_code is the SDK success code zero."""
    return call(self, "is_ok")


def _rotate(self, theta, rotationAxis):
    """Compose a rotation by theta degrees around FrameTransformation.Axis_X/Y/Z."""
    return call(self, "rotate", theta, rotationAxis)


def _translate(self, x, y, z):
    """Set translation to x, y, z in the same unit as the point coordinates."""
    return call(self, "translate", x, y, z)


def _is_valid(self):
    """Return whether the transform differs from identity according to the SDK.

    This checks for a custom reference frame, not rotation orthonormality."""
    return call(self, "is_valid")


ErrorStatus.is_ok = _status_is_ok
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
FrameTransformation.rotate = _rotate
FrameTransformation.translate = _translate
FrameTransformation.is_valid = _is_valid


class Version(Proxy):
    """Represent an SDK version and compare version components.

    Construct with no arguments, a dotted string, or three integers
    ``(major, minor, patch)``.
    """

    _native_name = "Version"

    def to_string(self):
        """Return the version as a dotted string."""
        return call(self, "to_string")

    def from_string(self, version):
        """Update this version from the SDK's dotted string syntax."""
        return call(self, "from_string", version)

    def is_empty(self):
        """Return whether the SDK version contains no version information."""
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
    """Return the SDK IP-assignment label, or an empty string for an unrecognized value."""
    return {0: "Unknown", 4: "DHCP", 5: "Static", 6: "LLA"}.get(type, "")


def get_api_version_info():
    """Return the loaded C++ SDK's version and copyright string."""
    from . import _native

    return _native.sdk_version()


def export_logs(dstPath, coverIfExist):
    """Explicitly export SDK diagnostic files to dstPath; return ErrorStatus.

    ``coverIfExist`` controls whether existing destination files can be replaced.
    This utility does not enable automatic Python logging.
    """
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
    """A device parameter handle obtained from UserSet.get_parameter().

    Direct construction is unavailable. Convert a generic handle with the desired
    typed subclass's convert_from_parameter() method before reading or writing it.
    """

    _native_name = "Parameter"
    _kind = None

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")

    def name(self):
        """Return the device parameter's SDK identifier."""
        return call(self, "name")

    def type(self):
        """Return the Parameter._* type identifier."""
        return call(self, "type")

    def description(self):
        """Return the SDK-provided description for this parameter."""
        return call(self, "description")

    def is_writable(self):
        """Return whether the parameter is currently writable."""
        return call(self, "is_writable")

    def is_readable(self):
        """Return whether the parameter is currently readable."""
        return call(self, "is_readable")

    @classmethod
    def convert_from_parameter(cls, param):
        """Return a typed view when param has this subclass's parameter kind.

        :param param: A Parameter handle or None.
        :return: A typed handle, or None if the handle is absent or its kind differs.
        :raises TypeError: A non-Parameter value is supplied.
        """
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
        """Return ``[status, value]`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_int_value", sequence=list)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_int_value", value)

    def get_min(self):
        """Return ``[status, minimum]`` for this parameter's supported range."""
        return call(self, "int_get_min", sequence=list)

    def get_max(self):
        """Return ``[status, maximum]`` for this parameter's supported range."""
        return call(self, "int_get_max", sequence=list)

    def get_step(self):
        """Return ``[status, step]`` for this parameter's increment."""
        return call(self, "int_get_step", sequence=list)

    def get_unit(self):
        """Return ``[status, unit]`` with the SDK's unit string."""
        return call(self, "int_get_unit", sequence=list)


class FloatParameter(Parameter):
    """Typed float device parameter."""

    _kind = 1

    def get_value(self):
        """Return ``[status, value]`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_float_value", sequence=list)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_float_value", value)

    def get_min(self):
        """Return ``[status, minimum]`` for this parameter's supported range."""
        return call(self, "float_get_min", sequence=list)

    def get_max(self):
        """Return ``[status, maximum]`` for this parameter's supported range."""
        return call(self, "float_get_max", sequence=list)

    def get_step(self):
        """Return ``[status, step]`` for this parameter's increment."""
        return call(self, "float_get_step", sequence=list)

    def get_unit(self):
        """Return ``[status, unit]`` with the SDK's unit string."""
        return call(self, "float_get_unit", sequence=list)


class BoolParameter(Parameter):
    """Typed bool device parameter."""

    _kind = 2

    def get_value(self):
        """Return ``[status, value]`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_bool_value", sequence=list)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_bool_value", value)


class EnumParameter(Parameter):
    """Typed enum device parameter."""

    _kind = 3

    def get_value(self):
        """Return ``[status, value]`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_enum_value", sequence=list)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_enum_value", value)

    def get_value_string(self):
        """Return ``[status, name]`` for the selected enum entry."""
        return call(self, "get_enum_value_string", sequence=list)

    def get_values(self):
        """Return the supported enum-entry map from names to integer values."""
        return call(self, "get_enum_values")


class RoiParameter(Parameter):
    """Typed roi device parameter."""

    _kind = 4

    def get_value(self):
        """Return ``(status, value)`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_roi_value", sequence=None)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_roi_value", value)

    def get_max_roi_size(self, maxSize):
        """Fill maxSize with the maximum ROI dimensions; return ErrorStatus."""
        return call(self, "get_max_roi_size", maxSize)


class RangeParameter(Parameter):
    """Typed range device parameter."""

    _kind = 5

    def get_value(self):
        """Return ``(status, value)`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_range_value", sequence=None)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_range_value", value)

    def get_min(self):
        """Return ``[status, minimum]`` for this parameter's supported range."""
        return call(self, "range_get_min", sequence=list)

    def get_max(self):
        """Return ``[status, maximum]`` for this parameter's supported range."""
        return call(self, "range_get_max", sequence=list)

    def get_step(self):
        """Return ``[status, step]`` for this parameter's increment."""
        return call(self, "range_get_step", sequence=list)

    def get_unit(self):
        """Return ``[status, unit]`` with the SDK's unit string."""
        return call(self, "range_get_unit", sequence=list)


class FloatArrayParameter(Parameter):
    """Typed float array device parameter."""

    _kind = 6

    def get_value(self):
        """Return ``(status, value)`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_float_array_value", sequence=None)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_float_array_value", value)

    def get_min(self):
        """Return ``[status, minimum]`` for this parameter's supported range."""
        return call(self, "float_array_get_min", sequence=list)

    def get_max(self):
        """Return ``[status, maximum]`` for this parameter's supported range."""
        return call(self, "float_array_get_max", sequence=list)

    def get_step(self):
        """Return ``[status, step]`` for this parameter's increment."""
        return call(self, "float_array_get_step", sequence=list)

    def get_unit(self):
        """Return ``[status, unit]`` with the SDK's unit string."""
        return call(self, "float_array_get_unit", sequence=list)

    def get_max_array_size(self):
        """Return ``[status, maximum_size]`` for the float array."""
        return call(self, "get_max_array_size", sequence=list)


class RoiArrayParameter(Parameter):
    """Typed roi array device parameter."""

    _kind = 7

    def get_value(self):
        """Return ``(status, value)`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_roi_array_value", sequence=None)


class ProfileRoiParameter(Parameter):
    """Typed profile roi device parameter."""

    _kind = 8

    def get_value(self):
        """Return ``(status, value)`` for this typed parameter.

        Check the status before reading the value.
        """
        return call(self, "get_profile_roi_value", sequence=None)

    def set_value(self, value):
        """Write a value through this typed parameter; return ErrorStatus."""
        return call(self, "set_profile_roi_value", value)

    def get_max_roi_size(self, maxSize):
        """Fill maxSize with the maximum ROI dimensions; return ErrorStatus."""
        return call(self, "get_max_profile_roi_size", maxSize)

    def get_min_roi_size(self, minSize):
        """Fill minSize with the minimum ROI dimensions; return ErrorStatus."""
        return call(self, "get_min_profile_roi_size", minSize)


class UserSet(Proxy):
    """Read and write the current device user set through a camera-owned handle.

    Obtain this object with Camera.current_user_set() or UserSetManager.current_user_set();
    direct construction is unavailable. Scalar reads return [status, value], structured
    reads return (status, value), and writes return an SDK ErrorStatus.
    """

    _native_name = "UserSet"

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")

    def __getitem__(self, parameterName):
        return self.get_parameter(parameterName)

    def get_name(self):
        """Return ``[status, name]`` for this device user set."""
        return call(self, "get_name", sequence=list)

    def rename(self, newName):
        """Rename this user set to newName; return ErrorStatus."""
        return call(self, "rename", newName, sequence=None)

    def get_available_parameter_names(self):
        """Return the SDK list of available parameter names."""
        return call(self, "get_available_parameter_names", sequence=None)

    def reset_all_parameters_to_default_values(self):
        """Reset current parameters to SDK defaults; return ErrorStatus."""
        return call(self, "reset_all_parameters_to_default_values", sequence=None)

    def save_all_parameters_to_device(self):
        """Persist current parameter values to the device; return ErrorStatus."""
        return call(self, "save_all_parameters_to_device", sequence=None)

    def get_available_parameters(self):
        """Return available Parameter handles owned by this connection."""
        return call(self, "get_available_parameters", sequence=None)

    def get_parameter(self, parameterName):
        """Return the named Parameter handle, or None when it is unavailable."""
        return call(self, "get_parameter", parameterName, sequence=None)

    def get_int_value(self, parameterName):
        """Read the named parameter and return ``[status, value]``.

        Check the status before using the returned int value.
        """
        return call(self, "get_int_value", parameterName, sequence=list)

    def set_int_value(self, parameterName, value):
        """Write the named int parameter; return ErrorStatus."""
        return call(self, "set_int_value", parameterName, value, sequence=None)

    def get_float_value(self, parameterName):
        """Read the named parameter and return ``[status, value]``.

        Check the status before using the returned float value.
        """
        return call(self, "get_float_value", parameterName, sequence=list)

    def set_float_value(self, parameterName, value):
        """Write the named float parameter; return ErrorStatus."""
        return call(self, "set_float_value", parameterName, value, sequence=None)

    def get_bool_value(self, parameterName):
        """Read the named parameter and return ``[status, value]``.

        Check the status before using the returned bool value.
        """
        return call(self, "get_bool_value", parameterName, sequence=list)

    def set_bool_value(self, parameterName, value):
        """Write the named bool parameter; return ErrorStatus."""
        return call(self, "set_bool_value", parameterName, value, sequence=None)

    def get_enum_value(self, parameterName):
        """Read the named parameter and return ``[status, value]``.

        Check the status before using the returned enum value.
        """
        return call(self, "get_enum_value", parameterName, sequence=list)

    def get_enum_value_string(self, parameterName):
        """Read the named parameter and return ``[status, value]``.

        Check the status before using the returned enum value string value.
        """
        return call(self, "get_enum_value_string", parameterName, sequence=list)

    def set_enum_value(self, parameterName, value):
        """Write the named enum parameter; return ErrorStatus."""
        return call(self, "set_enum_value", parameterName, value, sequence=None)

    def get_roi_value(self, parameterName):
        """Read the named parameter and return ``(status, value)``.

        Check the status before using the returned roi value.
        """
        return call(self, "get_roi_value", parameterName, sequence=None)

    def set_roi_value(self, parameterName, value):
        """Write the named roi parameter; return ErrorStatus."""
        return call(self, "set_roi_value", parameterName, value, sequence=None)

    def get_profile_roi_value(self, parameterName):
        """Read the named parameter and return ``(status, value)``.

        Check the status before using the returned profile roi value.
        """
        return call(self, "get_profile_roi_value", parameterName, sequence=None)

    def set_profile_roi_value(self, parameterName, value):
        """Write the named profile roi parameter; return ErrorStatus."""
        return call(self, "set_profile_roi_value", parameterName, value, sequence=None)

    def get_roi_array_value(self, parameterName):
        """Read the named parameter and return ``(status, value)``.

        Check the status before using the returned roi array value.
        """
        return call(self, "get_roi_array_value", parameterName, sequence=None)

    def get_range_value(self, parameterName):
        """Read the named parameter and return ``(status, value)``.

        Check the status before using the returned range value.
        """
        return call(self, "get_range_value", parameterName, sequence=None)

    def set_range_value(self, parameterName, value):
        """Write the named range parameter; return ErrorStatus."""
        return call(self, "set_range_value", parameterName, value, sequence=None)

    def get_float_array_value(self, parameterName):
        """Read the named parameter and return ``(status, value)``.

        Check the status before using the returned float array value.
        """
        return call(self, "get_float_array_value", parameterName, sequence=None)

    def set_float_array_value(self, parameterName, value):
        """Write the named float array parameter; return ErrorStatus."""
        return call(self, "set_float_array_value", parameterName, value, sequence=None)


register(UserSet)


class UserSetManager(Proxy):
    """Select, persist, import, and export device user sets.

    Obtain this handle with Camera.user_set_manager(); direct construction is unavailable.
    """

    _native_name = "UserSetManager"

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")

    def current_user_set(self):
        """Return the selected UserSet handle for this camera connection."""
        return call(self, "current_user_set", sequence=None)

    def get_all_user_set_names(self):
        """Return ``(status, names)`` for the device's available user sets."""
        return call(self, "get_all_user_set_names", sequence=None)

    def select_user_set(self, userSetName):
        """Select the named device user set; return ErrorStatus."""
        return call(self, "select_user_set", userSetName, sequence=None)

    def add_user_set(self, userSetName):
        """Create a named device user set; return ErrorStatus."""
        return call(self, "add_user_set", userSetName, sequence=None)

    def delete_user_set(self, userSetName):
        """Delete a named device user set; return ErrorStatus."""
        return call(self, "delete_user_set", userSetName, sequence=None)

    def save_to_file(self, fileName):
        """Export user-set settings to fileName; return ErrorStatus."""
        return call(self, "save_to_file", fileName, sequence=None)

    def load_from_file(self, fileName):
        """Import user-set settings from fileName; return ErrorStatus."""
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
        """Return this sequence; assigning values replaces it with float-converted elements."""
        return self

    @values.setter
    def values(self, values):
        self[:] = [float(value) for value in values]

    def push_back(self, value):
        """Append value after converting it to float."""
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
