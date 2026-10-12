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


def value_type(name, fields, module):
    namespace = {"_native_name": name, "_fields": tuple(fields), "__module__": module}
    for field in fields:
        namespace[field] = property(
            lambda self, field=field: self._get_field(field),
            lambda self, value, field=field: self._set_field(field, value),
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
        return call(self, "width")

    def height(self):
        return call(self, "height")

    def is_empty(self):
        return call(self, "is_empty")

    def resize(self, width, height):
        with _api_lock:
            old = (self.width(), self.height())
            result = call(self, "resize", width, height)
            if old != (self.width(), self.height()):
                self._generation += 1
            return result

    def release(self):
        with _api_lock:
            call(self, "release")
            self._generation += 1

    def clone(self):
        return call(self, "clone")

    def at(self, row, col):
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
    namespace = {"_native_name": name, "__module__": module}
    for accessor in accessors:
        namespace[accessor] = lambda self, accessor=accessor: self._array(accessor)
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
