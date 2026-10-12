"""Python sequence and mapping adapters for SDK container types."""

from __future__ import annotations

from copy import copy
import operator

from ._compat import _api_lock, _unwrap, _wrap, Proxy, _backend


def _copy(value):
    if isinstance(value, Proxy) and value._native_name in {
        "Parameter",
        "UserSet",
        "UserSetManager",
    }:
        return value
    if isinstance(value, Proxy):
        result = _wrap(_backend.clone_value(_unwrap(value)))
        return _snapshot(result) if "_snapshot_fields" in value.__dict__ else result
    return copy(value)


from ._compat import Ownership, _snapshot


class SwigPyIterator(Ownership):
    """Provide index-based iterator operations without exposing native pointers."""

    def __init__(self, sequence, index=0, reverse=False):
        self._sequence = sequence
        self._index = index
        self._direction = -1 if reverse else 1

    def value(self):
        with getattr(self._sequence, "_event_lock", _api_lock):
            if not 0 <= self._index < len(self._sequence):
                raise StopIteration
            return self._sequence[self._index]

    def incr(self, n=1):
        self._index += n * self._direction
        return self

    def decr(self, n=1):
        return self.incr(-n)

    def advance(self, n):
        return self.incr(n)

    def distance(self, other):
        if self._sequence is not other._sequence:
            raise ValueError("Iterators refer to different containers")
        return (other._index - self._index) * self._direction

    def equal(self, other):
        return self._sequence is other._sequence and self._index == other._index

    def copy(self):
        return type(self)(self._sequence, self._index, self._direction < 0)

    def next(self):
        value = self.value()
        self.incr()
        return value

    def previous(self):
        self.decr()
        return self.value()

    __next__ = next
    __eq__ = equal

    def __ne__(self, other):
        return not self.equal(other)

    def __iter__(self):
        return self

    def __iadd__(self, n):
        return self.incr(n)

    def __isub__(self, n):
        return self.decr(n)

    def __add__(self, n):
        return self.copy().incr(n)

    def __sub__(self, other):
        if isinstance(other, SwigPyIterator):
            return other.distance(self)
        return self.copy().decr(other)


class Vector(list, Ownership):
    """List-compatible typed vector with common SDK operations."""

    _element_type = str

    def __init__(self, *args):
        with getattr(self, "_event_lock", _api_lock):
            if not args:
                values = []
            elif isinstance(args[0], int):
                if args[0] < 0:
                    raise ValueError("Vector size cannot be negative")
                value = args[1] if len(args) > 1 else self._element_type()
                values = [_copy(value) for _ in range(args[0])]
            elif len(args) == 1:
                values = [_copy(value) for value in args[0]]
            else:
                raise TypeError("Expected a sequence or a size and optional value")
            super().__init__(values)
            self._capacity = len(values)

    def __iter__(self):
        return self.iterator()

    def iterator(self):
        return self.begin()

    def begin(self):
        return SwigPyIterator(self)

    def end(self):
        return SwigPyIterator(self, len(self))

    def rbegin(self):
        return SwigPyIterator(self, len(self) - 1, True)

    def rend(self):
        return SwigPyIterator(self, -1, True)

    def empty(self):
        return len(self) == 0

    def size(self):
        return len(self)

    def __getitem__(self, index):
        with getattr(self, "_event_lock", _api_lock):
            value = super().__getitem__(index)
            return type(self)(value) if isinstance(index, slice) else value

    def __setitem__(self, index, value):
        with getattr(self, "_event_lock", _api_lock):
            super().__setitem__(
                index,
                (
                    [_copy(item) for item in value]
                    if isinstance(index, slice)
                    else _copy(value)
                ),
            )

    def __delitem__(self, index):
        with getattr(self, "_event_lock", _api_lock):
            super().__delitem__(index)

    def append(self, value):
        with getattr(self, "_event_lock", _api_lock):
            super().append(_copy(value))
            self._capacity = max(self._capacity, len(self))

    push_back = append

    def pop(self, index=-1):
        with getattr(self, "_event_lock", _api_lock):
            return super().pop(index)

    def pop_back(self):
        self.pop()

    def front(self):
        return self[0]

    def back(self):
        return self[-1]

    def clear(self):
        with getattr(self, "_event_lock", _api_lock):
            super().clear()

    def swap(self, other):
        with getattr(self, "_event_lock", _api_lock):
            values = list(list.__iter__(self))
            self[:] = list(list.__iter__(other))
            other[:] = values

    def assign(self, n, value):
        self[:] = [_copy(value) for _ in range(n)]

    def resize(self, n, value=None):
        n = operator.index(n)
        if n < 0:
            raise ValueError("Vector size cannot be negative")
        with getattr(self, "_event_lock", _api_lock):
            if n < len(self):
                del self[n:]
            else:
                value = self._element_type() if value is None else value
                while len(self) < n:
                    self.append(value)

    def insert(self, position, *args):
        with getattr(self, "_event_lock", _api_lock):
            index = (
                position._index
                if isinstance(position, SwigPyIterator)
                else operator.index(position)
            )
            if len(args) == 1:
                super().insert(index, _copy(args[0]))
                return SwigPyIterator(self, index)
            if len(args) == 2:
                self[index:index] = [_copy(args[1]) for _ in range(args[0])]
                return None
            raise TypeError("Expected a position, optional count, and value")

    def erase(self, first, last=None):
        index = first._index
        stop = index + 1 if last is None else last._index
        del self[index:stop]
        return SwigPyIterator(self, index)

    def reserve(self, n):
        with getattr(self, "_event_lock", _api_lock):
            self._capacity = max(self._capacity, n)

    def capacity(self):
        return max(self._capacity, len(self))

    def get_allocator(self):
        return self._element_type

    def __getslice__(self, i, j):
        return self[i:j]

    def __setslice__(self, i, j, value=()):
        self[i:j] = value

    def __delslice__(self, i, j):
        del self[i:j]

    __nonzero__ = lambda self: bool(len(self))
    __bool__ = __nonzero__


def vector_type(name, element_type, module):
    return type(name, (Vector,), {"_element_type": element_type, "__module__": module})


class MechEyeMapStringInt(dict, Ownership):
    """String-to-integer map with SDK-compatible access helpers."""

    def __iter__(self):
        return iter(sorted(super().keys()))

    def __setitem__(self, key, value=0):
        with _api_lock:
            super().__setitem__(str(key), int(value))

    def keys(self):
        with _api_lock:
            return sorted(super().keys())

    def values(self):
        with _api_lock:
            return [self[key] for key in self.keys()]

    def items(self):
        with _api_lock:
            return [(key, self[key]) for key in self.keys()]

    def asdict(self):
        with _api_lock:
            return dict(self)

    def empty(self):
        return not self

    def size(self):
        return len(self)

    def has_key(self, key):
        return key in self

    def key_iterator(self):
        return SwigPyIterator(sorted(super().keys()))

    def value_iterator(self):
        return SwigPyIterator([self[key] for key in self])

    def iterator(self):
        return SwigPyIterator([(key, self[key]) for key in self])

    iterkeys = key_iterator
    itervalues = value_iterator
    iteritems = iterator
    begin = iterator

    def end(self):
        result = self.iterator()
        result._index = len(self)
        return result

    def rbegin(self):
        result = self.iterator()
        result._index = len(self) - 1
        result._direction = -1
        return result

    def rend(self):
        result = self.rbegin()
        result._index = -1
        return result

    def count(self, key):
        return int(key in self)

    def find(self, key):
        keys = sorted(super().keys())
        return SwigPyIterator(keys, keys.index(key) if key in self else len(keys))

    def lower_bound(self, key):
        import bisect

        keys = sorted(super().keys())
        return SwigPyIterator(keys, bisect.bisect_left(keys, key))

    def upper_bound(self, key):
        import bisect

        keys = sorted(super().keys())
        return SwigPyIterator(keys, bisect.bisect_right(keys, key))

    def erase(self, key, last=None):
        with _api_lock:
            if isinstance(key, SwigPyIterator):
                stop = key._index + 1 if last is None else last._index
                for value in key._sequence[key._index : stop]:
                    self.pop(value[0] if isinstance(value, tuple) else value, None)
                return None
            return int(self.pop(key, None) is not None)

    def swap(self, other):
        with _api_lock:
            values = dict(self)
            self.clear()
            self.update(other)
            other.clear()
            other.update(values)

    def get_allocator(self):
        return tuple

    __nonzero__ = lambda self: bool(len(self))
    __bool__ = __nonzero__
