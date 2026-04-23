import subprocess
import platform

def run_ping(host: str) -> str:
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '4', host]
    try:
        output = subprocess.check_output(command, universal_newlines=True)
        return output
    except subprocess.CalledProcessError as e:
        return f"Ping failed: {e}"

def run_traceroute(host: str) -> str:
    command = ['tracert'] if platform.system().lower() == 'windows' else ['traceroute']
    if platform.system().lower() == 'windows':
        command.extend(['-h', '15', host])
    else:
        command.extend(['-m', '15', host])
    try:
        output = subprocess.check_output(command, universal_newlines=True)
        return output
    except subprocess.CalledProcessError as e:
        return f"Traceroute failed: {e}"