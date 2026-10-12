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
