"""Check connection policy, configuration errors, and capture cleanup without a camera."""

from contextlib import redirect_stderr, redirect_stdout
import io
import sys
import sysconfig
import unittest
from unittest.mock import Mock, PropertyMock, patch

import numpy as np

from mecheye import _native, area_scan_3d_camera as a, shared as s
import test_camera


class CameraLifecycleTests(unittest.TestCase):
    def test_native_build_matches_interpreter_and_keeps_free_threading_enabled(self):
        self.assertEqual(tuple(_native.python_version), sys.version_info[:2])
        threaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
        self.assertEqual(_native.free_threaded, threaded)
        if threaded:
            self.assertFalse(sys._is_gil_enabled())

    def test_optional_ip_constructor_does_not_connect(self):
        with patch.object(a.Camera, "connect") as connect:
            camera = a.Camera("192.0.2.1")
            self.addCleanup(camera.disconnect)
            self.assertEqual(camera.ip, "192.0.2.1")
            self.assertFalse(camera.connected)
        connect.assert_not_called()

    def test_context_disconnects_and_preserves_body_exception(self):
        camera = a.Camera("192.0.2.1")
        self.addCleanup(camera.disconnect)
        with (
            patch.object(a.Camera, "connect", return_value=s.ErrorStatus()) as connect,
            patch.object(a.Camera, "disconnect", wraps=camera.disconnect) as disconnect,
        ):
            with self.assertRaisesRegex(ValueError, "body failed"):
                with camera as entered:
                    self.assertIs(entered, camera)
                    raise ValueError("body failed")
            connect.assert_called_once_with("192.0.2.1")
            disconnect.assert_called_once_with()

    def test_connection_failure_is_reported_once_without_logging(self):
        camera = a.Camera("192.0.2.1")
        self.addCleanup(camera.disconnect)
        with (
            patch.object(
                a.Camera,
                "connect",
                return_value=s.ErrorStatus(-1, "connection refused"),
            ) as connect,
            redirect_stdout(io.StringIO()) as stdout,
            redirect_stderr(io.StringIO()) as stderr,
        ):
            with self.assertRaisesRegex(s.MechEyeConnectionError, "connection refused"):
                camera.capture_points()
            connect.assert_called_once_with("192.0.2.1")
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_unconnected_conveniences_require_connection(self):
        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        with self.assertRaises(s.MechEyeConnectionError):
            camera.capture_points()
        with self.assertRaises(s.MechEyeConnectionError):
            _ = camera.device_info
        with self.assertRaises(s.MechEyeConnectionError):
            _ = camera.camera_parameters

    def test_exposure_mode_rejects_invalid_input_before_connecting(self):
        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        with patch.object(a.Camera, "connect") as connect:
            with self.assertRaises(ValueError):
                camera.configure_depth_source_2d_exposure("invalid")
        connect.assert_not_called()

    def test_exposure_configuration_checks_write_read_and_readback(self):
        camera = a.Camera()
        self.addCleanup(camera.disconnect)
        for mode, desired in (("timed", "Timed"), ("flash", "Flash")):
            user = Mock()
            user.set_enum_value.return_value = s.ErrorStatus()
            user.get_enum_value_string.return_value = [s.ErrorStatus(), desired]
            with (
                self.subTest(mode=mode),
                patch.object(camera, "_ensure_connected"),
                patch.object(camera, "current_user_set", return_value=user),
            ):
                self.assertEqual(camera.configure_depth_source_2d_exposure(mode), mode)
                user.set_enum_value.assert_called_once_with(
                    a.Scanning2DDepthSourceExposureMode.name, desired
                )
                user.get_enum_value_string.return_value = [
                    s.ErrorStatus(),
                    "unexpected",
                ]
                with self.assertRaisesRegex(
                    s.MechEyeConfigurationError, "readback mismatch"
                ):
                    camera.configure_depth_source_2d_exposure(mode)
                user.get_enum_value_string.return_value = [
                    s.ErrorStatus(-1, "read failed"),
                    "",
                ]
                with self.assertRaisesRegex(s.MechEyeConfigurationError, "read failed"):
                    camera.configure_depth_source_2d_exposure(mode)
                user.set_enum_value.return_value = s.ErrorStatus(-1, "write failed")
                with self.assertRaisesRegex(
                    s.MechEyeConfigurationError, "write failed"
                ):
                    camera.configure_depth_source_2d_exposure(mode)


class CaptureCleanupTests(unittest.TestCase):
    def setUp(self):
        self.camera, self.set_unit, self.image = (
            test_camera.ConvenienceTests.capture_setup(self)
        )

    def assert_units_restored(self):
        self.assertEqual(
            [item.args[0] for item in self.set_unit.call_args_list],
            [s.CoordinateUnit_Millimeter, s.CoordinateUnit_Meter],
        )

    def test_capture_failure_restores_units_and_preserves_sdk_message(self):
        with patch.object(
            a.Camera,
            "capture_depth_source_2d_and_3d",
            return_value=s.ErrorStatus(-4, "capture timed out"),
        ):
            with self.assertRaisesRegex(s.MechEyeCaptureError, "capture timed out"):
                self.camera.capture_points()
        self.assert_units_restored()

    def test_intrinsics_failure_restores_units(self):
        with patch.object(
            a.Camera,
            "get_camera_intrinsics",
            return_value=s.ErrorStatus(-1, "intrinsics unavailable"),
        ):
            with self.assertRaisesRegex(
                s.MechEyeCaptureError, "intrinsics unavailable"
            ):
                self.camera.capture_points()
        self.assert_units_restored()

    def test_empty_frame_and_grid_mismatch_restore_units(self):
        with patch.object(a, "Frame2DAnd3D") as frame:
            frame.return_value.frame_2d.return_value.is_empty.return_value = True
            with self.assertRaisesRegex(s.MechEyeCaptureError, "frame is empty"):
                self.camera.capture_points()
        self.assert_units_restored()
        self.set_unit.reset_mock()
        self.image.resize(3, 2)
        with self.assertRaisesRegex(s.MechEyeCaptureError, "does not match"):
            self.camera.capture_points()
        self.assert_units_restored()

    def test_unit_read_or_write_failure_prevents_capture(self):
        with patch.object(a.Camera, "capture_depth_source_2d_and_3d") as capture:
            with patch.object(
                a.Camera,
                "get_point_cloud_unit",
                return_value=[s.ErrorStatus(-1, "unit unavailable"), 0],
            ):
                with self.assertRaisesRegex(s.MechEyeCaptureError, "unit unavailable"):
                    self.camera.capture_points()
            self.set_unit.assert_not_called()
            self.set_unit.return_value = s.ErrorStatus(-1, "unit rejected")
            with self.assertRaisesRegex(s.MechEyeCaptureError, "unit rejected"):
                self.camera.capture_points()
            capture.assert_not_called()

    def test_millimeter_capture_does_not_change_units(self):
        with patch.object(
            a.Camera,
            "get_point_cloud_unit",
            return_value=[s.ErrorStatus(), s.CoordinateUnit_Millimeter],
        ):
            self.camera.capture_points()
        self.set_unit.assert_not_called()

    def test_restore_failure_is_reported(self):
        self.set_unit.side_effect = [
            s.ErrorStatus(),
            s.ErrorStatus(-1, "restore failed"),
        ]
        with self.assertRaisesRegex(s.MechEyeConfigurationError, "restore failed"):
            self.camera.capture_points()
        self.assert_units_restored()

    def test_invalid_mapped_points_become_nan_without_changing_grid(self):
        def mapping(depth, mask, intrinsics, cloud):
            cloud.resize(2, 2)
            values = [
                (10, 20, 1000),
                (0, 0, 0),
                (float("inf"), 20, 1000),
                (10, 20, float("nan")),
            ]
            for index, point in enumerate(values):
                cloud[index].x, cloud[index].y, cloud[index].z = point
            return s.ErrorStatus()

        with patch.object(a, "get_point_cloud_after_mapping", side_effect=mapping):
            _, points = self.camera.capture_points()
        np.testing.assert_array_equal(points[0, 0], [10, 20, 1000])
        self.assertTrue(np.isnan(points[0, 1]).all())
        self.assertTrue(np.isnan(points[1, 0, 0]))
        np.testing.assert_array_equal(points[1, 0, 1:], [20, 1000])
        self.assertTrue(np.isnan(points[1, 1, 2]))
        np.testing.assert_array_equal(points[1, 1, :2], [10, 20])
        self.assertEqual(points.shape, (2, 2, 3))
        self.assert_units_restored()

    def test_color_capture_returns_grayscale_and_owned_point_arrays(self):
        color = a.Color2DImage()
        color.resize(2, 2)
        for index in range(4):
            color[index].b, color[index].g, color[index].r = 0, 0, 255
        frame_type = a.Frame2DAnd3D

        def frame():
            result = frame_type()
            image = result.frame_2d()
            image.color_type = lambda: a.ColorTypeOf2DCamera_Color
            image.get_color_image = lambda: color
            result.frame_2d = lambda: image
            return result

        with patch.object(a, "Frame2DAnd3D", side_effect=frame):
            gray, points = self.camera.capture_points()
        np.testing.assert_array_equal(gray, np.full((2, 2), 76, dtype=np.uint8))
        self.assertEqual(points.shape, (2, 2, 3))
        color.release()
        self.assertTrue(gray.flags.c_contiguous)
        np.testing.assert_array_equal(gray, 76)
        self.assert_units_restored()

    def test_empty_depth_restores_units(self):
        frame_type = a.Frame2DAnd3D

        def frame():
            result = frame_type()
            result.frame_3d().get_depth_map().release()
            return result

        with patch.object(a, "Frame2DAnd3D", side_effect=frame):
            with self.assertRaisesRegex(s.MechEyeCaptureError, "depth map is empty"):
                self.camera.capture_points()
        self.assert_units_restored()

    def test_invalid_mapped_grids_restore_units(self):
        for size in (None, (3, 2)):

            def mapping(depth, mask, intrinsics, cloud):
                if size is not None:
                    cloud.resize(*size)
                return s.ErrorStatus()

            with (
                self.subTest(size=size),
                patch.object(a, "get_point_cloud_after_mapping", side_effect=mapping),
            ):
                with self.assertRaisesRegex(s.MechEyePointCloudError, "does not match"):
                    self.camera.capture_points()
            self.assert_units_restored()
            self.set_unit.reset_mock()
