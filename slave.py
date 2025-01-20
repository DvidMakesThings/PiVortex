import socket
import json
from commands import COMMANDS

HOST = "0.0.0.0"
PORT = 65432

def handle_request(command, params):
    handler = COMMANDS.get(command)
    if handler:
        return handler(params)
    else:
        return {"status": "error", "message": f"Unknown command: {command}"}

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Slave is ready to receive requests...")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connection from {addr}")
                try:
                    data = conn.recv(1024)
                    request = json.loads(data.decode())
                    command = request.get("command")
                    params = request.get("params", {})
                    response = handle_request(command, params)
                    conn.sendall(json.dumps(response).encode())
                except Exception as e:
                    conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode())

if __name__ == "__main__":
    main()