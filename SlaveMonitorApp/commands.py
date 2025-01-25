import subprocess

def request_adc(params):
    try:
        channel = params.get("channel", "EXT5V_V")
        result = subprocess.check_output(["vcgencmd", "pmic_read_adc", channel])
        return {"status": "success", "data": result.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_uptime(params):
    try:
        result = subprocess.check_output(["uptime", "-p"])
        return {"status": "success", "data": result.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_cpu_temp(params):
    try:
        result = subprocess.check_output(["vcgencmd", "measure_temp"])
        return {"status": "success", "data": result.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_usb(params):
    try:
        result = subprocess.check_output(["lsusb"])
        return {"status": "success", "data": result.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def reboot(params):
    try:
        subprocess.Popen(["sudo", "reboot"])
        return {"status": "success", "message": "Rebooting..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_disk_usage(params):
    try:
        result = subprocess.check_output(["df", "-h"])
        return {"status": "success", "data": result.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_script(params):
    """Execute a custom script or command."""
    try:
        script = params.get("script", "")
        if not script:
            return {"status": "error", "message": "No script provided"}
        # Execute the script
        result = subprocess.check_output(script, shell=True, stderr=subprocess.STDOUT)
        return {"status": "success", "data": result.decode().strip()}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.output.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

COMMANDS = {
    "REQUEST_ADC": request_adc,
    "GET_UPTIME": get_uptime,
    "GET_CPU_TEMP": get_cpu_temp,
    "LIST_USB": list_usb,
    "REBOOT": reboot,
    "GET_DISK_USAGE": get_disk_usage,
    "RUN_SCRIPT": run_script
}