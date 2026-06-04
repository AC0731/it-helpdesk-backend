import ipaddress
import re
import socket


class TargetValidationError(ValueError):
    pass


BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
}


DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,63}\.?$"
)


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip().lower().rstrip(".")

    if not target:
        raise TargetValidationError("Target IP or domain is required.")

    blocked_characters = ["://", "/", "\\", "?", "#", "@", "*", ",", ";"]

    if any(character in target for character in blocked_characters):
        raise TargetValidationError(
            "Enter only a domain or IP address, not a full URL or path."
        )

    if any(character.isspace() for character in target):
        raise TargetValidationError("Target cannot contain spaces.")

    return target


def is_public_ip(ip_address: str) -> bool:
    try:
        parsed_ip = ipaddress.ip_address(ip_address)
    except ValueError:
        return False

    return parsed_ip.is_global


def validate_ip_target(target: str) -> str | None:
    try:
        parsed_ip = ipaddress.ip_address(target)
    except ValueError:
        return None

    if not parsed_ip.is_global:
        raise TargetValidationError(
            "Private, local, reserved, or internal IP addresses are not allowed."
        )

    return target


def validate_domain_target(target: str) -> str:
    if target in BLOCKED_HOSTNAMES or target.endswith(".localhost"):
        raise TargetValidationError("Localhost targets are not allowed.")

    if not DOMAIN_PATTERN.match(target):
        raise TargetValidationError(
            "Target must be a valid public domain or public IP address."
        )

    try:
        resolved_addresses = socket.getaddrinfo(target, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise TargetValidationError("Target could not be resolved.")

    resolved_ips = {
        address_info[4][0]
        for address_info in resolved_addresses
        if address_info and address_info[4]
    }

    if not resolved_ips:
        raise TargetValidationError("Target could not be resolved.")

    for resolved_ip in resolved_ips:
        if not is_public_ip(resolved_ip):
            raise TargetValidationError(
                "Target resolves to a private, local, reserved, or internal IP address."
            )

    return target


def validate_public_target(raw_target: str) -> str:
    target = normalize_target(raw_target)

    ip_target = validate_ip_target(target)

    if ip_target:
        return ip_target

    return validate_domain_target(target)
