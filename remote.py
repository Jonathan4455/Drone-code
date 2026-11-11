import network
import socket
import time

import config
from remote_inputs import JoystickInputs, scan_i2c_buses
from protocol import encode_joystick


def connect_to_drone_ap():
    config.validate_wifi_password(config.WIFI_PASSWORD)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    started_ms = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), started_ms) >= config.WIFI_CONNECT_TIMEOUT_MS:
            wlan.disconnect()
            raise OSError("Timed out connecting to the drone access point")
        time.sleep_ms(100)
    return wlan


def main():
    inputs = JoystickInputs(scan_i2c_buses())
    wlan = connect_to_drone_ap()
    udp_socket = None
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        destination = (wlan.ifconfig()[2], config.UDP_PORT)
        while True:
            payload = encode_joystick(*inputs.read_axes())
            udp_socket.sendto(payload, destination)
            time.sleep_ms(config.JOYSTICK_PERIOD_MS)
    finally:
        if udp_socket is not None:
            udp_socket.close()
        wlan.disconnect()


if __name__ == "__main__":
    main()