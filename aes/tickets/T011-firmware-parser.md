---
ticket: T011
title: Firmware parser (cramfs/squashfs + kernel)
sprint: sprint-03
priority: high
status: done
created: 2026-09-26
---

# T011 — Firmware parser (cramfs/squashfs + kernel)

## Context
Parse Xiaomi vacuum firmware images to extract components (kernel, rootfs, DTB, header) for modification. Firmware images typically contain a header + kernel + cramfs/squashfs rootfs + optional DTB.

## Acceptance Criteria
- [ ] FirmwareParser class with parse(), extract(), rebuild() methods
- [ ] Detect firmware format (header magic, partition layout)
- [ ] Extract kernel (zImage/uImage), rootfs (cramfs/squashfs), DTB
- [ ] Parse header with partition offsets, sizes, checksums
- [ ] Support for known Xiaomi firmware formats (MiIO OTA format)
- [ ] Rebuild firmware from components with updated checksums
- [ ] Dry-run mode shows what would be parsed/extracted
- [ ] Unit tests with sample firmware structures
- [ ] Integration test with real firmware (if available)

## Scope
**In scope:**
- Binary parsing of firmware images
- Header parsing (magic, version, partitions)
- cramfs/squashfs detection and extraction
- Kernel extraction (zImage, uImage, fitImage)
- DTB extraction
- Checksum verification (CRC32, SHA256)
- Rebuild with updated checksums

**Out of scope:**
- Firmware patching (T012)
- Flashing (T015)
- Exploit vectors (T006-T008)

## Dependencies
- T010 (done): Post-injection verification confirms device access
- python-magic or filetype for format detection
- cramfsck, unsquashfs tools (system deps)
- struct, zlib, hashlib for parsing

## Rollback
Remove src/xvt/firmware/parser.py and related modules

## Known Risks
- Firmware formats vary by model/generation
- Encrypted firmware partitions (newer models)
- Custom Xiaomi header formats
- Proprietary compression
- Brick risk if rebuild fails

## Notes
- Reference: valetudo.cloud firmware analysis
- robotinfo.dev firmware database
- Xiaomi OTA format: header + kernel + rootfs + DTB
- cramfs: older models, squashfs: newer models
- Kernel often zImage with appended DTB
- Header typically 512 bytes with partition table