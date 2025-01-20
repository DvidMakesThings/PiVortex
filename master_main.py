import threading
import subprocess
from master import main as master_main
from master_discovery import listen_for_slaves
from dashboard import app
from logging_server import receive_logs


def run_master():
    print("Starting Master Command Handler...")
    master_main()


def run_discovery():
    print("Starting Slave Discovery Service...")
    listen_for_slaves()


def run_dashboard():
    print("Starting Dashboard Server...")
    app.run(host="0.0.0.0", port=5000)


def run_logging_server():
    print("Starting Centralized Logging Server...")
    receive_logs()


def main():
    # Run each service in a separate thread
    threads = [
        threading.Thread(target=run_master),
        threading.Thread(target=run_discovery),
        threading.Thread(target=run_dashboard),
        threading.Thread(target=run_logging_server),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
