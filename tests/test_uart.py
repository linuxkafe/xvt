"""Tests for XVT UART exploit module."""

from unittest.mock import MagicMock, patch

from src.xvt.exploits.uart import UARTConfig, UARTExploit, find_uart_ports


def test_uart_config_defaults():
    config = UARTConfig(port="/dev/ttyUSB0")
    assert config.port == "/dev/ttyUSB0"
    assert config.baudrate == 115200
    assert config.timeout == 2.0


def test_uart_exploit_dry_run_connect():
    config = UARTConfig(port="/dev/ttyUSB0")
    exploit = UARTExploit(config, dry_run=True)
    assert exploit.connect() is True
    assert exploit.dry_run is True


def test_uart_exploit_dry_run_get_root_shell():
    config = UARTConfig(port="/dev/ttyUSB0")
    exploit = UARTExploit(config, dry_run=True)
    # In dry_run, _read_until returns expected, so ROOT_PROMPT will be found
    assert exploit.get_root_shell() is True


def test_uart_exploit_dry_run_inject_key():
    config = UARTConfig(port="/dev/ttyUSB0")
    exploit = UARTExploit(config, dry_run=True)
    public_key = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI test@example.com"
    assert exploit.inject_ssh_key(public_key) is True


def test_uart_exploit_dry_run_run_exploit():
    config = UARTConfig(port="/dev/ttyUSB0")
    exploit = UARTExploit(config, dry_run=True)
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


def test_find_uart_ports_returns_list():
    ports = find_uart_ports()
    assert isinstance(ports, list)


@patch('serial.Serial')
def test_uart_exploit_connect_real(mock_serial):
    mock_instance = MagicMock()
    mock_instance.is_open = True
    mock_serial.return_value = mock_instance

    config = UARTConfig(port="/dev/ttyUSB0")
    exploit = UARTExploit(config, dry_run=False)
    result = exploit.connect()

    assert result is True
    mock_serial.assert_called_once()


@patch('serial.Serial')
def test_uart_exploit_connect_failure(mock_serial):
    import serial
    mock_serial.side_effect = serial.SerialException("Port not found")

    config = UARTConfig(port="/dev/ttyUSB999")
    exploit = UARTExploit(config, dry_run=False)
    result = exploit.connect()

    assert result is False


def test_uart_config_custom_settings():
    config = UARTConfig(
        port="/dev/ttyUSB0",
        baudrate=9600,
        bytesize=7,
        parity='E',
        stopbits=2,
        timeout=5.0
    )
    assert config.baudrate == 9600
    assert config.bytesize == 7
    assert config.parity == 'E'
    assert config.stopbits == 2
    assert config.timeout == 5.0

