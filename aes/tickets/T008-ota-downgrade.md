---
ticket: T008
title: OTA downgrade vector (T7, newer)
sprint: sprint-02
priority: high
status: done
created: 2026-09-19
---

# T008 — OTA downgrade vector (T7, newer)

## Context
Implement the OTA firmware downgrade exploit for newer Xiaomi models (T7, newer S7, Dreame L10s, etc.) that have no hardware vectors (UART/dustbin patched). This exploits the MiIO OTA update mechanism to flash an older vulnerable firmware version, then uses that version's exploit to gain root.

## Acceptance Criteria
- [ ] OTADowngradeExploit class with prepare(), flash(), verify() methods
- [ ] Firmware image fetching from known sources (builder.dontvacuum.me, etc.)
- [ ] MiIO OTA flash protocol implementation
- [ ] Checksum verification before/after flash
- [ ] Automatic rollback on failure
- [ ] Dry-run mode shows steps without executing
- [ ] Unit tests with mocked MiIO responses
- [ ] Integration test documentation (requires device + vulnerable firmware)

## Scope
**In scope:**
- MiIO OTA update protocol (packet structure, encryption)
- Firmware image validation (checksums, signatures)
- Flash process with progress monitoring
- Rollback mechanism (dual-bank or recovery partition)
- Integration with fingerprint DB for vulnerable firmware versions

**Out of scope:**
- Hardware vectors (T006, T007)
- Firmware modification (T011+)
- Key injection (T009)

## Dependencies
- T002 (done): Network scanner provides device IP + token
- T003 (done): Fingerprint DB identifies OTA-vulnerable models + target firmware versions
- T004/5 (done): CLI with dry-run/confirm and logging

## Rollback
Remove src/xvt/exploits/ota.py and related CLI integration

## Known Risks
- High brick risk if flash interrupted or wrong firmware
- Requires valid MiIO token (may need extraction via other vector first)
- OTA protocol varies by model/firmware
- Xiaomi may block downgrade in newer firmware
- No hardware fallback if OTA fails

## Notes
- Reference: valetudo.cloud OTA downgrade guide
- MiIO OTA uses encrypted packets with token-derived keys
- Typical flow: download firmware → verify checksum → send OTA start → stream chunks → verify → reboot
- Vulnerable firmware versions per model in fingerprint DB
- Dual-bank flash allows rollback if boot fails