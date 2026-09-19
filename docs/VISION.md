# Vision

## Problem

Xiaomi robot vacuum owners lack root access to their devices, preventing:
- Installation of Valetudo (open-source, cloud-free control software)
- Custom firmware modifications for privacy, localization, or feature extensions
- Full ownership and control of hardware they purchased

Current methods are scattered across forums (valetudo.cloud, builder.dontvacuum.me, robotinfo.dev), undocumented, model-specific, and error-prone. Users risk bricking devices.

## Solution

XVT provides a unified, reproducible, auditable toolchain that:
1. **Scans** the local network to discover Xiaomi vacuums and identify model/firmware
2. **Injects** SSH keys via documented exploits (e.g., UART, dustbin, OTA downgrade vectors)
3. **Modifies** firmware images to enable persistent root (dropbear, authorized_keys, su binary)
4. **Flashes** modified firmware safely with verification and rollback capability

All operations are logged, checksummed, and testable against known firmware vectors.

## Value

- **User sovereignty**: Full control over device, no cloud dependency
- **Reproducibility**: Same toolchain works across supported models (S5, S6, S7, T7, etc.)
- **Auditability**: Every modification step is visible, logged, and reversible
- **Safety**: Checksum verification, dry-run mode, automatic rollback on failure
- **Community**: Extensible framework for new models/exploits without forking