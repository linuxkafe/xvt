"""Tests for XVT SSH injection module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.xvt.injection.ssh import (
    InjectionConfig,
    InjectionResult,
    KeyInjector,
    generate_key_pair,
)


def test_injection_config_defaults():
    config = InjectionConfig(
        device_ip="10.0.0.103",
        public_key_path=Path("/tmp/test.pub"),
    )
    assert config.device_ip == "10.0.0.103"
    assert config.username == "root"
    assert config.port == 22
    assert len(config.authorized_keys_paths) == 3
    assert "/etc/dropbear/authorized_keys" in config.authorized_keys_paths


def test_injection_config_custom_paths():
    config = InjectionConfig(
        device_ip="10.0.0.103",
        public_key_path=Path("/tmp/test.pub"),
        authorized_keys_paths=["/custom/path/authorized_keys"],
    )
    assert config.authorized_keys_paths == ["/custom/path/authorized_keys"]


def test_injection_result():
    result = InjectionResult(
        success=True,
        paths_tried=["/path1", "/path2"],
        paths_succeeded=["/path1"],
    )
    assert result.success is True
    assert len(result.paths_tried) == 2
    assert len(result.paths_succeeded) == 1


def test_key_injector_dry_run():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pub', delete=False) as f:
        f.write("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI test@example.com")
        pub_path = Path(f.name)

    try:
        config = InjectionConfig(
            device_ip="10.0.0.103",
            public_key_path=pub_path,
        )
        injector = KeyInjector(config, dry_run=True)

        # Mock shell function that always succeeds
        mock_shell = MagicMock(return_value=True)
        result = injector.inject_via_shell(mock_shell)

        assert result.success is True
        assert len(result.paths_succeeded) == 3
        assert len(result.paths_tried) == 3
    finally:
        pub_path.unlink()


def test_key_injector_reads_key():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pub', delete=False) as f:
        f.write("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI test@example.com\n")
        pub_path = Path(f.name)

    try:
        config = InjectionConfig(
            device_ip="10.0.0.103",
            public_key_path=pub_path,
        )
        injector = KeyInjector(config, dry_run=True)
        key = injector._read_public_key()
        assert key == "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI test@example.com"
    finally:
        pub_path.unlink()


def test_generate_key_pair():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        priv_path, pub_path = generate_key_pair(output_dir, "test_key")

        assert priv_path.exists()
        assert pub_path.exists()
        assert priv_path.name == "test_key"
        assert pub_path.name == "test_key.pub"

        # Check permissions
        assert oct(priv_path.stat().st_mode & 0o777) == '0o600'
        assert oct(pub_path.stat().st_mode & 0o777) == '0o644'

        # Verify keys are valid
        priv_content = priv_path.read_bytes()
        pub_content = pub_path.read_bytes()
        assert b"PRIVATE KEY" in priv_content
        assert pub_content.startswith(b"ssh-ed25519 ")


def test_injection_result_success():
    result = InjectionResult(
        success=True,
        paths_tried=["/path1"],
        paths_succeeded=["/path1"],
    )
    assert result.success is True

    result = InjectionResult(
        success=False,
        paths_tried=["/path1"],
        paths_succeeded=[],
        error="Failed",
    )
    assert result.success is False
    assert result.error == "Failed"
