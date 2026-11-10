import time

import config


class ADS1115:
    CONVERSION_REGISTER = 0x00
    CONFIG_REGISTER = 0x01
    START_SINGLE_CONVERSION = 0x8000
    SINGLE_SHOT_MODE = 0x0100
    PGA_4_096V = 0x0200
    DATA_RATE_128_SPS = 0x0080
    COMPARATOR_DISABLED = 0x0003

    def __init__(self, i2c, address=config.REMOTE_ADS1115_ADDRESS):
        self.i2c = i2c
        self.address = address

    def read_channel(self, channel):
        if (
            isinstance(channel, bool)
            or not isinstance(channel, int)
            or channel not in range(4)
        ):
            raise ValueError("ADS1115 channel must be an integer from 0 to 3")

        mux = 0x4000 + channel * 0x1000
        configuration = (
            self.START_SINGLE_CONVERSION
            | mux
            | self.PGA_4_096V
            | self.SINGLE_SHOT_MODE
            | self.DATA_RATE_128_SPS
            | self.COMPARATOR_DISABLED
        )
        self.i2c.writeto_mem(
            self.address,
            self.CONFIG_REGISTER,
            bytes((configuration >> 8, configuration & 0xFF)),
        )

        started_ms = time.ticks_ms()
        timeout_ms = config.ADS1115_CONVERSION_TIMEOUT_MS
        while True:
            config_bytes = self.i2c.readfrom_mem(
                self.address, self.CONFIG_REGISTER, 2
            )
            if config_bytes[0] & 0x80:
                break
            if time.ticks_diff(time.ticks_ms(), started_ms) >= timeout_ms:
                raise OSError("ADS1115 conversion timed out")
            time.sleep_ms(1)

        result = self.i2c.readfrom_mem(
            self.address, self.CONVERSION_REGISTER, 2
        )
        raw = (result[0] << 8) | result[1]
        if raw & 0x8000:
            raw -= 0x10000
        raw = max(0, min(32767, raw))
        return raw * 65535 // 32767
