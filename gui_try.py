import socket
import json
import threading
import tkinter as tk
from tkinter import ttk
import datetime

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



class PCFrame(tk.Frame):
    def __init__(self, master, pc_name, ip=None):
        super().__init__(master, bg="#282c34")
        self.pc_name = pc_name
        self.ip = ip

        self.title_label = tk.Label(self, text=pc_name, fg="#abb2bf", bg="#282c34", font=("Helvetica", 12, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(5, 0))

        self.cpu_label = tk.Label(self, text="CPU Usage:", fg="#abb2bf", bg="#282c34")
        self.cpu_label.grid(row=1, column=0, sticky="w")
        self.cpu_progress = ttk.Progressbar(self, length=150, mode="determinate")
        self.cpu_progress.grid(row=1, column=1, padx=(5, 0), sticky="w")

        self.memory_label = tk.Label(self, text="Memory:", fg="#abb2bf", bg="#282c34")
        self.memory_label.grid(row=2, column=0, sticky="w")
        self.memory_progress = ttk.Progressbar(self, length=150, mode="determinate")
        self.memory_progress.grid(row=2, column=1, padx=(5, 0), sticky="w")

        self.disk_label = tk.Label(self, text="Disk Usage:", fg="#abb2bf", bg="#282c34")
        self.disk_label.grid(row=3, column=0, sticky="w")
        self.disk_progress = ttk.Progressbar(self, length=150, mode="determinate")
        self.disk_progress.grid(row=3, column=1, padx=(5, 0), sticky="w")

        self.temp_label = tk.Label(self, text="Temperature:", fg="#abb2bf", bg="#282c34")
        self.temp_label.grid(row=4, column=0, sticky="w")

        self.uptime_label = tk.Label(self, text=f"Uptime: --", fg="#abb2bf", bg="#282c34")
        self.uptime_label.grid(row=5, column=0, sticky="w")


        self.usb_label = tk.Label(self, text="USB Devices:", fg="#abb2bf", bg="#282c34", wraplength=150, justify="left") # USB devices label, with text wrapping
        self.usb_label.grid(row=6, column=0, columnspan=2, sticky="w")  # Spans two columns, positioned below


        self.online_label = tk.Label(self, text="Offline", fg="red", bg="#282c34")
        self.online_label.place(relx=0.9, y=10, anchor='ne')

        self.update_data({"cpu_usage": 0, "memory": 0, "disk_usage": 0, "temperature": "--", "uptime": "--"})
        if ip:
            self.query_details()


    def update_data(self, data):
        self.cpu_progress["value"] = data.get("cpu_usage", 0)
        self.memory_progress["value"] = data.get("memory", 0)
        self.disk_progress["value"] = data.get("disk_usage", 0)
        self.temp_label.config(text=f"Temperature: {data.get('temperature', '--')}°C")
        self.uptime_label.config(text=f"Uptime: {data.get('uptime', '--')}")

        usb_devices = data.get("usb_devices", "No USB data")
        self.usb_label.config(text=f"USB Devices:\n{usb_devices}")


    def query_details(self):
        if self.ip:
            threading.Thread(target=self.update_details, args=(self.ip,)).start()

    def update_details(self, ip):
            results = {}
            for cmd in DETAIL_COMMANDS:
                response = send_command(ip, cmd)
                if response.get("status") == "success":
                    results[cmd] = response.get("data")
                else:
                    results[cmd] = f"Error: {response.get('message', 'Unknown')}"

            try:
                cpu_temp = int(results.get("GET_CPU_TEMP", 0).replace("°C", ""))
                uptime = results.get("GET_UPTIME")
                disk_usage_lines = results.get("GET_DISK_USAGE", "").splitlines()
                if disk_usage_lines:
                    disk_usage = int(disk_usage_lines[1].split()[4].replace("%", ""))
                else:
                    disk_usage = 0
                usb_list = results.get("LIST_USB")

                self.update_data({
                    "cpu_usage": cpu_temp,
                    "memory": 0,
                    "disk_usage": disk_usage,
                    "temperature": results.get("GET_CPU_TEMP"),
                    "uptime": uptime,
                    "usb_devices": usb_list
                })
                self.online_label.config(text="Online", fg="green")


            except (ValueError, IndexError) as e:
                print(f"Error parsing data from {self.pc_name}: {e}")
                # Display more specific error messages on the labels
                self.cpu_progress["value"] = 0  # Reset to 0 on error
                self.memory_progress["value"] = 0  # Reset to 0 on error
                self.disk_progress["value"] = 0  # Reset to 0 on error

                self.temp_label.config(text="Temperature: Error")
                self.uptime_label.config(text="Uptime: Error")
                self.usb_label.config(text=f"USB Devices: Error")

class RackMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rack Monitoring System")
        self.configure(bg="#282c34")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background="#3e4452", foreground="#abb2bf", borderwidth=0, padding=5)
        style.configure("TFrame", background="#282c34")
        style.configure("TEntry", fieldbackground="#3e4452", foreground="#abb2bf")
        style.configure("TProgressbar", foreground="#2196f3", background="#2196f3", troughcolor="#3e4452", borderwidth=0, thickness=10)


        self.pc_frames = {}

        pcs = [("Master PC", None)] + [(f"Slave PC {i+1}", ip) for i, (name, ip) in enumerate(SLAVES.items())]

        row, col = 0, 0
        for name, ip in pcs:
            frame = PCFrame(self, name, ip)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.pc_frames[name] = frame

            col += 1
            if col > 2:  # 3 columns
                col = 0
                row += 1



        self.command_frame = ttk.Frame(self, padding=10, style="TFrame")
        self.command_frame.grid(row=1, column=0, columnspan=3, sticky="ew") # Columnspan updated

        self.command_entry = ttk.Entry(self.command_frame, width=50, style="TEntry")
        self.command_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.command_entry.insert(0, "Enter custom command...")
        self.command_entry.bind("<FocusIn>", self.clear_placeholder)
        self.command_entry.bind("<FocusOut>", self.add_placeholder)
        self.command_entry.bind("<Return>", self.send_command) # Bind Enter key

        self.send_button = ttk.Button(self.command_frame, text="Execute", command=self.send_command, style="TButton")
        self.send_button.grid(row=0, column=1, sticky="e")

        self.command_log = tk.Text(self.command_frame, height=10, width=50, bg="#3e4452", fg="#abb2bf", insertbackground="#abb2bf", borderwidth=0, wrap=tk.WORD, font=("Courier New", 10))
        self.command_log.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="nsew") # Updated columnspan
        self.command_log.config(state="disabled")



        self.status_label = tk.Label(self, text="System Monitor v1.0.0 | Connected Slaves: --/-- | Last Update: --", bg="#282c34", fg="#abb2bf", anchor="w")
        self.status_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 0)) # Updated columnspan


        self.refresh_interval = 2000
        self.query_pc_details()



    def clear_placeholder(self, event):
        if self.command_entry.get() == "Enter custom command...":
            self.command_entry.delete(0, tk.END)

    def add_placeholder(self, event):
        if not self.command_entry.get():
            self.command_entry.insert(0, "Enter custom command...")



    def query_pc_details(self):
        for pc_name, frame in self.pc_frames.items():
            if frame.ip:
                frame.query_details()

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_label.config(text=f"System Monitor v1.0.0 | Connected Slaves: {len(SLAVES)}/{len(SLAVES)} | Last Update: {now}")
        self.after(self.refresh_interval, self.query_pc_details)


    def send_command(self, event=None):
        command = self.command_entry.get()
        if command and command != "Enter custom command...":

            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.command_log.config(state="normal")
            self.command_log.insert(tk.END, f"> {command} (executed at {now})\n")
            self.command_log.see(tk.END)
            self.command_log.config(state="disabled")

            print(f"Sending command: {command}")  # Or your actual send command logic
            self.command_entry.delete(0, tk.END)


def run_gui():
    root = tk.Tk()
    app = RackMonitorApp()
    root.mainloop()

if __name__ == "__main__":
    run_gui()