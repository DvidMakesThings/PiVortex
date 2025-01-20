import socket
import json

SLAVES = {
    "slavepi1": "192.168.0.15", 
    "slavepi2": "192.168.0.20", 
    "slavepi3": "192.168.0.25",
    "slavepi4": "192.168.0.30"
}
PORT = 65432
TIMEOUT = 5

def send_command(ip, command, params=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, PORT))
            s.sendall(json.dumps({"command": command, "params": params}).encode())
            data = s.recv(1024)
            return json.loads(data.decode())
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    for name, ip in SLAVES.items():
        response = send_command(ip, "GET_CPU_TEMP")
        print(f"{name} ({ip}): {response}")

if __name__ == "__main__":
    main()