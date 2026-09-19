---
ticket: T017
title: Post-root Valetudo config generator
sprint: sprint-06
priority: high
status: in-progress
created: 2026-09-19
---

# T017 — Post-root Valetudo config generator

## Context
After achieving root access on a Xiaomi vacuum, generate the configuration files needed for Valetudo to run. This includes MQTT configuration, vacuum-specific capabilities, and vendor-specific settings.

## Acceptance Criteria
- [ ] ValetudoConfigGenerator class with generate() method
- [ ] Model-specific capability detection (lidar, camera, mop, etc.)
- [ ] MQTT broker configuration with authentication
- [ ] Vacuum-specific Valetudo config (vendor, model, capabilities)
- [ ] Map/floor plan configuration options
- [ ] Dry-run mode showing generated config
- [ ] Unit tests for different vacuum models
- [ ] Integration test documentation

## Scope
**In scope:**
- Generate valetudo.yaml with vacuum-specific settings
- MQTT configuration (host, port, auth, topics)
- Capability detection from firmware/model
- Map/entity configuration
- Vendor-specific overrides (xiaomi, viomi, roborock, dreame)

**Out of scope:**
- Valetudo installation (handled separately)
- Root exploit execution (T006-T008)
- Firmware flashing (T015-T016)

## Dependencies
- T015 (done): OTA flash provides root access
- T016 (done): UART flash fallback available
- T009 (done): SSH key injection for root access

## Rollback
Delete generated config files, no device modification.

## Known Risks
- **Model detection**: May need manual override for unknown models
- **Capability mapping**: Vendor-specific quirks (e.g., Dreame vs Xiaomi)
- **MQTT security**: Default credentials should be changed
- **Map data**: Requires vacuum to have mapping capability

## Notes
- Reference: Valetudo config schema (valetudo.io/docs)
- Generate config.yaml compatible with Valetudo 2024.x
- Support both MQTT v3.1.1 and v5.0
- Include vendor-specific quirks (xiaomi token, dreame map format)