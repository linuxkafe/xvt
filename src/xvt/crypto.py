"""Cryptographic utilities for key generation and firmware signing."""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_ed25519_keypair() -> tuple[bytes, bytes]:
    """Generate Ed25519 keypair. Returns (private_key_pem, public_key_openssh)."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_openssh = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    return private_pem, public_openssh


def load_private_key(path: Path) -> ed25519.Ed25519PrivateKey:
    """Load Ed25519 private key from PEM file."""
    with path.open("rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
        if not isinstance(key, ed25519.Ed25519PrivateKey):
            raise ValueError("Not an Ed25519 private key")
        return key


def load_public_key(path: Path) -> ed25519.Ed25519PublicKey:
    """Load Ed25519 public key from OpenSSH file."""
    with path.open("rb") as f:
        key = serialization.load_ssh_public_key(f.read())
        if not isinstance(key, ed25519.Ed25519PublicKey):
            raise ValueError("Not an Ed25519 public key")
        return key
