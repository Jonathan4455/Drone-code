from machine import ADC, I2C, Pin

import config
from ads1115 import ADS1115


class RemoteI2C:
    active_pair = None
    active_bus = None

    def __init__(self, sda_pin, scl_pin):
        self.sda_pin = sda_pin
        self.scl_pin = scl_pin

    def _bus(self):
        pair = (self.sda_pin, self.scl_pin)
        if RemoteI2C.active_pair != pair:
            RemoteI2C.active_bus = I2C(
                config.REMOTE_I2C_ID,
                sda=Pin(self.sda_pin),
                scl=Pin(self.scl_pin),
                freq=config.REMOTE_I2C_FREQUENCY_HZ,
            )
            RemoteI2C.active_pair = pair
        return RemoteI2C.active_bus

    def scan(self):
        return self._bus().scan()

    def writeto(self, address, data):
        return self._bus().writeto(address, data)

    def readfrom_mem(self, address, register, count):
        return self._bus().readfrom_mem(address, register, count)

    def writeto_mem(self, address, register, data):
        return self._bus().writeto_mem(address, register, data)


def scan_i2c_buses():
    buses = []
    for sda_pin, scl_pin in config.REMOTE_I2C_SCAN_PIN_PAIRS:
        try:
            bus = RemoteI2C(sda_pin, scl_pin)
            addresses = bus.scan()
        except Exception as error:
            print(
                "I2C scan failed on GP{}/GP{}: {}".format(
                    sda_pin, scl_pin, error
                )
            )
            continue

        print(
            "I2C GP{}/GP{}: {}".format(
                sda_pin,
                scl_pin,
                ", ".join("0x{:02X}".format(value) for value in addresses)
                if addresses
                else "no devices found",
            )
        )
        buses.append((bus, addresses, sda_pin, scl_pin))
    return buses


class JoystickInputs:
    def __init__(self, buses):
        self.ads = None
        for bus, addresses, _, _ in buses:
            if config.REMOTE_ADS1115_ADDRESS in addresses:
                self.ads = ADS1115(bus)
                break

        self.internal_adcs = None
        if self.ads is None:
            self.internal_adcs = [
                ADC(Pin(pin_number))
                for pin_number in config.REMOTE_INTERNAL_ADC_PINS
            ]
            print(
                "ADS1115 not found; using internal ADC pins {}. "
                "Roll will report center because only three pins are configured."
                .format(config.REMOTE_INTERNAL_ADC_PINS)
            )
        else:
            if (
                len(config.REMOTE_ADS1115_CHANNELS) != 4
                or any(
                    isinstance(channel, bool)
                    or not isinstance(channel, int)
                    or channel not in range(4)
                    for channel in config.REMOTE_ADS1115_CHANNELS
                )
            ):
                raise ValueError(
                    "REMOTE_ADS1115_CHANNELS must select four channels from 0 to 3"
                )
            print("ADS1115 found; reading four analog channels.")

    def read_axes(self):
        if self.ads is not None:
            return tuple(
                self.ads.read_channel(channel)
                for channel in config.REMOTE_ADS1115_CHANNELS
            )

        throttle, yaw, pitch = (
            adc.read_u16() for adc in self.internal_adcs
        )
        return throttle, yaw, pitch, 32768
