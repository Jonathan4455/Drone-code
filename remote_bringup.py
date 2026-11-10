from machine import Pin
import time

import config
import remote_inputs
from oled import SSD1306


def _blink_onboard_led():
    led = Pin("LED", Pin.OUT)
    for _ in range(3):
        led.on()
        time.sleep_ms(150)
        led.off()
        time.sleep_ms(150)
    return led


def _find_oled(buses):
    for bus, addresses, sda_pin, scl_pin in buses:
        if config.REMOTE_OLED_ADDRESS in addresses:
            print(
                "SSD1306 OLED found at 0x{:02X} on GP{}/GP{}.".format(
                    config.REMOTE_OLED_ADDRESS, sda_pin, scl_pin
                )
            )
            try:
                return SSD1306(bus, config.REMOTE_OLED_ADDRESS)
            except (OSError, ValueError) as error:
                print("OLED initialization failed: {}".format(error))
                return None
    print("OLED 0x{:02X} not found; continuing without display.".format(
        config.REMOTE_OLED_ADDRESS
    ))
    return None


def _show_values(display, values):
    if display is None:
        return
    display.fill(0)
    display.text("REMOTE INPUTS", 0, 0)
    for index, (label, value) in enumerate(zip(("THR", "YAW", "PIT", "ROL"), values)):
        display.text("{}: {}".format(label, value), 0, 16 + index * 12)
    display.show()


def main():
    led = _blink_onboard_led()
    display = None
    try:
        print("Scanning remote I2C buses...")
        buses = remote_inputs.scan_i2c_buses()
        for _, addresses, _, _ in buses:
            for expected, name in (
                (config.REMOTE_OLED_ADDRESS, "SSD1306 OLED"),
                (config.REMOTE_ADS1115_ADDRESS, "ADS1115 ADC"),
            ):
                if expected in addresses:
                    print("Detected {} at 0x{:02X}.".format(name, expected))

        inputs = remote_inputs.JoystickInputs(buses)
        display = _find_oled(buses)
        source = "ADS1115 AIN0-AIN3" if inputs.ads is not None else "internal ADC"
        print("Reading throttle, yaw, pitch, roll via {}. Press Ctrl-C to stop.".format(source))

        while True:
            values = inputs.read_axes()
            print(
                "Throttle={:5d} Yaw={:5d} Pitch={:5d} Roll={:5d}".format(
                    *values
                )
            )
            _show_values(display, values)
            time.sleep_ms(100)
    except KeyboardInterrupt:
        print("\nRemote bring-up stopped.")
    finally:
        try:
            if display is not None:
                display.deinit()
        finally:
            led.off()


if __name__ == "__main__":
    main()
