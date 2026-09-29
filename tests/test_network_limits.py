import subprocess

from app.services import network_tools


def test_bound_output_truncates_large_command_output(monkeypatch):
    monkeypatch.setattr(network_tools.settings, "diagnostic_output_limit", 1000)

    output = network_tools.bound_output("x" * 1500)

    assert len(output) < 1600
    assert output.startswith("x" * 1000)
    assert "truncated 500 characters" in output


def test_ping_timeout_returns_bounded_operational_message(monkeypatch):
    monkeypatch.setattr(network_tools.shutil, "which", lambda _name: "/usr/bin/ping")

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["ping"], timeout=15)

    monkeypatch.setattr(network_tools.subprocess, "check_output", timeout)

    assert network_tools.run_ping("8.8.8.8") == "Ping timed out after 15 seconds."


def test_traceroute_timeout_returns_bounded_operational_message(monkeypatch):
    monkeypatch.setattr(
        network_tools.shutil,
        "which",
        lambda name: f"/usr/bin/{name}",
    )

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["traceroute"], timeout=20)

    monkeypatch.setattr(network_tools.subprocess, "check_output", timeout)

    assert (
        network_tools.run_traceroute("8.8.8.8")
        == "Traceroute timed out after 20 seconds."
    )
