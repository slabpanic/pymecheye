Camera workflows
================

SDK capture
-----------

Camera methods that perform SDK operations return an
:class:`~mecheye.shared.ErrorStatus`. Check it before reading a frame. Capture
timeouts and heartbeat intervals are expressed in milliseconds.

.. code-block:: python

   from mecheye.area_scan_3d_camera import Camera, Frame3D

   camera = Camera()
   status = camera.connect("192.168.1.100")
   if not status.is_ok():
       raise RuntimeError(status.error_description)
   try:
       frame = Frame3D()
       status = camera.capture_3d(frame, timeoutMs=10000)
       if not status.is_ok():
           raise RuntimeError(status.error_description)
       xyz = frame.get_untextured_point_cloud().data()
   finally:
       camera.disconnect()

SDK calls do not connect lazily or retry failures. ``disconnect()`` returns
``None``. Camera copies share the same native connection and event context, so
disconnecting one copy affects the others.

Aligned NumPy capture
---------------------

:meth:`~mecheye.area_scan_3d_camera.Camera.capture_points` combines depth-source
2D and 3D capture with mapping and grayscale conversion. This workflow requires
a camera model that supports depth-source 2D capture.

.. code-block:: python

   from mecheye.area_scan_3d_camera import Camera

   with Camera("192.168.1.100") as camera:
       camera.configure_depth_source_2d_exposure("flash")
       image, points_mm = camera.capture_points(timeoutMs=10000)
       device = camera.device_info
       calibration = camera.camera_parameters

``image`` is an owned ``uint8`` array with shape ``(height, width)``.
``points_mm`` is an owned ``float64`` array with shape ``(height, width, 3)``.
SDK all-zero points become NaN triplets, and non-finite coordinate components
become NaN. The previous SDK cloud unit is restored after success or failure;
a restoration failure raises :class:`~mecheye.shared.MechEyeConfigurationError`.

An optional constructor IP connects only on context entry or first convenience
capture/configuration. Convenience failures raise subclasses of
:class:`~mecheye.shared.MechEyeError` and do not retry automatically.

Array layout and ownership
--------------------------

.. list-table:: NumPy accessors for nonempty grids
   :header-rows: 1

   * - Container/accessor
     - dtype
     - Shape and fields
   * - GrayScale2DImage.data()
     - uint8
     - (height, width)
   * - Color2DImage.data()
     - uint8
     - (height, width, 3), BGR
   * - DepthMap.data()
     - float32
     - (height, width), Z
   * - UntexturedPointCloud.data()
     - float32
     - (height, width, 3), XYZ
   * - UntexturedPointCloudWithNormals.data()
     - float32
     - (height, width, 7), XYZ, normal XYZ, curvature
   * - TexturedPointCloud.vertices() / colors()
     - float32 / uint8
     - (height, width, 3), XYZ / BGR
   * - TexturedPointCloudWithNormals.normals()
     - float32
     - (height, width, 4), normal XYZ and curvature

Every accessor returns an independent NumPy copy. Empty accessors return a
``float64`` zero array of shape ``(1,)``. Pixel references from ``at(row, col)``
or indexing allow field writes; a size-changing resize or release expires them
and subsequent access raises ``ReferenceError``. Raw frame clouds retain the
selected SDK coordinate unit; only ``capture_points()`` guarantees millimeters.

Hand-eye pose translations use millimeters when supplied as robot poses, while
calibrated :class:`~mecheye.area_scan_3d_camera.HandEyeTransformation` extrinsic
translations use meters. These units are separate from capture cloud units.

Parameters and user sets
------------------------

Use a descriptor's ``name`` with a :class:`~mecheye.shared.UserSet`. Reads return
``[status, value]`` for scalar values and ``(status, value)`` for structured values.
Writes return an SDK status.

.. code-block:: python

   from mecheye.area_scan_3d_camera import Scanning2DDepthSourceExposureMode

   user_set = camera.current_user_set()
   status, mode = user_set.get_enum_value_string(
       Scanning2DDepthSourceExposureMode.name
   )
   if not status.is_ok():
       raise RuntimeError(status.error_description)

Descriptor limits are nominal SDK metadata. Check parameter availability and
device-specific constraints on the connected camera before writing values.
Obtain fresh handles after reconnecting or selecting another user set.

Threads, events, and output
---------------------------

SDK operations are serialized across camera instances and release Python thread
state while blocked. Explicit locks protect SDK objects in regular and
free-threaded CPython. Caller-owned NumPy writes and application callback state
still require caller synchronization.

Subclass :class:`~mecheye.area_scan_3d_camera.EventCallbackBase` and register it
through :class:`~mecheye.area_scan_3d_camera.CameraEvent`. Event values and payloads
are copied before Python dispatch and can be read while a capture is running.
An SDK call made from a callback waits for the current SDK operation. Retrieve
callback failures with :meth:`~mecheye.area_scan_3d_camera.Camera.pop_callback_errors`.

The wrapper adds no automatic logging. On Linux the SDK worker silences its
standard output/error streams without redirecting application output. The SDK
may still create diagnostic files. ``show_error()`` and ``print_*()`` print only
when called explicitly; interactive selection helpers prompt only when called.

