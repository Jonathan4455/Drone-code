import time

from imu import create_default_sensor


def main():
    sensor = create_default_sensor()
    print("Keep the IMU still; calibrating gyro bias...")
    bias = sensor.calibrate_gyro()
    print("Gyro bias (degrees/second):", bias)
    print("Reading MPU6050 telemetry. Press Ctrl-C to stop.")

    try:
        while True:
            data = sensor.read()
            ax, ay, az = data["accel_g"]
            gx, gy, gz = data["gyro_dps"]
            temp = data["temperature_c"]
            print(
                "Accel (g): X={:+.2f} Y={:+.2f} Z={:+.2f} | "
                "Gyro (dps): X={:+.1f} Y={:+.1f} Z={:+.1f} | "
                "Temp: {:.1f}C".format(ax, ay, az, gx, gy, gz, temp)
            )
            time.sleep_ms(100)
    except KeyboardInterrupt:
        print("\nIMU telemetry test stopped.")


if __name__ == "__main__":
    main()