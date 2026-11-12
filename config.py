# Copy this file to both Pico W boards and set the same private AP password.
WIFI_SSID = "DroneNet"

try:
    from drone_secrets import WIFI_PASSWORD
except ImportError:
    WIFI_PASSWORD = ""


def validate_wifi_password(password):
    if not password:
        raise ValueError(
            "Set a valid WPA2 WIFI_PASSWORD (at least 8 characters) in drone_secrets.py"
        )
    if len(password) < 8:
        raise ValueError(
            "Set a valid WPA2 WIFI_PASSWORD (at least 8 characters) in drone_secrets.py"
        )
    if password == "replace-with-8-plus-char-password":
        raise ValueError(
            "Set a valid WPA2 WIFI_PASSWORD (at least 8 characters) in drone_secrets.py"
        )
    return password


UDP_PORT = 1234
COMMAND_TIMEOUT_MS = 250
JOYSTICK_PERIOD_MS = 50
WIFI_CONNECT_TIMEOUT_MS = 15000

MOTOR_PINS = (16, 17, 18, 19)

# Confirm this stop pulse and PWM rate with the exact ESC documentation.
ESC_PWM_HZ = 50
ESC_STOP_PULSE_US = 1000
ESC_MAX_PULSE_US = 2000
BENCH_MAX_THROTTLE_PERCENT = 20.0
BENCH_THROTTLE_START_FRACTION = 0.55
if not 0.0 <= BENCH_THROTTLE_START_FRACTION < 1.0:
    raise ValueError("BENCH_THROTTLE_START_FRACTION must satisfy 0.0 <= value < 1.0")
MAX_PACKET_BYTES = 32

IMU_I2C_ID = 0
IMU_SDA_PIN = 0
IMU_SCL_PIN = 1
IMU_I2C_FREQUENCY_HZ = 100000
IMU_ADDRESS = 0x68

# Remote I2C bus - controller PCB/wiring uses GP4 (SDA) and GP5 (SCL)
REMOTE_I2C_ID = 0
REMOTE_I2C_SDA_PIN = 4
REMOTE_I2C_SCL_PIN = 5

REMOTE_I2C_SCAN_PIN_PAIRS = (
    (REMOTE_I2C_SDA_PIN, REMOTE_I2C_SCL_PIN),
)

REMOTE_I2C_FREQUENCY_HZ = 400000
REMOTE_OLED_ADDRESS = 0x3C
REMOTE_ADS1115_ADDRESS = 0x48
REMOTE_ADS1115_CHANNELS = (0, 1, 2, 3)
REMOTE_INTERNAL_ADC_PINS = (26, 27, 28)
ADS1115_CONVERSION_TIMEOUT_MS = 30
