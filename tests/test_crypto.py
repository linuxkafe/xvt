"""Tests for XVT crypto module."""

import tempfile
from pathlib import Path

from src.xvt.crypto import generate_ed25519_keypair, load_private_key, load_public_key


def test_generate_keypair():
    private_pem, public_openssh = generate_ed25519_keypair()
    assert b"PRIVATE KEY" in private_pem
    assert public_openssh.startswith(b"ssh-ed25519 ")


def test_roundtrip_keys():
    private_pem, public_openssh = generate_ed25519_keypair()

    with tempfile.TemporaryDirectory() as tmpdir:
        priv_path = Path(tmpdir) / "id_ed25519"
        pub_path = Path(tmpdir) / "id_ed25519.pub"

        priv_path.write_bytes(private_pem)
        pub_path.write_bytes(public_openssh)

        loaded_priv = load_private_key(priv_path)
        loaded_pub = load_public_key(pub_path)

        # Verify they match
        assert (
            loaded_priv.public_key().public_bytes_raw()
            == loaded_pub.public_bytes_raw()
        )


def test_load_wrong_key_type_fails():
    # This test would need a non-Ed25519 key, skipped for now
    import pytest
    pytest.skip("Requires non-Ed25519 key fixture")
