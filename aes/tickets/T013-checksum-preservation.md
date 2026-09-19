---
ticket: T013
title: Checksum / signature preservation
sprint: sprint-03
priority: high
status: done
created: 2026-09-26
---

# T013 — Checksum / signature preservation

## Context
After patching firmware rootfs, the firmware image must be rebuilt with correct checksums and signatures so the device will accept it. Xiaomi devices verify firmware integrity before flashing.

## Acceptance Criteria
- [ ] ChecksumCalculator class for CRC32, SHA256, MD5
- [ ] Xiaomi firmware header checksum update (CRC32 of partitions)
- [ ] Partition checksum updates (CRC32/SHA256 per partition)
- [ ] OTA package signature verification (if applicable)
- [ ] Rebuild firmware image with updated checksums
- [ ] Verify rebuilt firmware passes device verification
- [ ] Dry-run mode shows what checksums would be updated
- [ ] Unit tests with known firmware samples
- [ ] Integration test with real device (if available)

## Scope
**In scope:**
- CRC32 checksum calculation (zlib)
- SHA256/MD5 for partition verification
- Xiaomi MiIO OTA header checksum format
- Partition table checksum updates
- Firmware image rebuild with updated checksums
- Verification that rebuilt firmware passes checks

**Out of scope:**
- Private key signing (Xiaomi uses proprietary keys)
- Bootloader unlocking
- Firmware parsing (T011)
- Patch engine (T012)

## Dependencies
- T011 (done): Firmware parser provides partition info
- T012 (done): Patch engine provides modified rootfs
- zlib, hashlib for checksums

## Rollback
Remove src/xvt/firmware/checksum.py and related modules

## Known Risks
- Xiaomi uses proprietary signing keys (cannot re-sign officially)
- Some devices verify signatures against Xiaomi servers
- Checksum algorithms may vary by model/generation
- Header format may include reserved fields
- OTA package may have additional integrity checks

## Notes
- Xiaomi OTA format: header + partitions with individual checksums
- Header typically has CRC32 of entire image or partition table
- Some devices accept firmware with correct CRC32 but invalid signature (dev mode)
- Reference: valetudo.cloud firmware modification guides
- robotinfo.dev has firmware checksum info