"""Exercise grayscale conversion and caller-controlled interactive helpers."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import Mock, patch

import numpy as np

from mecheye import (
    area_scan_3d_camera as a,
    area_scan_3d_camera_utils as utils,
    shared as s,
)


class GrayscaleTests(unittest.TestCase):
    def test_grayscale_output_owns_contiguous_copy(self):
        source = np.arange(24, dtype=np.uint16).reshape(4, 6)[:, ::2]
        result = utils.image_to_gray(source)
        np.testing.assert_array_equal(result, source)
        self.assertEqual(result.dtype, source.dtype)
        self.assertTrue(result.flags.c_contiguous)
        self.assertFalse(np.shares_memory(result, source))
        source[:] = 0
        self.assertGreater(result.max(), 0)

    def test_uint8_bgr_primary_colors_and_white(self):
        bgr = np.array(
            [[[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]]], dtype=np.uint8
        )
        result = utils.image_to_gray(bgr)
        np.testing.assert_array_equal(result, [[29, 150, 76, 255]])
        self.assertEqual(result.dtype, np.uint8)

    def test_uint16_color_does_not_overflow(self):
        bgr = np.full((3, 2, 3), 65535, dtype=np.uint16)
        result = utils.image_to_gray(bgr)
        np.testing.assert_array_equal(result, np.full((3, 2), 65535, dtype=np.uint16))

    def test_float_color_and_alpha_are_handled_independently(self):
        image = np.array(
            [[[1, 0, 0, 0], [0, 1, 0, 1], [0, 0, 1, 999]]], dtype=np.float32
        )
        result = utils.image_to_gray(image)
        np.testing.assert_allclose(result, [[0.114, 0.587, 0.299]], rtol=1e-6)
        self.assertEqual(result.dtype, np.float32)
        image[..., 3] = -1
        np.testing.assert_array_equal(result, utils.image_to_gray(image))

    def test_invalid_dimensions_channels_and_color_dtypes_are_rejected(self):
        for shape in ((3,), (2, 2, 1), (2, 2, 2), (2, 2, 5), (1, 2, 2, 3)):
            with self.subTest(shape=shape):
                with self.assertRaises(ValueError):
                    utils.image_to_gray(np.zeros(shape, dtype=np.uint8))
        for dtype in (np.float64, np.int32, np.bool_):
            with self.subTest(dtype=dtype):
                with self.assertRaises(TypeError):
                    utils.image_to_gray(np.zeros((2, 2, 3), dtype=dtype))

    def test_empty_color_grid_preserves_shape(self):
        self.assertEqual(
            utils.image_to_gray(np.zeros((0, 2, 4), dtype=np.uint8)).shape, (0, 2)
        )


class InteractiveHelperTests(unittest.TestCase):
    def test_confirmation_reprompts_and_accepts_case_insensitively(self):
        for answer, expected in (("Y", True), ("N", False)):
            with self.subTest(answer=answer):
                with patch("builtins.input", side_effect=["invalid", answer]) as prompt:
                    self.assertEqual(utils.confirm_capture_3d(), expected)
                    self.assertEqual(prompt.call_count, 2)

    def test_no_discovered_cameras_never_prompts_or_connects(self):
        camera = Mock()
        with (
            patch.object(utils, "_available_cameras", return_value=[]),
            patch("builtins.input") as prompt,
        ):
            self.assertFalse(utils.find_and_connect(camera))
            self.assertEqual(utils.find_and_connect_multi_camera(), [])
        prompt.assert_not_called()
        camera.connect.assert_not_called()

    def test_selection_rejects_invalid_indices_and_returns_connection_status(self):
        info = a.CameraInfo()
        for status, expected in (
            (s.ErrorStatus(), True),
            (s.ErrorStatus(-1, "failed"), False),
        ):
            with self.subTest(expected=expected):
                camera = Mock()
                camera.connect.return_value = status
                with (
                    patch.object(utils, "_available_cameras", return_value=[info]),
                    patch("builtins.input", side_effect=["invalid", "-1", "3", "0"]),
                    redirect_stdout(io.StringIO()) as output,
                ):
                    self.assertEqual(utils.find_and_connect(camera), expected)
                camera.connect.assert_called_once_with(info)
                self.assertEqual(bool(output.getvalue()), not expected)
