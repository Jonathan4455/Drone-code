from machine import SPI, Pin
import struct
import utime

import remote_inputs
from nrf24l01 import NRF24L01


# ============================================================
# REMOTE NRF24L01 TRANSMITTER TEST
#
# nRF24L01 wiring:
#   MISO -> GP16
#   CSN  -> GP17
#   SCK  -> GP18
#   MOSI -> GP19
#   CE   -> GP20
#   IRQ  -> not connected
#   VCC  -> 3.3V ONLY
#   GND  -> GND
#
# Joystick/ADS1115/OLED I2C remains on GP4/GP5.
# ============================================================

SPI_ID = 0
NRF_MISO_PIN = 16
NRF_CSN_PIN = 17
NRF_SCK_PIN = 18
NRF_MOSI_PIN = 19
NRF_CE_PIN = 20

CHANNEL = 46

# MUST exactly match drone_nrf.py.
RADIO_ADDRESS = b"DRONE"

PAYLOAD_FORMAT = "<HHHH"
PAYLOAD_SIZE = 8

SEND_PERIOD_MS = 50


def create_radio():
    spi = SPI(
        SPI_ID,
        baudrate=4_000_000,
        polarity=0,
        phase=0,
        sck=Pin(NRF_SCK_PIN),
        mosi=Pin(NRF_MOSI_PIN),
        miso=Pin(NRF_MISO_PIN),
    )

    csn = Pin(NRF_CSN_PIN, Pin.OUT, value=1)
    ce = Pin(NRF_CE_PIN, Pin.OUT, value=0)

    return NRF24L01(
        spi,
        csn,
        ce,
        channel=CHANNEL,
        payload_size=PAYLOAD_SIZE,
    )


def run_transmitter_test():
    print("Scanning remote I2C bus...")

    buses = remote_inputs.scan_i2c_buses()

    # For the actual transmitter, require the ADS1115.
    # Do not silently use the three-channel diagnostic fallback.
    inputs = remote_inputs.JoystickInputs(
        buses,
        allow_internal_adc_fallback=False,
    )

    print("Initializing nRF24L01 transmitter...")

    nrf = create_radio()
    nrf.open_tx_pipe(RADIO_ADDRESS)

    print("nRF24L01 hardware initialized.")
    print("Channel:", CHANNEL)
    print("Address:", RADIO_ADDRESS)
    print("Sending joystick packets...")
    print("Press Ctrl-C to stop.")

    try:
        while True:
            throttle, yaw, pitch, roll = inputs.read_axes()

            packet = struct.pack(
                PAYLOAD_FORMAT,
                throttle,
                yaw,
                pitch,
                roll,
            )

            try:
                nrf.send(packet)

                print(
                    "RF TX ->",
                    "THR:", throttle,
                    "YAW:", yaw,
                    "PIT:", pitch,
                    "ROL:", roll,
                )

            except OSError as error:
                print("RF send failed:", error)

            utime.sleep_ms(SEND_PERIOD_MS)

    except KeyboardInterrupt:
        print("\nTransmitter test stopped.")


if __name__ == "__main__":
    run_transmitter_test()