import time

from imu import create_default_sensor


def main():
    sensor = create_default_sensor()
    print("Keep the IMU still; calibrating gyro bias...")
    print("Gyro bias (degrees/second):", sensor.calibrate_gyro())
    print("Reading MPU6050 telemetry. Press Ctrl-C to stop.")

    while True:
        print(sensor.read())
        time.sleep_ms(100)


if __name__ == "__main__":
    main()
