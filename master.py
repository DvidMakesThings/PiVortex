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

DETAIL_COMMANDS = [
    "GET_CPU_TEMP",
    "GET_UPTIME",
    "GET_DISK_USAGE",
    "LIST_USB"
]

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
        print(f"\nQuerying details from {name} ({ip})...")
        results = {"slave": name, "ip": ip, "details": {}}
        for command in DETAIL_COMMANDS:
            response = send_command(ip, command)
            results["details"][command] = response

        # Print results in a structured format
        print("=" * 40)
        print(f"Slave: {results['slave']} ({results['ip']})")
        for cmd, result in results["details"].items():
            print(f"{cmd}: {result}")
        print("=" * 40)

if __name__ == "__main__":
    main()
