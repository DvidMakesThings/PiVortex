import socket
import json

def listen_for_slaves():
    slaves = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', 65433))
        while True:
            data, addr = s.recvfrom(1024)
            slave = json.loads(data.decode())
            slaves[addr[0]] = slave
            print(f"Discovered: {slave}")

if __name__ == "__main__":
    listen_for_slaves()