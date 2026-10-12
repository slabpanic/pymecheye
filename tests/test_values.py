"""Check real SDK value copies, matrix validation, and event snapshot ownership."""

import unittest

import numpy as np

from mecheye import area_scan_3d_camera as a, shared as s
from mecheye._compat import _snapshot, _unwrap, _wrap
from mecheye._containers import _copy


class ValueTests(unittest.TestCase):
    def test_version_parsing_and_all_comparisons(self):
        value = s.Version()
        self.assertTrue(value.is_empty())
        value.from_string("2.6.0")
        self.assertEqual(value.to_string(), "2.6.0")
        self.assertFalse(value.is_empty())
        equal, older, newer = s.Version(2, 6, 0), s.Version(2, 5, 4), s.Version(3, 0, 0)
        self.assertEqual(value, equal)
        self.assertNotEqual(value, older)
        self.assertGreaterEqual(value, equal)
        self.assertGreaterEqual(value, older)
        self.assertLessEqual(value, equal)
        self.assertLessEqual(value, newer)
        for method in ("__eq__", "__ne__", "__ge__", "__lt__", "__le__"):
            self.assertIs(getattr(value, method)("2.6.0"), NotImplemented)
        self.assertNotEqual(value, "2.6.0")
        with self.assertRaises(TypeError):
            _ = value < "2.6.0"

    def test_transform_rotation_translation_and_deep_copy(self):
        for cls, rotate, translate, valid in [
            (s.FrameTransformation, "rotate", "translate", "is_valid"),
            (a.FrameTransformation, "__rotate__", "__translate__", "__is__valid__"),
        ]:
            with self.subTest(cls=cls):
                transform = cls()
                self.assertFalse(getattr(transform, valid)())
                getattr(transform, rotate)(90, s.FrameTransformation.Axis_Z)
                expected = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
                np.testing.assert_allclose(
                    [list(row) for row in transform.rotation], expected, atol=1e-6
                )
                getattr(transform, translate)(10, 20, 30)
                self.assertTrue(getattr(transform, valid)())
                cloned = cls(transform)
                transform.translation[0] = 99
                self.assertEqual(list(cloned.translation), [10, 20, 30])

    def test_matrix_and_translation_validation_leave_native_state_unchanged(self):
        for transform in (a.FrameTransformation(), a.Transformation()):
            with self.subTest(cls=type(transform)):
                transform.rotation = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
                transform.translation = [10, 20, 30]
                original = [list(row) for row in transform.rotation]
                for matrix in ([[1, 2, 3]], [[1, 2, 3], [4, 5], [7, 8, 9]]):
                    with self.assertRaises(ValueError):
                        transform.rotation = matrix
                    np.testing.assert_array_equal(
                        [list(row) for row in transform.rotation], original
                    )
                with self.assertRaises(ValueError):
                    transform.translation = [1, 2]
                self.assertEqual(list(transform.translation), [10, 20, 30])

    def test_intrinsics_copy_helpers_make_independent_outputs(self):
        source = a.CameraIntrinsics()
        source.depth.camera_matrix.fx = 1000
        source.texture.camera_distortion.k1 = 0.25
        source.depth_to_texture.translation = [10, 20, 30]
        wrapped, restored = a.CameraIntrinsics(), a.CameraIntrinsics()
        self.assertIsNone(a.camera_intrinsics_to_wrapped(wrapped, source))
        self.assertIsNone(a.wrapped_to_camera_intrinsics(restored, wrapped))
        source.depth.camera_matrix.fx = 99
        wrapped.texture.camera_distortion.k1 = 0.5
        self.assertEqual(restored.depth.camera_matrix.fx, 1000)
        self.assertEqual(restored.texture.camera_distortion.k1, 0.25)
        self.assertEqual(list(restored.depth_to_texture.translation), [10, 20, 30])

    def test_frame_transformation_copy_helpers_preserve_all_components(self):
        source, wrapped, restored = (
            a.FrameTransformation(),
            a.FrameTransformation(),
            a.FrameTransformation(),
        )
        source.translation = [10, 20, 30]
        source.rotation[1][2] = 0.25
        self.assertIsNone(a.frame_transformation_towrapped(source, wrapped))
        self.assertIsNone(a.wrapped_to_frame_transformation(restored, wrapped))
        source.translation[0] = 99
        wrapped.rotation[1][2] = 0.5
        self.assertEqual(list(restored.translation), [10, 20, 30])
        self.assertEqual(restored.rotation[1][2], 0.25)

    def test_standalone_fixed_arrays_keep_mutable_row_views(self):
        matrix, vector = a.doubleMatrix3(), a.doubleArray3()
        matrix.data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        row = matrix[1]
        row[2] = 99
        self.assertEqual(matrix[1][2], 99)
        vector.data = row
        vector[0] = -1
        self.assertEqual(matrix[1][0], 4)
        self.assertEqual(len(matrix), 3)
        self.assertEqual(list(vector), [-1, 5, 99])

    def test_pixel_reference_survives_same_size_resize_but_not_release(self):
        cloud = a.TexturedPointCloudWithNormals()
        cloud.resize(1, 1)
        pixel = cloud[0]
        point, normal = pixel.color_point, pixel.normal
        cloud.resize(1, 1)
        point.x, normal.z = 10, 1
        self.assertEqual(cloud[0].color_point.x, 10)
        self.assertEqual(cloud[0].normal.z, 1)
        cloud.release()
        for reference, field in ((point, "x"), (normal, "z")):
            with self.subTest(field=field):
                with self.assertRaises(ReferenceError):
                    getattr(reference, field)
                with self.assertRaises(ReferenceError):
                    setattr(reference, field, 2)
                with self.assertRaises(ReferenceError):
                    _unwrap(reference)

    def test_event_snapshots_mutate_and_copy_without_sharing_fields(self):
        event = a.EventData()
        event.frame_id, event.event_name = 42, "ExposureEnd"
        native = _unwrap(event)
        snapshot = _snapshot(_wrap(native))
        snapshot.frame_id = 99
        self.assertEqual(native.frame_id, 42)
        self.assertEqual(_unwrap(snapshot).frame_id, 99)
        cloned = _copy(snapshot)
        cloned.frame_id = 100
        self.assertEqual(snapshot.frame_id, 99)
        self.assertEqual(cloned.event_name, "ExposureEnd")
        payload = a.PayloadMember()
        payload.type = a.PayloadMember.Type__String
        payload.name = "label"
        payload.value.string_value = "original"
        frozen = _snapshot(payload)
        frozen.value.string_value = "changed"
        self.assertEqual(_unwrap(frozen).value.string_value, "changed")
        container = a.Payload([frozen])
        container[0].value.string_value = "copied"
        self.assertEqual(frozen.value.string_value, "changed")

    def test_native_value_clone_preserves_nested_data_without_aliasing(self):
        cases = [
            (s.Size(2, 3), "width", 9),
            (s.SizeF(2, 3), "width", 9),
            (s.ROI(1, 2, 3, 4), "height", 9),
            (s.ProfileROI(1, 2, 3), "height", 9),
            (a.Gray(), "gray", 9),
            (a.ColorBGR(), "b", 9),
            (a.PointZ(), "z", 9),
            (a.PointXYZBGR(1.0, 2.0, 3.0, 12, 34, 56), "x", 9),
            (a.NormalVector(), "z", 9),
            (a.EventInfo("ExposureEnd", 1), "event_id", 9),
            (s.RangeFloat(1, 2), "max", 9),
            (s.RangeDouble(1, 2), "max", 9),
        ]
        for value, field, updated in cases:
            with self.subTest(cls=type(value)):
                before = getattr(value, field)
                cloned = _copy(value)
                setattr(cloned, field, updated)
                self.assertEqual(getattr(value, field), before)
                self.assertEqual(getattr(cloned, field), updated)

    def test_ownership_flags_never_detach_native_resources(self):
        image = a.GrayScale2DImage()
        image.thisown = False
        self.assertTrue(image.thisown)
        image.resize(1, 1)
        image[0].gray = 80
        self.assertEqual(image.data()[0, 0], 80)
        vector = s.MechEyeVectorString()
        self.assertTrue(vector.thisown)
        vector.thisown = False
        self.assertFalse(vector.thisown)
        vector.push_back("alive")
        self.assertEqual(list(vector), ["alive"])

    def test_recursive_wrap_and_unwrap_preserve_container_structure(self):
        native = {"size": _unwrap(s.Size(2, 3)), "nested": [_unwrap(s.ROI(1, 2, 3, 4))]}
        wrapped = _wrap(native)
        self.assertIsInstance(wrapped["size"], s.Size)
        self.assertIsInstance(wrapped["nested"][0], s.ROI)
        restored = _unwrap(wrapped)
        self.assertEqual(restored["size"].width, 2)
        self.assertEqual(restored["nested"][0].height, 4)
        self.assertIsInstance(_snapshot((1, [2])), tuple)
