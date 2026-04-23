# app/services/network_tools.py
import subprocess
import platform
import socket
from concurrent.futures import ThreadPoolExecutor

def run_ping(host: str) -> str:
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', host]
    try:
        output = subprocess.check_output(command, universal_newlines=True, stderr=subprocess.STDOUT)
        return output
    except Exception as e:
        return f"Ping failed or restricted on this server: {str(e)}"

def run_traceroute(host: str) -> str:
    # Use 'tracert' for Windows, 'traceroute' for Linux/Render
    command = ['tracert', '-d'] if platform.system().lower() == 'windows' else ['traceroute', '-n']
    if platform.system().lower() == 'windows':
        command.extend(['-h', '15', host])
    else:
        command.extend(['-m', '15', host])
    try:
        output = subprocess.check_output(command, universal_newlines=True, stderr=subprocess.STDOUT)
        return output
    except Exception as e:
        return f"Traceroute failed or restricted on this server: {str(e)}"

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