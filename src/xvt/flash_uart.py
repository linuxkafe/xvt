"""UART flash fallback for Xiaomi vacuum devices."""

import logging
import struct
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Runtime serial availability
try:
    import serial
    _HAS_SERIAL = True
except ImportError:
    _HAS_SERIAL = False
    serial = None  # type: ignore

# Type aliases for annotations (only used during type checking)
if TYPE_CHECKING:
    import serial
    Serial = serial.Serial
    SerialException = serial.SerialException
else:
    # Runtime aliases (Any for when serial is not available)
    Serial = Any
    SerialException = Any


@dataclass
class UARTFlashConfig:
    """Configuration for UART flashing."""
    port: str
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1
    timeout: float = 2.0
    firmware_path: Path = Path("")
    xmodem_block_size: int = 128
    xmodem_timeout: float = 10.0
    dry_run: bool = False


@dataclass
class UARTFlashResult:
    """Result of UART flash operation."""
    success: bool
    message: str
    error: str | None = None


class UARTFlasher:
    """UART-based firmware flasher with XMODEM protocol."""

    # U-Boot interaction
    UBOOT_PROMPT = b"Hit any key to stop autoboot"
    UBOOT_PROMPT_ALT = b"=>"
    XMODEM_START = b'\x01'  # SOH
    XMODEM_EOT = b'\x04'    # EOT
    XMODEM_ACK = b'\x06'
    XMODEM_NAK = b'\x15'
    XMODEM_CAN = b'\x18'

    def __init__(
        self,
        config: 'UARTFlashConfig',
        logger: logging.Logger | None = None,
        progress_cb: Callable[[int, int], None] | None = None,
    ):
        self.config = config
        self.dry_run = config.dry_run
        self.logger = logger or logging.getLogger(__name__)
        self.progress_cb = progress_cb
        self._ser: Serial | None = None

    def connect(self) -> bool:
        """Open serial connection."""
        if self.dry_run:
            self.logger.info("[DRY-RUN] Would open serial port %s at %d baud",
                           self.config.port, self.config.baudrate)
            return True

        if not _HAS_SERIAL:
            self.logger.error(
                "pyserial not installed. Install with: pip install pyserial"
            )
            return False

        # At this point, serial is guaranteed to be available
        _serial = serial
        assert _serial is not None

        try:
            self._ser = _serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.bytesize,
                parity=self.config.parity,
                stopbits=self.config.stopbits,
                timeout=self.config.timeout,
            )
            self.logger.info(
                "Connected to %s at %d baud", self.config.port, self.config.baudrate
            )
            return True
        except _serial.SerialException as e:
            self.logger.error("Failed to open serial port %s: %s", self.config.port, e)
            return False

    def disconnect(self) -> None:
        """Close serial connection."""
        if self._ser and self._ser.is_open:
            self._ser.close()
            self.logger.info("Disconnected from %s", self.config.port)

    def _send(self, data: bytes, delay: float = 0.1) -> None:
        """Send data to serial port."""
        if self.dry_run:
            self.logger.info(
                "[DRY-RUN] Would send: %s", data.decode(errors='replace').strip()
            )
            return
        if self._ser and self._ser.is_open:
            self._ser.write(data)
            self._ser.flush()
            time.sleep(delay)

    def _read_until(self, expected: bytes, timeout: float = 5.0) -> bytes:
        """Read until expected bytes or timeout."""
        if self.dry_run:
            return expected
        if not self._ser or not self._ser.is_open:
            return b""
        start = time.time()
        buffer = b""
        while time.time() - start < timeout:
            if self._ser.in_waiting:
                chunk = self._ser.read(self._ser.in_waiting)
                buffer += chunk
                if expected in buffer:
                    return buffer
            time.sleep(0.01)
        return buffer

    def interrupt_uboot(self) -> bool:
        """Interrupt U-Boot autoboot to get shell."""
        self.logger.info("Attempting to interrupt U-Boot...")
        self._send(b"\x03")  # Ctrl-C
        self._send(b"\n")
        response = self._read_until(self.UBOOT_PROMPT, timeout=3.0)
        if self.UBOOT_PROMPT in response:
            self.logger.info("U-Boot interrupted successfully")
            return True
        if self.UBOOT_PROMPT_ALT in response:
            self.logger.info("U-Boot prompt detected")
            return True
        self.logger.warning("U-Boot interrupt failed")
        return False

    def _xmodem_crc16(self, data: bytes) -> bytes:
        """Calculate XMODEM CRC16."""
        crc = 0
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return struct.pack('>H', crc)

    def _xmodem_send_block(self, block_num: int, data: bytes) -> bool:
        """Send a single XMODEM block."""
        # Pad data to block size
        padded = data + b'\x1A' * (self.config.xmodem_block_size - len(data))
        crc = self._xmodem_crc16(padded)

        packet = bytearray()
        packet.append(self.XMODEM_START[0])  # SOH
        packet.append(block_num & 0xFF)
        packet.append((~block_num) & 0xFF)
        packet.extend(padded)
        packet.extend(crc)

        self._send(bytes(packet))
        response = self._read_until(self.XMODEM_ACK, timeout=self.config.xmodem_timeout)

        return self.XMODEM_ACK in response

    def xmodem_send(self, firmware_data: bytes) -> bool:
        """Send firmware via XMODEM protocol."""
        self.logger.info("Starting XMODEM transfer (%d bytes)...", len(firmware_data))

        if self.dry_run:
            self.logger.info(
                "[DRY-RUN] Would send %d bytes via XMODEM", len(firmware_data)
            )
            return True

        # Wait for NAK from receiver
        response = self._read_until(self.XMODEM_NAK, timeout=10.0)
        if self.XMODEM_NAK not in response:
            self.logger.error("No NAK received from receiver")
            return False

        block_num = 1
        offset = 0

        while offset < len(firmware_data):
            chunk = firmware_data[offset:offset + 128]
            if not self._xmodem_send_block(block_num, chunk):
                self.logger.error("Block %d failed", block_num)
                return False

            offset += 128
            block_num = (block_num + 1) & 0xFF

            if self.progress_cb:
                self.progress_cb(min(offset, len(firmware_data)), len(firmware_data))

        # Send EOT
        self._send(self.XMODEM_EOT)
        response = self._read_until(self.XMODEM_ACK, timeout=5.0)
        if self.XMODEM_ACK not in response:
            self.logger.error("EOT not acknowledged")
            return False

        self.logger.info("XMODEM transfer complete")
        return True

    async def flash(self, firmware_path: Path) -> bool:
        """Run full UART flash process."""
        self.logger.info("Starting UART flash for %s", self.config.firmware_path)

        if not self.connect():
            return False

        try:
            # Read firmware
            firmware_data = firmware_path.read_bytes()
            self.logger.info("Firmware size: %d bytes", len(firmware_data))

            # Interrupt U-Boot
            if not self.interrupt_uboot():
                self.logger.error("Failed to interrupt U-Boot")
                return False

            # Enter XMODEM receive mode on device
            # This is device-specific - typically 'loadx' or similar
            self._send(b"loadx\n")
            response = self._read_until(b"Ready", timeout=5.0)

            # Send via XMODEM
            if not self.xmodem_send(self.config.firmware_path.read_bytes()):
                return False

            # Execute flash command (device-specific)
            self._send(b"nand write ${loadaddr} 0x0 ${filesize}\n")
            response = self._read_until(b"OK", timeout=30.0)

            if b"OK" not in response:
                self.logger.error("Flash write failed")
                return False

            self.logger.info("UART flash complete")
            return True

        finally:
            self.disconnect()


async def flash_uart(
    port: str,
    firmware_path: Path,
    baudrate: int = 115200,
    dry_run: bool = False,
    progress_cb: Callable[[int, int], None] | None = None,
) -> bool:
    """Convenience function for UART flashing."""
    config = UARTFlashConfig(
        port=port,
        baudrate=baudrate,
        firmware_path=firmware_path,
        dry_run=dry_run,
    )
    flasher = UARTFlasher(config)
    return await flasher.flash(Path(""))
