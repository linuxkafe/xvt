# Roadmap

## Sprint 1: Foundation (Core Discovery + Safety)

| ID | Task | Impact | Effort | Status |
|----|------|--------|--------|--------|
| T001 | Project scaffolding + AES setup | High | Low | done |
| T002 | Network scanner (ARP/mDNS/SSDP) + MiIO probe | High | Medium | todo |
| T003 | Device fingerprint DB (model → exploit vectors) | High | Medium | todo |
| T004 | CLI skeleton with dry-run / confirm flags | High | Low | todo |
| T005 | Logging + structured output (JSON) | High | Low | todo |

## Sprint 2: Key Injection Vectors

| ID | Task | Impact | Effort | Status |
|----|------|--------|--------|--------|
| T006 | UART exploit vector (S5/S6 gen1) | High | High | todo |
| T007 | Dustbin sensor vector (S6 gen2/S7) | High | High | todo |
| T008 | OTA downgrade vector (T7, newer) | High | High | todo |
| T009 | SSH key generation + injection logic | High | Medium | todo |
| T010 | Post-injection verification | High | Medium | todo |

## Sprint 3: Firmware Modification Engine

| ID | Task | Impact | Effort | Status |
|----|------|--------|--------|--------|
| T011 | Firmware parser (cramfs/squashfs + kernel) | High | High | todo |
| T012 | Patch engine (dropbear, su, authorized_keys) | High | High | todo |
| T013 | Checksum / signature preservation | High | High | todo |
| T014 | Test vectors for 3+ firmware versions | High | Medium | todo |

## Sprint 4: Flashing + Validation

| ID | Task | Impact | Effort | Status |
|----|------|--------|--------|--------|
| T015 | MiIO OTA flash with verify + rollback | High | High | todo |
| T016 | UART flash fallback | Medium | Medium | todo |
| T017 | Post-root Valetudo config generator | High | Medium | todo |
| T018 | End-to-end integration test (CI) | High | High | todo |

## Backlog (Prioritized)

- [ ] Multi-device parallel operations
- [ ] Web UI for non-technical users (separate repo)
- [ ] Valetudo auto-install via SSH
- [ ] Xiaomi cloud blockade (DNS/hosts automation)
- [ ] Support for Dreame / Roborock rebrands
- [ ] Firmware diff visualization tool

---

## Milestones

| Milestone | Target | Criteria |
|-----------|--------|----------|
| M1: Scan & Identify | Sprint 1 end | Discovers S5/S6/S7 on LAN, outputs JSON |
| M2: Root via UART | Sprint 2 end | Keys injected, SSH works on S5 gen1 |
| M3: Firmware Mod | Sprint 3 end | Modified firmware boots, SSH persists |
| M4: Full Pipeline | Sprint 4 end | Scan → Root → Flash → Valetudo ready |