"""Checksum calculation and firmware image rebuild for Xiaomi vacuum firmware."""

import hashlib
import logging
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

from src.xvt.firmware.parser import (
    FirmwareHeader,
    ParsedFirmware,
    PartitionInfo,
)


@dataclass
class ChecksumConfig:
    """Configuration for checksum calculation."""
    verify_existing: bool = True
    update_checksums: bool = True
    dry_run: bool = False


@dataclass
class ChecksumResult:
    """Result of checksum calculation."""
    crc32: str
    sha256: str
    md5: str
    size: int


class ChecksumCalculator:
    """Calculate and verify checksums for firmware components."""

    def __init__(self, config: ChecksumConfig, logger: logging.Logger | None = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def calculate_crc32(self, data: bytes) -> str:
        """Calculate CRC32 checksum."""
        return format(zlib.crc32(data) & 0xffffffff, '08x')

    def calculate_sha256(self, data: bytes) -> str:
        """Calculate SHA256 checksum."""
        return hashlib.sha256(data).hexdigest()

    def calculate_md5(self, data: bytes) -> str:
        """Calculate MD5 checksum."""
        return hashlib.md5(data).hexdigest()

    def calculate_all(self, data: bytes) -> ChecksumResult:
        """Calculate all checksums for data."""
        return ChecksumResult(
            crc32=self.calculate_crc32(data),
            sha256=self.calculate_sha256(data),
            md5=self.calculate_md5(data),
            size=len(data),
        )

    def verify_checksum(self, data: bytes, expected: str, algo: str = 'crc32') -> bool:
        """Verify data against expected checksum."""
        if algo == 'crc32':
            return self.calculate_crc32(data) == expected.lower()
        elif algo == 'sha256':
            return self.calculate_sha256(data) == expected.lower()
        elif algo == 'md5':
            return self.calculate_md5(data) == expected.lower()
        return False


class FirmwareImageRebuilder:
    """Rebuild firmware image with updated checksums."""

    def __init__(self, calculator: ChecksumCalculator, logger: logging.Logger | None = None):
        self.calculator = calculator
        self.logger = logger or logging.getLogger(__name__)

    def rebuild_miot_header(self, header: FirmwareHeader, partitions: list) -> bytes:
        """Rebuild MiOT OTA header with updated partition checksums."""
        # MiOT header format:
        # magic(4) + version(4) + total_size(4) + partition_count(4)
        # Then for each partition: name(32) + offset(8) + size(8) + format(4) + checksum(4) + checksum_type(4)

        magic = header.magic
        version = header.version
        total_size = header.total_size
        partition_count = len(partitions)

        # Calculate total size from partitions
        max_end = 0
        for p in partitions:
            end = p.offset + p.size
            if end > max_end:
                max_end = end
        total_size = max_end

        # Build header
        header_data = bytearray()
        header_data.extend(struct.pack('<4sIII', magic, version, total_size, len(partitions)))

        # Add partition entries
        for p in partitions:
            name_bytes = p.name.encode('ascii', errors='ignore')[:32].ljust(32, b'\x00')
            format_val = p.format.value if hasattr(p.format, 'value') else 0
            # Convert checksum hex to int
            checksum_int = int(p.checksum, 16) if p.checksum else 0
            checksum_type = 1 if p.checksum_type == 'crc32' else 2  # 1=crc32, 2=sha256

            header_data.extend(struct.pack('<32sQQIII',
                name_bytes, p.offset, p.size, format_val, checksum_int, checksum_type))

        # Pad to 512 bytes
        header_data.extend(b'\x00' * (512 - len(header_data)))

        # Calculate header CRC32 (if needed)
        if self.calculator.config.update_checksums:
            # Some formats have header checksum at specific offset
            pass

        return bytes(header_data)

    def rebuild_firmware_image(self, firmware: ParsedFirmware, output_path: Path) -> bool:
        """Rebuild complete firmware image with updated checksums."""
        self.logger.info(f"Rebuilding firmware to {output_path}")

        if self.calculator.config.dry_run:
            self.logger.info("[DRY-RUN] Would rebuild firmware image")
            return True

        try:
            # Get partition data from parsed firmware
            partition_data_map = {}
            for name, data in firmware.partitions.items():
                partition_data_map[name] = data

            # Create updated partitions list with new checksums
            updated_partitions = []
            for p in firmware.header.partitions:
                if p.name in partition_data_map:
                    data = partition_data_map[p.name]
                    # Calculate new checksums
                    new_crc32 = self.calculator.calculate_crc32(data)
                    new_sha256 = self.calculator.calculate_sha256(data)
                    new_md5 = self.calculator.calculate_md5(data)

                    # Create updated partition info
                    updated_partitions.append(PartitionInfo(
                        name=p.name,
                        offset=p.offset,
                        size=len(data),
                        format=p.format,
                        checksum=new_crc32,
                        checksum_type='crc32',
                    ))
                else:
                    updated_partitions.append(p)

            # Rebuild header with updated checksums
            new_header = self.rebuild_miot_header(firmware.header, updated_partitions)

            # Build complete firmware image
            output_data = bytearray()
            output_data.extend(new_header)

            # Add partition data at correct offsets
            # Sort partitions by offset
            sorted_partitions = sorted(updated_partitions, key=lambda p: p.offset)

            current_pos = len(new_header)
            for p in sorted_partitions:
                # Pad to partition offset
                if current_pos < p.offset:
                    output_data.extend(b'\x00' * (p.offset - current_pos))
                    current_pos = p.offset

                # Add partition data
                if p.name in firmware.partitions:
                    data = firmware.partitions[p.name]
                    output_data.extend(data)
                    current_pos += len(data)

            # Write to file
            output_path.write_bytes(output_data)

            # Verify final image
            final_data = output_path.read_bytes()
            final_crc32 = self.calculator.calculate_crc32(final_data)
            self.logger.info(f"Rebuilt firmware: {len(final_data)} bytes, CRC32: {final_crc32}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to rebuild firmware: {e}")
            return False

    def verify_firmware_image(self, firmware_path: Path) -> dict:
        """Verify firmware image checksums."""
        data = firmware_path.read_bytes()
        result = self.calculator.calculate_all(data)

        self.logger.info(f"Firmware verification: {firmware_path}")
        self.logger.info(f"  Size: {result.size} bytes")
        self.logger.info(f"  CRC32: {result.crc32}")
        self.logger.info(f"  SHA256: {result.sha256}")
        self.logger.info(f"  MD5: {result.md5}")

        return {
            'size': result.size,
            'crc32': result.crc32,
            'sha256': result.sha256,
            'md5': result.md5,
        }


def calculate_checksums(firmware_path: Path, dry_run: bool = False) -> dict:
    """Convenience function to calculate firmware checksums."""
    config = ChecksumConfig(dry_run=dry_run)
    calculator = ChecksumCalculator(config)
    data = firmware_path.read_bytes()
    result = calculator.calculate_all(data)
    return {
        'size': result.size,
        'crc32': result.crc32,
        'sha256': result.sha256,
        'md5': result.md5,
    }


def rebuild_firmware(firmware: ParsedFirmware, output_path: Path, dry_run: bool = False) -> bool:
    """Convenience function to rebuild firmware with updated checksums."""
    config = ChecksumConfig(dry_run=dry_run)
    calculator = ChecksumCalculator(config)
    rebuilder = FirmwareImageRebuilder(calculator)
    return rebuilder.rebuild_firmware_image(firmware, output_path)
