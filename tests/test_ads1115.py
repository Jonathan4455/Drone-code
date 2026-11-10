import unittest
from unittest.mock import patch

import ads1115


class FakeTime:
    def __init__(self):
        self.now = 0

    def ticks_ms(self):
        return self.now

    def ticks_diff(self, newer, older):
        return newer - older

    def sleep_ms(self, duration):
        self.now += duration


class FakeI2C:
    def __init__(self, conversion=0x7FFF, ready=True):
        self.conversion = conversion
        self.ready = ready
        self.configuration = None

    def writeto_mem(self, address, register, data):
        self.configuration = (data[0] << 8) | data[1]

    def readfrom_mem(self, address, register, count):
        if register == ads1115.ADS1115.CONFIG_REGISTER:
            ready_bit = 0x80 if self.ready else 0
            return bytes((ready_bit, 0))
        return bytes((self.conversion >> 8, self.conversion & 0xFF))


class ADS1115Tests(unittest.TestCase):
    def test_reads_single_shot_channel_and_scales_to_u16(self):
        bus = FakeI2C(conversion=0x4000)
        fake_time = FakeTime()
        with patch.object(ads1115, "time", fake_time):
            value = ads1115.ADS1115(bus).read_channel(2)

        self.assertEqual(value, 0x4000 * 65535 // 32767)
        self.assertEqual((bus.configuration & 0x7000), 0x6000)
        self.assertTrue(
            bus.configuration & ads1115.ADS1115.START_SINGLE_CONVERSION
        )

    def test_clamps_negative_single_ended_reading_to_zero(self):
        bus = FakeI2C(conversion=0xFFFF)
        with patch.object(ads1115, "time", FakeTime()):
            self.assertEqual(ads1115.ADS1115(bus).read_channel(0), 0)

    def test_rejects_invalid_channel(self):
        bus = FakeI2C()
        with self.assertRaises(ValueError):
            ads1115.ADS1115(bus).read_channel(4)
        self.assertIsNone(bus.configuration)

    def test_times_out_if_conversion_never_completes(self):
        bus = FakeI2C(ready=False)
        with patch.object(ads1115, "time", FakeTime()):
            with self.assertRaises(OSError):
                ads1115.ADS1115(bus).read_channel(0)


if __name__ == "__main__":
    unittest.main()
