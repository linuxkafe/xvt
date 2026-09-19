"""Tests for XVT SSH verification module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.xvt.verification.ssh import (
    SSHVerifier,
    VerificationConfig,
    VerificationResult,
    verify_ssh_access,
)


def test_verification_config_defaults():
    config = VerificationConfig(
        device_ip="10.0.0.103",
        private_key_path=Path("/tmp/test.key"),
    )
    assert config.device_ip == "10.0.0.103"
    assert config.username == "root"
    assert config.port == 22
    assert config.max_retries == 12
    assert config.base_delay == 5.0


def test_verification_result():
    result = VerificationResult(
        success=True,
        device_ip="10.0.0.103",
        server_type="dropbear",
        server_version="2022.83",
    )
    assert result.success is True
    assert result.device_ip == "10.0.0.103"
    assert result.server_type == "dropbear"


def test_ssh_verifier_dry_run():
    config = VerificationConfig(
        device_ip="10.0.0.103",
        private_key_path=Path("/tmp/test.key"),
    )
    verifier = SSHVerifier(config, dry_run=True)

    result = verifier.verify()

    assert result.success is True
    assert result.device_ip == "10.0.0.103"
    assert result.server_type == "dropbear (simulated)"
    assert len(result.commands_run) > 0
    verifier.close()


def test_ssh_verifier_dry_run_detect_server():
    config = VerificationConfig(
        device_ip="10.0.0.103",
        private_key_path=Path("/tmp/test.key"),
    )
    verifier = SSHVerifier(config, dry_run=True)

    server_type, version = verifier.detect_server_type()

    assert server_type == "dropbear (simulated)"
    assert version == "2022.83"
    verifier.close()


def test_ssh_verifier_dry_run_commands():
    config = VerificationConfig(
        device_ip="10.0.0.103",
        private_key_path=Path("/tmp/test.key"),
    )
    verifier = SSHVerifier(config, dry_run=True)

    commands = verifier.run_verification_commands()

    assert len(commands) == len(verifier.VERIFICATION_COMMANDS)
    for cmd in commands:
        assert "command" in cmd
        assert "description" in cmd
        assert cmd["stdout"] == "[DRY-RUN] simulated output"
    verifier.close()


def test_ssh_verifier_collect_info():
    config = VerificationConfig(
        device_ip="10.0.0.103",
        private_key_path=Path("/tmp/test.key"),
    )
    verifier = SSHVerifier(config, dry_run=True)

    mock_commands = [
        {"command": "uname -a", "stdout": "Linux vacuum 4.9.0 #1 SMP"},
        {"command": "cat /etc/os-release", "stdout": 'PRETTY_NAME="OpenWrt"\nVERSION="21.02"'},
    ]
    info = verifier.collect_device_info(mock_commands)

    assert "kernel" in info
    assert "pretty_name" in info or "PRETTY_NAME" in info
    verifier.close()


def test_verification_result_failed():
    result = VerificationResult(
        success=False,
        device_ip="10.0.0.103",
        error="Connection timeout",
    )
    assert result.success is False
    assert result.error == "Connection timeout"


def test_verify_ssh_access_function():
    with patch('src.xvt.verification.ssh.SSHVerifier') as mock_verifier_class:
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = VerificationResult(
            success=True, device_ip="10.0.0.103"
        )
        mock_verifier_class.return_value = mock_verifier

        result = verify_ssh_access("10.0.0.103", Path("/tmp/test.key"), dry_run=True)

        assert result.success is True
        assert result.device_ip == "10.0.0.103"


def test_verification_config_custom():
    config = VerificationConfig(
        device_ip="10.0.0.103",
        private_key_path=Path("/tmp/test.key"),
        username="admin",
        port=2222,
        timeout=30.0,
        max_retries=20,
        base_delay=10.0,
    )
    assert config.username == "admin"
    assert config.port == 2222
    assert config.timeout == 30.0
    assert config.max_retries == 20
    assert config.base_delay == 10.0
