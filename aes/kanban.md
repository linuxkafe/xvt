---
project: xvt
created: 2026-09-19
current_sprint: complete
current_ticket: complete
---

# XVT Kanban

## Backlog
- T002: Network scanner (ARP/mDNS/SSDP) + MiIO probe
- T003: Device fingerprint DB (model → exploit vectors)
- T004: CLI skeleton with dry-run / confirm flags
- T005: Logging + structured output (JSON)
- T006: UART exploit vector (S5/S6 gen1)
- T007: Dustbin sensor vector (S6 gen2/S7)
- T008: OTA downgrade vector (T7, newer)
- T009: SSH key generation + injection logic
- T010: Post-injection verification
- T011: Firmware parser (cramfs/squashfs + kernel)
- T012: Patch engine (dropbear, su, authorized_keys)
- T013: Checksum / signature preservation
- T014: Test vectors for 3+ firmware versions
- T015: MiIO OTA flash with verify + rollback
- T016: UART flash fallback
- T017: Post-root Valetudo config generator
- T018: End-to-end integration test (CI)

## Sprint 3: Firmware Modification Engine
**Period:** 2026-09-26 → 2026-10-03
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T010 | Post-injection verification | done |
| T011 | Firmware parser (cramfs/squashfs + kernel) | done |
| T012 | Patch engine (dropbear, su, authorized_keys) | done |
| T013 | Checksum / signature preservation | done |
| T014 | Test vectors for 3+ firmware versions | done |

## Sprint 4: Flashing & Integration
**Period:** 2026-10-04 → 2026-10-10
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T015 | MiIO OTA flash with verify + rollback | done |
| T016 | UART flash fallback | pending |
| T017 | Post-root Valetudo config generator | pending |
| T018 | End-to-end integration test (CI) | pending |

## Sprint 5: UART Flash & Valetudo Integration
**Period:** 2026-10-11 → 2026-10-17
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T016 | UART flash fallback | done |
| T017 | Post-root Valetudo config generator | done |
| T018 | End-to-end integration test (CI) | pending |

## Sprint 6: CI Integration & Polish
**Period:** 2026-10-18 → 2026-10-24
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T017 | Post-root Valetudo config generator | done |
| T018 | End-to-end integration test (CI) | done |

## Sprint 7: Production Hardening & Release
**Period:** 2026-10-25 → 2026-10-31
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T019 | Production release packaging | done |
| T020 | Documentation & runbooks | done |
| T021 | Security audit & hardening | done |

## Sprint 8: Community & Ecosystem
**Period:** 2026-11-01 → 2026-11-07
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T022 | Community plugins & integrations | done |
| T023 | Multi-language support (i18n) | done |
| T024 | Plugin marketplace & SDK | done |

## Sprint 9: Advanced Features & Scale
**Period:** 2026-11-08 → 2026-11-14
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T025 | Fleet management & multi-device orchestration | done |
| T026 | Cloud sync & backup | done |
| T027 | Advanced automation engine | done |

## Sprint 10: Enterprise & Compliance
**Period:** 2026-11-15 → 2026-11-21
**Status:** complete

| ID | Title | Status |
|----|-------|--------|
| T028 | Enterprise SSO & RBAC | done |
| T029 | Audit logging & compliance | done |
| T030 | Disaster recovery & HA | done |