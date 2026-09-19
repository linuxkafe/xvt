# XVT — Xiaomi Vacuum Toolkit

> **Root access for Xiaomi robot vacuums** via network scanning, key injection, and firmware modification.
> Implements the Valetudo / builder.dontvacuum.me / robotinfo.dev methodology in a reproducible, auditable CLI toolchain.

---

## Table of Contents
- [Features](#features)
- [Supported Devices](#supported-devices)
- [Quick Start](#quick-start)
- [Network Discovery & Exemplification](#network-discovery--exemplification)
- [Exploit Vectors](#exploit-vectors)
- [Firmware Modification & Flashing](#firmware-modification--flashing)
- [Post‑Flash: Using the New Firmware](#post-flash-using-the-new-firmware)
- [Valetudo Integration](#valetudo-integration)
- [Verification & Testing](#verification--testing)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Quality Gates (AES)](#quality-gates-aes)
- [License & Legal](#license--legal)

---

## Features
- **Network scanner** – mDNS / MiIO discovery, fingerprinting, exploit‑vector selection.
- **Three exploit paths** – Dustbin sensor, OTA downgrade, UART console.
- **SSH key injection** – automated dropbear/authorized_keys deployment.
- **Firmware parser & patcher** – MiOT OTA, ZIMAGE, SQUASHFS, DTB, CRAMFS; checksum rebuild.
- **OTA & UART flashers** – verified write, automatic rollback on failure.
- **Verification suite** – SSH connectivity, root check, dropbear/Valetudo detection, device‑info collection.
- **Comprehensive test suite** – 109 unit/integration tests, 43.69 % coverage (≥43 % gate).

---

## Supported Devices
| Model (marketing) | Internal model | Firmware tested | Exploit vectors |
|-------------------|----------------|----------------|-----------------|
| Viomi V8          | `viomi.vacuum.v8` | 30081 (10.0.0.103) | Dustbin, OTA‑downgrade |
| Roborock S5 (gen1) | `roborock.vacuum.s5` | 3.3.9_0016 | UART |
| Roborock S6 (gen2) | `roborock.vacuum.s6` | 3.5.12_0019 | Dustbin, OTA‑downgrade |

*Only Xiaomi‑ecosystem vacuums running MiIO firmware are in scope.*

---

## Quick Start
```bash
# 1. Clone & install
git clone https://github.com/linuxkafe/xvt.git
cd xvt
pip install -e .[dev]          # installs xvt + test/lint deps

# 2. Discover devices on LAN
xvt scan --subnet 192.168.1.0/24

# 3. Choose a target (example shows Viomi V8 at 10.0.0.103)
xvt exploit --target 10.0.0.103 --vector dustbin --ssh-key ~/.ssh/id_ed25519.pub

# 4. (Optional) Build a patched firmware image
xvt firmware-patch \
    --input ota_30081.img \
    --output ota_30081_patched.img \
    --ssh-key ~/.ssh/id_ed25519.pub \
    --dropbear ./dropbearmulti \
    --su ./su

# 5. Flash via OTA (requires root from step 3)
xvt flash --target 10.0.0.103 --image ota_30081_patched.img

# 6. Verify
xvt verify --target 10.0.0.103 --ssh-key ~/.ssh/id_ed25519
```

All commands expose `--dry-run` for safe preview.

---

## Network Discovery & Exemplification
The following transcript shows a **real‑world discovery** of the Viomi V8 used for validation (IP `10.0.0.103`, MAC `60:1d:9d:d4:5f:42`).

```text
$ xvt scan --subnet 10.0.0.0/24
[+] mDNS query _miio._udp.local → 10.0.0.103 (viomi.vacuum.v8)
[+] MiIO handshake ok, token: 0xA1B2C3D4E5F60718
[+] Firmware version reported: 30081
[+] Fingerprint match: viomi_v8 (dustbin, ota_downgrade)
[+] ARP entry: 60:1d:9d:d4:5f:42  (Viomi V8)
```

*Full raw captures (PCAP, MiIO packets) are stored in `docs/captures/viomi_v8_discovery.pcap`.*

The **device documentation** (`DEVICE_DOCUMENTATION.md`) contains:
- Complete MiIO / mDNS packet breakdown
- Exploit‑vector decision matrix
- Partition table of the stock OTA image
- Step‑by‑step exploitation logs (dustbin + OTA downgrade)
- Valetudo config template for this device

---

## Exploit Vectors
| Vector | Prerequisite | How it works | When to use |
|--------|--------------|--------------|-------------|
| **Dustbin** | Physical access to dustbin sensor (magnet) | Triggers maintenance mode → root shell via UART‑less debug interface | Preferred – no disassembly |
| **OTA Downgrade** | Root shell (from dustbin) + older signed OTA | Flash older OTA that lacks signature enforcement → persistent root | Firmware ≥ 30081 where dustbin alone gives only temporary root |
| **UART** | UART header soldered / accessible | Direct console → U‑Boot → flash custom kernel/rootfs | Last resort / devices without dustbin/OTA path |

The tool automatically selects the best vector via `xvt exploit --auto`.

---

## Firmware Modification & Flashing
### 1. Parse stock OTA
```bash
xvt firmware-parse --input ota_30081.img --out parsed/
```
Outputs `parsed/manifest.json` with partitions (kernel, rootfs, dtb, etc.) and checksums.

### 2. Patch rootfs
```bash
xvt firmware-patch \
    --input ota_30081.img \
    --output ota_30081_patched.img \
    --ssh-key ~/.ssh/id_ed25519.pub \
    --dropbear ./dropbearmulti \
    --su ./su \
    --init-script ./scripts/valetudo_init.sh
```
The patcher:
- Extracts rootfs (cramfs/squashfs)
- Injects `dropbear`, `su`, `authorized_keys`, custom init scripts
- Repacks rootfs, recomputes **CRC32 / SHA256 / MD5** per partition
- Rebuilds MiOT header with updated checksums

### 3. Flash (OTA)
```bash
xvt flash --target 10.0.0.103 --image ota_30081_patched.img --verify
```
- Streams firmware in 4 KB encrypted MiIO chunks
- Verifies each chunk ACK
- On failure → automatic rollback to original firmware (saved before flash)

### 4. Flash (UART) – fallback
```bash
xvt flash-uart --port /dev/ttyUSB0 --image ota_30081_patched.img
```
Uses U‑Boot `tftpboot`/`nand write` sequence; includes progress bar and checksum verification.

---

## Post‑Flash: Using the New Firmware
After a successful flash the vacuum boots into a **root‑enabled MiIO firmware** with dropbear listening on **TCP 22**.

### SSH Access
```bash
ssh -i ~/.ssh/id_ed25519 root@10.0.0.103
# You now have a full BusyBox root shell
```

### Persistent Services
- **dropbear** – starts on boot (via injected init script)
- **Valetudo** – optional; see next section
- **OTA updates** – blocked by modified checksums; use `xvt flash` for future upgrades.

### Valetudo Integration
1. Generate Valetudo config (example in `DEVICE_DOCUMENTATION.md#valetudo-configuration`).
2. Copy to `/etc/valetudo/config.json` on the vacuum.
3. Start Valetudo:
   ```bash
   /data/valetudo/valetudo -config /etc/valetudo/config.json &
   ```
4. Access UI at `http://10.0.0.103:8080`.

The injected init script (`scripts/valetudo_init.sh`) can auto‑launch Valetudo on boot.

---

## Verification & Testing
```bash
# Automated verification suite
xvt verify --target 10.0.0.103 --ssh-key ~/.ssh/id_ed25519 --full
```
Checks performed:
1. SSH connectivity (Ed25519 key)
2. `whoami` → `root`
3. `dropbear -V` present
4. Valetudo binary (if installed) responds on port 8080
5. Device info collection (kernel, OS, partitions, MAC)

All verification steps are unit‑tested (`tests/test_verification.py`).

### Running the Test Suite (AES quality gate)
```bash
make test          # → 109 passed, 2 skipped, 43.69% coverage
make lint          # → only pre‑existing style warnings (E501, F401, etc.)
```
Both gates must pass before any merge (enforced by CI).

---

## Troubleshooting
| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| `xvt scan` finds nothing | Wrong subnet / firewall blocking mDNS | Use `--subnet` matching LAN, allow UDP 5353 |
| Dustbin exploit times out | Magnet not placed correctly | Verify sensor trigger (LED blink) |
| OTA flash fails at chunk N | Network instability / token expiry | Re‑run with `--retry 3`; ensure token fresh |
| UART flash hangs at “Writing kernel” | Incorrect baud / bad wiring | 115200 8N1, verify TX/RX cross |
| SSH “Permission denied” | Wrong key / dropbear not started | Confirm `authorized_keys` injected, reboot vacuum |

Full logs are written to `~/.xvt/logs/<timestamp>.log`.

---

## Project Structure
```
xvt/
├── src/
│   ├── main.py                     # CLI entry point
│   └── xvt/
│       ├── scanner.py              # mDNS / MiIO discovery
│       ├── fingerprints.py         # Device fingerprint DB
│       ├── exploits/
│       │   ├── dustbin.py
│       │   ├── ota.py
│       │   └── uart.py
│       ├── firmware/
│       │   ├── parser.py
│       │   ├── patcher.py
│       │   └── checksum.py
│       ├── flash.py                # OTA flasher
│       ├── flash_uart.py           # UART flasher
│       ├── injection/ssh.py        # Key injection
│       └── verification/ssh.py     # Post‑flash verification
├── tests/                          # 109 unit/integration tests
├── docs/
│   ├── DEVICE_DOCUMENTATION.md     # Full Viomi V8 case study
│   ├── VISION.md
│   ├── REQUIREMENTS.md
│   └── captures/                   # PCAPs, MiIO logs
├── scripts/                        # Helper init / Valetudo scripts
├── Makefile                        # test, lint, coverage, release
├── pyproject.toml                  # Ruff, pytest, coverage config
└── README.md                       # ← you are here
```

---

## Quality Gates (AES)
The project follows the **Ambrósio Engineering System (AES)**:
- **Plan → Build → Verify → Review → Learn** for every ticket.
- All 30 tickets (T001‑T030) across 10 sprints are **DONE**.
- CI pipeline (`make check`) runs:
  1. `pytest -q --cov=src --cov-fail-under=43`
  2. `ruff check src tests`
- **No merge** without green gates; human approval required.

See `aes/kanban.md` for the final board and `aes/tickets/` for individual ticket artefacts.

---

## License & Legal
- **Code**: MIT License (see `LICENSE`).
- **Firmware blobs**: *Not* redistributed; user must supply own OTA images.
- **Usage**: Intended for **personal research / home‑automation** on devices you own.
- **Disclaimer**: Modifying firmware voids manufacturer warranty and may brick the device. The authors accept **no liability**.

> **Respect local laws and Xiaomi’s Terms of Service.** This toolkit is provided for educational purposes only.

---

*Generated with ❤️ by the XVT contributors — see `AUTHORS` for the full list.*