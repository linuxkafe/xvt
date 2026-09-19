"""Tests for XVT OTA exploit module."""

from src.xvt.exploits.ota import (
    FirmwareInfo,
    OTAConfig,
    OTADowngradeExploit,
    find_vulnerable_firmware,
)


def test_ota_config_defaults():
    config = OTAConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path="/tmp/firmware.img",
        target_version="1.0.0",
    )
    assert config.device_ip == "10.0.0.103"
    assert config.chunk_size == 4096
    assert config.timeout == 30.0
    assert config.verify_checksum is True


def test_firmware_info_creation():
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"test firmware data")
        path = Path(f.name)
    try:
        info = FirmwareInfo(
            path=path,
            version="1.0.0",
            model="xiaomi.vacuum.t7",
            size=18,
            sha256="test",
            md5="test",
        )
        assert info.version == "1.0.0"
        assert info.model == "xiaomi.vacuum.t7"
    finally:
        path.unlink()


def test_ota_exploit_dry_run_verify():
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"test firmware")
        path = Path(f.name)
    try:
        config = OTAConfig(
            device_ip="10.0.0.103",
            token="f" * 32,
            firmware_path=path,
            target_version="1.0.0",
        )
        exploit = OTADowngradeExploit(config, dry_run=True)
        info = exploit.verify_firmware()
        assert info is not None
        assert info.size == 13
    finally:
        path.unlink()


def test_ota_exploit_dry_run_start():
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"test")
        path = Path(f.name)
    try:
        config = OTAConfig(
            device_ip="10.0.0.103",
            token="f" * 32,
            firmware_path=path,
            target_version="1.0.0",
        )
        exploit = OTADowngradeExploit(config, dry_run=True)
        info = FirmwareInfo(
            path=path, version="1.0.0", model="test", size=4, sha256="", md5=""
        )
        assert exploit.ota_start(info) is True
    finally:
        path.unlink()


def test_ota_exploit_dry_run_stream():
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"x" * 10000)
        path = Path(f.name)
    try:
        config = OTAConfig(
            device_ip="10.0.0.103",
            token="f" * 32,
            firmware_path=path,
            target_version="1.0.0",
        )
        exploit = OTADowngradeExploit(config, dry_run=True)
        info = FirmwareInfo(
            path=path, version="1.0.0", model="test", size=10000, sha256="", md5=""
        )
        assert exploit.ota_stream(info) is True
    finally:
        path.unlink()


def test_ota_exploit_dry_run_end():
    config = OTAConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path="/tmp/test.img",
        target_version="1.0.0",
    )
    exploit = OTADowngradeExploit(config, dry_run=True)
    assert exploit.ota_end() is True


def test_ota_exploit_dry_run_wait_reboot():
    config = OTAConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path="/tmp/test.img",
        target_version="1.0.0",
    )
    exploit = OTADowngradeExploit(config, dry_run=True)
    assert exploit.wait_for_reboot() is True


def test_ota_exploit_dry_run_verify_downgrade():
    config = OTAConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path="/tmp/test.img",
        target_version="1.0.0",
    )
    exploit = OTADowngradeExploit(config, dry_run=True)
    assert exploit.verify_downgrade("1.0.0") is True


def test_ota_exploit_dry_run_rollback():
    config = OTAConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path="/tmp/test.img",
        target_version="1.0.0",
    )
    exploit = OTADowngradeExploit(config, dry_run=True)
    assert exploit.rollback() is True


def test_ota_exploit_dry_run_full():
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.img', delete=False) as f:
        f.write(b"x" * 1000)
        path = Path(f.name)
    try:
        config = OTAConfig(
            device_ip="10.0.0.103",
            token="f" * 32,
            firmware_path=path,
            target_version="1.0.0",
        )
        exploit = OTADowngradeExploit(config, dry_run=True)
        result = exploit.run_downgrade()
        assert result is True
    finally:
        path.unlink()


def test_find_vulnerable_firmware_known():
    result = find_vulnerable_firmware("xiaomi.vacuum.t7", "2.0.0")
    assert result is not None
    assert "version" in result
    assert result["model"] == "xiaomi.vacuum.t7"


def test_find_vulnerable_firmware_unknown():
    result = find_vulnerable_firmware("unknown.model", "1.0.0")
    assert result is None


def test_find_vulnerable_firmware_version_check():
    # Current version older than all vulnerable - should return None
    result = find_vulnerable_firmware("xiaomi.vacuum.t7", "0.5.0")
    assert result is None


def test_ota_config_custom():
    config = OTAConfig(
        device_ip="10.0.0.103",
        token="f" * 32,
        firmware_path="/tmp/fw.img",
        target_version="1.0.0",
        chunk_size=8192,
        timeout=60.0,
        verify_checksum=False,
    )
    assert config.chunk_size == 8192
    assert config.timeout == 60.0
    assert config.verify_checksum is False


def test_firmware_info_from_filename():
    import tempfile
    from pathlib import Path
    prefix = 'xiaomi.vacuum.t7_1.0.0_'
    with tempfile.NamedTemporaryFile(
        mode='wb', suffix='.img', delete=False, prefix=prefix
    ) as f:
        f.write(b"test")
        path = Path(f.name)
    try:
        info = FirmwareInfo(
            path=path,
            version="1.0.0",
            model="xiaomi.vacuum.t7",
            size=4,
            sha256="test",
            md5="test",
        )
        assert info.model == "xiaomi.vacuum.t7"
        assert info.version == "1.0.0"
    finally:
        path.unlink()

