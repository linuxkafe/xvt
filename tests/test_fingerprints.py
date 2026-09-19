"""Tests for XVT fingerprints module."""

from src.xvt.fingerprints import (
    FingerprintDatabase,
    VectorType,
    get_vectors_for_device,
    load_fingerprints,
    match_fingerprint,
    parse_version,
    version_in_range,
)


def test_parse_version():
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("1.2.3_4567") == (1, 2, 3, 4567)
    assert parse_version("30081") == (30081,)
    assert parse_version("3.5.9") == (3, 5, 9)


def test_version_in_range():
    assert version_in_range("30081", "1.0.0", "30081")
    assert version_in_range("3.5.9", "1.0.0", "3.5.9")
    assert not version_in_range("30082", "1.0.0", "30081")
    assert not version_in_range("0.9.9", "1.0.0", "30081")


def test_load_fingerprints():
    db = load_fingerprints("data/fingerprints.yaml")
    assert isinstance(db, FingerprintDatabase)
    assert len(db.fingerprints) >= 8
    assert "uart" in db.vector_types
    assert "dustbin" in db.vector_types
    assert "ota_downgrade" in db.vector_types
    assert "su_binary" in db.vector_types


def test_match_fingerprint_exact():
    db = load_fingerprints("data/fingerprints.yaml")
    fp = match_fingerprint(db, "viomi.vacuum.v8", "30081")
    assert fp is not None
    assert fp.model == "viomi.vacuum.v8"
    assert fp.name == "Viomi V8 / Viomi S7"
    assert len(fp.vectors) == 2


def test_match_fingerprint_version_out_of_range():
    db = load_fingerprints("data/fingerprints.yaml")
    # Firmware too new for dustbin vector
    fp = match_fingerprint(db, "viomi.vacuum.v8", "30082")
    assert fp is None


def test_match_fingerprint_unknown_model():
    db = load_fingerprints("data/fingerprints.yaml")
    fp = match_fingerprint(db, "unknown.model", "1.0.0")
    assert fp is None


def test_get_vectors_for_device():
    db = load_fingerprints("data/fingerprints.yaml")
    vectors = get_vectors_for_device(db, "viomi.vacuum.v8", "30081")
    assert len(vectors) == 2
    assert any(v.type == VectorType.DUSTBIN for v in vectors)
    assert any(v.type == VectorType.OTA_DOWNGRADE for v in vectors)


def test_vector_info_fields():
    db = load_fingerprints("data/fingerprints.yaml")
    fp = match_fingerprint(db, "viomi.vacuum.v8", "30081")
    for v in fp.vectors:
        assert isinstance(v.type, VectorType)
        assert isinstance(v.description, str)
        assert isinstance(v.difficulty, str)
        assert isinstance(v.requirements, list)
        assert isinstance(v.persistent, bool)
        assert isinstance(v.requires_opening, bool)


def test_s5_has_uart_vector():
    db = load_fingerprints("data/fingerprints.yaml")
    fp = match_fingerprint(db, "rockrobo.vacuum.s5", "3.5.9")
    assert fp is not None
    assert any(v.type == VectorType.UART for v in fp.vectors)
    assert any(v.type == VectorType.SU_BINARY for v in fp.vectors)


def test_newer_model_only_ota():
    db = load_fingerprints("data/fingerprints.yaml")
    fp = match_fingerprint(db, "xiaomi.vacuum.t7", "99999")
    assert fp is not None
    # T7 should only have OTA_DOWNGRADE
    assert len(fp.vectors) == 1
    assert fp.vectors[0].type == VectorType.OTA_DOWNGRADE
