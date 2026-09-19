---
ticket: T014
title: Test vectors for 3+ firmware versions
sprint: sprint-03
priority: high
status: done
created: 2026-09-26
---

# T014 — Test vectors for 3+ firmware versions

## Context
Create test vectors (known firmware images with expected parse/verify results) for at least 3 different Xiaomi vacuum models/firmware versions. These serve as regression tests for the firmware parser, patcher, and checksum modules.

## Acceptance Criteria
- [ ] Obtain or create test firmware images for 3+ models (e.g., S5, S6 gen1, S6 gen2, S7, Viomi V8, T7)
- [ ] Document expected parse results (header, partitions, checksums)
- [ ] Create test fixtures in tests/fixtures/
- [ ] Add integration tests that verify parse → patch → checksum roundtrip
- [ ] Document firmware version / exploit vector mapping

## Scope
**In scope:**
- Test firmware images (can be synthetic/minimal for CI)
- Expected parse results as JSON fixtures
- Integration tests for parse → patch → checksum roundtrip
- Documentation of model → firmware version → exploit vector mapping

**Out of scope:**
- Actual device firmware downloads (copyright)
- Real hardware testing

## Dependencies
- T011 (done): Firmware parser
- T012 (done): Patch engine
- T013 (done): Checksum preservation

## Rollback
Remove test fixtures and integration tests

## Known Risks
- Xiaomi firmware is proprietary - cannot include real images in repo
- Must use synthetic/minimal test fixtures
- Firmware formats vary significantly across generations

## Notes
- Reference: robotinfo.dev for firmware version database
- valetudo.cloud has supported device list with firmware versions
- Test fixtures should be minimal valid firmware structures