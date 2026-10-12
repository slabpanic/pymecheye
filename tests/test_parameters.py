"""Validate user-set errors, handle lifetimes, and typed parameter conversion."""

import unittest
from unittest.mock import patch

from mecheye import area_scan_3d_camera as a, shared as s


class UserSetTests(unittest.TestCase):
    def setUp(self):
        self.camera = a.Camera()
        self.addCleanup(self.camera.disconnect)
        self.user = self.camera.current_user_set()
        self.manager = self.camera.user_set_manager()

    def assert_invalid_device(self, status):
        self.assertIsInstance(status, s.ErrorStatus)
        self.assertEqual(status.error_code, s.ErrorStatus.MMIND_STATUS_INVALID_DEVICE)
        self.assertTrue(status.error_description)

    def test_unconnected_user_set_metadata_has_stable_result_types(self):
        result = self.user.get_name()
        self.assertIsInstance(result, list)
        self.assert_invalid_device(result[0])
        self.assertEqual(result[1], "")
        result = self.user.get_available_parameter_names()
        self.assertIsInstance(result, tuple)
        self.assert_invalid_device(result[0])
        self.assertEqual(result[1], [])
        self.assertEqual(self.user.get_available_parameters(), [])
        self.assertIsNone(self.user["missing"])
        result = self.user.get_profile_roi_value("missing")
        self.assertIsInstance(result, tuple)
        self.assert_invalid_device(result[0])
        self.assertIsInstance(result[1], s.ProfileROI)

    def test_all_user_set_writes_report_connection_errors(self):
        for method, args in [
            ("rename", ("custom",)),
            ("reset_all_parameters_to_default_values", ()),
            ("save_all_parameters_to_device", ()),
            ("set_int_value", ("missing", 42)),
            ("set_float_value", ("missing", 1.25)),
            ("set_bool_value", ("missing", True)),
            ("set_enum_value", ("missing", 1)),
            ("set_enum_value", ("missing", "Timed")),
            ("set_roi_value", ("missing", s.ROI(1, 2, 3, 4))),
            ("set_profile_roi_value", ("missing", s.ProfileROI(1, 2, 3))),
            ("set_range_value", ("missing", s.RangeInt(1, 10))),
            ("set_float_array_value", ("missing", s.WrappedDoubleList([1, 2]))),
        ]:
            with self.subTest(method=method, args=args):
                self.assert_invalid_device(getattr(self.user, method)(*args))

    def test_manager_operations_reject_unconnected_and_expired_handles(self):
        for expired in (False, True):
            with self.subTest(expired=expired):
                if expired:
                    self.camera.disconnect()
                current = self.manager.current_user_set()
                self.assertIsInstance(current, s.UserSet)
                self.assert_invalid_device(current.get_name()[0])
                result = self.manager.get_all_user_set_names()
                self.assertIsInstance(result, tuple)
                self.assert_invalid_device(result[0])
                self.assertEqual(result[1], [])
                for method in (
                    "select_user_set",
                    "add_user_set",
                    "delete_user_set",
                    "save_to_file",
                    "load_from_file",
                ):
                    with self.subTest(method=method):
                        self.assert_invalid_device(
                            getattr(self.manager, method)("missing")
                        )

    def test_user_set_retains_camera_resource_after_wrapper_is_collected(self):
        self.camera.disconnect()
        camera = a.Camera()
        user = camera.current_user_set()
        manager = camera.user_set_manager()
        del camera
        self.assert_invalid_device(user.get_name()[0])
        self.assert_invalid_device(manager.get_all_user_set_names()[0])

    def test_device_owned_handles_have_no_public_constructor(self):
        for cls in (
            s.Parameter,
            s.IntParameter,
            s.UserSet,
            s.UserSetManager,
            s.VirtualUserSet,
        ):
            with self.subTest(cls=cls.__name__):
                with self.assertRaisesRegex(AttributeError, "No constructor"):
                    cls()

    def test_typed_conversion_checks_kind_and_preserves_shared_handle(self):
        classes = (
            s.IntParameter,
            s.FloatParameter,
            s.BoolParameter,
            s.EnumParameter,
            s.RoiParameter,
            s.RangeParameter,
            s.FloatArrayParameter,
            s.RoiArrayParameter,
            s.ProfileRoiParameter,
        )
        for cls in classes:
            with self.subTest(cls=cls.__name__):
                self.assertIsNone(cls.convert_from_parameter(None))
                with self.assertRaisesRegex(TypeError, "Expected Parameter"):
                    cls.convert_from_parameter("missing")
                # Conversion is a Python adapter operation; a live device owns the native handle.
                generic = object.__new__(s.Parameter)
                generic._native = object()
                generic._owner = self.user
                handles = s.MechEyeVectorParameterPointer([generic])
                self.assertIs(handles[0], generic)
                with patch.object(s.Parameter, "type", return_value=cls._kind):
                    typed = cls.convert_from_parameter(generic)
                self.assertIsInstance(typed, cls)
                self.assertIs(typed._native, generic._native)
                self.assertIs(typed._owner, self.user)
                with patch.object(s.Parameter, "type", return_value=-1):
                    self.assertIsNone(cls.convert_from_parameter(generic))
