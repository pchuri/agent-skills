"""Unit tests for the SmartThings skill helper (plugins/smartthings/.../st.py).

The tests load st.py directly and replace its device lookup and command
functions, so no credentials, user files, or network access are used.
"""

import argparse
import importlib.util
import io
import pathlib
import unittest
from unittest import mock

ST_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "plugins" / "smartthings" / "skills" / "smartthings" / "scripts" / "st.py"
)


def load_st():
    spec = importlib.util.spec_from_file_location("smartthings_st_under_test", ST_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


st = load_st()


def device(device_id, label=None, name=None, **extra):
    d = {"deviceId": device_id}
    if label is not ...:
        d["label"] = label
    if name is not ...:
        d["name"] = name
    d.update(extra)
    return d


class ResolveDeviceIdTests(unittest.TestCase):
    def setUp(self):
        guard = mock.patch.object(
            st, "api_request", side_effect=AssertionError("network access is not allowed in tests")
        )
        guard.start()
        self.addCleanup(guard.stop)
        self.stderr = io.StringIO()
        stderr_patch = mock.patch.object(st.sys, "stderr", self.stderr)
        stderr_patch.start()
        self.addCleanup(stderr_patch.stop)

    def use_devices(self, devices):
        patcher = mock.patch.object(st, "get_devices", return_value=devices)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_exits(self, identifier):
        with self.assertRaises(SystemExit) as ctx:
            st.resolve_device_id(identifier)
        self.assertEqual(ctx.exception.code, 1)
        return self.stderr.getvalue()

    def test_duplicate_exact_labels_are_ambiguous(self):
        self.use_devices([
            device("id-a", label="Living Room Light", name="Bulb A"),
            device("id-b", label="living room light", name="Bulb B"),
            device("id-c", label="Living Room Light Strip", name="Strip"),
        ])

        err = self.assert_exits("Living Room Light")

        self.assertIn("Ambiguous device label", err)
        self.assertIn("id-a", err)
        self.assertIn("id-b", err)
        self.assertNotIn("id-c", err)
        self.assertIn("device ID", err)

    def test_unique_exact_label_wins_over_substring_matches(self):
        self.use_devices([
            device("id-a", label="Lamp", name="Desk"),
            device("id-b", label="Lamp Shade", name="Shade"),
        ])

        self.assertEqual(st.resolve_device_id("lamp"), ("id-a", "Lamp"))

    def test_explicit_device_id_wins_over_duplicate_labels(self):
        self.use_devices([
            device("id-a", label="Fan"),
            device("id-b", label="Fan"),
        ])

        self.assertEqual(st.resolve_device_id("id-b"), ("id-b", "Fan"))

    def test_device_id_equal_to_a_duplicated_label_is_selected_by_id(self):
        self.use_devices([
            device("Fan", label="Ceiling"),
            device("id-b", label="Fan"),
            device("id-c", label="Fan"),
        ])

        self.assertEqual(st.resolve_device_id("Fan"), ("Fan", "Ceiling"))

    def test_null_and_missing_label_or_name_are_handled(self):
        self.use_devices([
            device("id-null-label", label=None, name="Garage Door"),
            device("id-missing-both", label=..., name=...),
            device("id-null-name", label="Porch", name=None),
            device("id-null-both", label=None, name=None),
        ])

        self.assertEqual(st.resolve_device_id("garage"), ("id-null-label", "Garage Door"))
        self.assertEqual(st.resolve_device_id("porch"), ("id-null-name", "Porch"))

    def test_unique_partial_match_is_preserved(self):
        self.use_devices([
            device("id-a", label="Kitchen Light", name="Bulb"),
            device("id-b", label="Bedroom Fan", name="Fan"),
        ])

        self.assertEqual(st.resolve_device_id("kitch"), ("id-a", "Kitchen Light"))
        self.assertEqual(st.resolve_device_id("fan"), ("id-b", "Bedroom Fan"))

    def test_ambiguous_partial_match_exits(self):
        self.use_devices([
            device("id-a", label="Kitchen Light"),
            device("id-b", label="Hall Light"),
        ])

        err = self.assert_exits("light")

        self.assertIn("Ambiguous device identifier 'light'", err)
        self.assertIn("id-a", err)
        self.assertIn("id-b", err)

    def test_no_match_exits(self):
        self.use_devices([device("id-a", label="Kitchen Light", name=None)])

        err = self.assert_exits("garage")

        self.assertIn("Device 'garage' not found.", err)


class CommandTargetingTests(unittest.TestCase):
    def setUp(self):
        guard = mock.patch.object(
            st, "api_request", side_effect=AssertionError("network access is not allowed in tests")
        )
        guard.start()
        self.addCleanup(guard.stop)
        self.send_command = mock.Mock(return_value={})
        send_patch = mock.patch.object(st, "send_command", self.send_command)
        send_patch.start()
        self.addCleanup(send_patch.stop)
        self.stderr = io.StringIO()
        self.stdout = io.StringIO()
        for target, stream in (("stderr", self.stderr), ("stdout", self.stdout)):
            p = mock.patch.object(st.sys, target, stream)
            p.start()
            self.addCleanup(p.stop)

    def use_devices(self, devices):
        patcher = mock.patch.object(st, "get_devices", return_value=devices)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_duplicate_exact_labels_send_no_command(self):
        self.use_devices([
            device("id-a", label="Heater"),
            device("id-b", label="Heater"),
        ])

        with self.assertRaises(SystemExit) as ctx:
            st.cmd_on(argparse.Namespace(device="Heater", component="main"))

        self.assertEqual(ctx.exception.code, 1)
        self.send_command.assert_not_called()
        self.assertNotIn("Turned ON", self.stdout.getvalue())

    def test_unique_exact_label_sends_one_command_to_that_device(self):
        self.use_devices([
            device("id-a", label="Heater"),
            device("id-b", label="Heater Two"),
        ])

        st.cmd_off(argparse.Namespace(device="heater", component="main"))

        self.send_command.assert_called_once_with("id-a", "switch", "off", component="main")
        self.assertIn("Turned OFF: Heater (id-a)", self.stdout.getvalue())

    def test_explicit_id_targets_one_of_duplicate_labels(self):
        self.use_devices([
            device("id-a", label="Heater"),
            device("id-b", label="Heater"),
        ])

        st.cmd_on(argparse.Namespace(device="id-b", component="main"))

        self.send_command.assert_called_once_with("id-b", "switch", "on", component="main")


if __name__ == "__main__":
    unittest.main()
