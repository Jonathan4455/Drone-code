import network
import socket

# Set up the Pico W as a Wi-Fi Access Point
ap = network.WLAN(network.AP_IF)
ap.config(essid='DroneNet', password='dronepassword')
ap.active(True)

while not ap.active():
    pass
print('Drone AP Active! IP Address:', ap.ifconfig()[0])

# Set up a UDP socket to listen for incoming data
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(('0.0.0.0', 1234)) 

print("Listening for joystick data...")

while True:
    data, addr = udp_socket.recvfrom(1024)
    print(f"Received Joystick Data: {data.decode()} from {addr}")