"""Device fingerprint database loader and exploit vector matching."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml


class VectorType(Enum):
    """Known exploit vector types."""
    UART = "uart"
    DUSTBIN = "dustbin"
    OTA_DOWNGRADE = "ota_downgrade"
    SU_BINARY = "su_binary"


@dataclass
class VectorInfo:
    """Exploit vector details."""
    type: VectorType
    description: str
    difficulty: str
    requirements: list[str]
    persistent: bool = True
    requires_opening: bool = True


@dataclass
class DeviceFingerprint:
    """Device fingerprint with exploit vectors."""
    model: str
    name: str
    vendor: str
    firmware_min: str
    firmware_max: str
    vectors: list[VectorInfo]
    notes: str = ""


@dataclass
class FingerprintDatabase:
    """Loaded fingerprint database."""
    fingerprints: list[DeviceFingerprint]
    vector_types: dict[str, dict]


def parse_version(version: str) -> tuple[int, ...]:
    """Parse version string to tuple for comparison."""
    # Handle formats like "1.2.3_4567" or "30081"
    parts = version.replace('_', '.').split('.')
    return tuple(int(p) for p in parts if p.isdigit())


def version_in_range(version: str, min_ver: str, max_ver: str) -> bool:
    """Check if version is within [min, max] range."""
    v = parse_version(version)
    v_min = parse_version(min_ver)
    v_max = parse_version(max_ver)
    return v_min <= v <= v_max


def load_fingerprints(
    path: Path | str = "data/fingerprints.yaml"
) -> FingerprintDatabase:
    """Load fingerprint database from YAML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Fingerprint database not found: {path}")

    with path.open() as f:
        data = yaml.safe_load(f)

    fingerprints = []
    for fp_data in data.get("fingerprints", []):
        vectors = []
        for v_data in fp_data.get("vectors", []):
            vectors.append(VectorInfo(
                type=VectorType(v_data["type"]),
                description=v_data["description"],
                difficulty=v_data["difficulty"],
                requirements=v_data["requirements"],
                persistent=v_data.get("persistent", True),
                requires_opening=v_data.get("requires_opening", True),
            ))
        fingerprints.append(DeviceFingerprint(
            model=fp_data["model"],
            name=fp_data["name"],
            vendor=fp_data["vendor"],
            firmware_min=fp_data["firmware_min"],
            firmware_max=fp_data["firmware_max"],
            vectors=vectors,
            notes=fp_data.get("notes", ""),
        ))

    return FingerprintDatabase(
        fingerprints=fingerprints,
        vector_types=data.get("vector_types", {}),
    )


def match_fingerprint(
    db: FingerprintDatabase, model: str, firmware: str
) -> DeviceFingerprint | None:
    """Find matching fingerprint for model and firmware version."""
    for fp in db.fingerprints:
        if fp.model == model and version_in_range(
            firmware, fp.firmware_min, fp.firmware_max
        ):
            return fp
    return None


def get_vectors_for_device(
    db: FingerprintDatabase, model: str, firmware: str
) -> list[VectorInfo]:
    """Get applicable exploit vectors for a device."""
    fp = match_fingerprint(db, model, firmware)
    if fp:
        return fp.vectors
    return []


# CLI helper
def format_vector_info(v: VectorInfo) -> str:
    """Format vector info for display."""
    reqs = ", ".join(v.requirements)
    return (
        f"  - {v.type.value.upper()}: {v.description}\n"
        f"    Difficulty: {v.difficulty}\n"
        f"    Requirements: {reqs}\n"
        f"    Persistent: {'Yes' if v.persistent else 'No'}\n"
        f"    Requires opening: {'Yes' if v.requires_opening else 'No'}\n"
    )
