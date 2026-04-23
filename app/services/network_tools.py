import subprocess
import platform
import socket
from concurrent.futures import ThreadPoolExecutor

def run_ping(host: str) -> str:
    # Use -n for Windows, -c for Linux (Render)
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', host]
    try:
        # We catch ALL Exceptions now so the API never crashes
        output = subprocess.check_output(command, universal_newlines=True, stderr=subprocess.STDOUT)
        return output
    except Exception as e:
        return f"Ping is restricted on this cloud server. Error: {str(e)}"

def run_traceroute(host: str) -> str:
    # Render is Linux, so it uses 'traceroute'
    command = ['tracert', '-d'] if platform.system().lower() == 'windows' else ['traceroute', '-n']
    if platform.system().lower() == 'windows':
        command.extend(['-h', '15', host])
    else:
        command.extend(['-m', '15', host])
    try:
        output = subprocess.check_output(command, universal_newlines=True, stderr=subprocess.STDOUT)
        return output
    except Exception as e:
        return f"Traceroute is restricted on this cloud server. Error: {str(e)}"

def scan_single_port(host: str, port: int) -> tuple:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        result = sock.connect_ex((host, port))
        sock.close()
        return port, result == 0
    except:
        return port, False

def run_port_scan(host: str) -> dict:
    common_ports = [21, 22, 80, 443, 3389] 
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_single_port, host, p) for p in common_ports]
        for future in futures:
            port, is_open = future.result()
            results[str(port)] = "Open" if is_open else "Closed"
    return results