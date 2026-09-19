"""Tests for XVT dustbin exploit module."""

import importlib.util
from unittest.mock import MagicMock, patch

from src.xvt.exploits.dustbin import DustbinConfig, DustbinExploit, find_dustbin_gpio


def test_dustbin_config_defaults():
    config = DustbinConfig()
    assert config.gpio_chip == "gpiochip0"
    assert config.gpio_line == 0
    assert config.short_duration == 2.0
    assert config.boot_wait == 5.0


def test_dustbin_exploit_dry_run_setup():
    config = DustbinConfig(gpio_chip="gpiochip0", gpio_line=12)
    exploit = DustbinExploit(config, dry_run=True)
    assert exploit.setup_gpio() is True


def test_dustbin_exploit_dry_run_apply_short():
    config = DustbinConfig(gpio_chip="gpiochip0", gpio_line=12)
    exploit = DustbinExploit(config, dry_run=True)
    assert exploit.apply_short(1.5) is True


def test_dustbin_exploit_dry_run_wait_for_boot():
    config = DustbinConfig()
    exploit = DustbinExploit(config, dry_run=True)
    assert exploit.wait_for_boot() is True


def test_dustbin_exploit_dry_run_get_recovery_shell():
    config = DustbinConfig()
    exploit = DustbinExploit(config, dry_run=True)
    assert exploit.get_recovery_shell() is True


def test_dustbin_exploit_dry_run_inject_key():
    config = DustbinConfig()
    exploit = DustbinExploit(config, dry_run=True)
    public_key = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI test@example.com"
    assert exploit.inject_ssh_key(public_key) is True


def test_dustbin_exploit_dry_run_run_exploit():
    config = DustbinConfig()
    exploit = DustbinExploit(config, dry_run=True)
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pub', delete=False) as f:
        f.write("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI test@example.com")
        key_path = Path(f.name)
    try:
        result = exploit.run_exploit("10.0.0.103", key_path)
        assert result is True
    finally:
        key_path.unlink()


def test_dustbin_from_model():
    exploit = DustbinExploit.from_model("viomi.vacuum.v8", dry_run=True)
    assert exploit.config.gpio_chip == "gpiochip0"
    assert exploit.config.gpio_line == 12


def test_dustbin_from_model_unknown():
    exploit = DustbinExploit.from_model("unknown.model", dry_run=True)
    assert exploit.config.gpio_chip == "gpiochip0"
    assert exploit.config.gpio_line == 12


def test_find_dustbin_gpio_known():
    gpio = find_dustbin_gpio("viomi.vacuum.v8")
    assert gpio == {"chip": "gpiochip0", "line": 12}


def test_find_dustbin_gpio_unknown():
    gpio = find_dustbin_gpio("unknown.model")
    assert gpio is None


def test_dustbin_exploit_setup_gpio_real():
    # Skip if gpiod not available (mocking gpiod.Chip requires gpiod to be importable)
    if importlib.util.find_spec("gpiod") is None:
        import pytest
        pytest.skip("gpiod not available")

    with patch('gpiod.Chip') as mock_chip:
        mock_chip_instance = MagicMock()
        mock_line = MagicMock()
        mock_chip.return_value = mock_chip_instance
        mock_chip_instance.get_line.return_value = mock_line

        config = DustbinConfig(gpio_chip="gpiochip0", gpio_line=12)
        exploit = DustbinExploit(config, dry_run=False)
        result = exploit.setup_gpio()

        assert result is True
        mock_chip.assert_called_once_with("gpiochip0")
        mock_chip_instance.get_line.assert_called_once_with(12)
        # Check that request was called (API may vary)
        assert mock_line.request.called


def test_dustbin_exploit_cleanup():
    config = DustbinConfig()
    exploit = DustbinExploit(config, dry_run=True)
    exploit._chip = MagicMock()
    exploit._line = MagicMock()
    exploit.cleanup_gpio()
    exploit._line.release.assert_called_once()
    exploit._chip.close.assert_called_once()


def test_dustbin_config_custom():
    config = DustbinConfig(
        gpio_chip="gpiochip1",
        gpio_line=24,
        short_duration=3.0,
        boot_wait=10.0,
    )
    assert config.gpio_chip == "gpiochip1"
    assert config.gpio_line == 24
    assert config.short_duration == 3.0
    assert config.boot_wait == 10.0
