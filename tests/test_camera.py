"""Validate the SDK API contract, real native data operations, and threaded access."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import weakref

import numpy as np

import mecheye
from mecheye import area_scan_3d_camera as a, shared as s
from mecheye._compat import _api_lock, _snapshot, _unwrap, _wrap


class ApiTests(unittest.TestCase):
    def test_public_surface_matches_reference_package(self):
        reference = json.loads(Path(__file__).with_name("api_surface.json").read_text())
        for name, spec in reference["modules"].items():
            module = importlib.import_module("mecheye." + name)
            for cls, members in spec["classes"].items():
                with self.subTest(module=name, cls=cls):
                    target = getattr(module, cls)
                    for member in members:
                        self.assertTrue(hasattr(target, member), member)
            for member in spec["functions"] + spec["constants"]:
                with self.subTest(module=name, member=member):
                    self.assertTrue(hasattr(module, member))

    def test_discovery_preserves_vector_type(self):
        with patch.object(a, "function", return_value=[]):
            result = a.Camera.discover_cameras(1)
        self.assertIsInstance(result, a.VectorCameraInfo)
        self.assertTrue(result.empty())

    def test_camera_copy_shares_connection_and_event_state(self):
        original = a.Camera("192.168.1.100")
        copied = a.Camera(original)
        self.assertEqual(copied.ip, original.ip)
        self.assertIs(copied._event_context, original._event_context)
        original._callbacks[1] = (a.EventCallbackBase(), False)
        self.assertEqual(len(copied._callbacks), 1)
        copied.disconnect()
        self.assertEqual(original._callbacks, {})
        self.assertFalse(original.connected)

    def test_root_camera_export_matches_camera_class(self):
        self.assertIs(mecheye.Camera, a.Camera)

    def test_status_fields_and_version_comparisons(self):
        self.assertTrue(s.ErrorStatus().is_ok())
        error = s.ErrorStatus(s.ErrorStatus.MMIND_STATUS_INVALID_INPUT_ERROR, "invalid")
        self.assertFalse(error.is_ok())
        self.assertEqual(error.error_code, -7)
        self.assertEqual(error.error_description, "invalid")
        error.error_code = 0
        self.assertTrue(error.is_ok())
        self.assertLess(s.Version("2.5.4"), s.Version(2, 6, 0))
        self.assertIn("V2.6.0", s.get_api_version_info())
        self.assertEqual(
            s.ip_assignment_method_to_string(s.IpAssignmentMethod_DHCP), "DHCP"
        )

    def test_unconnected_sdk_operations_return_status(self):
        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        cases = [
            ("get_camera_info", (a.CameraInfo(),)),
            ("get_camera_status", (a.CameraStatus(),)),
            ("get_camera_resolutions", (a.CameraResolutions(),)),
            ("get_camera_intrinsics", (a.CameraIntrinsics(),)),
            ("capture_2d", (a.Frame2D(), 1)),
            ("capture_depth_source_2d", (a.Frame2D(), 1)),
            ("capture_3d", (a.Frame3D(), 1)),
            ("capture_3d_with_normal", (a.Frame3D(), 1)),
            ("capture_2d_and_3d", (a.Frame2DAnd3D(), 1)),
            ("capture_depth_source_2d_and_3d", (a.Frame2DAnd3D(), 1)),
            ("capture_2d_and_3d_with_normal", (a.Frame2DAnd3D(), 1)),
            ("capture_stereo_2d", (a.Frame2D(), a.Frame2D(), False, 1)),
        ]
        for method, args in cases:
            with self.subTest(method=method):
                status = getattr(camera, method)(*args)
                self.assertIsInstance(status, s.ErrorStatus)
                expected = (
                    -3
                    if method
                    in {
                        "capture_depth_source_2d",
                        "capture_depth_source_2d_and_3d",
                        "capture_stereo_2d",
                    }
                    else -1
                )
                self.assertEqual(status.error_code, expected)
        result = camera.get_point_cloud_unit()
        self.assertIsInstance(result, list)
        self.assertEqual(result[0].error_code, 0)
        user = camera.current_user_set()
        self.assertIsInstance(user, s.UserSet)
        for method in [
            "get_int_value",
            "get_float_value",
            "get_bool_value",
            "get_enum_value",
            "get_enum_value_string",
        ]:
            result = getattr(user, method)("missing")
            self.assertIsInstance(result, list)
            self.assertEqual(result[0].error_code, -1)
        for method in [
            "get_roi_value",
            "get_range_value",
            "get_float_array_value",
            "get_roi_array_value",
        ]:
            result = getattr(user, method)("missing")
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[0].error_code, -1)
        self.assertIsNone(user.get_parameter("missing"))
        self.assertEqual(user.get_available_parameters(), [])
        self.assertIsInstance(camera.user_set_manager(), s.UserSetManager)
        self.assertEqual(
            camera.user_set_manager().get_all_user_set_names()[0].error_code, -1
        )

    def test_array_layouts_match_array_contract(self):
        cases = [
            (a.GrayScale2DImage, [("data", (2, 3), np.uint8)]),
            (a.Color2DImage, [("data", (2, 3, 3), np.uint8)]),
            (a.DepthMap, [("data", (2, 3), np.float32)]),
            (a.UntexturedPointCloud, [("data", (2, 3, 3), np.float32)]),
            (a.UntexturedPointCloudWithNormals, [("data", (2, 3, 7), np.float32)]),
            (
                a.TexturedPointCloud,
                [("vertices", (2, 3, 3), np.float32), ("colors", (2, 3, 3), np.uint8)],
            ),
            (
                a.TexturedPointCloudWithNormals,
                [
                    ("vertices", (2, 3, 3), np.float32),
                    ("colors", (2, 3, 3), np.uint8),
                    ("normals", (2, 3, 4), np.float32),
                ],
            ),
        ]
        for cls, accessors in cases:
            with self.subTest(cls=cls.__name__):
                array = cls()
                for name, shape, dtype in accessors:
                    value = getattr(array, name)()
                    self.assertEqual(value.shape, (1,))
                    self.assertEqual(value.dtype, np.float64)
                array.resize(3, 2)
                for name, shape, dtype in accessors:
                    value = getattr(array, name)()
                    self.assertEqual(value.shape, shape)
                    self.assertEqual(value.dtype, dtype)
                clone = array.clone()
                array.release()
                self.assertFalse(clone.is_empty())

    def test_pixel_mutation_nested_normals_and_owned_arrays(self):
        image = a.Color2DImage()
        image.resize(2, 1)
        pixel = image.at(0, 1)
        pixel.b, pixel.g, pixel.r = 12, 34, 56
        value = image.data()
        np.testing.assert_array_equal(value[0, 1], [12, 34, 56])
        clone = image.clone()
        pixel.b = 99
        self.assertEqual(clone.at(0, 1).b, 12)
        self.assertEqual(value[0, 1, 0], 12)
        cloud = a.UntexturedPointCloudWithNormals()
        cloud.resize(1, 1)
        cloud[0].point.x = 5
        cloud[0].normal.curvature = 0.25
        self.assertEqual(cloud.data()[0, 0, 0], 5)
        self.assertEqual(cloud.data()[0, 0, 6], 0.25)

    def test_pixel_reference_expiration_is_safe(self):
        image = a.GrayScale2DImage()
        image.resize(1, 1)
        pixel = image[0]
        image.resize(2, 2)
        with self.assertRaises(ReferenceError):
            pixel.gray = 1
        pixel = image[0]
        image.release()
        with self.assertRaises(ReferenceError):
            _ = pixel.gray

    def test_transformation_wrappers_and_sdk_point_cloud_transform(self):
        transform = a.FrameTransformation()
        self.assertIsInstance(transform.rotation, a.doubleMatrix3)
        self.assertIsInstance(transform.rotation[0], a.doubleArray3)
        transform.__translate__(10, 20, 30)
        transform.rotation[0][0] = 2
        cloud = a.UntexturedPointCloud()
        cloud.resize(1, 1)
        cloud[0].x, cloud[0].y, cloud[0].z = 1, 2, 3
        result = a.transform_point_cloud(transform, cloud)
        np.testing.assert_allclose(result.data()[0, 0], [12, 22, 33])
        np.testing.assert_allclose(cloud.data()[0, 0], [1, 2, 3])
        matrix = a.doubleMatrix3()
        matrix[1][2] = 9
        transform.rotation = matrix
        self.assertEqual(transform.rotation[1][2], 9)

    def test_parameter_descriptors_and_vector_copy_semantics(self):
        self.assertEqual(
            a.Scanning2DDepthSourceExposureMode.name, "Scan2DPatternRoleExposureMode"
        )
        self.assertEqual(a.Scanning2DDepthSourceExposureMode.type, s.Parameter._Enum)
        self.assertEqual(a.Scanning2DDepthSourceExposureMode.Value_Flash, 1)
        limit = a.Scanning3DExposureSequence.range()
        limit.max = 1
        self.assertEqual(a.Scanning3DExposureSequence.range().max, 99)
        self.assertEqual(a.Scanning3DExposureSequence.max_size(), 3)
        roi = s.ROI(1, 2, 3, 4)
        vector = s.MechEyeVectorROI()
        vector.push_back(roi)
        roi.width = 99
        self.assertEqual(vector[0].width, 3)
        self.assertEqual(vector.begin().value().width, 3)
        self.assertEqual(vector.size(), 1)
        self.assertEqual(len(list(vector)), 1)
        vector.resize(3)
        vector.erase(vector.begin(), vector.begin() + 2)
        self.assertEqual(vector.size(), 1)

    def test_sdk_mapping_and_file_export_without_extra_dependencies(self):
        depth = a.DepthMap()
        mask = a.GrayScale2DImage()
        depth.resize(2, 2)
        mask.resize(2, 2)
        for index in range(4):
            depth[index].z = 1000
            mask[index].gray = 255
        intrinsics = a.CameraIntrinsics()
        for camera in (intrinsics.depth, intrinsics.texture):
            camera.camera_matrix.fx = 1000
            camera.camera_matrix.fy = 1000
        cloud = a.UntexturedPointCloud()
        status = a.get_point_cloud_after_mapping(depth, mask, intrinsics, cloud)
        self.assertTrue(status.is_ok(), status.error_description)
        self.assertEqual(cloud.data().shape, (2, 2, 3))
        np.testing.assert_allclose(cloud.data()[..., 2], 1000)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cloud.ply"
            status = a.Frame3D.save_point_cloud(
                cloud, s.FileFormat_PLY, str(path), True
            )
            self.assertTrue(status.is_ok(), status.error_description)
            self.assertTrue(path.read_bytes().startswith(b"ply"))

    def test_threaded_pixel_updates_and_clone(self):
        cloud = a.UntexturedPointCloud()
        cloud.resize(8, 1)

        def update(index):
            for value in range(50):
                cloud[index].x = value
                cloud[index].y = index
                cloud.clone().data()

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(update, range(8)))
        np.testing.assert_allclose(cloud.data()[0, :, 0], 49)
        np.testing.assert_allclose(cloud.data()[0, :, 1], np.arange(8))

    def test_event_data_can_be_read_during_a_blocking_sdk_operation(self):
        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        event = a.EventData()
        event.event_id = a.CameraEvent.CAMERA_EVENT_EXPOSURE_END
        event.frame_id = 42
        payload = a.PayloadMember()
        payload.name = "frame"
        payload.type = a.PayloadMember.Type__Int64
        payload.value.int_64value = 42
        pending = [(_unwrap(event), [_unwrap(payload)])]
        done = threading.Event()
        values = []

        class Callback(a.EventCallbackBase):
            def process_event_with_payload(self, eventData, extraPayload):
                values.append((eventData.frame_id, extraPayload[0].value.int_64value))
                done.set()

        camera._callbacks[event.event_id] = (Callback(), False)
        worker = threading.Thread(
            target=a._dispatch_events, args=(weakref.ref(camera), camera._event_stop)
        )
        with patch.object(
            camera,
            "_native",
            SimpleNamespace(poll_events=lambda: [pending.pop()] if pending else []),
        ):
            # Hold the SDK lock as a blocking capture would; callback access must still work.
            with _api_lock:
                worker.start()
                self.assertTrue(done.wait(2))
            camera._event_stop.set()
            worker.join(2)
        self.assertEqual(values, [(42, 42)])
        self.assertEqual(camera.pop_callback_errors(), [])


class ConvenienceTests(unittest.TestCase):
    def capture_setup(self):
        from unittest.mock import PropertyMock

        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        depth = a.DepthMap()
        image = a.GrayScale2DImage()
        depth.resize(2, 2)
        image.resize(2, 2)
        for index in range(4):
            depth[index].z = 1000
            image[index].gray = 80

        class Fake2D:
            def is_empty(self):
                return False

            def color_type(self):
                return a.ColorTypeOf2DCamera_Monochrome

            def get_gray_scale_image(self):
                return image

        class Fake3D:
            def is_empty(self):
                return False

            def get_depth_map(self):
                return depth

        class FakeFrame:
            def frame_2d(self):
                return Fake2D()

            def frame_3d(self):
                return Fake3D()

        def intrinsics(out):
            for value in (out.depth, out.texture):
                value.camera_matrix.fx = 1000
                value.camera_matrix.fy = 1000
            return s.ErrorStatus()

        patches = [
            patch.object(
                a.Camera, "connected", new_callable=PropertyMock, return_value=True
            ),
            patch.object(a, "Frame2DAnd3D", FakeFrame),
            patch.object(
                a.Camera,
                "get_point_cloud_unit",
                return_value=[s.ErrorStatus(), s.CoordinateUnit_Meter],
            ),
            patch.object(
                a.Camera, "capture_depth_source_2d_and_3d", return_value=s.ErrorStatus()
            ),
            patch.object(a.Camera, "get_camera_intrinsics", side_effect=intrinsics),
            patch.object(
                a.Camera, "set_point_cloud_unit", return_value=s.ErrorStatus()
            ),
        ]
        mocks = [item.start() for item in patches]
        for item in patches:
            self.addCleanup(item.stop)
        return camera, mocks[-1], image

    def test_capture_points_uses_frames_and_restores_units(self):
        camera, set_unit, image = self.capture_setup()
        gray, points = camera.capture_points(timeoutMs=250)
        self.assertEqual(gray.dtype, np.uint8)
        self.assertEqual(gray.shape, (2, 2))
        self.assertEqual(points.dtype, np.float64)
        self.assertEqual(points.shape, (2, 2, 3))
        np.testing.assert_allclose(points[..., 2], 1000)
        self.assertEqual(
            [item.args[0] for item in set_unit.call_args_list],
            [s.CoordinateUnit_Millimeter, s.CoordinateUnit_Meter],
        )
        image[0].gray = 0
        self.assertEqual(gray[0, 0], 80)

    def test_mapping_failure_still_restores_units(self):
        camera, set_unit, image = self.capture_setup()
        with patch.object(
            a,
            "get_point_cloud_after_mapping",
            return_value=s.ErrorStatus(-6, "mapping failed"),
        ):
            with self.assertRaises(s.MechEyePointCloudError):
                camera.capture_points()
        self.assertEqual(
            [item.args[0] for item in set_unit.call_args_list],
            [s.CoordinateUnit_Millimeter, s.CoordinateUnit_Meter],
        )

    def test_callback_exception_is_retrievable_without_logging(self):
        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        event = a.EventData()
        event.event_id = a.CameraEvent.CAMERA_EVENT_DISCONNECTED
        pending = [(_unwrap(event), [])]
        called = threading.Event()

        class Callback(a.EventCallbackBase):
            def process_event(self, eventData):
                called.set()
                raise ValueError("Callback failed")

        camera._callbacks[event.event_id] = (Callback(), False)
        worker = threading.Thread(
            target=a._dispatch_events, args=(weakref.ref(camera), camera._event_stop)
        )
        with patch.object(
            camera,
            "_native",
            SimpleNamespace(poll_events=lambda: [pending.pop()] if pending else []),
        ):
            worker.start()
            self.assertTrue(called.wait(2))
            camera._event_stop.set()
            worker.join(2)
        errors = camera.pop_callback_errors()
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValueError)
        self.assertEqual(camera.pop_callback_errors(), [])


if __name__ == "__main__":
    unittest.main()
