import socket

import pytest

from app.services.network_tools import NetworkTargetError, resolve_public_target_ip


def test_resolution_rejects_private_address_after_initial_validation(monkeypatch):
    """A hostname that later resolves internally must never reach diagnostic tools."""

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.10.20.15", 0))
        ],
    )

    with pytest.raises(NetworkTargetError, match="non-public"):
        resolve_public_target_ip("support-target.example")


def test_resolution_rejects_mixed_public_and_private_answers(monkeypatch):
    """Mixed DNS answers are rejected rather than selecting the public address."""

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.50.10", 0)),
        ],
    )

    with pytest.raises(NetworkTargetError, match="non-public"):
        resolve_public_target_ip("support-target.example")


def test_resolution_returns_deterministic_public_ip(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.35", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
        ],
    )

    assert resolve_public_target_ip("support-target.example") == "93.184.216.34"
