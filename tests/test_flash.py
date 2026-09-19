"""Tests for XVT OTA flash module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.xvt.flash import (
    FlashConfig,
    FlashResult,
    OTAFlasher,
    flash_firmware,
)


def test_flash_config_defaults():
    config = FlashConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path=Path("/tmp/firmware.img"),
    )
    assert config.device_ip == "10.0.0.103"
    assert config.chunk_size == 4096
    assert config.timeout == 30.0
    assert config.verify_timeout == 120.0
    assert config.dry_run is False


def test_flash_result():
    result = FlashResult(
        success=True,
        message="Flash successful",
        rolled_back=False,
    )
    assert result.success is True
    assert result.rolled_back is False

    result = FlashResult(
        success=False,
        message="Failed",
        rolled_back=True,
        error="Verification failed",
    )
    assert result.success is False
    assert result.rolled_back is True
    assert result.error == "Verification failed"


def test_ota_flasher_dry_run():
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"test firmware")
        path = Path(f.name)

    try:
        config = FlashConfig(
            device_ip="10.0.0.103",
            token="f" * 32,
            firmware_path=path,
            dry_run=True,
        )
        flasher = OTAFlasher(config)
        # Can't easily test async without event loop, just verify instantiation
        assert flasher.dry_run is True
    finally:
        path.unlink()


def test_flash_config_custom():
    config = FlashConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path=Path("/tmp/fw.img"),
        chunk_size=8192,
        timeout=60.0,
        verify_timeout=180.0,
        dry_run=True,
    )
    assert config.chunk_size == 8192
    assert config.timeout == 60.0
    assert config.verify_timeout == 180.0
    assert config.dry_run is True