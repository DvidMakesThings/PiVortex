import socket
import json

def receive_logs():
    """
    Listens for log messages sent by slaves and prints them to the console.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', 65434))  # Bind to the logging port
        print("Listening for logs on port 65434...")
        while True:
            data, addr = s.recvfrom(1024)  # Receive logs
            try:
                log = json.loads(data.decode())
                print(f"Log from {log['slave_name']} ({addr[0]}): {log['log_message']}")
            except json.JSONDecodeError:
                print(f"Received malformed log data from {addr[0]}: {data.decode()}")

if __name__ == "__main__":
    receive_logs()
