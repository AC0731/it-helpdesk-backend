import ipaddress
import platform
import shutil
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor


class NetworkTargetError(ValueError):
    """Raised when a diagnostic target crosses a protected network boundary."""


def resolve_public_target_ip(host: str) -> str:
    """
    Resolve once at the execution boundary and pin diagnostics to a public IP.

    Rejecting the complete answer set when any private/reserved address appears
    closes the validation-to-use gap that can otherwise allow DNS rebinding.
    """
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        if not literal.is_global:
            raise NetworkTargetError("Target resolved to a non-public address.")
        return str(literal)

    try:
        answers = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise NetworkTargetError(f"Target resolution failed: {exc}") from exc

    addresses = {
        answer[4][0]
        for answer in answers
        if answer and len(answer) > 4 and answer[4]
    }

    if not addresses:
        raise NetworkTargetError("Target resolution returned no usable addresses.")

    parsed_addresses = []
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global:
            raise NetworkTargetError(
                "Target resolution included a non-public address; diagnostics stopped."
            )
        parsed_addresses.append(parsed)

    selected = sorted(parsed_addresses, key=lambda value: (value.version, int(value)))[0]
    return str(selected)


def run_ping(host: str) -> str:
    command_name = "ping"

    if shutil.which(command_name):
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = [command_name, param, "4", host]

        try:
            return subprocess.check_output(
                command,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
                timeout=15,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            return f"Ping command failed or was restricted on this server: {exc}"

    return run_tcp_reachability_check(host)


def run_tcp_reachability_check(host: str) -> str:
    ports_to_test = [443, 80, 22]
    output_lines = [
        "System ping command is not available in this server environment.",
        "Running fallback TCP reachability check instead.",
        "",
        f"Pinned public address: {host}",
    ]

    for port in ports_to_test:
        start_time = time.monotonic()

        try:
            with socket.create_connection((host, port), timeout=3):
                latency_ms = round((time.monotonic() - start_time) * 1000, 2)
                output_lines.append(f"Port {port}: reachable in {latency_ms} ms")
        except OSError:
            output_lines.append(f"Port {port}: not reachable or filtered")

    return "\n".join(output_lines)


def run_traceroute(host: str) -> str:
    is_windows = platform.system().lower() == "windows"
    command_name = "tracert" if is_windows else "traceroute"

    if shutil.which(command_name):
        command = ["tracert", "-d", "-h", "15", host] if is_windows else [
            "traceroute",
            "-n",
            "-m",
            "15",
            host,
        ]

        try:
            return subprocess.check_output(
                command,
                universal_newlines=True,
                stderr=subprocess.STDOUT,
                timeout=20,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            return f"Traceroute command failed or was restricted on this server: {exc}"

    return (
        "Traceroute command is not available in this server environment.\n"
        "The app can continue with DNS validation, TCP reachability, and port checks."
    )


def scan_single_port(host: str, port: int) -> tuple[int, bool]:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return port, True
    except OSError:
        return port, False


def run_port_scan(host: str) -> dict:
    common_ports = [21, 22, 80, 443, 3389]
    results = {}

    with ThreadPoolExecutor(max_workers=len(common_ports)) as executor:
        futures = [
            executor.submit(scan_single_port, host, port)
            for port in common_ports
        ]

        for future in futures:
            port, is_open = future.result()
            results[str(port)] = "Open" if is_open else "Closed"

    return results
