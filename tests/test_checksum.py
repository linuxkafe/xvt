"""Tests for XVT firmware checksum module."""

import tempfile
from pathlib import Path

from src.xvt.firmware.checksum import (
    ChecksumCalculator,
    ChecksumConfig,
    ChecksumResult,
    calculate_checksums,
)


def test_checksum_calculator_crc32():
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"
    crc32 = calc.calculate_crc32(data)
    assert crc32 == "d308aeb2"  # CRC32 of "test data"


def test_checksum_calculator_sha256():
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"
    sha256 = calc.calculate_sha256(data)
    expected = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert sha256 == expected


def test_checksum_calculator_md5():
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"
    md5 = calc.calculate_md5(data)
    expected = "eb733a00c0c9d336e65691a37ab54293"
    assert md5 == expected


def test_checksum_calculator_all():
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"
    result = calc.calculate_all(data)

    assert isinstance(result, ChecksumResult)
    assert result.size == 9
    assert result.crc32 == "d308aeb2"
    assert result.sha256 == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert result.md5 == "eb733a00c0c9d336e65691a37ab54293"


def test_checksum_verification():
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"

    assert calc.verify_checksum(data, "d308aeb2", "crc32")
    assert calc.verify_checksum(data, "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9", "sha256")
    assert calc.verify_checksum(data, "eb733a00c0c9d336e65691a37ab54293", "md5")
    assert not calc.verify_checksum(data, "ffffffff", "crc32")


def test_calculate_checksums_function():
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"test firmware data")
        path = Path(f.name)

    try:
        result = calculate_checksums(path, dry_run=True)
        assert 'size' in result
        assert 'crc32' in result
        assert 'sha256' in result
        assert 'md5' in result
    finally:
        path.unlink()


def test_checksum_config():
    config = ChecksumConfig(
        verify_existing=True,
        update_checksums=True,
        dry_run=True
    )
    assert config.verify_existing is True
    assert config.update_checksums is True
    assert config.dry_run is True


def test_checksum_result():
    result = ChecksumResult(
        crc32="abcdef12",
        sha256="abcdef1234567890",
        md5="abcdef1234567890",
        size=100
    )
    assert result.crc32 == "abcdef12"
    assert result.sha256 == "abcdef1234567890"
    assert result.md5 == "abcdef1234567890"
    assert result.size == 100
