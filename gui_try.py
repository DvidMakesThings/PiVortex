import platform
import socket
import json
import tkinter as tk
from tkinter import ttk
import time
import datetime
import threading
import subprocess as sp

import psutil

# Configuration
SLAVES = {
    "masterpc": "localhost",  # Add master PC as localhost
    "slavepi1": "192.168.0.15",
    "slavepi2": "192.168.0.20",
    "slavepi3": "192.168.0.25",
}
PORT = 65432
TIMEOUT = 5
DETAIL_COMMANDS = [
    "GET_CPU_TEMP",
    "GET_UPTIME",
    "GET_DISK_USAGE",
    "LIST_USB",
    "REQUEST_ADC",
]


def send_command(ip, command, params=None):
    """Send a command to a slave or fetch local data for the master."""
    try:
        if ip == "localhost":
            return fetch_local_data(command)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, PORT))
            s.sendall(json.dumps({"command": command, "params": params}).encode())
            data = s.recv(4096)
            return json.loads(data.decode())
    except Exception as e:
        return {"status": "error", "message": str(e)}


def fetch_local_data(command):
    """Fetch data locally for the master PC."""
    try:
        if command == "GET_CPU_TEMP":
            if platform.system() == "Linux":
                # Check common thermal sensor locations
                paths = [
                    "/sys/class/thermal/thermal_zone0/temp",
                    "/sys/class/hwmon/hwmon0/temp1_input"
                ]
                for path in paths:
                    try:
                        with open(path, "r") as f:
                            temp = int(f.read().strip()) / 1000.0
                            return {"status": "success", "data": f"{temp:.2f}"}
                    except FileNotFoundError:
                        continue
                return {"status": "error", "message": "Temperature file not found"}
            elif platform.system() == "Windows":
                # Use psutil for temperature if available
                try:
                    import wmi
                    c = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                    sensors = c.Sensor()
                    for sensor in sensors:
                        if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                            return {"status": "success", "data": f"{sensor.Value:.2f}"}
                except Exception:
                    pass
                return {"status": "error", "message": "Temperature not available on Windows"}
            else:
                return {"status": "error", "message": "Unsupported platform"}
        elif command == "GET_UPTIME":
            try:
                # Calculate system uptime
                uptime_seconds = time.time() - psutil.boot_time()
                uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
                return {"status": "success", "data": uptime_str.split(".")[0]}
            except Exception as e:
                return {"status": "error", "message": f"Uptime retrieval failed: {e}"}
        elif command == "GET_DISK_USAGE":
            try:
                disk_usage = psutil.disk_usage("/")
                used_percentage = (disk_usage.used / disk_usage.total) * 100
                return {"status": "success", "data": f"{used_percentage:.1f}%"}
            except Exception as e:
                return {"status": "error", "message": f"Disk usage command failed: {e}"}
        elif command == "LIST_USB":
            try:
                if platform.system() == "Linux":
                    usb_devices = sp.getoutput("lsusb | wc -l")
                    return {"status": "success", "data": f"{usb_devices} devices"}
                else:
                    # Simulate USB device count for non-Linux platforms
                    return {"status": "success", "data": "N/A"}
            except Exception as e:
                return {"status": "error", "message": f"USB list retrieval failed: {e}"}
        elif command == "REQUEST_ADC":
            return {"status": "error", "message": "ADC not available on master PC"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_raspberry_pi_model(ip):
    """Fetch the Raspberry Pi model using /proc/device-tree/model."""
    if ip == "localhost":
        return "Master PC"
    try:
        response = send_command(ip, "RUN_SCRIPT", params={"script": "cat /proc/device-tree/model"})
        if response.get("status") == "success":
            raw_model = response.get("data", "Unknown").strip()
            if "Raspberry Pi 5" in raw_model:
                return "Raspberry Pi 5"
            elif "Raspberry Pi 4" in raw_model:
                return "Raspberry Pi 4"
            else:
                return raw_model
        else:
            print(f"[WARNING] Failed to detect model for {ip}: {response.get('message')}")
    except Exception as e:
        print(f"[ERROR] Exception while detecting model for {ip}: {e}")
    return "Unknown"


class SlaveFrame(tk.Frame):
    def __init__(self, master, slave_id, ip, model="Unknown"):
        super().__init__(master, bg="#282c34")
        self.slave_id = slave_id
        self.ip = ip
        self.model = model

        # Adjust title formatting for masterpc
        if slave_id == "masterpc":
            title_text = f"Master PC ({ip})"
        else:
            title_text = f"Slave PC {slave_id} ({ip}) - {model}"

        self.title_label = tk.Label(
            self,
            text=title_text,
            fg="#abb2bf",
            bg="#282c34",
            font=("Helvetica", 12, "bold"),
        )
        self.title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(5, 0))


        # CPU Temp
        self.cpu_label = tk.Label(self, text="CPU Temp:", fg="#abb2bf", bg="#282c34")
        self.cpu_label.grid(row=1, column=0, sticky="w")

        self.cpu_progress = ttk.Progressbar(self, length=150, mode="determinate")
        self.cpu_progress.grid(row=1, column=1, padx=(5, 0), sticky="w")

        self.cpu_temp_label = tk.Label(
            self,
            text="--°C",
            fg="#abb2bf",
            bg="#282c34",
            font=("Helvetica", 10, "bold"),
        )
        self.cpu_temp_label.grid(row=1, column=2, padx=(5, 0), sticky="w")

        # Disk Usage
        self.disk_label = tk.Label(self, text="Disk Usage:", fg="#abb2bf", bg="#282c34")
        self.disk_label.grid(row=2, column=0, sticky="w")
        self.disk_progress = ttk.Progressbar(self, length=150, mode="determinate")
        self.disk_progress.grid(row=2, column=1, padx=(5, 0), sticky="w")

        self.disk_usage_label = tk.Label(
            self,
            text="--%",
            fg="#abb2bf",
            bg="#282c34",
            font=("Helvetica", 10, "bold"),
        )
        self.disk_usage_label.grid(row=2, column=2, padx=(5, 0), sticky="w")

        # USB Devices
        self.usb_label = tk.Label(self, text="USB Devices: --", fg="#abb2bf", bg="#282c34")
        self.usb_label.grid(row=3, column=0, columnspan=3, sticky="w")

        # ADC Value
        self.adc_label = tk.Label(self, text="ADC Value: --", fg="#abb2bf", bg="#282c34")
        self.adc_label.grid(row=4, column=0, columnspan=3, sticky="w")

        # Uptime
        self.uptime_label = tk.Label(self, text="Uptime: --", fg="#abb2bf", bg="#282c34")
        self.uptime_label.grid(row=5, column=0, sticky="w")

        # Status
        self.status_label = tk.Label(
            self, text="Status: Unknown", fg="#abb2bf", bg="#282c34"
        )
        self.status_label.grid(row=6, column=0, sticky="w")

    def update_data(self, data):
        """Update the frame's data and progress bars."""
        # Update CPU Temp
        cpu_temp = data.get("cpu_temp", 0)
        self.cpu_progress["value"] = self._safe_value(cpu_temp)
        self.cpu_temp_label.config(text=f"{cpu_temp:.1f}°C")

        # Update Disk Usage
        disk_usage = data.get("disk_usage", 0)
        self.disk_progress["value"] = self._safe_value(disk_usage)
        self.disk_usage_label.config(text=f"{disk_usage:.1f}%")

        # Update USB Devices
        self.usb_label.config(text=f"USB Devices: {data.get('usb_devices', '--')}")

        # Update ADC Value
        self.adc_label.config(text=f"ADC Value: {data.get('adc_value', '--')}")

        # Update Uptime
        self.uptime_label.config(text=f"Uptime: {data.get('uptime', '--')}")

        # Update Status
        self.status_label.config(text=f"Status: {data.get('status', 'Online')}")

    @staticmethod
    def _safe_value(value):
        """Ensure a valid value for progress bars (0-100)."""
        try:
            value = float(value)
            return max(0, min(100, value))
        except (ValueError, TypeError):
            return 0


class RackMonitorApp(tk.Tk):
    """Main application for monitoring the slaves."""
    def __init__(self):
        super().__init__()
        self.title("Rack Monitoring System")
        self.configure(bg="#282c34")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TProgressbar",
            foreground="#2196f3",
            background="#2196f3",
            troughcolor="#3e4452",
            thickness=10,
        )

        # Slave Frames
        self.slave_frames = []
        for idx, (slave_id, ip) in enumerate(SLAVES.items(), start=1):
            # Fetch the model and strip details
            model = get_raspberry_pi_model(ip)
            frame = SlaveFrame(self, slave_id, ip, model=model)
            frame.grid(row=0, column=idx - 1, padx=10, pady=10)  # Place frames side by side
            self.slave_frames.append((slave_id, frame))

        # Command Input
        self.command_entry = ttk.Entry(self, width=50)
        self.command_entry.grid(row=1, column=0, padx=10, pady=10, columnspan=len(SLAVES))
        self.command_entry.insert(0, "Enter custom command...")  # Placeholder text

        # Bind events for focus in and out
        self.command_entry.bind("<FocusIn>", self.clear_placeholder)
        self.command_entry.bind("<FocusOut>", self.add_placeholder)
        self.command_entry.bind("<Return>", self.send_command)  # Execute command on Enter

        # Command Log
        self.command_log = tk.Text(
            self, height=10, width=80, bg="#3e4452", fg="#abb2bf", borderwidth=0
        )
        self.command_log.grid(row=2, column=0, columnspan=len(SLAVES), padx=10, pady=10)
        self.command_log.config(state="disabled")

        # Status Label
        self.status_label = tk.Label(
            self,
            text="System Monitor v1.0.0 | Connected Slaves: --/4 | Last Update: --",
            bg="#282c34",
            fg="#abb2bf",
        )
        self.status_label.grid(row=3, column=0, columnspan=len(SLAVES), padx=10, pady=(0, 10))

        self.update_real_data()

    def clear_placeholder(self, event):
        """Clear placeholder text when the user clicks the entry box."""
        if self.command_entry.get() == "Enter custom command...":
            self.command_entry.delete(0, tk.END)

    def add_placeholder(self, event):
        """Restore placeholder text if the entry box is empty."""
        if not self.command_entry.get():
            self.command_entry.insert(0, "Enter custom command...")

    def fetch_slave_data(self, ip):
        """Fetch and parse data from a slave."""
        data = {}
        is_online = False

        # Detect Raspberry Pi model
        model = get_raspberry_pi_model(ip)
        supports_adc = "5" in model  # Only Raspberry Pi 5 supports ADC

        for command in DETAIL_COMMANDS:
            if command == "REQUEST_ADC" and not supports_adc:
                data["adc_value"] = "Not Supported"
                continue

            params = {"channel": "EXT5V_V"} if command == "REQUEST_ADC" else None
            response = send_command(ip, command, params)
            if response.get("status") == "success":
                is_online = True
                raw_data = response.get("data", "")
                if command == "GET_CPU_TEMP":
                    try:
                        data["cpu_temp"] = float(raw_data.split("=")[1].strip("'C"))
                    except Exception:
                        data["cpu_temp"] = 0
                elif command == "GET_UPTIME":
                    data["uptime"] = raw_data
                elif command == "GET_DISK_USAGE":
                    try:
                        data["disk_usage"] = float(raw_data.strip("%"))
                    except Exception:
                        data["disk_usage"] = 0
                elif command == "LIST_USB":
                    data["usb_devices"] = len(raw_data.splitlines())
                elif command == "REQUEST_ADC":
                    try:
                        data["adc_value"] = f"{float(raw_data.split('=')[-1].strip('V')):.2f}V"
                    except Exception:
                        data["adc_value"] = "N/A"
            else:
                print(f"[WARNING] Command {command} failed for {ip}: {response.get('message')}")
        data["status"] = "Online" if is_online else "Offline"
        return data

    def update_real_data(self):
        """Fetch and update data for all slaves."""
        for slave_id, frame in self.slave_frames:
            ip = SLAVES[slave_id]
            threading.Thread(target=self.update_slave_frame, args=(frame, ip)).start()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_label.config(
            text=f"System Monitor v1.0.0 | Connected Slaves: {len(self.slave_frames)}/{len(SLAVES)} | Last Update: {now}"
        )
        self.after(2000, self.update_real_data)

    def update_slave_frame(self, frame, ip):
        """Update a single slave frame with fetched data."""
        try:
            data = self.fetch_slave_data(ip)
            frame.update_data(data)
        except Exception as e:
            print(f"[ERROR] Failed to update {ip}: {e}")

    def send_command(self, event=None):
        """Send a custom command to all slaves and log responses."""
        command = self.command_entry.get()
        if command:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.command_log.config(state="normal")
            self.command_log.insert(tk.END, f"> Sending command: {command} ({now})\n")
            for slave_id, ip in SLAVES.items():
                response = send_command(ip, command)
                self.command_log.insert(
                    tk.END, f"{slave_id} ({ip}): {response}\n"
                )
            self.command_log.config(state="disabled")
            self.command_entry.delete(0, tk.END)


if __name__ == "__main__":
    app = RackMonitorApp()
    app.mainloop()
