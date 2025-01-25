import socket
import time
import json

def broadcast_slave_info():
    slave_info = {"name": "slavepi1", "ip": "192.168.0.15", "description": "Raspberry Pi 4"}
    message = json.dumps(slave_info).encode()
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(message, ("<broadcast>", 65433))
        time.sleep(10)

if __name__ == "__main__":
    broadcast_slave_info()
