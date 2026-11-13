from machine import SPI, Pin
import struct
import utime

from nrf24l01 import NRF24L01


# ============================================================
# DRONE NRF24L01 RECEIVER TEST
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
# This test DOES NOT control motors.
# It only receives and prints joystick values.
# ============================================================

SPI_ID = 0
NRF_MISO_PIN = 16
NRF_CSN_PIN = 17
NRF_SCK_PIN = 18
NRF_MOSI_PIN = 19
NRF_CE_PIN = 20

CHANNEL = 46

# nRF24L01 address MUST be exactly 5 bytes.
# This must exactly match remote_nrf.py.
RADIO_ADDRESS = b"DRONE"

# Four unsigned 16-bit values:
# throttle, yaw, pitch, roll
PAYLOAD_FORMAT = "<HHHH"
PAYLOAD_SIZE = 8


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


def run_receiver_test():
    print("Initializing nRF24L01 receiver...")

    nrf = create_radio()

    nrf.open_rx_pipe(0, RADIO_ADDRESS)
    nrf.start_listening()

    print("nRF24L01 hardware initialized.")
    print("Channel:", CHANNEL)
    print("Address:", RADIO_ADDRESS)
    print("Waiting for joystick packets...")
    print("Motors are NOT controlled by this test.")

    try:
        while True:
            if nrf.any():
                packet = nrf.recv()

                if len(packet) != PAYLOAD_SIZE:
                    print(
                        "Rejected packet with unexpected length:",
                        len(packet),
                    )
                    continue

                throttle, yaw, pitch, roll = struct.unpack(
                    PAYLOAD_FORMAT,
                    packet,
                )

                print(
                    "RF RX ->",
                    "THR:", throttle,
                    "YAW:", yaw,
                    "PIT:", pitch,
                    "ROL:", roll,
                )

            utime.sleep_ms(10)

    except KeyboardInterrupt:
        print("\nReceiver test stopped.")

    finally:
        nrf.stop_listening()


if __name__ == "__main__":
    run_receiver_test()