"""Firmware parsing, modification, and flashing utilities."""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FirmwareImage:
    """Parsed firmware image components."""
    path: Path
    kernel: bytes
    rootfs: bytes  # cramfs/squashfs
    dtb: bytes | None = None
    header: bytes | None = None

    def sha256(self) -> str:
        return hashlib.sha256(self.path.read_bytes()).hexdigest()


class FirmwareParser:
    """Parse Xiaomi vacuum firmware images."""

    @staticmethod
    def parse(path: Path) -> FirmwareImage:
        raise NotImplementedError


class FirmwarePatcher:
    """Modify firmware to enable persistent root."""

    def __init__(self, image: FirmwareImage):
        self.image = image

    def inject_dropbear(self, binary: bytes) -> None:
        raise NotImplementedError

    def inject_su(self, binary: bytes) -> None:
        raise NotImplementedError

    def inject_authorized_keys(self, keys: bytes) -> None:
        raise NotImplementedError

    def build(self, output: Path) -> FirmwareImage:
        raise NotImplementedError


class FirmwareFlasher:
    """Flash modified firmware to device."""

    def __init__(self, device_ip: str, token: str):
        self.device_ip = device_ip
        self.token = token

    def flash_ota(self, image: FirmwareImage, dry_run: bool = True) -> bool:
        raise NotImplementedError

    def flash_uart(self, image: FirmwareImage, port: str, dry_run: bool = True) -> bool:
        raise NotImplementedError

    def verify_flash(self, image: FirmwareImage) -> bool:
        raise NotImplementedError
