from machine import I2C, Pin, SoftI2C
import time

import config


class MPU6050:
    PWR_MGMT_1 = 0x6B
    SMPLRT_DIV = 0x19
    CONFIG = 0x1A
    GYRO_CONFIG = 0x1B
    ACCEL_CONFIG = 0x1C
    ACCEL_DATA = 0x3B
    WHO_AM_I = 0x75
    VALID_IDENTITIES = (0x68, 0x70, 0x71, 0x72, 0x98)

    def __init__(self, i2c, address=config.IMU_ADDRESS):
        self.i2c = i2c
        self.address = address
        self.gyro_bias_dps = (0.0, 0.0, 0.0)

        if address not in i2c.scan():
            raise OSError("MPU6050 not found at I2C address 0x{:02x}".format(address))

        identity = i2c.readfrom_mem(address, self.WHO_AM_I, 1)[0]
        if identity not in self.VALID_IDENTITIES:
            raise OSError(
                "Unexpected MPU6050 identity: 0x{:02x}".format(identity)
            )

        i2c.writeto_mem(address, self.PWR_MGMT_1, b"\x00")
        time.sleep_ms(50)
        i2c.writeto_mem(address, self.CONFIG, b"\x03")
        i2c.writeto_mem(address, self.SMPLRT_DIV, b"\x04")
        i2c.writeto_mem(address, self.GYRO_CONFIG, b"\x00")
        i2c.writeto_mem(address, self.ACCEL_CONFIG, b"\x00")

    @staticmethod
    def _signed_word(high, low):
        value = (high << 8) | low
        if value >= 0x8000:
            value -= 0x10000
        return value

    def read_raw(self):
        data = self.i2c.readfrom_mem(self.address, self.ACCEL_DATA, 14)
        values = []
        for offset in range(0, 14, 2):
            values.append(self._signed_word(data[offset], data[offset + 1]))
        return {
            "accel": (values[0], values[1], values[2]),
            "temperature": values[3],
            "gyro": (values[4], values[5], values[6]),
        }

    def read(self):
        raw = self.read_raw()
        return {
            "accel_g": tuple(value / 16384.0 for value in raw["accel"]),
            "temperature_c": raw["temperature"] / 340.0 + 36.53,
            "gyro_dps": tuple(
                raw["gyro"][axis] / 131.0 - self.gyro_bias_dps[axis]
                for axis in range(3)
            ),
        }

    def calibrate_gyro(self, samples=200, delay_ms=5):
        """Average stationary gyro readings; keep the sensor motionless."""
        if samples <= 0 or delay_ms < 0:
            raise ValueError("samples must be positive and delay_ms nonnegative")

        totals = [0, 0, 0]
        for _ in range(samples):
            gyro = self.read_raw()["gyro"]
            for axis in range(3):
                totals[axis] += gyro[axis]
            if delay_ms:
                time.sleep_ms(delay_ms)

        self.gyro_bias_dps = tuple(
            total / samples / 131.0 for total in totals
        )
        return self.gyro_bias_dps


def create_default_sensor():
    try:
        i2c = I2C(
            config.IMU_I2C_ID,
            sda=Pin(config.IMU_SDA_PIN),
            scl=Pin(config.IMU_SCL_PIN),
            freq=config.IMU_I2C_FREQUENCY_HZ,
        )
    except ValueError:
        i2c = SoftI2C(
            sda=Pin(config.IMU_SDA_PIN),
            scl=Pin(config.IMU_SCL_PIN),
            freq=config.IMU_I2C_FREQUENCY_HZ,
        )
    return MPU6050(i2c)