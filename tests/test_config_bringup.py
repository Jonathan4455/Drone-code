import importlib
import sys
import types
import unittest
from unittest.mock import patch

import config


class FakePin:
    def __init__(self, number, *_args, **_kwargs):
        self.number = number


class FakeADC:
    values = {26: 101, 27: 202, 28: 303}

    def __init__(self, pin):
        self.pin = pin

    def read_u16(self):
        return self.values[self.pin.number]


class FakePWM:
    def __init__(self, _pin):
        pass


class ConfigPasswordTests(unittest.TestCase):
    def test_invalid_wifi_passwords_are_rejected(self):
        for password in ("", "short", "replace-with-8-plus-char-password"):
            with self.subTest(password=password):
                with self.assertRaises(ValueError):
                    config.validate_wifi_password(password)

    def test_valid_wifi_password_is_returned_unchanged(self):
        password = "test-only-password-42"
        self.assertEqual(config.validate_wifi_password(password), password)


class HardwareBringupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        machine = types.ModuleType("machine")
        machine.Pin = FakePin
        machine.PWM = FakePWM
        machine.ADC = FakeADC
        machine.I2C = object
        network = types.ModuleType("network")
        cls._module_patcher = patch.dict(
            sys.modules, {"machine": machine, "network": network}
        )
        cls._module_patcher.start()
        for module_name in ("hardware_bringup", "drone", "motors"):
            sys.modules.pop(module_name, None)
        cls.hardware_bringup = importlib.import_module("hardware_bringup")

    @classmethod
    def tearDownClass(cls):
        for module_name in ("hardware_bringup", "drone", "motors"):
            sys.modules.pop(module_name, None)
        cls._module_patcher.stop()

    def test_extracts_throttle_from_four_axis_packet(self):
        axes = (123, 456, 789, 1011)
        self.assertEqual(
            self.hardware_bringup._extract_throttle_axis(axes), axes[0]
        )

    def test_extracts_throttle_from_legacy_two_axis_packet(self):
        axes = (123, 456)
        self.assertEqual(
            self.hardware_bringup._extract_throttle_axis(axes), axes[1]
        )

    def test_rejects_unsupported_axis_count(self):
        with self.assertRaises(ValueError):
            self.hardware_bringup._extract_throttle_axis((1, 2, 3))


class RemoteInputTests(unittest.TestCase):
    def setUp(self):
        machine = types.ModuleType("machine")
        machine.Pin = FakePin
        machine.ADC = FakeADC
        machine.I2C = object
        self._module_patcher = patch.dict(sys.modules, {"machine": machine})
        self._module_patcher.start()
        sys.modules.pop("remote_inputs", None)
        self.addCleanup(lambda: sys.modules.pop("remote_inputs", None))
        self.addCleanup(self._module_patcher.stop)
        self.remote_inputs = importlib.import_module("remote_inputs")

    def test_missing_ads1115_rejects_remote_operation_with_runtime_error(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "ADS1115 not found; remote operation requires the ADS1115",
        ):
            self.remote_inputs.JoystickInputs([], allow_internal_adc_fallback=False)

    def test_diagnostic_fallback_reads_internal_adc_values(self):
        inputs = self.remote_inputs.JoystickInputs(
            [], allow_internal_adc_fallback=True
        )
        self.assertEqual(inputs.read_axes(), (101, 202, 303, 32768))


if __name__ == "__main__":
    unittest.main()
