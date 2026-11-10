from machine import Pin, PWM
import math

import config


def _pulse_to_duty_u16(pulse_us, frequency_hz):
    return pulse_us * frequency_hz * 65535 // 1000000


def _validate_esc_settings():
    if config.ESC_PWM_HZ <= 0:
        raise ValueError("ESC_PWM_HZ must be positive")
    if not 0 < config.ESC_STOP_PULSE_US < config.ESC_MAX_PULSE_US:
        raise ValueError("ESC pulse settings must satisfy 0 < stop < maximum")
    if config.ESC_MAX_PULSE_US * config.ESC_PWM_HZ >= 1000000:
        raise ValueError("ESC_MAX_PULSE_US must be shorter than the PWM period")
    if not 0 <= config.BENCH_MAX_THROTTLE_PERCENT <= 100:
        raise ValueError("BENCH_MAX_THROTTLE_PERCENT must be from 0 to 100")


def throttle_to_duty(percent):
    """Convert a bounded bench throttle percentage to a PWM duty value."""
    _validate_esc_settings()
    if isinstance(percent, bool) or not isinstance(percent, (int, float)):
        raise ValueError("throttle must be a finite number")
    if percent < 0 or percent > config.BENCH_MAX_THROTTLE_PERCENT:
        raise ValueError(
            "throttle must be from 0 to {} percent".format(
                config.BENCH_MAX_THROTTLE_PERCENT
            )
        )
    if not math.isfinite(percent):
        raise ValueError("throttle must be a finite number")

    pulse_range = config.ESC_MAX_PULSE_US - config.ESC_STOP_PULSE_US
    pulse_us = config.ESC_STOP_PULSE_US + pulse_range * percent / 100
    return int(_pulse_to_duty_u16(pulse_us, config.ESC_PWM_HZ))


def initialize():
    """Initialize all ESC outputs at the configured stop pulse."""
    _validate_esc_settings()
    outputs = []
    try:
        for pin_number in config.MOTOR_PINS:
            output = PWM(Pin(pin_number))
            outputs.append(output)
            output.freq(config.ESC_PWM_HZ)
            output.duty_u16(
                _pulse_to_duty_u16(config.ESC_STOP_PULSE_US, config.ESC_PWM_HZ)
            )
    except Exception:
        try:
            send_stop_pulse(outputs)
        finally:
            deinitialize(outputs)
        raise
    return outputs


def send_stop_pulse(outputs):
    """Send only the configured stop pulse to every initialized output."""
    _validate_esc_settings()
    stop_duty = _pulse_to_duty_u16(config.ESC_STOP_PULSE_US, config.ESC_PWM_HZ)
    for output in outputs:
        output.duty_u16(stop_duty)


def deinitialize(outputs):
    for output in outputs:
        output.deinit()


def set_throttles(outputs, throttles):
    """Set each motor to a validated, bench-limited throttle percentage."""
    _validate_esc_settings()
    if not isinstance(outputs, (list, tuple)) or len(outputs) != len(config.MOTOR_PINS):
        raise ValueError("outputs must contain one initialized output per motor")
    if not isinstance(throttles, (list, tuple)) or len(throttles) != len(outputs):
        raise ValueError("throttles must contain one value per motor output")

    duties = [throttle_to_duty(percent) for percent in throttles]
    for output, duty in zip(outputs, duties):
        output.duty_u16(duty)
