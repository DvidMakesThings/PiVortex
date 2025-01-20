import threading
from master import query_slaves
from master_discovery import listen_for_slaves
from dashboard import app
from logging_server import receive_logs
import time


def run_master():
    print("Starting Master Command Handler...")
    while True:
        print("\n[INFO] Querying slaves...")
        query_slaves()
        print("[INFO] Completed querying slaves. Waiting for next cycle...\n")
        time.sleep(30)


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
        threading.Thread(target=run_master, daemon=True),
        threading.Thread(target=run_discovery, daemon=True),
        threading.Thread(target=run_dashboard, daemon=True),
        threading.Thread(target=run_logging_server, daemon=True),
    ]

    for thread in threads:
        thread.start()

    print("[INFO] All threads started. Main program running.\n")

    try:
        while True:  # Keep main thread alive for daemon threads
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down services... Exiting program.")


if __name__ == "__main__":
    main()
