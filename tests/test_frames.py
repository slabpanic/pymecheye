"""Exercise real frame ownership, mapping, transformations, and SDK file writers."""

from pathlib import Path
import tempfile
import unittest

import numpy as np

from mecheye import area_scan_3d_camera as a, shared as s


class FrameTests(unittest.TestCase):
    def test_empty_frames_keep_metadata_and_copies_valid_after_clear(self):
        for cls in (a.Frame2D, a.Frame3D):
            with self.subTest(frame=cls.__name__):
                frame = cls()
                clone = cls(frame)
                self.assertTrue(frame.is_empty())
                self.assertEqual(
                    (frame.image_size().width, frame.image_size().height), (0, 0)
                )
                self.assertEqual(frame.frame_id(), 0)
                self.assertIsNone(frame.clear())
                self.assertTrue(clone.is_empty())
                self.assertEqual(clone.frame_id(), 0)
        self.assertEqual(a.Frame2D().color_type(), a.ColorTypeOf2DCamera_Undefined)

    def test_empty_frame_accessors_return_independent_typed_containers(self):
        cases = [
            (a.Frame2D(), "get_gray_scale_image", a.GrayScale2DImage),
            (a.Frame2D(), "get_color_image", a.Color2DImage),
            (a.Frame3D(), "get_depth_map", a.DepthMap),
            (a.Frame3D(), "get_untextured_point_cloud", a.UntexturedPointCloud),
            (
                a.Frame3D(),
                "get_untextured_point_cloud_with_normals",
                a.UntexturedPointCloudWithNormals,
            ),
            (a.Frame2DAnd3D(), "get_textured_point_cloud", a.TexturedPointCloud),
            (
                a.Frame2DAnd3D(),
                "get_textured_point_cloud_with_normals",
                a.TexturedPointCloudWithNormals,
            ),
        ]
        for frame, method, cls in cases:
            with self.subTest(method=method):
                value = getattr(frame, method)()
                self.assertIsInstance(value, cls)
                self.assertTrue(value.is_empty())
                value.resize(2, 1)
                frame.clear()
                self.assertEqual((value.width(), value.height()), (2, 1))
                self.assertTrue(getattr(frame, method)().is_empty())

    def test_combined_frame_components_survive_parent_clear(self):
        frame = a.Frame2DAnd3D()
        copied = a.Frame2DAnd3D(frame)
        image, cloud = frame.frame_2d(), frame.frame_3d()
        frame.clear()
        del frame
        self.assertTrue(image.is_empty())
        self.assertTrue(cloud.is_empty())
        self.assertTrue(copied.frame_2d().is_empty())
        self.assertTrue(copied.frame_3d().is_empty())
        orthogonal = cloud.get_orthogonal_depth_map()
        self.assertIsInstance(orthogonal, list)
        self.assertEqual(len(orthogonal), 5)
        self.assertIsInstance(orthogonal[0], a.DepthMap)
        self.assertTrue(orthogonal[0].is_empty())
        self.assertEqual(orthogonal[1:], [0.0] * 4)

    def test_empty_frame_exports_report_no_data_without_creating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.ply"
            for frame, method in [
                (a.Frame3D(), "save_untextured_point_cloud"),
                (a.Frame3D(), "save_untextured_point_cloud_with_normals"),
                (a.Frame2DAnd3D(), "save_textured_point_cloud"),
                (a.Frame2DAnd3D(), "save_textured_point_cloud_with_normals"),
            ]:
                with self.subTest(method=method):
                    status = getattr(frame, method)(s.FileFormat_PLY, str(path), True)
                    self.assertEqual(
                        status.error_code, s.ErrorStatus.MMIND_STATUS_NO_DATA_ERROR
                    )
                    self.assertTrue(status.error_description)
                    self.assertFalse(path.exists())

    def test_all_point_cloud_types_export_coordinates_colors_and_normals(self):
        cases = [
            (a.UntexturedPointCloud, a.Frame3D.save_point_cloud),
            (
                a.UntexturedPointCloudWithNormals,
                a.Frame3D.save_point_cloud_with_normals,
            ),
            (a.TexturedPointCloud, a.Frame2DAnd3D.save_point_cloud),
            (
                a.TexturedPointCloudWithNormals,
                a.Frame2DAnd3D.save_point_cloud_with_normals,
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for cls, writer in cases:
                with self.subTest(cloud=cls.__name__):
                    cloud = cls()
                    cloud.resize(2, 1)
                    for index in range(2):
                        pixel = cloud[index]
                        point = getattr(
                            pixel, "color_point", getattr(pixel, "point", pixel)
                        )
                        point.x, point.y, point.z = index + 1, 2, 1000
                        if hasattr(point, "b"):
                            point.b, point.g, point.r = 12, 34, 56
                        if hasattr(pixel, "normal"):
                            pixel.normal.x, pixel.normal.y, pixel.normal.z = 0, 0, 1
                    path = Path(directory) / f"{cls.__name__}.ply"
                    status = writer(
                        cloud,
                        s.FileFormat_PLY,
                        str(path),
                        True,
                        s.CoordinateUnit_Millimeter,
                    )
                    self.assertTrue(status.is_ok(), status.error_description)
                    header, body = (
                        path.read_bytes()
                        .replace(b"\r\n", b"\n")
                        .split(b"end_header\n", 1)
                    )
                    self.assertTrue(header.startswith(b"ply\n"))
                    self.assertIn(b"element vertex 2", header)
                    self.assertTrue(body)
                    self.assertIn(b"format ascii 1.0", header)
                    properties = [
                        line.split()[-1].decode()
                        for line in header.splitlines()
                        if line.startswith(b"property ")
                    ]
                    rows = [
                        dict(zip(properties, map(float, line.split())))
                        for line in body.splitlines()
                    ]
                    self.assertEqual(len(rows), 2)
                    for index, row in enumerate(rows):
                        self.assertEqual(
                            [row[name] for name in ("x", "y", "z")],
                            [index + 1, 2, 1000],
                        )
                        if "Textured" in cls.__name__:
                            self.assertEqual(
                                [row[name] for name in ("blue", "green", "red")],
                                [12, 34, 56],
                            )
                        if "Normals" in cls.__name__:
                            self.assertEqual(
                                [row[name] for name in ("nx", "ny", "nz")], [0, 0, 1]
                            )
                    if "Textured" in cls.__name__:
                        self.assertIn(b"red", header)
                        self.assertIn(b"blue", header)
                    if "Normals" in cls.__name__:
                        self.assertIn(b"nx", header)
                        self.assertIn(b"nz", header)
                    missing = Path(directory) / "missing" / "cloud.ply"
                    error = writer(cloud, s.FileFormat_PLY, str(missing))
                    self.assertFalse(error.is_ok())
                    self.assertTrue(error.error_description)
                    self.assertFalse(missing.exists())

    def test_textured_mapping_keeps_grid_and_color_channels(self):
        depth, mask, color = a.DepthMap(), a.GrayScale2DImage(), a.Color2DImage()
        for array in (depth, mask, color):
            array.resize(2, 2)
        for index in range(4):
            depth[index].z = 1000
            mask[index].gray = 255
            color[index].b, color[index].g, color[index].r = 12, 34, 56
        intrinsics = a.CameraIntrinsics()
        for calibration in (intrinsics.depth, intrinsics.texture):
            calibration.camera_matrix.fx = calibration.camera_matrix.fy = 1000
        cloud = a.TexturedPointCloud()
        status = a.get_point_cloud_after_mapping(depth, mask, color, intrinsics, cloud)
        self.assertTrue(status.is_ok(), status.error_description)
        np.testing.assert_allclose(cloud.vertices()[..., 2], 1000)
        np.testing.assert_array_equal(cloud.colors(), np.tile([12, 34, 56], (2, 2, 1)))
        depth.release()
        color.release()
        self.assertEqual(cloud.vertices().shape, (2, 2, 3))

    def test_transforms_preserve_input_and_texture(self):
        transform = a.FrameTransformation()
        transform.__translate__(10, 20, 30)
        for cls, method, output_type in [
            (
                a.UntexturedPointCloud,
                a.transform_point_cloud_with_normals,
                a.UntexturedPointCloudWithNormals,
            ),
            (
                a.TexturedPointCloud,
                a.transform_textured_point_cloud,
                a.TexturedPointCloud,
            ),
            (
                a.TexturedPointCloud,
                a.transform_textured_point_cloud_with_normals,
                a.TexturedPointCloudWithNormals,
            ),
        ]:
            with self.subTest(method=method.__name__):
                cloud = cls()
                cloud.resize(3, 3)
                for index in range(9):
                    pixel = cloud[index]
                    pixel.x, pixel.y, pixel.z = index % 3, index // 3, 1000
                    if hasattr(pixel, "b"):
                        pixel.b, pixel.g, pixel.r = 12, 34, 56
                accessor = "vertices" if cls is a.TexturedPointCloud else "data"
                original = getattr(cloud, accessor)().copy()
                result = method(transform, cloud)
                self.assertIsInstance(result, output_type)
                actual = (
                    result.vertices()
                    if hasattr(result, "vertices")
                    else result.data()[..., :3]
                )
                np.testing.assert_allclose(actual, original + [10, 20, 30])
                np.testing.assert_array_equal(getattr(cloud, accessor)(), original)
                if hasattr(result, "colors"):
                    np.testing.assert_array_equal(result.colors(), cloud.colors())
