from machine import Pin
import network
import socket
import time

import config
from protocol import encode_joystick
from remote_inputs import JoystickInputs, scan_i2c_buses


def _get_status_led():
    try:
        return Pin("LED", Pin.OUT)
    except Exception:
        return None


def connect_to_drone_ap(wlan=None, led=None):
    config.validate_wifi_password(config.WIFI_PASSWORD)
    if wlan is None:
        wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    started_ms = time.ticks_ms()
    while not wlan.isconnected():
        if led is not None:
            led.toggle()
        if time.ticks_diff(time.ticks_ms(), started_ms) >= config.WIFI_CONNECT_TIMEOUT_MS:
            wlan.disconnect()
            if led is not None:
                led.off()
            raise OSError("Timed out connecting to the drone access point")
        time.sleep_ms(100)

    if led is not None:
        led.on()
    return wlan


def main():
    inputs = JoystickInputs(scan_i2c_buses())
    led = _get_status_led()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while True:
        udp_socket = None
        try:
            if not wlan.isconnected():
                print("Connecting to {}...".format(config.WIFI_SSID))
                connect_to_drone_ap(wlan, led)
                print("Connected! Streaming joystick packets...")

            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            destination = (wlan.ifconfig()[2], config.UDP_PORT)

            while wlan.isconnected():
                payload = encode_joystick(*inputs.read_axes())
                udp_socket.sendto(payload, destination)
                time.sleep_ms(config.JOYSTICK_PERIOD_MS)

            print("Wi-Fi link lost; reconnecting...")
        except OSError as error:
            print("Connection retry ({})...".format(error))
            time.sleep_ms(500)
        finally:
            if led is not None and not wlan.isconnected():
                led.off()
            if udp_socket is not None:
                udp_socket.close()


if __name__ == "__main__":
    main()