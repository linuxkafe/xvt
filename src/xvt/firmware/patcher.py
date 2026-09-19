"""Firmware patch engine for injecting root access components."""

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from src.xvt.firmware.parser import FirmwareFormat, ParsedFirmware


@dataclass
class PatchConfig:
    """Configuration for firmware patching."""
    rootfs_path: Path
    output_path: Path
    dropbear_binary: Path | None = None
    su_binary: Path | None = None
    authorized_keys: bytes | None = None
    preserve_permissions: bool = True


@dataclass
class PatchResult:
    """Result of firmware patching."""
    success: bool
    output_path: Path
    components_injected: list[str]
    error: str | None = None


class PatchEngine:
    """Patch firmware rootfs to inject root access components."""

    # Default paths in rootfs
    DROPBEAR_PATH = "usr/sbin/dropbear"
    DROPBEAR_KEY_DIR = "etc/dropbear"
    SU_PATH = "bin/su"
    AUTHORIZED_KEYS_PATHS = [
        "etc/dropbear/authorized_keys",
        "root/.ssh/authorized_keys",
    ]
    INIT_SCRIPTS = [
        "etc/init.d/S50dropbear",
        "etc/rc.d/S50dropbear",
        "etc/rc.local",
    ]

    def __init__(self, config: PatchConfig, dry_run: bool = False, logger: logging.Logger | None = None):
        self.config = config
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)
        self._work_dir: Path | None = None

    def _get_default_dropbear(self) -> bytes:
        """Get embedded dropbear binary (placeholder)."""
        # In real implementation, this would be a statically linked dropbear binary
        # For now, return a minimal placeholder
        return b"#!/bin/sh\necho 'dropbear placeholder'\n"

    def _get_default_su(self) -> bytes:
        """Get embedded su binary (placeholder)."""
        return b"#!/bin/sh\necho 'su placeholder'\n"

    def extract_rootfs(self, firmware: ParsedFirmware, work_dir: Path) -> Path | None:
        """Extract rootfs to working directory."""
        if not firmware.rootfs:
            self.logger.error("No rootfs in firmware")
            return None

        rootfs_dir = work_dir / "rootfs"
        rootfs_dir.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            self.logger.info("[DRY-RUN] Would extract rootfs to %s", rootfs_dir)
            return rootfs_dir

        # Detect rootfs format
        fmt = self.detect_format(firmware.rootfs)

        try:
            if fmt == FirmwareFormat.CRAMFS:
                return self._extract_cramfs(firmware.rootfs, rootfs_dir)
            elif fmt == FirmwareFormat.SQUASHFS:
                return self._extract_squashfs(firmware.rootfs, rootfs_dir)
            else:
                self.logger.error("Unsupported rootfs format: %s", fmt.value)
                return None
        except Exception as e:
            self.logger.error("Failed to extract rootfs: %s", e)
            return None

    def detect_format(self, data: bytes):
        """Detect filesystem format."""
        # Simple magic detection
        if data.startswith(b'\x28\xcd\x3d\x45'):  # cramfs
            from src.xvt.firmware.parser import FirmwareFormat
            return FirmwareFormat.CRAMFS
        if data.startswith(b'hsqs'):  # squashfs
            from src.xvt.firmware.parser import FirmwareFormat
            return FirmwareFormat.SQUASHFS
        return None

    def _extract_cramfs(self, rootfs_data: bytes, output_dir: Path) -> Path | None:
        """Extract cramfs filesystem."""
        if self.dry_run:
            self.logger.info("[DRY-RUN] Would extract cramfs")
            return Path("/tmp/cramfs_root")

        # Write rootfs to temp file
        with tempfile.NamedTemporaryFile(suffix='.cramfs', delete=False) as f:
            f.write(rootfs_data)
            cramfs_file = Path(f.name)

        try:
            # Extract with cramfsck
            result = subprocess.run(
                ['cramfsck', '-x', str(output_dir), str(cramfs_file)],
                capture_output=True, check=True
            )
            self.logger.info("cramfs extracted to %s", output_dir)
            return output_dir
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error("cramfsck failed: %s", e)
            return None
        finally:
            cramfs_file.unlink(missing_ok=True)

    def _extract_squashfs(self, rootfs_data: bytes, output_dir: Path) -> Path | None:
        """Extract squashfs filesystem."""
        if self.dry_run:
            self.logger.info("[DRY-RUN] Would extract squashfs")
            return Path("/tmp/squashfs_root")

        # Write rootfs to temp file
        with tempfile.NamedTemporaryFile(suffix='.sqfs', delete=False) as f:
            f.write(rootfs_data)
            sqfs_file = Path(f.name)

        try:
            # Extract with unsquashfs
            result = subprocess.run(
                ['unsquashfs', '-d', str(output_dir), str(sqfs_file)],
                capture_output=True, check=True
            )
            self.logger.info("squashfs extracted to %s", output_dir)
            return output_dir
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error("unsquashfs failed: %s", e)
            return None
        finally:
            sqfs_file.unlink(missing_ok=True)

    def inject_components(self, rootfs_dir: Path) -> list[str]:
        """Inject root access components into extracted rootfs."""
        injected = []

        if self.dry_run:
            self.logger.info("[DRY-RUN] Would inject: dropbear, su, authorized_keys, init scripts")
            return ["dropbear", "su", "authorized_keys", "init_scripts"]

        # Inject dropbear
        if self._inject_dropbear(rootfs_dir):
            injected.append("dropbear")

        # Inject su
        if self._inject_su(rootfs_dir):
            injected.append("su")

        # Inject authorized_keys
        if self._inject_authorized_keys(rootfs_dir):
            injected.append("authorized_keys")

        # Inject init scripts
        if self._inject_init_scripts(rootfs_dir):
            injected.append("init_scripts")

        return injected

    def _inject_dropbear(self, rootfs_dir: Path) -> bool:
        """Inject dropbear SSH server."""
        try:
            # Get binary
            dropbear_data = self.config.dropbear_binary.read_bytes() if self.config.dropbear_binary else self._get_default_dropbear()

            # Write binary
            dropbear_path = rootfs_dir / self.DROPBEAR_PATH
            dropbear_path.parent.mkdir(parents=True, exist_ok=True)
            dropbear_path.write_bytes(dropbear_data)
            dropbear_path.chmod(0o755)

            # Create key directory
            key_dir = rootfs_dir / self.DROPBEAR_KEY_DIR
            key_dir.mkdir(parents=True, exist_ok=True)
            key_dir.chmod(0o700)

            # Generate host key placeholder
            host_key = key_dir / "dropbear_rsa_host_key"
            host_key.write_bytes(b"placeholder_host_key")
            host_key.chmod(0o600)

            # Create authorized_keys
            if self.config.authorized_keys:
                auth_keys = key_dir / "authorized_keys"
                auth_keys.write_bytes(self.config.authorized_keys)
                auth_keys.chmod(0o600)

            self.logger.info("Dropbear injected to %s", dropbear_path)
            return True
        except Exception as e:
            self.logger.error("Failed to inject dropbear: %s", e)
            return False

    def _inject_su(self, rootfs_dir: Path) -> bool:
        """Inject su binary."""
        try:
            su_data = self.config.su_binary.read_bytes() if self.config.su_binary else self._get_default_su()

            su_path = rootfs_dir / self.SU_PATH
            su_path.parent.mkdir(parents=True, exist_ok=True)
            su_path.write_bytes(su_data)
            su_path.chmod(0o755)

            self.logger.info("su injected to %s", su_path)
            return True
        except Exception as e:
            self.logger.error("Failed to inject su: %s", e)
            return False

    def _inject_authorized_keys(self, rootfs_dir: Path) -> bool:
        """Inject authorized_keys files."""
        if not self.config.authorized_keys:
            self.logger.warning("No authorized_keys provided")
            return False

        try:
            for key_path in self.AUTHORIZED_KEYS_PATHS:
                full_path = rootfs_dir / key_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_bytes(self.config.authorized_keys)
                full_path.chmod(0o600)
                full_path.parent.chmod(0o700)

            self.logger.info("Authorized keys injected to %d locations", len(self.AUTHORIZED_KEYS_PATHS))
            return True
        except Exception as e:
            self.logger.error("Failed to inject authorized_keys: %s", e)
            return False

    def _inject_init_scripts(self, rootfs_dir: Path) -> bool:
        """Inject init scripts to start dropbear on boot."""
        init_script = """#!/bin/sh
# Start dropbear SSH server
/usr/sbin/dropbear -r /etc/dropbear/dropbear_rsa_host_key -p 22
"""

        try:
            for script_path in self.INIT_SCRIPTS:
                full_path = rootfs_dir / script_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Append to existing script or create new
                if full_path.exists():
                    content = full_path.read_text()
                    if "dropbear" not in content:
                        full_path.write_text(content + "\n" + init_script)
                else:
                    full_path.write_text("#!/bin/sh\n" + init_script)

                full_path.chmod(0o755)

            self.logger.info("Init scripts updated for dropbear")
            return True
        except Exception as e:
            self.logger.error("Failed to inject init scripts: %s", e)
            return False

    def repack_rootfs(self, rootfs_dir: Path, original_format, output_path: Path) -> bool:
        """Repack rootfs to firmware format."""
        if self.dry_run:
            self.logger.info("[DRY-RUN] Would repack rootfs to %s", output_path)
            return True

        try:
            if original_format == FirmwareFormat.CRAMFS:
                return self._repack_cramfs(rootfs_dir, output_path)
            elif original_format == FirmwareFormat.SQUASHFS:
                return self._repack_squashfs(rootfs_dir, output_path)
            else:
                self.logger.error("Unknown format for repack")
                return False
        except Exception as e:
            self.logger.error("Repack failed: %s", e)
            return False

    def _repack_cramfs(self, rootfs_dir: Path, output_path: Path) -> bool:
        """Repack cramfs filesystem."""
        try:
            result = subprocess.run(
                ['mkcramfs', str(rootfs_dir), str(output_path)],
                capture_output=True, check=True
            )
            self.logger.info("cramfs repacked to %s", output_path)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error("mkcramfs failed: %s", e)
            return False

    def _repack_squashfs(self, rootfs_dir: Path, output_path: Path) -> bool:
        """Repack squashfs filesystem."""
        try:
            result = subprocess.run(
                ['mksquashfs', str(rootfs_dir), str(output_path), '-comp', 'xz'],
                capture_output=True, check=True
            )
            self.logger.info("squashfs repacked to %s", output_path)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error("mksquashfs failed: %s", e)
            return False

    def patch(self, firmware: ParsedFirmware) -> PatchResult:
        """Run full patch process on firmware."""
        self.logger.info("Starting firmware patch")

        if not firmware.rootfs:
            return PatchResult(
                success=False,
                output_path=self.config.output_path,
                components_injected=[],
                error="No rootfs in firmware",
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)

            # Extract rootfs
            rootfs_dir = self.extract_rootfs(firmware, work_dir)
            if not rootfs_dir:
                return PatchResult(
                    success=False,
                    output_path=self.config.output_path,
                    components_injected=[],
                    error="Failed to extract rootfs",
                )

            # Detect format
            original_format = self.detect_format(firmware.rootfs)
            if not original_format:
                return PatchResult(
                    success=False,
                    output_path=self.config.output_path,
                    components_injected=[],
                    error="Unknown rootfs format",
                )

            # Inject components
            injected = self.inject_components(rootfs_dir)

            # Repack rootfs
            rootfs_output = work_dir / "rootfs_patched.img"
            if not self.repack_rootfs(rootfs_dir, original_format, rootfs_output):
                return PatchResult(
                    success=False,
                    output_path=self.config.output_path,
                    components_injected=[],
                    error="Failed to repack rootfs",
                )

            # TODO: Rebuild full firmware with patched rootfs (requires T013)
            # For now, just copy patched rootfs as output
            shutil.copy2(rootfs_output, self.config.output_path)

        self.logger.info("Patch completed. Injected: %s", injected)
        return PatchResult(
            success=True,
            output_path=self.config.output_path,
            components_injected=injected,
        )


def patch_firmware(
    firmware: ParsedFirmware,
    output_path: Path,
    authorized_keys: bytes | None = None,
    dry_run: bool = False,
) -> PatchResult:
    """Convenience function for firmware patching."""
    config = PatchConfig(
        rootfs_path=Path(""),
        output_path=output_path,
        authorized_keys=authorized_keys,
    )
    engine = PatchEngine(config, dry_run=dry_run)
    return engine.patch(firmware)
