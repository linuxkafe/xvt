"""SSH key injection logic for Xiaomi vacuum root access."""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.xvt.crypto import generate_ed25519_keypair, load_public_key


@dataclass
class InjectionConfig:
    """Configuration for SSH key injection."""
    device_ip: str
    public_key_path: Path
    username: str = "root"
    port: int = 22
    timeout: float = 10.0
    authorized_keys_paths: list[str] | None = None

    def __post_init__(self):
        if self.authorized_keys_paths is None:
            self.authorized_keys_paths = [
                "/etc/dropbear/authorized_keys",
                "/root/.ssh/authorized_keys",
                "/home/root/.ssh/authorized_keys",
            ]


@dataclass
class InjectionResult:
    """Result of key injection attempt."""
    success: bool
    paths_tried: list[str]
    paths_succeeded: list[str]
    error: str | None = None


class KeyInjector:
    """Inject SSH public keys into target device."""

    def __init__(
        self,
        config: InjectionConfig,
        dry_run: bool = False,
        logger: logging.Logger | None = None,
    ):
        self.config = config
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)

    def _read_public_key(self) -> str:
        """Read and normalize public key."""
        key = self.config.public_key_path.read_text().strip()
        # Ensure it's a single line
        return key.split('\n')[0].strip()

    def inject_via_shell(self, shell_send_fn) -> InjectionResult:
        """Inject key via shell command function.

        Args:
            shell_send_fn: Function(bytes) -> bool that sends command to shell
        """
        public_key = self._read_public_key()
        paths_tried: list[str] = []
        paths_succeeded: list[str] = []

        for ak_path in self.config.authorized_keys_paths or []:
            paths_tried.append(ak_path)
            self.logger.info("Injecting key to %s", ak_path)

            if self.dry_run:
                self.logger.info("[DRY-RUN] Would inject key to %s", ak_path)
                paths_succeeded.append(ak_path)
                continue

            # Build injection commands
            commands = [
                f"mkdir -p $(dirname {ak_path})",
                f"touch {ak_path}",
                f"chmod 600 {ak_path}",
                f"grep -q '{public_key}' {ak_path} || echo '{public_key}' >> {ak_path}",
                f"chmod 600 {ak_path}",
            ]

            # Also ensure .ssh dir permissions if it's an SSH path
            if ".ssh" in ak_path:
                ssh_dir = str(Path(ak_path).parent)
                commands.insert(0, f"mkdir -p {ssh_dir}")
                commands.insert(1, f"chmod 700 {ssh_dir}")

            all_ok = True
            for cmd in commands:
                if not shell_send_fn(cmd.encode() + b'\n'):
                    self.logger.warning("Command failed: %s", cmd)
                    all_ok = False
                    break

            if all_ok:
                paths_succeeded.append(ak_path)
                self.logger.info("Key injected successfully to %s", ak_path)
            else:
                self.logger.error("Failed to inject key to %s", ak_path)

        return InjectionResult(
            success=len(paths_succeeded) > 0,
            paths_tried=paths_tried,
            paths_succeeded=paths_succeeded,
            error=None if paths_succeeded else "All injection attempts failed",
        )

    def inject_via_firmware(self, firmware_path: Path, output_path: Path) -> bool:
        """Inject key into firmware image (for OTA).

        This modifies the firmware filesystem to add the key.
        """
        self.logger.info(
            "Injecting key into firmware: %s -> %s", firmware_path, output_path
        )

        if self.dry_run:
            self.logger.info("[DRY-RUN] Would inject key into firmware")
            return True

        # This would use the firmware patcher from T012
        # For now, delegate to firmware patcher
        self.logger.warning("Firmware injection not yet implemented, requires T012")
        return False

    def verify_ssh_access(self) -> bool:
        """Verify SSH access with injected key."""
        self.logger.info(
            "Verifying SSH access to %s:%d", self.config.device_ip, self.config.port
        )

        if self.dry_run:
            self.logger.info("[DRY-RUN] Would verify SSH access")
            return True

        try:
            # Use ssh command with key
            cmd = [
                "ssh", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-i", str(self.config.public_key_path.with_suffix('')),  # private key
                f"{self.config.username}@{self.config.device_ip}",
                "echo 'SSH OK'"
            ]
            result = subprocess.run(
                cmd, capture_output=True, timeout=self.config.timeout
            )
            if result.returncode == 0:
                self.logger.info("SSH verification successful")
                return True
            else:
                self.logger.error("SSH verification failed: %s", result.stderr.decode())
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("SSH verification timeout")
            return False
        except Exception as e:
            self.logger.error("SSH verification error: %s", e)
            return False


def generate_key_pair(output_dir: Path, name: str = "xvt_key") -> tuple[Path, Path]:
    """Generate Ed25519 key pair and save to files.

    Returns:
        (private_key_path, public_key_path)
    """
    private_pem, public_openssh = generate_ed25519_keypair()

    output_dir.mkdir(parents=True, exist_ok=True)

    priv_path = output_dir / name
    pub_path = output_dir / f"{name}.pub"

    priv_path.write_bytes(private_pem)
    priv_path.chmod(0o600)

    pub_path.write_bytes(public_openssh)
    pub_path.chmod(0o644)

    return priv_path, pub_path


def load_existing_key(key_path: Path) -> str:
    """Load existing public key from file."""
    key = load_public_key(key_path)
    return key.public_bytes_raw().hex()

