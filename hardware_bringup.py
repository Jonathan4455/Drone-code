import time

import config
import drone
import motors
import protocol


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


def _extract_throttle_axis(axes):
    if len(axes) == 4:
        return axes[0]
    if len(axes) == 2:
        return axes[1]
    raise ValueError(
        "joystick packet must contain two or four axes; received {}".format(len(axes))
    )


def run_sequential_motor_check(outputs):
    print("\n--- SEQUENTIAL MOTOR SPIN CHECK ---")
    print("Each motor runs one at a time; propellers must remain removed.")
    throttle = min(12.0, config.BENCH_MAX_THROTTLE_PERCENT)
    motors.send_stop_pulse(outputs)
    time.sleep(3)

    try:
        for index, pin_number in enumerate(config.MOTOR_PINS):
            print(
                "Spinning motor {} (GP{}) at {:.1f}% for 1.5 seconds".format(
                    index + 1, pin_number, throttle
                )
            )
            motor_throttles = [0.0] * len(outputs)
            motor_throttles[index] = throttle
            motors.set_throttles(outputs, motor_throttles)
            time.sleep(1.5)
            motors.send_stop_pulse(outputs)
            time.sleep(1)
    finally:
        motors.send_stop_pulse(outputs)

    print("Sequential motor check complete.")


def run_sensor_output_check(outputs, sensor):
    """Experimental raw accelerometer-to-motor mapping; not enabled in the normal menu."""
    print("\n--- EXPERIMENTAL RAW SENSOR-TO-OUTPUT MAPPING CHECK ---")
    print("This is not flight stabilization and is not for flight use.")
    print("The frame must remain restrained and propellers removed.")
    time.sleep(2)

    baseline = min(5.0, config.BENCH_MAX_THROTTLE_PERCENT)
    response_limit = min(15.0, config.BENCH_MAX_THROTTLE_PERCENT)
    start_time = time.ticks_ms()
    try:
        while time.ticks_diff(time.ticks_ms(), start_time) < 10000:
            reading = sensor.read()
            accel_x, accel_y, _ = reading["accel_g"]
            pitch_effort = _clamp(
                accel_x * response_limit, -response_limit, response_limit
            )
            roll_effort = _clamp(
                accel_y * response_limit, -response_limit, response_limit
            )

            throttles = (
                baseline + pitch_effort + roll_effort,
                baseline + pitch_effort - roll_effort,
                baseline - pitch_effort + roll_effort,
                baseline - pitch_effort - roll_effort,
            )
            throttles = tuple(
                _clamp(value, 0.0, config.BENCH_MAX_THROTTLE_PERCENT)
                for value in throttles
            )
            motors.set_throttles(outputs, throttles)
            print(
                "Accel (g): X={:+.2f} Y={:+.2f} | "
                "Motor throttle (%): {}".format(
                    accel_x,
                    accel_y,
                    ", ".join("{:.1f}".format(value) for value in throttles),
                )
            )
            time.sleep_ms(100)
    finally:
        motors.send_stop_pulse(outputs)

    print("Raw sensor-to-output check complete.")


def run_remote_throttle_check(outputs):
    print("\n--- REMOTE THROTTLE BENCH CHECK ---")
    print("Keep propellers removed; throttle is limited by config.py.")
    ap = None
    udp_socket = None
    last_packet_ms = time.ticks_ms()
    start_time = last_packet_ms
    try:
        motors.send_stop_pulse(outputs)
        ap = drone.start_access_point()
        udp_socket = drone.open_socket()
        udp_socket.settimeout(0.1)
        print("Waiting up to 15 seconds for joystick packets...")

        while time.ticks_diff(time.ticks_ms(), start_time) < 15000:
            try:
                payload, address = udp_socket.recvfrom(config.MAX_PACKET_BYTES)
            except OSError:
                if time.ticks_diff(time.ticks_ms(), last_packet_ms) > 500:
                    motors.send_stop_pulse(outputs)
                continue

            try:
                axes = protocol.decode_joystick(payload)
                throttle_value = _extract_throttle_axis(axes)
            except ValueError as error:
                print("Rejected invalid packet from {}: {}".format(address, error))
                continue

            last_packet_ms = time.ticks_ms()
            normalized_throttle = throttle_value / 65535.0
            threshold = config.BENCH_THROTTLE_START_FRACTION
            if normalized_throttle <= threshold:
                throttle = 0.0
            else:
                throttle = (
                    (normalized_throttle - threshold)
                    / (1.0 - threshold)
                    * config.BENCH_MAX_THROTTLE_PERCENT
                )
            motors.set_throttles(outputs, [throttle] * len(outputs))
            print(
                "Joystick throttle={} -> bench throttle {:.1f}%".format(
                    throttle_value, throttle
                )
            )
    finally:
        try:
            motors.send_stop_pulse(outputs)
        finally:
            try:
                if udp_socket is not None:
                    udp_socket.close()
            finally:
                if ap is not None:
                    ap.active(False)

    print("Remote throttle check complete.")


def _choose_check():
    print("\nChoose one bench check:")
    print("1. Sequential motor-only spin check")
    print("2. Remote joystick throttle check")
    print("3. Cancel")
    choice = input("Enter 1, 2, or 3: ").strip()
    checks = {
        "1": "motor",
        "2": "remote",
    }
    return checks.get(choice)


def run_hardware_bringup():
    print("==========================================")
    print("       DRONE HARDWARE BENCH CHECKS        ")
    print("==========================================")
    check = _choose_check()
    if check is None:
        print("No check selected; no motors will be initialized.")
        return
    confirmation = input(
        "Physically remove every propeller, then type PROPS REMOVED to continue: "
    ).strip()
    if confirmation != "PROPS REMOVED":
        print("Confirmation not received; no motors will be initialized.")
        return

    outputs = None
    try:
        outputs = motors.initialize()
        if check == "motor":
            run_sequential_motor_check(outputs)
        else:
            run_remote_throttle_check(outputs)
    except KeyboardInterrupt:
        print("\nBench check interrupted.")
    finally:
        if outputs is not None:
            try:
                motors.send_stop_pulse(outputs)
            finally:
                motors.deinitialize(outputs)
        print("Bench outputs deinitialized.")


if __name__ == "__main__":
    run_hardware_bringup()
