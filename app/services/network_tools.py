# app/services/network_tools.py
import platform
import shutil
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor


def run_ping(host: str) -> str:
    command_name = "ping"

    if shutil.which(command_name):
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = [command_name, param, "4", host]

        try:
            output = subprocess.check_output(
                command,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
                timeout=15
            )
            return output
        except Exception as e:
            return f"Ping command failed or was restricted on this server: {str(e)}"

    return run_tcp_reachability_check(host)


def run_tcp_reachability_check(host: str) -> str:
    ports_to_test = [443, 80, 22]
    output_lines = [
        "System ping command is not available in this server environment.",
        "Running fallback TCP reachability check instead.",
        ""
    ]

    try:
        resolved_ip = socket.gethostbyname(host)
        output_lines.append(f"Resolved host: {host} -> {resolved_ip}")
    except Exception as e:
        output_lines.append(f"DNS resolution failed for {host}: {str(e)}")
        return "\n".join(output_lines)

    for port in ports_to_test:
        start_time = time.time()

        try:
            with socket.create_connection((host, port), timeout=3):
                latency_ms = round((time.time() - start_time) * 1000, 2)
                output_lines.append(f"Port {port}: reachable in {latency_ms} ms")
        except Exception:
            output_lines.append(f"Port {port}: not reachable or filtered")

    return "\n".join(output_lines)


def run_traceroute(host: str) -> str:
    command_name = "tracert" if platform.system().lower() == "windows" else "traceroute"

    if shutil.which(command_name):
        command = ["tracert", "-d"] if platform.system().lower() == "windows" else ["traceroute", "-n"]

        if platform.system().lower() == "windows":
            command.extend(["-h", "15", host])
        else:
            command.extend(["-m", "15", host])

        try:
            output = subprocess.check_output(
                command,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
                timeout=20
            )
            return output
        except Exception as e:
            return f"Traceroute command failed or was restricted on this server: {str(e)}"

    return (
        "Traceroute command is not available in this server environment.\n"
        "This usually happens on cloud deployments where traceroute is not installed "
        "or where network diagnostic commands are restricted.\n"
        "The app is still able to perform DNS resolution, TCP reachability checks, "
        "and port scanning."
    )


def scan_single_port(host: str, port: int) -> tuple:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        result = sock.connect_ex((host, port))
        sock.close()
        return port, result == 0
    except Exception:
        return port, False


def run_port_scan(host: str) -> dict:
    common_ports = [21, 22, 80, 443, 3389]
    results = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_single_port, host, port) for port in common_ports]

        for future in futures:
            port, is_open = future.result()
            results[str(port)] = "Open" if is_open else "Closed"

    return results