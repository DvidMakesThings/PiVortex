import socket
import json
import time

LOGGING_MASTER_IP = "192.168.0.10"  # IP of the master
LOGGING_PORT = 65434

def push_logs_to_master():
    """
    Periodically sends log messages to the logging server on the master.
    """
    log_data = {
        "slave_name": "slavepi1",
        "log_message": "System is operational"
    }
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        while True:
            s.sendto(json.dumps(log_data).encode(), (LOGGING_MASTER_IP, LOGGING_PORT))
            time.sleep(10)

if __name__ == "__main__":
    push_logs_to_master()
