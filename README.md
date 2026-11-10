# Drone-code

MicroPython bench bring-up code for two Raspberry Pi Pico W boards. This
repository is **not a flight controller and is not ready to fly**. The receiver
validates joystick telemetry and reports timeouts, but it never maps commands
to motor outputs. The motor module includes a throttle API for propeller-off
bench checks, hard-capped by configuration; that signal does not guarantee an
ESC is disarmed.

## Safety first

- Remove all propellers before powering the flight electronics or testing
  firmware. Keep the frame restrained and clear of loose objects.
- A PWM stop pulse is not a physical motor disconnect and is not guaranteed to
  stop every ESC. Disconnect the battery to make the system electrically safe.
- Confirm your ESC's input protocol, PWM rate, arming behavior, and stop pulse
  before connecting it. The defaults in `config.py` are assumptions, not
  verified hardware settings.
- Do not use this code for flight. It has no attitude estimator, stabilization,
  motor mixer, arming workflow, or tested flight failsafe.

## Files

- `config.py`: shared Wi-Fi, pin, timeout, and ESC stop-pulse settings. Copy it
  to both boards and replace the example Wi-Fi password with the same private
  password on each.
- `protocol.py`: strict encoder/decoder for legacy two-axis packets and
  four-axis `throttle,yaw,pitch,roll` packets.
- `remote.py`: reads four axes from the ADS1115 when found, or three internal
  ADC pins with a centered roll fallback, then sends packets at 20 Hz.
- `remote_inputs.py`: scans configured I2C pin pairs and selects the ADS1115 or
  internal ADC inputs.
- `ads1115.py` and `oled.py`: dependency-free MicroPython drivers for
  single-shot ADS1115 readings and 128x64 SSD1306 text output.
- `remote_bringup.py`: standalone remote-board diagnostic with onboard LED
  blink, I2C scans, live terminal readings, and optional OLED output.
- `drone.py`: starts the access point, accepts and validates packets, and
  reports when valid packets go stale. It also exposes helpers for starting
  the AP and binding the UDP socket.
- `motors.py`: side-effect-free on import; outputs are created only when
  `initialize()` is explicitly called. Its throttle API is capped by
  `BENCH_MAX_THROTTLE_PERCENT` in `config.py`.
- `hardware_bringup.py`: interactive, propeller-off bench checks for individual
  motors, a remote throttle link, and an experimental raw IMU-to-output
  mapping. The IMU mapping is not flight stabilization.
- `imu.py`: reusable MPU6050 driver with contiguous sensor reads, conversion
  to g/degrees per second, and stationary gyro-bias calibration.
- `imu_test.py`: standalone IMU telemetry test.

## Bench setup

1. Verify Pico W, joystick, IMU, ESC, and power wiring against their hardware
   documentation. The defaults assume joystick ADC pins GP26/GP27, IMU I2C0
   SDA/SCL on GP0/GP1, and motor signal pins GP16–GP19. In the sequential
   check, motor 1 corresponds to `MOTOR_PINS[0]`, motor 2 to `MOTOR_PINS[1]`,
   and so on; record and verify each pin's actual frame position and rotation
   direction because this code does not define a universal frame layout.
2. Set a private Wi-Fi password in `config.py`. Copy `config.py`, `protocol.py`,
   `remote_inputs.py`, `ads1115.py`, `oled.py`, `remote.py`, and
   `remote_bringup.py` to the remote board. Copy `config.py` and `protocol.py`
   to the drone board.
3. Before connecting the remote over USB, see [Remote Pico connection
   troubleshooting](#remote-pico-connection-troubleshooting). Run
   `remote_bringup.py` standalone on the remote. It blinks the onboard LED,
   scans the configured common I2C pin pairs, then reports live input values
   and uses the OLED if detected. Default ADS1115 channels 0-3 map to throttle,
   yaw, pitch, and roll. Without the ADS1115, GP26/GP27/GP28 map to throttle,
   yaw, and pitch; roll reports midpoint because the internal fallback has
   only three ADC inputs.
4. With propellers removed, run `imu_test.py` on the drone-side board. Keep the
   IMU still during gyro calibration; check axis directions and readings before
   using those values elsewhere.
5. With propellers still removed, run `drone.py` on the drone-side board and
   `remote.py` on the remote. Confirm packets arrive and that stopping the
   remote causes a timeout message.
6. Test ESC signals only with propellers removed and only after confirming the
   ESC's signal requirements. The configured PWM frequency, stop pulse, maximum
   pulse, motor pins, and bench throttle cap are assumptions; verify each
   against the actual board, ESC, and wiring.
7. To run the interactive hardware checks on the drone-side Pico W, copy
   `hardware_bringup.py`, `motors.py`, `config.py`, `drone.py`, `protocol.py`,
   and `imu.py` to the board. Start `hardware_bringup.py`, choose one check,
   then type `PROPS REMOVED` only after physically removing every propeller.
   Choose the sequential motor-only option to test motor outputs independently.
   The remote option also needs the remote board running `remote.py`; its Y
   axis stays at zero throttle through 55% of travel, then ramps to the bench
   cap, so verify the joystick direction with outputs stopped first. The sensor
   check requires the IMU. This check is an experimental raw-sensor-to-output
   mapping, not stabilization and not suitable for flight.
   Keep the frame restrained and clear of people and objects, and disconnect
   battery power to make the hardware electrically safe.

## Remote Pico connection troubleshooting

- Use a known data-capable Micro-USB cable; charge-only cables power the Pico
  but do not expose its USB device to the computer. Try another USB port and
  check Device Manager for a new serial/USB device.
- To install or recover MicroPython, hold **BOOTSEL** while plugging the Pico W
  into USB. It should appear as the `RPI-RP2` drive. Copy the official
  MicroPython UF2 firmware specifically for Pico W to that drive; the board
  will reboot when flashing completes.
- In the editor/serial tool, select the Pico W's serial port and run
  `remote_bringup.py`. The LED blink confirms the script started. The I2C scan
  prints addresses by SDA/SCL pin pair; default candidates are GP0/GP1 and
  GP4/GP5. If devices are not found, verify 3.3V power, shared ground, SDA/SCL
  wiring, and `REMOTE_I2C_SCAN_PIN_PAIRS` in `config.py`.
- If the teammate wired joystick buttons, their GPIO pins and active levels
  still need to be identified and configured; this bring-up currently reports
  the four analog axes only.

`remote.py` and `drone.py` use MicroPython-only hardware/network modules; the
packet codec in `protocol.py` can be tested on a desktop Python interpreter.
The host-side unit tests run with `python -m unittest discover -s tests -v`.
