---
ticket: T002
title: Network scanner (ARP/mDNS/SSDP) + MiIO probe
sprint: sprint-01
priority: high
status: pending
created: 2026-09-19
---

# T002 — Network scanner (ARP/mDNS/SSDP) + MiIO probe

## Context
First functional component. Need to discover Xiaomi vacuums on the local network and identify model/firmware via MiIO protocol. This enables all downstream operations.

## Acceptance Criteria
- [ ] ARP scan discovers all devices on local subnet
- [ ] mDNS/SSDP discovers Xiaomi devices advertising `_miio._udp` or similar
- [ ] MiIO handshake retrieves device info (model, firmware, MAC, hardware rev)
- [ ] Output is machine-readable JSON with schema
- [ ] Unit tests with mocked network responses
- [ ] Integration test against real device (manual, documented)

## Scope
**In scope:**
- ARP scanner using scapy or /proc/net/arp fallback
- mDNS browser (zeroconf) for `_miio._udp.local`
- SSDP M-SEARCH for UPnP devices
- MiIO discovery protocol (handshake + get_device_info)
- JSON output with device schema

**Out of scope:**
- Exploit vector selection (T003)
- Key injection (T006+)
- CLI integration (T004)

## Dependencies
- T001 (done): project scaffolding
- Python deps: scapy, zeroconf, python-miio (or custom MiIO impl)

## Rollback
N/A — read-only network operations

## Known Risks
- Scapy requires root for ARP on some systems → provide non-root fallback
- MiIO protocol varies by firmware version → test against multiple versions
- Network segmentation (VLANs, guest networks) may hide devices

## Notes
- Reference: python-miio library for protocol details
- robotinfo.dev has device fingerprint database
- Consider async implementation for parallel scanning