---
ticket: T015
title: MiIO OTA flash with verify + rollback
sprint: sprint-04
priority: high
status: done
created: 2026-09-19
---

# T015 — MiIO OTA flash with verify + rollback

## Context
Implement the MiIO OTA flashing protocol to write patched firmware to the device. This is the critical path for the OTA downgrade exploit vector (T008). Must include verification after flash and automatic rollback on failure.

## Acceptance Criteria
- [ ] MiIO OTA flash protocol implementation (start, data chunks, end)
- [ ] Firmware verification after flash (checksum, version check)
- [ ] Automatic rollback on verification failure
- [ ] Progress reporting with callbacks
- [ ] Dry-run mode showing what would be flashed
- [ ] Unit tests with mocked device responses
- [ ] Integration test documentation (requires real device)

## Scope
**In scope:**
- MiIO OTA protocol: `miIO.ota_start`, `miIO.ota_data`, `miIO.ota_end`
- Chunked transmission with progress reporting
- Post-flash verification (checksum, version, boot success)
- Automatic rollback to original firmware on failure
- Dry-run mode for safety

**Out of scope:**
- UART flash fallback (T016)
- Exploit vector implementation (T006-T008)
- Firmware patching (T012)

## Dependencies
- T012 (done): Patch engine provides patched firmware
- T013 (done): Checksum preservation for rebuild
- T008 (done): OTA downgrade vector defines target firmware

## Rollback
If flash fails verification, automatically flash back original firmware image. Requires storing original firmware before flash.

## Known Risks
- **Brick risk**: Power loss during flash = brick (mitigation: U-Boot recovery via UART)
- **Token expiration**: MiIO token may change after reboot (use default token `f*32`)
- **Firmware mismatch**: Wrong model/firmware = brick (mitigation: fingerprint verification)
- **Power loss**: During flash = brick (mitigation: U-Boot recovery, battery backup)

## Notes
- Reference: valetudo.cloud OTA flash guide
- MiIO OTA uses encrypted chunks with AES-CBC (key derived from token)
- Chunk size typically 4096 bytes
- Device reboots automatically after `miIO.ota_end`
- Verification window: ~60-120 seconds for reboot + SSH check