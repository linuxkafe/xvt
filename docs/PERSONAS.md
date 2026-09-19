# Personas

## Primary User: Vacuum Owner / Privacy Enthusiast

**Profile:** Technical user who owns a Xiaomi robot vacuum (Mi Robot, Roborock, Dreame variants). Values privacy, local control, and hardware ownership. Comfortable with CLI tools.

**Goals:**
- Root their vacuum without bricking it
- Install Valetudo for cloud-free operation
- Block Xiaomi telemetry/data collection
- Integrate with Home Assistant / local automation

**Pain Points:**
- Fragmented, model-specific guides on forums
- Risk of bricking expensive hardware
- No verification of firmware modifications
- OTA updates break root access
- No rollback mechanism

---

## Secondary User: Security Researcher / Valetudo Contributor

**Profile:** Developer contributing to Valetudo or researching IoT security. Needs to test exploits, analyze firmware, develop new root vectors.

**Goals:**
- Analyze firmware images for vulnerabilities
- Test key injection vectors safely
- Contribute new model support upstream
- Automate regression testing of exploits

**Pain Points:**
- Manual firmware extraction/analysis
- No test vectors for regression
- Hard to share reproducible exploit chains
- Device-specific quirks undocumented

---

## Maintainer

**Profile:** Engineer maintaining XVT codebase

**Goals:**
- Keep code clean, auditable, minimal
- Ensure quality gates catch firmware corruption
- Support new models without code duplication
- Document exploit chains for reproducibility

**Tools:**
- AES (Ambrósio Engineering System)
- `make check` for validation (lint, test, firmware checksum verify)
- `make test-firmware` for vector validation