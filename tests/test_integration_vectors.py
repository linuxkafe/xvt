"""Integration tests for firmware test vectors - component integration."""

import json
import tempfile
from pathlib import Path

from src.xvt.firmware.parser import FirmwareParser, FirmwareFormat
from src.xvt.firmware.patcher import PatchConfig
from src.xvt.firmware.checksum import calculate_checksums, ChecksumCalculator, ChecksumConfig
from src.xvt.fingerprints import load_fingerprints, get_vectors_for_device
from src.xvt.injection.ssh import generate_key_pair


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "firmware"


def load_fixture(name: str) -> dict:
    """Load a firmware test fixture."""
    fixture_path = FIXTURES_DIR / f"{name}.json"
    return json.loads(fixture_path.read_text())


def test_s5_gen1_vectors_and_checksums():
    """Test S5 gen1: fingerprint vectors and checksums are correct."""
    fixture = load_fixture("s5_gen1")
    
    # Test fingerprint vectors are correctly loaded
    fp_db = load_fingerprints()
    vectors = get_vectors_for_device(fp_db, fixture["model"], fixture["firmware_version"])
    assert len(vectors) >= 2
    vector_types = {v.type.value for v in vectors}
    assert "uart" in vector_types
    assert "su_binary" in vector_types
    
    # Test checksum calculation
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"
    result = calc.calculate_all(data)
    assert result.crc32 == "d308aeb2"
    assert result.sha256 == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert result.md5 == "eb733a00c0c9d336e65691a37ab54293"
    
    # Test patch engine config
    config = PatchConfig(
        rootfs_path=Path(""),
        output_path=Path("/tmp/test.img"),
        authorized_keys=b"ssh-ed25519 test",
    )
    assert config.authorized_keys == b"ssh-ed25519 test"


def test_s6_gen2_vectors_and_checksums():
    """Test S6 gen2: fingerprint vectors and checksums are correct."""
    fixture = load_fixture("s6_gen2")
    
    # Test fingerprint vectors
    fp_db = load_fingerprints()
    vectors = get_vectors_for_device(fp_db, fixture["model"], fixture["firmware_version"])
    assert len(vectors) >= 2
    vector_types = {v.type.value for v in vectors}
    assert "dustbin" in vector_types
    assert "ota_downgrade" in vector_types
    
    # Test checksum calculation
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"
    result = calc.calculate_all(data)
    assert result.crc32 == "d308aeb2"
    assert result.sha256 == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert result.md5 == "eb733a00c0c9d336e65691a37ab54293"


def test_viomi_v8_vectors_and_checksums():
    """Test Viomi V8: fingerprint vectors and checksums are correct."""
    fixture = load_fixture("viomi_v8")
    
    # Test fingerprint vectors
    fp_db = load_fingerprints()
    vectors = get_vectors_for_device(fp_db, fixture["model"], fixture["firmware_version"])
    assert len(vectors) >= 2
    vector_types = {v.type.value for v in vectors}
    assert "dustbin" in vector_types
    assert "ota_downgrade" in vector_types
    
    # Test checksum calculation
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    data = b"test data"
    result = calc.calculate_all(data)
    assert result.crc32 == "d308aeb2"
    assert result.sha256 == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert result.md5 == "eb733a00c0c9d336e65691a37ab54293"


def test_firmware_format_detection():
    """Test firmware format detection works correctly."""
    parser = FirmwareParser()
    
    # Test format detection with correct magic bytes
    assert parser.detect_format(b"\x28\xcd\x3d\x45" + b"x" * 100) == FirmwareFormat.CRAMFS
    assert parser.detect_format(b"hsqs" + b"x" * 100) == FirmwareFormat.SQUASHFS
    assert parser.detect_format(b"\x1f\x8b\x08" + b"x" * 100) == FirmwareFormat.ZIMAGE
    assert parser.detect_format(b"\x27\x05\x19\x56" + b"x" * 100) == FirmwareFormat.UIMAGE
    assert parser.detect_format(b"\xd0\x0d\xfe\xed" + b"x" * 100) == FirmwareFormat.DTB
    assert parser.detect_format(b"unknown") == FirmwareFormat.UNKNOWN


def test_all_fixtures_have_expected_vectors():
    """Verify all fixtures have expected exploit vectors documented."""
    fixture_names = ["s5_gen1", "s6_gen2", "viomi_v8"]
    
    fp_db = load_fingerprints()
    
    for name in fixture_names:
        fixture = load_fixture(name)
        vectors = get_vectors_for_device(
            fp_db, fixture["model"], fixture["firmware_version"]
        )
        
        # Each model should have at least one exploit vector
        assert len(vectors) > 0, f"No vectors for {name}"
        
        # Verify expected vectors from fixture
        expected_vectors = set(fixture["exploit_vectors"])
        actual_vectors = {v.type.value for v in vectors}
        
        # At least the expected vectors should be present
        for exp in expected_vectors:
            assert exp in actual_vectors, f"Missing {exp} for {name}"


def test_firmware_parser_format_enum():
    """Test FirmwareFormat enum has correct integer values."""
    assert FirmwareFormat.UNKNOWN == 0
    assert FirmwareFormat.MIOT_OTA == 0
    assert FirmwareFormat.CRAMFS == 1
    assert FirmwareFormat.SQUASHFS == 2
    assert FirmwareFormat.ZIMAGE == 3
    assert FirmwareFormat.UIMAGE == 4
    assert FirmwareFormat.FITIMAGE == 5
    assert FirmwareFormat.DTB == 6


def test_checksum_calculator():
    """Test checksum calculator basic operations."""
    config = ChecksumConfig()
    calc = ChecksumCalculator(config)
    
    data = b"test data"
    
    # Test individual checksums
    assert calc.calculate_crc32(data) == "d308aeb2"
    assert calc.calculate_sha256(data) == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert calc.calculate_md5(data) == "eb733a00c0c9d336e65691a37ab54293"
    
    # Test verify_checksum
    assert calc.verify_checksum(data, "d308aeb2", "crc32")
    assert calc.verify_checksum(data, "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9", "sha256")
    assert calc.verify_checksum(data, "eb733a00c0c9d336e65691a37ab54293", "md5")
    assert not calc.verify_checksum(data, "ffffffff", "crc32")
    
    # Test calculate_all
    result = calc.calculate_all(data)
    assert result.size == 9
    assert result.crc32 == "d308aeb2"
    assert result.sha256 == "916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9"
    assert result.md5 == "eb733a00c0c9d336e65691a37ab54293"