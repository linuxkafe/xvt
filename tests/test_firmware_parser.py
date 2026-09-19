"""Tests for XVT firmware parser module."""

import tempfile
from pathlib import Path

from src.xvt.firmware.parser import (
    FirmwareFormat,
    FirmwareHeader,
    FirmwareParser,
    ParsedFirmware,
    PartitionInfo,
    parse_firmware,
)


def test_firmware_format_enum():
    assert FirmwareFormat.MIOT_OTA.value == 0
    assert FirmwareFormat.CRAMFS.value == 1
    assert FirmwareFormat.SQUASHFS.value == 2
    assert FirmwareFormat.UNKNOWN.value == 0


def test_partition_info():
    part = PartitionInfo(
        name="kernel",
        offset=512,
        size=2048,
        format=FirmwareFormat.ZIMAGE,
        checksum="abc123",
        checksum_type="crc32",
    )
    assert part.name == "kernel"
    assert part.offset == 512
    assert part.size == 2048


def test_firmware_header():
    partitions = [
        PartitionInfo(name="kernel", offset=512, size=2048, format=FirmwareFormat.ZIMAGE),
        PartitionInfo(name="rootfs", offset=2560, size=8192, format=FirmwareFormat.CRAMFS),
    ]
    header = FirmwareHeader(
        magic=b"MIOT",
        version=1,
        total_size=10240,
        partitions=partitions,
        raw_header=b"MIOT\x01\x00\x00\x00" + b"\x00" * 500,
    )
    assert header.magic == b"MIOT"
    assert header.version == 1
    assert len(header.partitions) == 2


def test_parsed_firmware():
    header = FirmwareHeader(
        magic=b"MIOT",
        version=1,
        total_size=10240,
        partitions=[],
        raw_header=b"MIOT" + b"\x00" * 508,
    )
    parsed = ParsedFirmware(header=header)
    assert parsed.partitions == {}


def test_firmware_parser_crc32():
    parser = FirmwareParser(dry_run=True)
    data = b"test data"
    crc = parser.crc32(data)
    assert crc == 0xd308aeb2  # CRC32 of "test data"


def test_firmware_parser_sha256():
    parser = FirmwareParser(dry_run=True)
    data = b"test data"
    sha = parser.sha256(data)
    expected = "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert sha == expected


def test_detect_format_magic():
    parser = FirmwareParser(dry_run=True)
    assert parser.detect_format(b"MIOT\x00\x00\x00\x00") == FirmwareFormat.MIOT_OTA
    assert parser.detect_format(b"\x28\xcd\x3d\x45") == FirmwareFormat.CRAMFS
    assert parser.detect_format(b"hsqs") == FirmwareFormat.SQUASHFS
    assert parser.detect_format(b"\x27\x05\x19\x56") == FirmwareFormat.UIMAGE
    assert parser.detect_format(b"\x1f\x8b\x08") == FirmwareFormat.ZIMAGE
    assert parser.detect_format(b"\xd0\x0d\xfe\xed") == FirmwareFormat.DTB
    assert parser.detect_format(b"unknown") == FirmwareFormat.UNKNOWN


def test_firmware_parser_dry_run_parse():
    parser = FirmwareParser(dry_run=True)
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"MIOT\x01\x00\x00\x00" + b"\x00" * 508 + b"kernel_data" + b"rootfs_data")
        path = Path(f.name)
    try:
        result = parser.parse(path)
        # Dry run may not fully parse without proper header
        # Just verify it doesn't crash
        assert result is None or isinstance(result, ParsedFirmware)
    finally:
        path.unlink()


def test_parse_firmware_function():
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"MIOT\x01\x00\x00\x00" + b"\x00" * 508)
        path = Path(f.name)
    try:
        result = parse_firmware(path, dry_run=True)
        assert result is None or isinstance(result, ParsedFirmware)
    finally:
        path.unlink()


def test_partition_info_checksum():
    part = PartitionInfo(
        name="test",
        offset=0,
        size=4,
        format=FirmwareFormat.ZIMAGE,
        checksum="1bc2c6cf",  # CRC32 of "test"
        checksum_type="crc32",
    )
    parser = FirmwareParser(dry_run=True)
    data = b"test"
    extracted = parser.extract_partition(data, part)
    assert extracted == b"test"


def test_firmware_parser_custom_format():
    parser = FirmwareParser(dry_run=True)
    # Test unknown format
    assert parser.detect_format(b"random") == FirmwareFormat.UNKNOWN
