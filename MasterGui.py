import platform
import socket
import json
import tkinter as tk
from tkinter import ttk
import time
import gc
import datetime
import threading
import subprocess as sp

import psutil

DEBUG = False

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
                # Use vcgencmd to get the temperature
                temp = float(sp.getoutput("vcgencmd measure_temp").split("=")[1].split("'")[0])
                return {"status": "success", "data": f"{temp:.2f}"}
            elif platform.system() == "Windows":
                return {"status": "error", "message": "CPU temperature not available on Windows"}
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
                try:
                    adc_value = float(
                        sp.getoutput(f"vcgencmd pmic_read_adc EXT5V_V").split("=")[-1].strip("V")
                    )
                    return {"status": "success", "data": f"{adc_value:.2f}V"}
                except Exception as e:
                    return {"status": "error", "message": str(e)}
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
            if DEBUG: print(f"[WARNING] Failed to detect model for {ip}: {response.get('message')}")
    except Exception as e:
        print(f"[ERROR] Exception while detecting model for {ip}: {e}")
    return "Unknown"


class SlaveFrame(tk.Frame):
    """Frame representing a single PC's status and data."""
    def __init__(self, master, slave_id, ip, model="Unknown", is_master=False):
        super().__init__(master, bg="#282c34")
        self.slave_id = slave_id
        self.ip = ip
        self.model = model
        self.is_master = is_master  # Flag to identify the master PC

        # Title with model info
        title_text = f"Master PC ({ip}) - {model}" if self.is_master else f"Slave PC {slave_id} ({ip}) - {model}"
        self.title_label = tk.Label(
            self,
            text=title_text,
            fg="#abb2bf",
            bg="#282c34",
            font=("Helvetica", 10, "bold"),  # Reduced font size for title
        )
        self.title_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(2, 0))  # Reduced padding

        # Rows for different data
        self._create_row(1, "CPU Temp:", "--°C", is_progressbar=True)
        self._create_row(2, "Disk Usage:", "--%", is_progressbar=True)
        self._create_row(3, "USB Devices:", "--")
        self._create_row(4, "ADC Value:", "N/A" if self.is_master else "--")
        self._create_row(5, "Uptime:", "--")
        self._create_row(6, "Status:", "Unknown")

    def _create_row(self, row, label_text, default_value, is_progressbar=False):
        """Helper to create a row with consistent alignment."""
        # Label for the row
        tk.Label(self, text=label_text, fg="#abb2bf", bg="#282c34", font=("Helvetica", 10)).grid(
            row=row, column=0, sticky="w", padx=8, pady=1  # Reduced padding and font size
        )

        # If the row has a progress bar
        if is_progressbar:
            progress = ttk.Progressbar(self, length=140, mode="determinate")  # Reduced width
            progress.grid(row=row, column=1, sticky="w", padx=(4, 8), pady=2)  # Reduced padding
            setattr(self, f"progress_{label_text.lower().replace(' ', '_').strip(':')}", progress)

        # Value label
        value_label = tk.Label(self, text=default_value, fg="#abb2bf", bg="#282c34", font=("Helvetica", 9, "bold"))
        value_label.grid(
            row=row, column=2, sticky="w", padx=(4, 0), pady=2  # Reduced padding and font size
        )
        setattr(self, f"value_{label_text.lower().replace(' ', '_').strip(':')}", value_label)

    def update_data(self, data):
        """Update the frame's data and progress bars."""
        # Update CPU Temp
        cpu_temp = data.get("cpu_temp", 0)
        self.progress_cpu_temp["value"] = self._safe_value(cpu_temp)
        self.value_cpu_temp.config(text=f"{cpu_temp:.1f}°C")

        # Update Disk Usage
        disk_usage = data.get("disk_usage", 0)
        self.progress_disk_usage["value"] = self._safe_value(disk_usage)
        self.value_disk_usage.config(text=f"{disk_usage:.1f}%")

        # Update USB Devices
        self.value_usb_devices.config(text=f"{data.get('usb_devices', '--')}")

        # Update ADC Value (only for slaves)
        if not self.is_master:
            self.value_adc_value.config(text=f"{data.get('adc_value', '--')}")

        # Update Uptime
        self.value_uptime.config(text=f"{data.get('uptime', '--')}")

        # Update Status
        self.value_status.config(text=f"{data.get('status', 'Online')}")

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

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Slave Frames
        self.slave_frames = []
        for idx, (slave_id, ip) in enumerate(SLAVES.items(), start=1):
            is_master = ip == "localhost"  # Detect master PC
            model = "Master PC" if is_master else self.fetch_slave_model(ip)
            frame = SlaveFrame(self, slave_id, ip, model=model, is_master=is_master)
            frame.grid(row=(idx - 1) // 2, column=(idx - 1) % 2, padx=10, pady=10, sticky="nsew")
            self.slave_frames.append((slave_id, frame))


        # Command Input
        self.command_frame = tk.Frame(self, bg="#282c34")
        self.command_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=10)

        self.command_frame.grid_columnconfigure(0, weight=1)

        self.command_entry = tk.Entry(self.command_frame, bg="#3e4452", fg="#abb2bf", insertbackground="#abb2bf", borderwidth=1)
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=5)  # Stretched
        self.command_entry.insert(0, "Enter custom command...")  # Placeholder text

        # Bind events for focus in and out
        self.command_entry.bind("<FocusIn>", self.clear_placeholder)
        self.command_entry.bind("<FocusOut>", self.add_placeholder)
        self.command_entry.bind("<Return>", self.send_command)  # Execute command on Enter

        self.send_button = ttk.Button(self.command_frame, text="Execute", command=self.send_command)
        self.send_button.grid(row=0, column=1, sticky="e", padx=(5, 0))  # Execute button

        # Command Log
        self.command_log = tk.Text(
            self,
            height=10,
            width=80,
            bg="#3e4452",
            fg="#abb2bf",
            insertbackground="#abb2bf",
            borderwidth=0,
            wrap=tk.WORD,
        )
        self.command_log.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        self.command_log.config(state="disabled")

        # Status Label
        self.status_label = tk.Label(
            self,
            text="System Monitor v1.0.0 | Connected Slaves: --/3 | Last Update: --",
            bg="#282c34",
            fg="#abb2bf",
        )
        self.status_label.grid(row=4, column=0, columnspan=3, padx=10, pady=(0, 10))

        self.update_real_data()
    
    def fetch_slave_model(self, ip):
        """Fetch the Raspberry Pi model for a given IP."""
        if ip == "localhost":
            # No model detection for localhost
            return "Master PC"
        try:
            response = send_command(ip, "RUN_SCRIPT", params={"script": "cat /proc/device-tree/model"})
            if response.get("status") == "success":
                raw_model = response.get("data", "Unknown").strip()
                if "Raspberry Pi 5" in raw_model:
                    return "Raspberry Pi 5"
                elif "Raspberry Pi 4" in raw_model:
                    return "Raspberry Pi 4"
                return raw_model
            else:
                print(f"[WARNING] Failed to fetch model for {ip}: {response.get('message')}")
        except Exception as e:
            print(f"[ERROR] Error fetching model for {ip}: {e}")
        return "Unknown"
    
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

        if ip == "localhost":
            # Fetch data locally for the master PC
            for command in DETAIL_COMMANDS:
                try:
                    params = {"channel": "EXT5V_V"} if command == "REQUEST_ADC" else None
                    response = fetch_local_data(command)
                    if response.get("status") == "success":
                        is_online = True
                        raw_data = response.get("data", "")
                        if command == "GET_CPU_TEMP":
                            data["cpu_temp"] = float(raw_data)
                        elif command == "GET_UPTIME":
                            data["uptime"] = raw_data
                        elif command == "GET_DISK_USAGE":
                            data["disk_usage"] = float(raw_data.strip("%"))
                        elif command == "LIST_USB":
                            data["usb_devices"] = raw_data
                        elif command == "REQUEST_ADC":
                            data["adc_value"] = raw_data
                    else:
                        if DEBUG: print(f"[WARNING] Command {command} failed for localhost: {response.get('message')}")
                except Exception as e:
                    print(f"[ERROR] Failed to execute {command} on localhost: {e}")
        else:
            # Fetch data from the slave
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
                    if DEBUG: print(f"[WARNING] Command {command} failed for {ip}: {response.get('message')}")

        data["status"] = "Online" if is_online else "Offline"
        return data

    
    def update_real_data(self):
        """Fetch and update data for all slaves."""
        for slave_id, frame in self.slave_frames:
            ip = SLAVES[slave_id]
            threading.Thread(target=self.update_slave_frame, args=(frame, ip)).start()
        
        # Perform garbage collection to free up memory
        gc.collect()

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_label.config(
            text=f"System Monitor v1.0.0 | Connected PC's: {len(self.slave_frames)}/{len(SLAVES)} | Last Update: {now}"
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
            self.command_log.insert(tk.END, f"> Sending command: {command} ({now})\n\n")

            # Send the command to all slaves
            for slave_id, ip in SLAVES.items():
                if ip == "localhost":  # Skip localhost
                    continue

                try:
                    response = send_command(ip, "RUN_SCRIPT", params={"script": command})
                    if response is None:
                        response = {"status": "error", "message": "No response"}
                    status = response.get("status", "unknown")
                    message = response.get("data", response.get("message", "No response"))

                    # Append response with enforced line breaks
                    self.command_log.insert(
                        tk.END, f"{slave_id} ({ip}) [{now}]: {message}\n\n"
                    )
                    self.command_log.insert(tk.END, "\n")  # Extra line break to ensure spacing
                except Exception as e:
                    self.command_log.insert(
                        tk.END, f"{slave_id} ({ip}) [{now}]: ERROR - {str(e)}\n\n"
                    )

            # Add final line break for spacing
            self.command_log.insert(tk.END, "\n\n")
            self.command_log.see(tk.END)
            self.command_log.config(state="disabled")
            self.command_entry.delete(0, tk.END)


    def _execute_command_on_slave(self, slave_id, ip, command):
        """Execute a custom command on a single slave and log the response."""
        try:
            # Send the command as part of RUN_SCRIPT
            response = send_command(ip, "RUN_SCRIPT", {"script": command})
            now = datetime.datetime.now().strftime("%H:%M:%S")
            if response.get("status") == "success":
                output = response.get("data", "No output")
                self.command_log.insert(tk.END, f"{slave_id} ({ip}) [{now}]: {output}\n")
            else:
                error_message = response.get("message", "Unknown error")
                self.command_log.insert(tk.END, f"{slave_id} ({ip}) [{now}]: ERROR - {error_message}\n")
        except Exception as e:
            self.command_log.insert(tk.END, f"{slave_id} ({ip}): ERROR - {e}\n")
        finally:
            self.command_log.config(state="disabled")
            self.command_log.see(tk.END)



if __name__ == "__main__":
    app = RackMonitorApp()
    app.mainloop()
