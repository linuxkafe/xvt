---
ticket: T003
title: Device fingerprint DB (model → exploit vectors)
sprint: sprint-01
priority: high
status: done
created: 2026-09-19
---

# T003 — Device fingerprint DB (model → exploit vectors)

## Context
Map discovered devices (model + firmware version) to known exploit vectors. This database drives the exploit selection logic for T006-T008. Data sourced from valetudo.cloud, builder.dontvacuum.me, robotinfo.dev.

## Acceptance Criteria
- [ ] YAML database with model/firmware → vector mapping
- [ ] Covers at least 5 Xiaomi/Viomi/Roborock/Dreame models
- [ ] Each entry: model, firmware_min, firmware_max, vectors[], notes
- [ ] Loader module with validation
- [ ] CLI command to lookup vectors for a device
- [ ] Unit tests for loader and matching logic

## Scope
**In scope:**
- Data file: `data/fingerprints.yaml`
- Loader: `src/xvt/fingerprints.py`
- Vector enum: UART, DUSTBIN, OTA_DOWNGRADE, SU_BINARY
- Matching logic: exact model + firmware range
- CLI: `xvt vectors <ip>` or `xvt vectors --model <model> --firmware <fw>`

**Out of scope:**
- Exploit implementation (T006-T008)
- Firmware modification (T011+)
- Key injection (T009)

## Dependencies
- T002 (done): Network scanner provides model/firmware
- T004 (parallel): CLI skeleton for command integration

## Rollback
Delete `data/fingerprints.yaml` and `src/xvt/fingerprints.py`

## Known Risks
- Firmware version parsing varies (e.g., "1.2.3_4567" vs "3.5.8")
- Some models share hardware but different firmware branches
- New firmware may patch vectors → need version ranges
- Community data may be incomplete/outdated

## Notes
- Sources: valetudo.cloud/supported-devices, builder.dontvacuum.me, robotinfo.dev
- Vector types:
  - UART: Serial header access (S5, S6 gen1, early S7)
  - DUSTBIN: Dustbin sensor exploit (S6 gen2, S7, T7)
  - OTA_DOWNGRADE: Downgrade to vulnerable firmware (newer models)
  - SU_BINARY: Pre-rooted firmware with su binary