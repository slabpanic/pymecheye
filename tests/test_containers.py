"""Check container value ownership, iterator boundaries, and concurrent mutations."""

from concurrent.futures import ThreadPoolExecutor
import unittest

from mecheye import area_scan_3d_camera as a, shared as s


class ContainerTests(unittest.TestCase):
    def test_vector_iterator_traversal_arithmetic_and_boundaries(self):
        vector = s.MechEyeVectorString(["a", "b", "c"])
        self.assertEqual(list(vector), ["a", "b", "c"])
        self.assertEqual(list(vector.rbegin()), ["c", "b", "a"])
        self.assertEqual(vector.end() - vector.begin(), 3)
        iterator = vector.begin()
        copied = iterator + 2
        self.assertEqual(copied.value(), "c")
        self.assertEqual(iterator.value(), "a")
        self.assertEqual(copied.previous(), "b")
        iterator += 2
        iterator -= 1
        self.assertEqual(iterator.value(), "b")
        self.assertEqual((copied - 1).value(), "a")
        self.assertEqual(vector.rend(), vector.rbegin() + 3)
        with self.assertRaises(StopIteration):
            vector.end().value()
        with self.assertRaises(ValueError):
            vector.begin().distance(s.MechEyeVectorString().begin())

    def test_vector_mutations_slices_and_independent_value_copies(self):
        original = s.ROI(1, 2, 3, 4)
        vector = s.MechEyeVectorROI(2, original)
        vector[0].width = 50
        self.assertEqual(vector[1].width, 3)
        self.assertEqual(original.width, 3)
        sliced = vector[:1]
        sliced[0].width = 60
        self.assertEqual(vector[0].width, 50)
        vector.assign(2, original)
        vector.insert(vector.begin() + 1, 2, original)
        self.assertEqual(vector.size(), 4)
        vector.erase(vector.begin() + 1, vector.begin() + 3)
        vector.pop_back()
        other = s.MechEyeVectorROI()
        vector.swap(other)
        self.assertTrue(vector.empty())
        self.assertEqual(other.front().width, 3)
        self.assertEqual(other.back().height, 4)
        other.reserve(20)
        self.assertGreaterEqual(other.capacity(), 20)
        other.clear()
        self.assertFalse(other)

    def test_vector_rejects_negative_sizes(self):
        with self.assertRaises(ValueError):
            s.MechEyeVectorString(-1)
        with self.assertRaises(ValueError):
            s.MechEyeVectorString().resize(-1)

    def test_map_sorted_views_lookup_bounds_and_erasure(self):
        mapping = s.MechEyeMapStringInt()
        mapping["z"] = 3
        mapping["a"] = 1
        mapping["m"] = 2
        self.assertEqual(mapping.keys(), ["a", "m", "z"])
        self.assertEqual(mapping.values(), [1, 2, 3])
        self.assertEqual(mapping.items(), [("a", 1), ("m", 2), ("z", 3)])
        self.assertEqual(mapping.asdict(), {"a": 1, "m": 2, "z": 3})
        self.assertEqual(mapping.find("m").value(), "m")
        self.assertEqual(mapping.lower_bound("b").value(), "m")
        self.assertEqual(mapping.upper_bound("m").value(), "z")
        with self.assertRaises(StopIteration):
            mapping.find("missing").value()
        self.assertEqual(mapping.erase("missing"), 0)
        self.assertEqual(mapping.erase("m"), 1)
        mapping.erase(mapping.begin(), mapping.end())
        self.assertTrue(mapping.empty())

    def test_threaded_vector_append_keeps_all_values(self):
        vector = s.MechEyeVectorString()
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(lambda i: vector.push_back(str(i)), range(200)))
        self.assertEqual(vector.size(), 200)
        self.assertEqual(set(vector), {str(i) for i in range(200)})

    def test_fixed_array_assignment_and_indices_are_checked(self):
        transform = a.FrameTransformation()
        transform.translation.data = [1, 2, 3]
        self.assertEqual([transform.translation[i] for i in range(3)], [1, 2, 3])
        for index in (-1, 3):
            with self.subTest(index=index):
                with self.assertRaises(IndexError):
                    _ = transform.translation[index]
                with self.assertRaises(IndexError):
                    transform.translation[index] = 1
        with self.assertRaises(ValueError):
            transform.translation.data = [1, 2]
        with self.assertRaises(TypeError):
            _ = transform.translation[0.5]

    def test_pixel_coordinates_and_indices_are_checked(self):
        image = a.GrayScale2DImage()
        image.resize(2, 2)
        for row, col in ((-1, 0), (0, -1), (2, 0), (0, 2)):
            with self.subTest(row=row, col=col):
                with self.assertRaises(IndexError):
                    image.at(row, col)
        for index in (-1, 4):
            with self.assertRaises(IndexError):
                image[index]
        with self.assertRaises(TypeError):
            image[0.5]


class ContainerBoundaryTests(unittest.TestCase):
    def test_vector_single_insert_erase_and_slice_adapters(self):
        vector = s.MechEyeVectorString(["a", "c"])
        inserted = vector.insert(1, "b")
        self.assertEqual(inserted.value(), "b")
        self.assertEqual(vector.erase(inserted).value(), "c")
        self.assertEqual(list(vector.__getslice__(0, 2)), ["a", "c"])
        vector.__setslice__(1, 2, ["b", "c"])
        vector.__delslice__(0, 1)
        self.assertEqual(list(vector), ["b", "c"])
        vector.resize(1)
        self.assertEqual(list(vector), ["b"])
        self.assertIs(vector.get_allocator(), str)
        with self.assertRaises(TypeError):
            s.MechEyeVectorString([], [])
        for args in ((), (1, 2, 3)):
            with self.assertRaises(TypeError):
                vector.insert(0, *args)

    def test_iterator_advance_comparison_and_reverse_boundaries(self):
        vector = s.MechEyeVectorString(["a", "b", "c"])
        iterator = vector.begin()
        self.assertIs(iterator.advance(2), iterator)
        self.assertEqual(iterator.value(), "c")
        self.assertNotEqual(iterator, vector.begin())
        self.assertEqual(iterator.distance(vector.end()), 1)
        self.assertEqual(iterator.decr(2).value(), "a")
        self.assertEqual(vector.rbegin().next(), "c")
        with self.assertRaises(StopIteration):
            vector.rend().value()
        vector.clear()
        for method in (vector.front, vector.back, vector.pop_back):
            with self.assertRaises(IndexError):
                method()

    def test_map_snapshot_iterators_and_swap_do_not_share_contents(self):
        mapping = s.MechEyeMapStringInt()
        mapping["b"], mapping["a"] = 2, 1
        keys, values, items = (
            mapping.iterkeys(),
            mapping.itervalues(),
            mapping.iteritems(),
        )
        mapping["c"] = 3
        self.assertEqual(list(keys), ["a", "b"])
        self.assertEqual(list(values), [1, 2])
        self.assertEqual(list(items), [("a", 1), ("b", 2)])
        self.assertEqual(list(mapping.rbegin()), [("c", 3), ("b", 2), ("a", 1)])
        with self.assertRaises(StopIteration):
            mapping.rend().value()
        self.assertEqual(mapping.size(), 3)
        self.assertTrue(mapping.has_key("a"))
        self.assertEqual(mapping.count("a"), 1)
        self.assertEqual(mapping.count("missing"), 0)
        self.assertIs(mapping.get_allocator(), tuple)
        other = s.MechEyeMapStringInt({"z": 9})
        mapping.swap(other)
        self.assertEqual(mapping.asdict(), {"z": 9})
        self.assertEqual(other.keys(), ["a", "b", "c"])
        other.erase(other.find("b"))
        other.erase(other.begin())
        self.assertEqual(other.asdict(), {"c": 3})

    def test_wrapped_double_list_converts_values_without_aliasing_input(self):
        values = s.WrappedDoubleList()
        source = ["1.25", 2]
        values.values = source
        source[0] = 99
        values.push_back("3.5")
        self.assertIs(values.values, values)
        self.assertEqual(values, [1.25, 2.0, 3.5])
        self.assertTrue(all(isinstance(value, float) for value in values))
        with self.assertRaises(ValueError):
            values.push_back("invalid")
        self.assertEqual(values, [1.25, 2.0, 3.5])


class ContainerRegressionTests(unittest.TestCase):
    def test_map_iterators_share_owner_and_reach_their_sentinel(self):
        for contents in ({}, {"b": 2, "a": 1}):
            with self.subTest(contents=contents):
                mapping = s.MechEyeMapStringInt(contents)
                begin, end = mapping.begin(), mapping.end()
                self.assertEqual(end - begin, len(contents))
                self.assertEqual(mapping.rend() - mapping.rbegin(), len(contents))
                seen = []
                while begin != end:
                    seen.append(next(begin))
                self.assertEqual(seen, sorted(contents.items()))
                self.assertEqual(mapping.find("missing"), end)
                self.assertEqual(mapping.upper_bound("z"), end)
                self.assertEqual(mapping.lower_bound("z"), end)
                self.assertEqual(begin.copy(), end)
                self.assertEqual(
                    list(mapping.rbegin()), sorted(contents.items(), reverse=True)
                )
        mapping = s.MechEyeMapStringInt({"a": 1})
        self.assertNotEqual(mapping.begin(), mapping.rbegin())
        self.assertNotEqual(mapping.begin(), None)
        with self.assertRaisesRegex(ValueError, "directions"):
            mapping.begin().distance(mapping.rbegin())
        other = s.MechEyeMapStringInt({"a": 1})
        self.assertNotEqual(mapping.begin(), other.begin())
        with self.assertRaisesRegex(ValueError, "different containers"):
            mapping.end() - other.begin()
        for first, last in ((other.begin(), None), (mapping.begin(), other.end())):
            with self.assertRaisesRegex(ValueError, "different containers"):
                mapping.erase(first, last)
        self.assertEqual(mapping.asdict(), {"a": 1})

    def test_bulk_vector_writes_copy_values_and_support_self_extension(self):
        for operation in ("extend", "iadd"):
            with self.subTest(operation=operation):
                original = s.ROI(1, 2, 3, 4)
                vector = s.MechEyeVectorROI()
                if operation == "extend":
                    self.assertIsNone(vector.extend([original]))
                else:
                    alias = vector
                    vector += [original]
                    self.assertIs(vector, alias)
                original.width = 99
                self.assertEqual(vector[0].width, 3)
                vector.extend(vector)
                vector[0].width = 50
                self.assertEqual(vector[1].width, 3)
                self.assertGreaterEqual(vector.capacity(), 2)

    def test_vector_repetition_copies_each_added_value(self):
        vector = s.MechEyeVectorROI([s.ROI(1, 2, 3, 4)])
        first, alias = vector[0], vector
        vector *= 3
        self.assertIs(vector, alias)
        self.assertIs(vector[0], first)
        vector[0].width = 99
        self.assertEqual([value.width for value in vector], [99, 3, 3])
        vector[1].height = 50
        self.assertEqual(vector[2].height, 4)
        vector *= 1
        self.assertEqual(len(vector), 3)
        vector *= -1
        self.assertTrue(vector.empty())
        with self.assertRaises(TypeError):
            vector *= 0.5

    def test_negative_sizes_never_modify_vector_contents(self):
        vector = s.MechEyeVectorString(["preserved"])
        for operation in (
            lambda: vector.assign(-1, "lost"),
            lambda: vector.insert(vector.begin(), -1, "lost"),
            lambda: vector.reserve(-1),
            lambda: vector.resize(-1),
        ):
            with self.assertRaises(ValueError):
                operation()
            self.assertEqual(list(vector), ["preserved"])
        with self.assertRaises(TypeError):
            s.MechEyeVectorString(1, "value", "extra")
        for operation in (
            lambda: vector.assign(0.5, "lost"),
            lambda: vector.insert(0, 0.5, "lost"),
            lambda: vector.reserve(0.5),
        ):
            with self.assertRaises(TypeError):
                operation()
            self.assertEqual(list(vector), ["preserved"])

    def test_bulk_vector_write_failure_preserves_contents(self):
        vector = s.MechEyeVectorString(["preserved"])

        def values():
            yield "partial"
            raise ValueError("source failed")

        with self.assertRaisesRegex(ValueError, "source failed"):
            vector.extend(values())
        self.assertEqual(list(vector), ["preserved"])

    def test_threaded_bulk_appends_copy_all_rois(self):
        vector = s.MechEyeVectorROI()
        original = s.ROI(1, 2, 3, 4)
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(lambda _: vector.extend([original]), range(100)))
        original.width = 99
        self.assertEqual(len(vector), 100)
        self.assertEqual([value.width for value in vector], [3] * 100)
        self.assertEqual(len({id(value) for value in vector}), 100)
