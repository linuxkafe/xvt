# Requirements

## Functional

### FR-1: Network Discovery
- Scan local network (ARP, mDNS, SSDP) for Xiaomi vacuum devices
- Identify model, firmware version, MAC, IP via MiIO protocol
- Output machine-readable JSON for automation

### FR-2: Exploit Vector Selection
- Map (model, firmware) → known exploit vectors
- Vectors: UART header, dustbin sensor, OTA downgrade, su binary injection
- Dry-run mode: show what would be attempted without executing

### FR-3: Key Injection
- Generate or accept user SSH keypair (Ed25519 preferred)
- Inject authorized_keys via selected vector
- Verify SSH access post-injection

### FR-4: Firmware Modification
- Parse firmware image (cramfs/squashfs + kernel + DTB)
- Inject dropbear SSH server, su binary, authorized_keys
- Preserve checksums / sign if required by bootloader
- Output modified firmware with verification manifest

### FR-5: Firmware Flashing
- Flash modified firmware via MiIO OTA or UART
- Verify write with read-back checksum
- Automatic rollback on verification failure
- Progress logging with timestamps

### FR-6: Post-Root Validation
- Verify SSH access with injected key
- Confirm Valetudo compatibility (port 22, filesystem layout)
- Generate device-specific config for Valetudo

## Non-Functional

### NFR-1: Safety
- All write operations require explicit `--confirm` flag
- Dry-run default for all mutating operations
- Checksum verification before and after flash
- Automatic rollback on any verification failure

### NFR-2: Auditability
- Every operation logs to structured JSON (timestamp, action, params, result)
- Firmware modifications produce diff manifest (what changed, why)
- No binary blobs in repo; all modifications expressed as patches

### NFR-3: Reproducibility
- Deterministic firmware modification given same input + key
- Test vectors for each supported (model, firmware) pair
- CI validates test vectors on every commit

### NFR-4: Extensibility
- New exploit vectors added via plugin interface (no core changes)
- Model/firmware database in data/ (YAML), not code
- Valetudo config templates per model

### NFR-5: Security
- No hardcoded keys, passwords, or tokens
- Keys generated per-device or user-supplied
- No network calls to Xiaomi cloud (local-only operation)

## Constraints

- Language: Python 3.11+
- Platform: Linux (primary), macOS (discovery only), Windows (WSL2)
- Deployment: CLI tool via pipx / standalone binary (PyInstaller)
- Dependencies: Minimal; cryptography, pyyaml, click, pyserial, scapy
- No cloud APIs; pure local network + physical access vectors