---
ticket: T009
title: SSH key generation + injection logic
sprint: sprint-02
priority: high
status: done
created: 2026-09-19
---

# T009 — SSH key generation + injection logic

## Context
Implement SSH key generation and injection logic that works across all exploit vectors (UART, dustbin, OTA). This is the core "payload" that gets delivered by the exploit vectors to enable persistent root access.

## Acceptance Criteria
- [ ] KeyGenerator class: generate Ed25519 keypairs, load existing keys
- [ ] KeyInjector class: inject authorized_keys via multiple methods
- [ ] Support for dropbear and OpenSSH authorized_keys formats
- [ ] Injection via shell commands (for UART/dustbin recovery shell)
- [ ] Injection via firmware modification (for OTA)
- [ ] Verification: test SSH connectivity post-injection
- [ ] Dry-run mode shows what would be injected
- [ ] Unit tests for key generation and injection logic

## Scope
**In scope:**
- Ed25519 key generation (modern, secure, small keys)
- Key loading from files (PEM private, OpenSSH public)
- authorized_keys file management (append, deduplicate)
- Injection via shell (echo/cat/tee to authorized_keys)
- Injection via firmware patch (T012 integration)
- SSH connectivity test (paramiko or subprocess)

**Out of scope:**
- Exploit vector implementations (T006-T008)
- Firmware modification engine (T011+)
- Dropbear/OpenSSH server configuration (handled by vectors)

## Dependencies
- T006 (done): UART exploit provides shell access
- T007 (done): Dustbin exploit provides shell access
- T008 (done): OTA provides firmware flash capability
- T004/5 (done): CLI with dry-run/confirm and logging

## Rollback
Remove src/xvt/injection/ directory and related CLI integration

## Known Risks
- Different devices use different SSH servers (dropbear vs OpenSSH)
- authorized_keys location varies (/etc/dropbear/, /root/.ssh/, /home/root/.ssh/)
- Permissions must be correct (600 for file, 700 for .ssh dir)
- Some firmwares have read-only rootfs requiring remount
- Key format compatibility (Ed25519 vs RSA)

## Notes
- Reuse crypto.py for key generation
- Reference: valetudo.cloud key injection guides
- Dropbear uses /etc/dropbear/authorized_keys
- OpenSSH uses ~/.ssh/authorized_keys
- Test with paramiko for SSH verification