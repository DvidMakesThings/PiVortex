import socket
import json
import threading
from tkinter import Tk, Frame, Label, Button, BOTH, Scrollbar, Text, VERTICAL, END

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


def filter_usb_devices(raw_data):
    # Only include meaningful USB device descriptions
    filtered = [
        line for line in raw_data.splitlines()
        if "Linux Foundation" not in line and "root hub" not in line
    ]
    return "\n".join(filtered) if filtered else "No peripherals connected."


def summarize_disk_usage(raw_data):
    # Show only the first two lines (header and root partition)
    lines = raw_data.splitlines()
    return "\n".join(lines[:2]) if len(lines) > 1 else raw_data

class SlaveMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Slave Monitor")
        self.root.geometry("800x700")

        # Main container
        self.main_frame = Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Header
        Label(self.main_frame, text="Slave Monitor", font=("Arial", 16), pady=10).grid(row=0, column=0, columnspan=2)

        # Slave Frames Container
        self.slave_frames = {}

        # Arrange slaves in a 2x2 grid
        row, col = 1, 0
        for name, ip in SLAVES.items():
            frame = Frame(self.main_frame, relief="groove", bd=2, padx=10, pady=5)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            Label(frame, text=f"{name} ({ip})", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

            self.slave_frames[name] = {
                "frame": frame,
                "labels": {
                    cmd: Label(frame, text=f"{cmd}: Loading...", anchor="w", justify="left", wraplength=300)
                    for cmd in DETAIL_COMMANDS
                }
            }

            # Add labels to the frame
            for cmd_row, cmd in enumerate(DETAIL_COMMANDS, start=1):
                self.slave_frames[name]["labels"][cmd].grid(row=cmd_row, column=0, sticky="w")

            # Move to the next grid cell
            col += 1
            if col >= 2:  # 2 columns per row
                col = 0
                row += 1

        # Refresh Button
        self.refresh_button = Button(self.root, text="Refresh", command=self.query_slaves, padx=10, pady=5)
        self.refresh_button.pack(pady=10)

        # Initial Query
        self.query_slaves()

    def query_slaves(self):
        # Update slave details
        for name, ip in SLAVES.items():
            threading.Thread(target=self.update_slave_details, args=(name, ip)).start()

    def update_slave_details(self, name, ip):
        results = {}
        for cmd in DETAIL_COMMANDS:
            response = send_command(ip, cmd)
            if cmd == "LIST_USB" and response.get("status") == "success":
                response["data"] = filter_usb_devices(response["data"])
            elif cmd == "GET_DISK_USAGE" and response.get("status") == "success":
                response["data"] = summarize_disk_usage(response["data"])
            results[cmd] = response

        # Update the GUI labels
        for cmd, response in results.items():
            status = response.get("status", "unknown")
            if status == "success":
                data = response.get("data", "No data available")
                text = f"{cmd}:\n{data}"
            else:
                message = response.get("message", "Unknown error")
                text = f"{cmd}: ERROR - {message}"

            # Update the corresponding label
            self.slave_frames[name]["labels"][cmd].config(text=text)


def run_gui():
    root = Tk()
    app = SlaveMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()