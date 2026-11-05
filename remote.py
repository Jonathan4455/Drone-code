import network
import socket
import time
from machine import ADC, Pin

# Initialize Analog Joystick
x_axis = ADC(Pin(26))
y_axis = ADC(Pin(27))

# Connect to the Drone's Wi-Fi network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('DroneNet', 'dronepassword')

while not wlan.isconnected():
    time.sleep(0.5)

# The default IP address of the Drone AP
drone_ip = '192.168.4.1'
port = 1234
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    # Read physical joystick
    x_val = x_axis.read_u16()
    y_val = y_axis.read_u16()
    
    payload = f"{x_val},{y_val}"
    udp_socket.sendto(payload.encode(), (drone_ip, port))
    
    time.sleep(0.05) # Send 20 times per second