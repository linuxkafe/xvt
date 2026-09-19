---
ticket: T016
title: UART flash fallback
sprint: sprint-05
priority: high
status: done
created: 2026-09-19
---

# T016 — UART flash fallback

## Context
Implement UART-based firmware flashing as a fallback when OTA flashing fails or is unavailable. This provides a hardware-level recovery path for bricked devices or devices with locked OTA.

## Acceptance Criteria
- [ ] UARTFlasher class with serial communication via pyserial
- [ ] XMODEM/YMODEM protocol implementation for firmware transfer
- [ ] Bootloader interaction (U-Boot) for flash write commands
- [ ] Progress reporting with callbacks
- [ ] Dry-run mode showing what would be flashed
- [ ] Automatic verification after flash
- [ ] Unit tests with mocked serial port
- [ ] Integration test documentation (requires hardware)

## Scope
**In scope:**
- Serial communication via pyserial (115200 8N1)
- U-Boot command interaction (boot delay interruption, flash commands)
- XMODEM/YMODEM file transfer protocol
- Flash write commands (nand write, sf update, etc.)
- Progress reporting with callbacks
- Dry-run mode for safety

**Out of scope:**
- OTA flashing (T015)
- Exploit vectors (T006-T008)
- Firmware patching (T012)

## Dependencies
- T006 (done): UART exploit vector provides shell access pattern
- T015 (done): OTA flash provides verification pattern
- pyserial dependency

## Rollback
If UART flash fails, device may be bricked. Requires JTAG or hardware programmer for recovery.

## Known Risks
- **High brick risk**: Power loss during UART flash = permanent brick
- **Timing sensitivity**: U-Boot interrupt window is narrow (~1-3 seconds)
- **Baud rate mismatch**: Wrong baud = garbled communication
- **Hardware variation**: Different U-Boot versions/commands per model

## Notes
- Reference: valetudo.cloud UART flash guide
- Typical baud: 115200 8N1
- U-Boot prompt: "Hit any key to stop autoboot"
- Flash commands vary: `nand write`, `sf update`, `mtd write`
- XMODEM: 128-byte packets, CRC16, 10 retries typical