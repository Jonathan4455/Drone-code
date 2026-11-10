import network
import select
import socket
import time

import config
import motors
from protocol import decode_joystick


def start_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=config.WIFI_SSID, password=config.WIFI_PASSWORD)
    ap.active(True)

    started_ms = time.ticks_ms()
    while not ap.active():
        if time.ticks_diff(time.ticks_ms(), started_ms) >= config.WIFI_CONNECT_TIMEOUT_MS:
            ap.active(False)
            raise OSError("Timed out starting the drone access point")
        time.sleep_ms(100)
    return ap


def open_socket():
    """Open and bind the UDP command socket, closing it if setup fails."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.bind(("0.0.0.0", config.UDP_PORT))
    except Exception:
        udp_socket.close()
        raise
    return udp_socket


def run_receiver():
    ap = start_access_point()
    udp_socket = None
    try:
        udp_socket = open_socket()
        poller = select.poll()
        poller.register(udp_socket, select.POLLIN)
        print("Drone AP active at {}; ESCs receive only the stop pulse".format(ap.ifconfig()[0]))
        print("Waiting for valid joystick packets...")

        last_valid_ms = None
        last_report_ms = 0
        failsafe_active = True
        while True:
            events = poller.poll(100)
            if events:
                payload, address = udp_socket.recvfrom(config.MAX_PACKET_BYTES)
                try:
                    axes = decode_joystick(payload)
                except ValueError as error:
                    print("Rejected invalid packet from {}: {}".format(address, error))
                else:
                    last_valid_ms = time.ticks_ms()
                    if failsafe_active:
                        print("Valid joystick packets received; ESCs still receive only the stop pulse")
                        failsafe_active = False
                    if time.ticks_diff(last_valid_ms, last_report_ms) >= 1000:
                        print("Joystick axes={} from {}".format(axes, address))
                        last_report_ms = last_valid_ms

            now_ms = time.ticks_ms()
            timed_out = (
                last_valid_ms is None
                or time.ticks_diff(now_ms, last_valid_ms) > config.COMMAND_TIMEOUT_MS
            )
            if timed_out and not failsafe_active:
                print("Joystick timeout; motors remain disarmed")
                failsafe_active = True
    finally:
        try:
            if udp_socket is not None:
                udp_socket.close()
        finally:
            ap.active(False)


def main():
    outputs = motors.initialize()
    try:
        run_receiver()
    finally:
        try:
            motors.send_stop_pulse(outputs)
        finally:
            motors.deinitialize(outputs)


if __name__ == "__main__":
    main()