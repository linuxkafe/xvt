---
ticket: T012
title: Patch engine (dropbear, su, authorized_keys)
sprint: sprint-03
priority: high
status: done
created: 2026-09-26
---

# T012 — Patch engine (dropbear, su, authorized_keys)

## Context
Modify firmware rootfs to inject persistent root access components: dropbear SSH server, su binary, and authorized_keys. This is the core firmware modification that enables persistent root after OTA flash.

## Acceptance Criteria
- [ ] PatchEngine class with inject_dropbear(), inject_su(), inject_authorized_keys() methods
- [ ] cramfs/squashfs rootfs extraction and repacking
- [ ] Dropbear SSH server binary injection (statically linked)
- [ ] su binary injection (toybox/busybox su or standalone)
- [ ] authorized_keys file creation with injected public key
- [ ] Init script modification to start dropbear on boot
- [ ] Preserve file permissions and ownership
- [ ] Dry-run mode shows what would be patched
- [ ] Unit tests with sample rootfs
- [ ] Integration test with real firmware

## Scope
**In scope:**
- cramfs extraction (cramfsck -x) and repacking (mkcramfs)
- squashfs extraction (unsquashfs) and repacking (mksquashfs)
- Binary injection into /usr/sbin/, /bin/, /etc/
- Init script modification (/etc/init.d/, /etc/rc.local)
- File permission preservation (755 for binaries, 600 for keys)
- Checksum verification after repack

**Out of scope:**
- Firmware parsing (T011)
- Checksum/signature preservation (T013)
- Flashing (T015)

## Dependencies
- T011 (done): Firmware parser provides rootfs extraction
- T009 (done): SSH key injection logic provides key material
- System tools: cramfsck, mkcramfs, unsquashfs, mksquashfs

## Rollback
Remove src/xvt/firmware/patcher.py and related modules

## Known Risks
- cramfs/squashfs tools may not be available on all systems
- Rootfs may be read-only compressed (need tmpfs for extraction)
- Binary compatibility (architecture, libc, kernel version)
- Dropbear config location varies (/etc/dropbear/ vs /etc/)
- Init system varies (sysvinit, systemd, custom)
- Space constraints in firmware partitions

## Notes
- Statically linked dropbear from OpenWrt SDK
- su binary from toybox or busybox
- Dropbear config: /etc/dropbear/dropbear_rsa_host_key, /etc/dropbear/authorized_keys
- Init scripts: /etc/init.d/S50dropbear or /etc/rc.d/S50dropbear
- Preserve SELinux/AppArmor contexts if present