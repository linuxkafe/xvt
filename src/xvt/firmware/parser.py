"""Firmware parser for Xiaomi vacuum firmware images."""

import hashlib
import logging
import struct
import zlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class FirmwareFormat(int, Enum):
    """Known firmware formats (integer values match MiOT OTA header)."""
    UNKNOWN = 0
    MIOT_OTA = 0      # Xiaomi MiIO OTA format
    CRAMFS = 1
    SQUASHFS = 2
    ZIMAGE = 3
    UIMAGE = 4
    FITIMAGE = 5
    DTB = 6


@dataclass
class PartitionInfo:
    """Firmware partition information."""
    name: str
    offset: int
    size: int
    format: FirmwareFormat
    checksum: str | None = None
    checksum_type: str = "crc32"


@dataclass
class FirmwareHeader:
    """Parsed firmware header."""
    magic: bytes
    version: int
    total_size: int
    partitions: list[PartitionInfo]
    raw_header: bytes


@dataclass
class ParsedFirmware:
    """Complete parsed firmware."""
    header: FirmwareHeader
    kernel: bytes | None = None
    rootfs: bytes | None = None
    dtb: bytes | None = None
    partitions: dict[str, bytes] = field(default_factory=dict)


class FirmwareParser:
    """Parse Xiaomi vacuum firmware images."""

    # Known magic bytes
    MIOT_OTA_MAGIC = b'MIOT'
    CRAMFS_MAGIC = b'\x28\xcd\x3d\x45'  # cramfs magic
    SQUASHFS_MAGIC = b'\x68\x73\x71\x73'  # squashfs magic (hsqs)
    UIMAGE_MAGIC = b'\x27\x05\x19\x56'  # uImage magic
    ZIMAGE_MAGIC = b'\x1f\x8b\x08'  # gzip magic (zImage often gzipped)
    DTB_MAGIC = b'\xd0\x0d\xfe\xed'  # DTB magic

    def __init__(self, dry_run: bool = False, logger: logging.Logger | None = None):
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)

    def detect_format(self, data: bytes) -> FirmwareFormat:
        """Detect firmware format from magic bytes."""
        if data.startswith(self.MIOT_OTA_MAGIC):
            return FirmwareFormat.MIOT_OTA
        if data.startswith(self.CRAMFS_MAGIC):
            return FirmwareFormat.CRAMFS
        if data.startswith(self.SQUASHFS_MAGIC):
            return FirmwareFormat.SQUASHFS
        if data.startswith(self.UIMAGE_MAGIC):
            return FirmwareFormat.UIMAGE
        if data.startswith(self.ZIMAGE_MAGIC):
            return FirmwareFormat.ZIMAGE
        if data.startswith(self.DTB_MAGIC):
            return FirmwareFormat.DTB
        return FirmwareFormat.UNKNOWN

    def crc32(self, data: bytes) -> int:
        """Calculate CRC32 checksum."""
        return zlib.crc32(data) & 0xffffffff

    def sha256(self, data: bytes) -> str:
        """Calculate SHA256 checksum."""
        return hashlib.sha256(data).hexdigest()

    def parse_header(self, data: bytes) -> FirmwareHeader | None:
        """Parse firmware header."""
        if len(data) < 512:
            self.logger.error("Data too small for header")
            return None

        # Try MiOT OTA header format
        if data.startswith(self.MIOT_OTA_MAGIC):
            return self._parse_miot_header(data)

        # Generic header detection
        return self._parse_generic_header(data)

    def _parse_miot_header(self, data: bytes) -> FirmwareHeader:
        """Parse MiIO OTA firmware header."""
        # MiOT header: magic(4) + version(4) + total_size(4) + partition_count(4) + partitions...
        # Each partition: name(32) + offset(8) + size(8) + format(4) + checksum(4) + checksum_type(4)
        header_size = 512  # Standard MiOT header size
        raw_header = data[:header_size]

        magic, version, total_size, part_count = struct.unpack('<4sIII', data[:16])
        partitions = []

        offset = 16
        for _ in range(part_count):
            if offset + 60 > len(data):
                break
            name = data[offset:offset+32].rstrip(b'\x00').decode('ascii', errors='ignore')
            p_offset, p_size, fmt, checksum, checksum_type = struct.unpack('<QQIII', data[offset+32:offset+60])
            partitions.append(PartitionInfo(
                name=name,
                offset=p_offset,
                size=p_size,
                format=FirmwareFormat(fmt),
                checksum=format(checksum, '08x'),
                checksum_type="crc32" if checksum_type == 1 else "sha256",
            ))
            offset += 60

        return FirmwareHeader(
            magic=magic,
            version=version,
            total_size=total_size,
            partitions=partitions,
            raw_header=raw_header,
        )

    def _parse_generic_header(self, data: bytes) -> FirmwareHeader | None:
        """Attempt to parse generic header."""
        # Try to find known magic bytes in first 1KB
        for fmt, magic in [
            (FirmwareFormat.CRAMFS, self.CRAMFS_MAGIC),
            (FirmwareFormat.SQUASHFS, self.SQUASHFS_MAGIC),
            (FirmwareFormat.UIMAGE, self.UIMAGE_MAGIC),
        ]:
            idx = data.find(magic)
            if idx >= 0:
                return FirmwareHeader(
                    magic=magic,
                    version=0,
                    total_size=len(data),
                    partitions=[
                        PartitionInfo(
                            name=fmt.value,
                            offset=idx,
                            size=len(data) - idx,
                            format=fmt,
                        )
                    ],
                    raw_header=data[:idx] if idx > 0 else b'',
                )
        return None

    def extract_partition(self, data: bytes, partition: PartitionInfo) -> bytes | None:
        """Extract partition data from firmware."""
        if partition.offset + partition.size > len(data):
            self.logger.error("Partition %s exceeds firmware size", partition.name)
            return None

        partition_data = data[partition.offset:partition.offset + partition.size]

        # Verify checksum
        if partition.checksum:
            if partition.checksum_type == "crc32":
                calc = format(self.crc32(partition_data), '08x')
            else:
                calc = self.sha256(partition_data)
            if calc != partition.checksum:
                self.logger.warning("Checksum mismatch for %s: expected %s, got %s",
                                  partition.name, partition.checksum, calc)

        return partition_data

    def parse(self, firmware_path: Path) -> ParsedFirmware | None:
        """Parse complete firmware image."""
        self.logger.info("Parsing firmware: %s", firmware_path)

        if not firmware_path.exists():
            self.logger.error("Firmware file not found: %s", firmware_path)
            return None

        data = firmware_path.read_bytes()
        self.logger.info("Firmware size: %d bytes", len(data))
        self.logger.info("SHA256: %s", self.sha256(data))

        # Detect overall format
        fmt = self.detect_format(data)
        self.logger.info("Detected format: %s", fmt.value)

        # Parse header
        header = self.parse_header(data)
        if not header:
            self.logger.error("Failed to parse header")
            return None

        self.logger.info("Header parsed: %d partitions", len(header.partitions))

        # Extract partitions
        parsed = ParsedFirmware(header=header)
        for partition in header.partitions:
            self.logger.info("Extracting partition: %s (offset=%d, size=%d, fmt=%s)",
                           partition.name, partition.offset, partition.size, partition.format.value)

            partition_data = self.extract_partition(data, partition)
            if partition_data is None:
                continue

            parsed.partitions[partition.name] = partition_data

            # Identify partition type
            p_fmt = self.detect_format(partition_data)
            if p_fmt in (FirmwareFormat.ZIMAGE, FirmwareFormat.UIMAGE, FirmwareFormat.FITIMAGE):
                parsed.kernel = partition_data
            elif p_fmt in (FirmwareFormat.CRAMFS, FirmwareFormat.SQUASHFS):
                parsed.rootfs = partition_data
            elif p_fmt == FirmwareFormat.DTB:
                parsed.dtb = partition_data

        return parsed

    def rebuild(self, parsed: ParsedFirmware, output_path: Path) -> bool:
        """Rebuild firmware from parsed components."""
        self.logger.info("Rebuilding firmware to: %s", output_path)

        if self.dry_run:
            self.logger.info("[DRY-RUN] Would rebuild firmware")
            return True

        # Reconstruct header with updated checksums
        # This is a simplified rebuild - real implementation would be more complex
        try:
            # For now, just write the raw header + partition data
            output_data = bytearray()
            output_data.extend(parsed.header.raw_header)

            # This is a placeholder - real rebuild would reconstruct the full image
            self.logger.warning("Full firmware rebuild not yet implemented")
            return False

        except Exception as e:
            self.logger.error("Rebuild failed: %s", e)
            return False


def parse_firmware(firmware_path: Path, dry_run: bool = False) -> ParsedFirmware | None:
    """Convenience function for firmware parsing."""
    parser = FirmwareParser(dry_run=dry_run)
    return parser.parse(firmware_path)
