---
ticket: T010
title: Post-injection verification
sprint: sprint-03
priority: high
status: done
created: 2026-09-26
---

# T010 — Post-injection verification

## Context
After SSH key injection via any exploit vector (UART, dustbin, OTA), verify that the device is actually accessible via SSH with the injected key. This is the final confirmation that root access was achieved.

## Acceptance Criteria
- [ ] SSHVerifier class with connect(), verify_key(), run_command() methods
- [ ] Paramiko-based SSH connection with injected Ed25519 key
- [ ] Retry logic with exponential backoff (device reboot takes time)
- [ ] Command execution test (e.g., `id`, `uname -a`, `cat /etc/passwd`)
- [ ] Dropbear/OpenSSH server detection
- [ ] Device info collection (model, firmware, kernel, rootfs)
- [ ] Dry-run mode shows what would be verified
- [ ] Unit tests with mocked SSH server
- [ ] Integration test documentation (requires rooted device)

## Scope
**In scope:**
- Paramiko SSH client for Ed25519 key authentication
- Connection retry with backoff (device may be rebooting)
- Command execution and output capture
- Server type detection (dropbear vs OpenSSH)
- Structured result output (JSON)

**Out of scope:**
- Exploit execution (T006-T008)
- Key injection (T009)
- Firmware modification (T011+)

## Dependencies
- T009 (done): SSH key injection logic
- T006-T008 (done): Exploit vectors provide the shell access

## Rollback
Remove src/xvt/verification/ssh.py and related CLI integration

## Known Risks
- Device IP may change after reboot (DHCP)
- SSH server may take 30-60s to start after boot
- Dropbear on non-standard port (sometimes 2222)
- Firewall rules may block SSH temporarily
- Key format issues (Ed25519 vs RSA)

## Notes
- Reuse crypto.py for key loading
- Paramiko supports Ed25519 natively
- Reference: valetudo.cloud post-root verification
- Collect device info for Valetudo config generation (T017)