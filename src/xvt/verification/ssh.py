"""SSH post-injection verification for Xiaomi vacuum root access."""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import paramiko

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
    paramiko = None


@dataclass
class VerificationConfig:
    """Configuration for SSH verification."""
    device_ip: str
    private_key_path: Path
    username: str = "root"
    port: int = 22
    timeout: float = 10.0
    max_retries: int = 12
    base_delay: float = 5.0
    max_delay: float = 60.0


@dataclass
class VerificationResult:
    """Result of SSH verification."""
    success: bool
    device_ip: str
    server_type: str = "unknown"
    server_version: str = ""
    commands_run: list[dict[str, Any]] = field(default_factory=list)
    device_info: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    duration_seconds: float = 0.0


class SSHVerifier:
    """Verify SSH access after key injection."""

    # Common commands to run for verification
    VERIFICATION_COMMANDS = [
        ("id", "Check user ID"),
        ("uname -a", "Kernel info"),
        ("cat /etc/os-release", "OS info"),
        ("cat /proc/version", "Kernel version"),
        ("df -h", "Disk usage"),
        ("cat /etc/passwd", "User list"),
        ("which dropbear", "Dropbear path"),
        ("dropbear -V 2>&1 | head -1", "Dropbear version"),
        ("sshd -V 2>&1 | head -1", "OpenSSH version"),
    ]

    def __init__(
        self,
        config: VerificationConfig,
        dry_run: bool = False,
        logger: logging.Logger | None = None,
    ):
        self.config = config
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)
        self._client: paramiko.SSHClient | None = None

    def _load_private_key(self) -> "paramiko.PKey | None":
        """Load Ed25519 private key."""
        if not HAS_PARAMIKO:
            self.logger.error("paramiko not installed. Install with: pip install paramiko")
            return None

        try:
            return paramiko.Ed25519Key.from_private_key_file(str(self.config.private_key_path))
        except Exception as e:
            self.logger.error("Failed to load private key: %s", e)
            return None

    def _create_client(self) -> "paramiko.SSHClient | None":
        """Create and configure SSH client."""
        if not HAS_PARAMIKO:
            return None

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def connect_with_retry(self) -> bool:
        """Connect with exponential backoff retry."""
        if self.dry_run:
            self.logger.info("[DRY-RUN] Would connect to %s:%d with retries", self.config.device_ip, self.config.port)
            return True

        if not HAS_PARAMIKO:
            self.logger.error("paramiko not available")
            return False

        private_key = self._load_private_key()
        if not private_key:
            return False

        delay = self.config.base_delay
        for attempt in range(1, self.config.max_retries + 1):
            self.logger.info("Connection attempt %d/%d to %s:%d",
                           attempt, self.config.max_retries, self.config.device_ip, self.config.port)

            try:
                self._client = self._create_client()
                self._client.connect(
                    hostname=self.config.device_ip,
                    port=self.config.port,
                    username=self.config.username,
                    pkey=private_key,
                    timeout=self.config.timeout,
                    banner_timeout=self.config.timeout,
                    auth_timeout=self.config.timeout,
                )
                self.logger.info("SSH connection established on attempt %d", attempt)
                return True

            except paramiko.AuthenticationException:
                self.logger.warning("Authentication failed (attempt %d/%d)", attempt, self.config.max_retries)
            except paramiko.SSHException as e:
                self.logger.warning("SSH error (attempt %d/%d): %s", attempt, self.config.max_retries, e)
            except Exception as e:
                self.logger.warning("Connection error (attempt %d/%d): %s", attempt, self.config.max_retries, e)

            if attempt < self.config.max_retries:
                self.logger.info("Waiting %.1fs before retry...", delay)
                time.sleep(delay)
                delay = min(delay * 1.5, self.config.max_delay)

        self.logger.error("All connection attempts failed")
        return False

    def detect_server_type(self) -> tuple[str, str]:
        """Detect SSH server type and version."""
        if self.dry_run or not self._client:
            return "dropbear (simulated)", "2022.83"

        try:
            stdin, stdout, stderr = self._client.exec_command("dropbear -V 2>&1 | head -1", timeout=5)
            output = stdout.read().decode().strip()
            if output and "dropbear" in output.lower():
                version = output.split()[-1] if output.split() else "unknown"
                return "dropbear", version
        except Exception:
            pass

        try:
            stdin, stdout, stderr = self._client.exec_command("sshd -V 2>&1 | head -1", timeout=5)
            output = stderr.read().decode().strip()
            if output and "openssh" in output.lower():
                version = output.split()[-1] if output.split() else "unknown"
                return "openssh", version
        except Exception:
            pass

        return "unknown", ""

    def run_verification_commands(self) -> list[dict[str, Any]]:
        """Run verification commands and collect output."""
        results = []
        if self.dry_run or not self._client:
            for cmd, desc in self.VERIFICATION_COMMANDS:
                results.append({
                    "command": cmd,
                    "description": desc,
                    "stdout": "[DRY-RUN] simulated output",
                    "stderr": "",
                    "exit_code": 0,
                })
            return results

        for cmd, desc in self.VERIFICATION_COMMANDS:
            try:
                stdin, stdout, stderr = self._client.exec_command(cmd, timeout=10)
                exit_code = stdout.channel.recv_exit_status()
                stdout_text = stdout.read().decode().strip()
                stderr_text = stderr.read().decode().strip()
                results.append({
                    "command": cmd,
                    "description": desc,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "exit_code": exit_code,
                })
            except Exception as e:
                results.append({
                    "command": cmd,
                    "description": desc,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                })

        return results

    def collect_device_info(self, commands_output: list[dict[str, Any]]) -> dict[str, str]:
        """Extract device info from command outputs."""
        info = {}
        for item in commands_output:
            cmd = item["command"]
            stdout = item["stdout"]

            if cmd == "uname -a" and stdout:
                info["kernel"] = stdout
            elif cmd == "cat /etc/os-release" and stdout:
                for line in stdout.split('\n'):
                    if '=' in line:
                        k, v = line.split('=', 1)
                        info[k.lower()] = v.strip('"')
            elif cmd == "cat /proc/version" and stdout:
                info["proc_version"] = stdout
            elif cmd == "which dropbear" and stdout:
                info["dropbear_path"] = stdout
            elif cmd == "dropbear -V 2>&1 | head -1" and stdout:
                info["dropbear_version"] = stdout

        return info

    def verify(self) -> VerificationResult:
        """Run full verification process."""
        start_time = time.time()
        self.logger.info("Starting SSH verification for %s", self.config.device_ip)

        if not self.connect_with_retry():
            return VerificationResult(
                success=False,
                device_ip=self.config.device_ip,
                error="Failed to establish SSH connection",
                duration_seconds=time.time() - start_time,
            )

        server_type, server_version = self.detect_server_type()
        self.logger.info("Detected SSH server: %s %s", server_type, server_version)

        commands_output = self.run_verification_commands()
        device_info = self.collect_device_info(commands_output)

        duration = time.time() - start_time
        self.logger.info("Verification completed in %.1fs", duration)

        return VerificationResult(
            success=True,
            device_ip=self.config.device_ip,
            server_type=server_type,
            server_version=server_version,
            commands_run=commands_output,
            device_info=device_info,
            duration_seconds=duration,
        )

    def close(self) -> None:
        """Close SSH connection."""
        if self._client:
            self._client.close()
            self._client = None


def verify_ssh_access(
    device_ip: str,
    private_key_path: Path,
    username: str = "root",
    port: int = 22,
    dry_run: bool = False,
    logger: logging.Logger | None = None,
) -> VerificationResult:
    """Convenience function for SSH verification."""
    config = VerificationConfig(
        device_ip=device_ip,
        private_key_path=private_key_path,
        username=username,
        port=port,
    )
    verifier = SSHVerifier(config, dry_run=dry_run, logger=logger)
    try:
        return verifier.verify()
    finally:
        verifier.close()
