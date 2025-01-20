from flask import Flask, jsonify

app = Flask(__name__)
slaves = [
    {"name": "slavepi1", "ip": "192.168.0.15", "description": "Raspberry Pi 4"},
    {"name": "slavepi2", "ip": "192.168.0.20", "description": "Raspberry Pi 5"},
    {"name": "slavepi3", "ip": "192.168.0.25", "description": "Raspberry Pi 5"},
    {"name": "slavepi4", "ip": "192.168.0.30", "description": "Raspberry Pi 4"}
]

@app.route("/slaves", methods=["GET"])
def get_slaves():
    return jsonify(slaves)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# 7. `logging_server.py`: Centralized Logging Server
import socket
import json

def receive_logs():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', 65434))
        print("Listening for logs...")
        while True:
            data, addr = s.recvfrom(1024)
            log = json.loads(data.decode())
            print(f"Log from {log['slave_name']}: {log['log_message']}")

if __name__ == "__main__":
    receive_logs()
