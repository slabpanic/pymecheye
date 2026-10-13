"""Python sequence and mapping adapters for SDK container types."""

from __future__ import annotations

from copy import copy
import operator

from ._compat import _api_lock, _unwrap, _wrap, Proxy, _backend


def _size(value):
    value = operator.index(value)
    if value < 0:
        raise ValueError("Vector size cannot be negative")
    return value


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

    def __init__(self, sequence, index=0, reverse=False, owner=None):
        self._sequence = sequence
        self._owner = sequence if owner is None else owner
        self._index = index
        self._direction = -1 if reverse else 1

    def value(self):
        """Return the current element; raise StopIteration outside the container."""
        with getattr(self._sequence, "_event_lock", _api_lock):
            if not 0 <= self._index < len(self._sequence):
                raise StopIteration
            return self._sequence[self._index]

    def incr(self, n=1):
        """Advance n elements in this iterator's traversal direction and return self."""
        self._index += n * self._direction
        return self

    def decr(self, n=1):
        """Move n elements against this iterator's traversal direction and return self."""
        return self.incr(-n)

    def advance(self, n):
        """Advance by signed n elements and return self."""
        return self.incr(n)

    def distance(self, other):
        """Return the distance to other in the traversal direction.

        :raises ValueError: The iterators refer to different containers.
        """
        if not isinstance(other, SwigPyIterator) or self._owner is not other._owner:
            raise ValueError("Iterators refer to different containers")
        if self._direction != other._direction:
            raise ValueError("Iterators have different traversal directions")
        return (other._index - self._index) * self._direction

    def equal(self, other):
        """Return whether both iterators refer to the same container and index."""
        return (
            isinstance(other, SwigPyIterator)
            and self._owner is other._owner
            and self._index == other._index
            and self._direction == other._direction
        )

    def copy(self):
        """Return an independent iterator at the same position and direction."""
        return type(self)(
            self._sequence, self._index, self._direction < 0, owner=self._owner
        )

    def next(self):
        """Return the current element, then advance in the traversal direction."""
        value = self.value()
        self.incr()
        return value

    def previous(self):
        """Move against the traversal direction, then return the element."""
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
                if len(args) > 2:
                    raise TypeError("Expected a size and optional value")
                n = _size(args[0])
                value = args[1] if len(args) > 1 else self._element_type()
                values = [_copy(value) for _ in range(n)]
            elif len(args) == 1:
                values = [_copy(value) for value in args[0]]
            else:
                raise TypeError("Expected a sequence or a size and optional value")
            super().__init__(values)
            self._capacity = len(values)

    def __iter__(self):
        return self.iterator()

    def iterator(self):
        """Return an iterator starting at the first element."""
        return self.begin()

    def begin(self):
        """Return an iterator positioned at the first element."""
        return SwigPyIterator(self)

    def end(self):
        """Return the one-past-end iterator; dereferencing it raises StopIteration."""
        return SwigPyIterator(self, len(self))

    def rbegin(self):
        """Return a reverse iterator positioned at the last element."""
        return SwigPyIterator(self, len(self) - 1, True)

    def rend(self):
        """Return the one-past-end reverse iterator."""
        return SwigPyIterator(self, -1, True)

    def empty(self):
        """Return whether the vector contains no elements."""
        return len(self) == 0

    def size(self):
        """Return the number of stored elements."""
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
            self._capacity = max(self._capacity, len(self))

    def __delitem__(self, index):
        with getattr(self, "_event_lock", _api_lock):
            super().__delitem__(index)

    def append(self, value):
        """Append a copied value; camera-owned parameter handles retain shared ownership."""
        with getattr(self, "_event_lock", _api_lock):
            super().append(_copy(value))
            self._capacity = max(self._capacity, len(self))

    push_back = append

    def extend(self, values):
        """Append independent copies of values, retaining shared parameter handles."""
        with getattr(self, "_event_lock", _api_lock):
            copied = [_copy(value) for value in values]
            super().extend(copied)
            self._capacity = max(self._capacity, len(self))

    def __iadd__(self, values):
        self.extend(values)
        return self

    def __imul__(self, count):
        count = operator.index(count)
        with getattr(self, "_event_lock", _api_lock):
            original = list(list.__iter__(self))
            values = (
                original + [_copy(item) for _ in range(count - 1) for item in original]
                if count > 0
                else []
            )
            super().__setitem__(slice(None), values)
            self._capacity = max(self._capacity, len(self))
            return self

    def pop(self, index=-1):
        """Remove and return the indexed element; default to the last element."""
        with getattr(self, "_event_lock", _api_lock):
            return super().pop(index)

    def pop_back(self):
        """Remove the last element."""
        self.pop()

    def front(self):
        """Return the first element; an empty vector raises IndexError."""
        return self[0]

    def back(self):
        """Return the last element; an empty vector raises IndexError."""
        return self[-1]

    def clear(self):
        """Remove all elements."""
        with getattr(self, "_event_lock", _api_lock):
            super().clear()

    def swap(self, other):
        """Exchange the contents of this vector and other."""
        with getattr(self, "_event_lock", _api_lock):
            values = list(list.__iter__(self))
            self[:] = list(list.__iter__(other))
            other[:] = values

    def assign(self, n, value):
        """Replace the contents with n independent copies of value."""
        n = _size(n)
        with getattr(self, "_event_lock", _api_lock):
            self[:] = [_copy(value) for _ in range(n)]

    def resize(self, n, value=None):
        """Resize to n elements, copying value or default-constructed elements when growing.

        :raises ValueError: n is negative.
        """
        n = _size(n)
        with getattr(self, "_event_lock", _api_lock):
            if n < len(self):
                del self[n:]
            else:
                value = self._element_type() if value is None else value
                while len(self) < n:
                    self.append(value)

    def insert(self, position, *args):
        """Insert at an index or iterator position.

        Use ``insert(position, value)`` to return an iterator to the inserted value.
        ``insert(position, count, value)`` inserts count copies and returns None.
        """
        with getattr(self, "_event_lock", _api_lock):
            index = (
                position._index
                if isinstance(position, SwigPyIterator)
                else operator.index(position)
            )
            if len(args) == 1:
                super().insert(index, _copy(args[0]))
                self._capacity = max(self._capacity, len(self))
                return SwigPyIterator(self, index)
            if len(args) == 2:
                self[index:index] = [_copy(args[1]) for _ in range(_size(args[0]))]
                return None
            raise TypeError("Expected a position, optional count, and value")

    def erase(self, first, last=None):
        """Erase one iterator element, or the half-open range first to last.

        :return: An iterator positioned at the first element following the erased range.
        """
        index = first._index
        stop = index + 1 if last is None else last._index
        del self[index:stop]
        return SwigPyIterator(self, index)

    def reserve(self, n):
        """Record a minimum logical capacity without allocating SDK storage."""
        n = _size(n)
        with getattr(self, "_event_lock", _api_lock):
            self._capacity = max(self._capacity, n)

    def capacity(self):
        """Return the adapter's logical reserved capacity, at least the current size."""
        return max(self._capacity, len(self))

    def get_allocator(self):
        """Return the Python element type used to create default values."""
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
    """Generate an SDK-named vector with documented element-copy semantics."""
    return type(
        name,
        (Vector,),
        {
            "_element_type": element_type,
            "__module__": module,
            "__doc__": f"Mutable vector of {element_type.__name__} values.\n\nConstruct from a sequence, or a size and optional initial value. Value objects\nare copied on insertion; parameter handles retain their camera ownership.",
        },
    )


class MechEyeMapStringInt(dict, Ownership):
    """String-to-integer map with SDK-compatible access helpers."""

    def __iter__(self):
        return iter(sorted(super().keys()))

    def __setitem__(self, key, value=0):
        with _api_lock:
            super().__setitem__(str(key), int(value))

    def keys(self):
        """Return a new list of keys in lexicographic order."""
        with _api_lock:
            return sorted(super().keys())

    def values(self):
        """Return a new list of values in lexicographic key order."""
        with _api_lock:
            return [self[key] for key in self.keys()]

    def items(self):
        """Return a new list of key-value tuples in lexicographic key order."""
        with _api_lock:
            return [(key, self[key]) for key in self.keys()]

    def asdict(self):
        """Return a plain dictionary copy."""
        with _api_lock:
            return dict(self)

    def empty(self):
        """Return whether the map has no entries."""
        return not self

    def size(self):
        """Return the number of entries."""
        return len(self)

    def has_key(self, key):
        """Return whether key exists."""
        return key in self

    def key_iterator(self):
        """Return an iterator over a sorted snapshot of keys."""
        with _api_lock:
            return SwigPyIterator(sorted(super().keys()), owner=self)

    def value_iterator(self):
        """Return an iterator over a snapshot of values in key order."""
        with _api_lock:
            return SwigPyIterator([self[key] for key in self], owner=self)

    def iterator(self):
        """Return an iterator over a sorted snapshot of key-value tuples."""
        with _api_lock:
            return SwigPyIterator([(key, self[key]) for key in self], owner=self)

    iterkeys = key_iterator
    itervalues = value_iterator
    iteritems = iterator
    begin = iterator

    def end(self):
        """Return a one-past-end iterator over key-value tuples."""
        result = self.iterator()
        result._index = len(result._sequence)
        return result

    def rbegin(self):
        """Return a reverse iterator over a sorted snapshot of key-value tuples."""
        result = self.iterator()
        result._index = len(result._sequence) - 1
        result._direction = -1
        return result

    def rend(self):
        """Return the one-past-end reverse iterator."""
        result = self.rbegin()
        result._index = -1
        return result

    def count(self, key):
        """Return 1 when key exists and 0 otherwise."""
        return int(key in self)

    def find(self, key):
        """Return a sorted-key iterator for key, or a one-past-end iterator if absent."""
        with _api_lock:
            keys = sorted(super().keys())
            return SwigPyIterator(
                keys, keys.index(key) if key in self else len(keys), owner=self
            )

    def lower_bound(self, key):
        """Return an iterator to the first key greater than or equal to key."""
        import bisect

        with _api_lock:
            keys = sorted(super().keys())
            return SwigPyIterator(keys, bisect.bisect_left(keys, key), owner=self)

    def upper_bound(self, key):
        """Return an iterator to the first key strictly greater than key."""
        import bisect

        with _api_lock:
            keys = sorted(super().keys())
            return SwigPyIterator(keys, bisect.bisect_right(keys, key), owner=self)

    def erase(self, key, last=None):
        """Erase a key or iterator range.

        A key argument returns 1 if removed, otherwise 0. An iterator or a half-open
        iterator range erases the corresponding entries and returns None.
        """
        with _api_lock:
            if isinstance(key, SwigPyIterator):
                if key._owner is not self or (
                    last is not None and last._owner is not self
                ):
                    raise ValueError("Iterators refer to different containers")
                stop = key._index + 1 if last is None else last._index
                for value in key._sequence[key._index : stop]:
                    self.pop(value[0] if isinstance(value, tuple) else value, None)
                return None
            return int(self.pop(key, None) is not None)

    def swap(self, other):
        """Exchange this map's contents with other."""
        with _api_lock:
            values = dict(self)
            self.clear()
            self.update(other)
            other.clear()
            other.update(values)

    def get_allocator(self):
        """Return tuple, the adapter's key-value item type."""
        return tuple

    __nonzero__ = lambda self: bool(len(self))
    __bool__ = __nonzero__
