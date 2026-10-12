"""Exercise camera metadata conversion and native failures without network devices."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from mecheye import area_scan_3d_camera as a, shared as s


class CameraStateTests(unittest.TestCase):
    def setUp(self):
        self.camera = a.Camera()
        self.addCleanup(self.camera.disconnect)

    def test_invalid_ip_and_camera_info_connects_do_not_change_connection(self):
        for target in ("invalid-ip", a.CameraInfo()):
            with self.subTest(target=type(target)):
                status = self.camera.connect(target, 1)
                self.assertEqual(
                    status.error_code, s.ErrorStatus.MMIND_STATUS_INVALID_INPUT_ERROR
                )
                self.assertTrue(status.error_description)
                self.assertFalse(self.camera.connected)
                self.assertIsNone(self.camera.ip)

    def test_successful_connect_remembers_string_or_info_ip(self):
        for target in ("192.0.2.1", a.CameraInfo()):
            if isinstance(target, a.CameraInfo):
                target.ip_address = "192.0.2.2"
            with (
                self.subTest(target=type(target)),
                patch.object(
                    self.camera,
                    "_native",
                    SimpleNamespace(connect=lambda *args: s.ErrorStatus()._native),
                ),
            ):
                self.assertTrue(self.camera.connect(target).is_ok())
                self.assertEqual(
                    self.camera.ip,
                    target.ip_address if isinstance(target, a.CameraInfo) else target,
                )

    def test_point_cloud_unit_roundtrip_is_shared_between_camera_copies(self):
        copied = a.Camera(self.camera)
        for unit in (s.CoordinateUnit_Meter, s.CoordinateUnit_Millimeter):
            self.assertTrue(self.camera.set_point_cloud_unit(unit).is_ok())
            status, actual = copied.get_point_cloud_unit()
            self.assertTrue(status.is_ok())
            self.assertEqual(actual, unit)
        for method, args in (
            ("set_heartbeat_interval", (1000,)),
            ("save_virtual_device_file", ("missing.mraw",)),
        ):
            status = getattr(self.camera, method)(*args)
            self.assertEqual(
                status.error_code, s.ErrorStatus.MMIND_STATUS_INVALID_DEVICE
            )
        transformation = a.get_transformation_params(self.camera)
        self.assertIsInstance(transformation, a.FrameTransformation)
        self.assertEqual(list(transformation.translation), [0.0] * 3)

    def test_device_info_uses_sdk_fields_and_preserves_error_messages(self):
        def fill(info):
            info.model, info.device_name, info.serial_number = "Model", "Camera", "123"
            info.ip_address, info.subnet_mask = "192.0.2.1", "255.255.255.0"
            info.platform, info.ip_assignment_method, info.port = (
                s.Platform_PLATFORM_C,
                s.IpAssignmentMethod_Static,
                5000,
            )
            info.hardware_version, info.firmware_version = s.Version(
                "2.6.0"
            ), s.Version("2.5.4")
            info.supported = True
            return s.ErrorStatus()

        with patch.object(self.camera, "get_camera_info", side_effect=fill):
            info = self.camera.device_info
        self.assertEqual(info["ip"], "192.0.2.1")
        self.assertEqual(info["platform"], "PlatformC")
        self.assertEqual(info["firmware_version"], "2.5.4")
        self.assertEqual(info["hardware_version"], "2.6.0")
        self.assertEqual(info["ip_assignment_method"], "Static")
        self.assertEqual(info["serial_number"], "123")
        self.assertTrue(info["supported"])
        with patch.object(
            self.camera,
            "get_camera_info",
            return_value=s.ErrorStatus(-1, "metadata unavailable"),
        ):
            with self.assertRaisesRegex(
                s.MechEyeConnectionError, "metadata unavailable"
            ):
                _ = self.camera.device_info

    def test_camera_parameters_keep_matrix_order_distortion_order_and_units(self):
        def fill(info):
            for name, focal in (("depth", 1000), ("texture", 500)):
                camera = getattr(info, name)
                camera.camera_matrix.fx, camera.camera_matrix.fy = focal, focal + 1
                camera.camera_matrix.cx, camera.camera_matrix.cy = 10, 20
                for index, field in enumerate(("k1", "k2", "p1", "p2", "k3")):
                    setattr(camera.camera_distortion, field, index / 10)
            info.depth_to_texture.translation = [10, 20, 30]
            return s.ErrorStatus()

        with patch.object(self.camera, "get_camera_intrinsics", side_effect=fill):
            parameters = self.camera.camera_parameters
        self.assertEqual(
            parameters["depth"]["intrinsic_matrix"], [1000, 0, 10, 0, 1001, 20, 0, 0, 1]
        )
        self.assertEqual(parameters["texture"]["intrinsic_matrix"][0], 500)
        self.assertEqual(
            parameters["depth"]["distortion_k1_k2_p1_p2_k3"], [0, 0.1, 0.2, 0.3, 0.4]
        )
        self.assertEqual(
            parameters["T_texture_camera_depth_camera_matrix_mm"],
            [[1, 0, 0, 10], [0, 1, 0, 20], [0, 0, 1, 30], [0, 0, 0, 1]],
        )

    def test_unconnected_hand_eye_calibration_returns_errors_without_output_data(self):
        calibration = a.HandEyeCalibration()
        image, transform, corner = (
            a.Color2DImage(),
            a.HandEyeTransformation(),
            s.PointXYZ(),
        )
        cases = [
            (
                "initialize_calibration",
                (
                    self.camera,
                    calibration.CameraMountingMode_EyeInHand,
                    calibration.CalibrationBoardModel_BDB_5,
                ),
            ),
            ("add_pose_and_detect", (self.camera, transform, image, 1)),
            ("calculate_extrinsics", (self.camera, transform)),
            ("test_recognition", (self.camera, image, 1)),
            ("extract_current_image_first_corner", (self.camera, corner, 1)),
        ]
        for method, args in cases:
            with self.subTest(method=method):
                result = getattr(calibration, method)(*args)
                self.assertIsInstance(result, s.ErrorStatus)
                self.assertFalse(result.is_ok())
                self.assertTrue(result.error_description)
                self.assertTrue(image.is_empty())
        pose = a.HandEyeTransformation(1, 2, 3, 1, 0, 0, 0)
        self.assertEqual(
            [float(value) for value in pose.to_string().split(",")],
            [1, 2, 3, 1, 0, 0, 0],
        )
