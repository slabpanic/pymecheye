"""Check event registration, dispatch selection, and asynchronous error propagation."""

from types import SimpleNamespace
import threading
import unittest
from unittest.mock import patch
import weakref

from mecheye import area_scan_3d_camera as a, shared as s
from mecheye._compat import _unwrap


class EventTests(unittest.TestCase):
    def setUp(self):
        self.camera = a.Camera()
        self.addCleanup(self.camera.disconnect)
        self.events = a.CameraEvent()

    def test_supported_events_replace_output_and_registration_reports_sdk_failure(self):
        infos = a.EventInfos([a.EventInfo("stale", 99)])
        status = self.events.get_supported_events(self.camera, infos)
        self.assertTrue(status.is_ok(), status.error_description)
        self.assertNotIn(99, [info.event_id for info in infos])
        self.assertTrue(all(isinstance(info, a.EventInfo) for info in infos))
        status = self.events.register_camera_event_callback(
            self.camera, self.events.CAMERA_EVENT_EXPOSURE_END, a.EventCallbackBase()
        )
        self.assertEqual(status.error_code, s.ErrorStatus.MMIND_STATUS_INVALID_DEVICE)
        self.assertEqual(self.camera._callbacks, {})
        self.assertIsNone(self.camera._event_context.thread)
        status = self.events.unregister_camera_event_callback(
            self.camera, self.events.CAMERA_EVENT_EXPOSURE_END
        )
        self.assertFalse(status.is_ok())

    def test_registration_rejects_invalid_arguments_before_calling_sdk(self):
        with patch.object(a, "function") as function:
            for args in ((), (self.camera,), (None, 1, a.EventCallbackBase())):
                with self.assertRaises(TypeError):
                    self.events.register_camera_event_callback(*args)
            status = self.events.register_camera_event_callback(
                self.camera, 1, object()
            )
        function.assert_not_called()
        self.assertEqual(
            status.error_code, s.ErrorStatus.MMIND_STATUS_INVALID_CALLBACKFUNC
        )

    def test_successful_registration_reuses_worker_and_unregisters_individually_or_all(
        self,
    ):
        callback = a.EventCallbackBase()
        with patch.object(a, "function", return_value=s.ErrorStatus()):
            try:
                self.assertTrue(
                    self.events.register_camera_event_callback(
                        self.camera, 1, callback
                    ).is_ok()
                )
                worker = self.camera._event_context.thread
                self.assertTrue(worker.is_alive())
                self.events.register_camera_event_callback(
                    self.camera, callback, None, self.events.CAMERA_EVENT_ALL
                )
                self.assertIs(self.camera._event_context.thread, worker)
                self.assertEqual(
                    set(self.camera._callbacks), {1, self.events.CAMERA_EVENT_ALL}
                )
                self.events.unregister_camera_event_callback(self.camera, 1)
                self.assertFalse(self.camera._event_stop.is_set())
                self.assertEqual(
                    set(self.camera._callbacks), {self.events.CAMERA_EVENT_ALL}
                )
                self.events.unregister_camera_event_callback(
                    self.camera, self.events.CAMERA_EVENT_ALL
                )
                self.assertEqual(self.camera._callbacks, {})
                self.assertTrue(self.camera._event_stop.is_set())
            finally:
                self.camera._event_stop.set()
                if self.camera._event_context.thread is not None:
                    self.camera._event_context.thread.join(2)
        self.assertFalse(worker.is_alive())
        self.assertIs(callback.__disown__(), callback)

    def test_failed_unregister_preserves_callback_registration(self):
        callback = a.EventCallbackBase()
        self.camera._callbacks[1] = (callback, False)
        with patch.object(a, "function", return_value=s.ErrorStatus(-1, "unavailable")):
            self.assertFalse(
                self.events.unregister_camera_event_callback(self.camera, 1).is_ok()
            )
        self.assertIs(self.camera._callbacks[1][0], callback)

    def test_dispatch_filters_event_ids_and_supports_legacy_and_modern_callbacks(self):
        event = a.EventData()
        event.event_id, event.frame_id = 1, 42
        seen, done = [], threading.Event()

        class Modern(a.EventCallbackBase):
            def process_event(self, data):
                seen.append(("modern", data.frame_id))

        class Legacy(a.EventCallbackBase):
            def run(self, event_id):
                seen.append(("legacy", event_id))
                done.set()

        self.camera._callbacks[2] = (Modern(), False)
        self.camera._callbacks[1] = (Modern(), False)
        self.camera._callbacks[self.events.CAMERA_EVENT_ALL] = (Legacy(), True)
        pending = [(_unwrap(event), [])]
        native = SimpleNamespace(poll_events=lambda: [pending.pop()] if pending else [])
        with patch.object(self.camera, "_native", native):
            worker = threading.Thread(
                target=a._dispatch_events,
                args=(weakref.ref(self.camera._event_context), self.camera._event_stop),
            )
            try:
                worker.start()
                self.assertTrue(done.wait(2))
            finally:
                self.camera._event_stop.set()
                worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(seen, [("modern", 42), ("legacy", 1)])
        self.assertEqual(self.camera.pop_callback_errors(), [])

    def test_polling_exception_is_returned_through_error_queue(self):
        def poll():
            self.camera._event_stop.set()
            raise RuntimeError("poll failed")

        with patch.object(self.camera, "_native", SimpleNamespace(poll_events=poll)):
            a._dispatch_events(weakref.ref(self.camera), self.camera._event_stop)
        errors = self.camera.pop_callback_errors()
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], RuntimeError)
        self.assertEqual(str(errors[0]), "poll failed")
        self.assertEqual(self.camera.pop_callback_errors(), [])

    def test_dispatch_exits_when_connection_wrappers_have_been_collected(self):
        camera = a.Camera()
        context = camera._event_context
        del camera
        a._dispatch_events(weakref.ref(context), context.stop)
        self.assertEqual(context.owners, [])
        del context
        a._dispatch_events(lambda: None, threading.Event())
