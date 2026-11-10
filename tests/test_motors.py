import importlib
import sys
import types
import unittest
from unittest.mock import patch

import config


class FakePin:
    def __init__(self, number):
        self.number = number


class FakePWM:
    instances = []
    fail_frequency_on = None

    def __init__(self, pin):
        self.pin = pin
        self.frequency = None
        self.duty = None
        self.deinitialized = False
        self.instances.append(self)

    def freq(self, frequency):
        if self.pin.number == self.fail_frequency_on:
            raise OSError("mock PWM frequency failure")
        self.frequency = frequency

    def duty_u16(self, duty):
        self.duty = duty

    def deinit(self):
        self.deinitialized = True


class MotorOutputTests(unittest.TestCase):
    def setUp(self):
        FakePWM.instances = []
        machine = types.ModuleType("machine")
        machine.Pin = FakePin
        machine.PWM = FakePWM
        patcher = patch.dict(sys.modules, {"machine": machine})
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.modules.pop("motors", None)
        self.addCleanup(lambda: sys.modules.pop("motors", None))
        self.motors = importlib.import_module("motors")

    def _duty_for_pulse(self, pulse_us):
        return pulse_us * config.ESC_PWM_HZ * 65535 // 1000000

    def test_initialization_and_stop_use_configured_stop_pulse(self):
        outputs = self.motors.initialize()
        self.assertEqual(len(outputs), len(config.MOTOR_PINS))
        self.assertEqual(
            [output.frequency for output in outputs],
            [config.ESC_PWM_HZ] * len(outputs),
        )
        expected = self._duty_for_pulse(config.ESC_STOP_PULSE_US)
        self.assertEqual([output.duty for output in outputs], [expected] * len(outputs))

        self.motors.send_stop_pulse(outputs)
        self.assertEqual([output.duty for output in outputs], [expected] * len(outputs))
        self.motors.deinitialize(outputs)
        self.assertTrue(all(output.deinitialized for output in FakePWM.instances))

    def test_throttle_conversion_uses_configured_pulses_and_bench_limit(self):
        stop_duty = self._duty_for_pulse(config.ESC_STOP_PULSE_US)
        limited_pulse = config.ESC_STOP_PULSE_US + (
            config.ESC_MAX_PULSE_US - config.ESC_STOP_PULSE_US
        ) * config.BENCH_MAX_THROTTLE_PERCENT / 100
        limited_duty = self._duty_for_pulse(limited_pulse)
        self.assertEqual(self.motors.throttle_to_duty(0), stop_duty)
        self.assertEqual(
            self.motors.throttle_to_duty(config.BENCH_MAX_THROTTLE_PERCENT),
            limited_duty,
        )

    def test_throttle_conversion_respects_nondefault_esc_configuration(self):
        with patch.object(config, "ESC_PWM_HZ", 100), patch.object(
            config, "ESC_STOP_PULSE_US", 900
        ), patch.object(config, "ESC_MAX_PULSE_US", 2100), patch.object(
            config, "BENCH_MAX_THROTTLE_PERCENT", 10.0
        ):
            expected_stop = 900 * 100 * 65535 // 1000000
            expected_limit = 1020 * 100 * 65535 // 1000000
            self.assertEqual(self.motors.throttle_to_duty(0), expected_stop)
            self.assertEqual(self.motors.throttle_to_duty(10), expected_limit)

    def test_set_throttles_sets_each_output_independently(self):
        outputs = self.motors.initialize()
        values = [0.0, 5.0, 10.0, config.BENCH_MAX_THROTTLE_PERCENT]
        self.motors.set_throttles(outputs, values)
        expected = [self.motors.throttle_to_duty(value) for value in values]
        self.assertEqual([output.duty for output in outputs], expected)
        self.motors.deinitialize(outputs)

    def test_invalid_throttles_are_rejected_without_partial_output(self):
        outputs = self.motors.initialize()
        original_duties = [output.duty for output in outputs]
        invalid_values = (
            -0.1,
            config.BENCH_MAX_THROTTLE_PERCENT + 0.1,
            "10",
            True,
            float("nan"),
            float("inf"),
        )
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.motors.set_throttles(outputs, [0.0, 0.0, value, 0.0])
                self.assertEqual([output.duty for output in outputs], original_duties)
        self.motors.deinitialize(outputs)

    def test_set_throttles_requires_one_value_per_motor(self):
        outputs = self.motors.initialize()
        with self.assertRaises(ValueError):
            self.motors.set_throttles(outputs, [0.0])
        with self.assertRaises(ValueError):
            self.motors.set_throttles(outputs[:-1], [0.0] * len(outputs))
        self.motors.deinitialize(outputs)

    def test_initialization_failure_stops_and_deinitializes_partial_outputs(self):
        FakePWM.fail_frequency_on = config.MOTOR_PINS[1]
        try:
            with self.assertRaises(OSError):
                self.motors.initialize()
        finally:
            FakePWM.fail_frequency_on = None
        self.assertEqual(len(FakePWM.instances), 2)
        self.assertTrue(all(output.deinitialized for output in FakePWM.instances))


if __name__ == "__main__":
    unittest.main()
