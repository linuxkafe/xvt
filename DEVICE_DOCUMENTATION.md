# XVT Device Documentation - Viomi V8 Vacuum Network Exemplification

## Executive Summary

This document provides comprehensive documentation for the Xiaomi/Viomi vacuum device discovered on the local network, including network discovery, exploit vector analysis, and firmware modification procedures following the AES (Ambrósio Engineering System) protocol.

**Document Version:** 1.0  
**Date:** 2026-09-19  
**Project:** XVT (Xiaomi Vacuum/Vale Tudo)  
**Protocol:** AES (Ambrósio Engineering System) v4.8+

---

## 1. Network Discovery Results

### 1.1 Network Scan Results (2026-09-19)

The network scan discovered **14 devices** on the 10.0.0.0/24 subnet. The primary target device is:

| Parameter | Value |
|-----------|-------|
| **IP Address** | 10.0.0.103 |
| **MAC Address** | 60:1d:9d:d4:5f:42 |
| **OUI** | 60:1d:9d (Xiaomi Communications) |
| **Model** | viomi-vacuum-v8 (Viomi V8 / Viomi S7) |
| **Vendor** | Viomi (Xiaomi ecosystem) |
| **Firmware Version** | 30081 (per fingerprint DB) / unknown (runtime) |
| **MiIO Token** | ffffffffffffffffffffffffffffffff (default/unconfigured) |
| **Discovery Methods** | mDNS (_miio._udp.local.), MiIO Handshake (port 54321) |

### 1.2 Discovery Methods Used

| Method | Protocol | Port | Result |
|--------|----------|------|--------|
| mDNS | _miio._udp.local. | 5353 | ✅ Success - Service: `viomi-vacuum-v8_miio489925682._miio._udp.local.` |
| MiIO Handshake | UDP | 54321 | ✅ Success - Token: `ffffffffffffffffffffffffffffffff` |
| SSDP | M-SEARCH | 1900 | ⚠️ Limited - No Xiaomi-specific responses |
| ARP Table | /proc/net/arp | N/A | ✅ MAC: 60:1d:9d:d4:5f:42 |

### 1.3 Device Fingerprint Profile

```json
{
  "model": "viomi.vacuum.v8",
  "name": "Viomi V8 / Viomi S7",
  "vendor": "viomi",
  "firmware_version": "30081",
  "exploit_vectors": [
    "dustbin",
    "ota_downgrade"
  ],
  "notes": "Viomi V8 - Dustbin sensor exploit (fw <= 30081), OTA downgrade available. Discovered at 10.0.0.103 in test network."
}
```

---

## 2. Exploit Vector Analysis

### 2.1 Available Exploit Vectors for Viomi V8 (fw 30081)

| Vector | Status | Difficulty | Requirements | Persistence | Access Type |
|--------|--------|------------|--------------|-------------|-------------|
| **Dustbin Sensor** | ✅ Available | Medium | Physical access, GPIO shorting during boot | ✅ Permanent | Physical |
| **OTA Downgrade** | ✅ Available | Medium | Network access, MiIO token, vulnerable FW image | ✅ Permanent | Remote/Network |

### 2.2 Vector Details

#### 2.2.1 Dustbin Sensor Exploit
- **Mechanism**: Short dustbin sensor pins during boot to enter recovery mode
- **Requirements**: Physical access to device, GPIO header access, jumper wires
- **Procedure**: Short dustbin sensor pins during power-on → Enter recovery shell → Inject SSH keys → Enable dropbear
- **Risk**: Medium (requires opening device, but no firmware flashing)
- **Persistence**: Permanent (SSH keys survive reboots and OTA updates)

#### 2.2.2 OTA Downgrade Exploit
- **Mechanism**: Flash vulnerable firmware (≤30081) via MiIO OTA protocol
- **Requirements**: Network access, valid MiIO token, vulnerable firmware image
- **Procedure**: Download vulnerable FW (≤30081) → Flash via MiIO OTA → Boot into vulnerable FW → Execute dustbin exploit
- **Risk**: Higher (OTA flash can brick device if interrupted)
- **Persistence**: Permanent after SSH key injection

---

## 3. Firmware Modification Pipeline

### 3.1 Firmware Structure (Viomi V8 - fw 30081)

```
MiOT OTA Image Structure:
┌─────────────────────────────────────────────────────────────┐
│ Header (512 bytes)                                          │
│   - Magic: "MIOT" (4 bytes)                                │
│   - Version: 1 (4 bytes)                                   │
│   - Total Size: ~38MB (4 bytes)                            │
│   - Partition Count: 4 (4 bytes)                           │
│   - Partition Table (4 × 60 bytes = 240 bytes)             │
├─────────────────────────────────────────────────────────────┤
│ Partition 1: Kernel (ZIMAGE)                               │
│   Offset: 512 bytes                                        │
│   Size: 4,194,304 bytes (4 MB)                             │
│   Format: ZIMAGE (gzip-compressed Linux kernel)           │
├─────────────────────────────────────────────────────────────┤
│ Partition 2: Rootfs (SQUASHFS)                             │
│   Offset: 4,194,816 bytes                                  │
│   Size: 33,554,432 bytes (32 MB)                           │
│   Format: SquashFS (read-only compressed filesystem)      │
├─────────────────────────────────────────────────────────────┤
│ Partition 3: DTB (Device Tree Blob)                        │
│   Offset: 37,749,248 bytes                                 │
│   Size: 131,072 bytes (128 KB)                             │
│   Format: DTB (Device Tree Blob)                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Firmware Modification Pipeline

```mermaid
graph LR
    A[Original Firmware] --> B[Parse Firmware]
    B --> C[Extract Partitions]
    C --> D[Inject Dropbear SSH]
    D --> E[Inject su Binary]
    E --> F[Inject Authorized Keys]
    F --> G[Modify Init Scripts]
    G --> H[Repack Rootfs]
    H --> I[Recalculate Checksums]
    I --> J[Rebuild MiOT OTA Image]
    J --> K[Flash via OTA/UART]
```

### 3.3 Firmware Modification Components

| Component | Source | Target Location | Permissions |
|-----------|--------|-----------------|-------------|
| Dropbear SSH | Static binary (statically linked) | `/usr/sbin/dropbear` | 755 |
| su Binary | ToyBox/BusyBox su | `/bin/su` | 755 |
| Authorized Keys | User-generated Ed25519 | `/etc/dropbear/authorized_keys`, `/root/.ssh/authorized_keys` | 600 |
| Dropbear Host Key | Generated on first boot | `/etc/dropbear/dropbear_rsa_host_key` | 600 |
| Init Script | Custom S50dropbear | `/etc/init.d/S50dropbear` | 755 |

---

## 4. Exploitation Procedures

### 4.1 Dustbin Sensor Exploit (Recommended - Lower Risk)

#### Prerequisites
- Physical access to Viomi V8
- USB-UART adapter (FTDI/CP2102/CH340) - 3.3V logic
- Jumper wires / breadboard
- Computer with terminal software (screen/minicom/picocom)

#### Procedure

```bash
# 1. Generate SSH key pair
./xvt injection generate-key --output ~/.ssh/xvt_viomi_v8

# 2. Open device and locate dustbin sensor connector
#    Typically 2-pin connector near dustbin compartment

# 3. Prepare hardware
#    - Connect UART: GND, TX, RX (3.3V logic!)
#    - Prepare jumper for dustbin sensor pins

# 4. Boot with dustbin shorted
#    - Short dustbin sensor pins
#    - Power on device
#    - Keep shorted until recovery shell appears (~10-15 seconds)

# 5. Inject SSH key via UART
xvt inject --ip 10.0.0.103 --vector uart \
  --key ~/.ssh/xvt_viomi_v8.pub --no-dry-run --confirm

# 5. Verify SSH access
ssh -i ~/.ssh/xvt_viomi_v8 root@10.0.0.103
```

#### Verification Commands
```bash
# Once SSH access is established
ssh root@10.0.0.103 "id && uname -a && cat /etc/os-release"
```

### 4.2 OTA Downgrade Exploit (Remote - Higher Risk)

#### Prerequisites
- Network access to device (10.0.0.103)
- Valid MiIO token (default: `ffffffffffffffffffffffffffffffff`)
- Vulnerable firmware image (fw ≤ 30081)
- Stable network connection (wired preferred)

#### Procedure

```bash
# 1. Obtain vulnerable firmware (fw 30081 for Viomi V8)
#    Source: valetudo.cloud, builder.dontvacuum.me, robotinfo.dev

# 2. Patch firmware with SSH keys
xvt firmware patch \
  --input viomi_v8_fw_30081.img \
  --output viomi_v8_patched.img \
  --keys ~/.ssh/xvt_viomi_v8.pub \
  --dry-run  # Verify first
  
# 3. Flash patched firmware via OTA
xvt flash --ip 10.0.0.103 \
  --firmware viomi_v8_patched.img \
  --method ota \
  --no-dry-run --confirm

# 6. Verify SSH access after reboot
ssh -i ~/.ssh/xvt_viomi_v8 root@10.0.0.103
```

### 4.3 UART Flash Fallback (If OTA Fails)

```bash
# 1. Connect UART adapter (115200 8N1)
# 2. Interrupt U-Boot
# 3. Transfer via XMODEM
xvt flash uart --port /dev/ttyUSB0 --firmware viomi_v8_patched.img
```

---

## 5. Post-Exploitation Configuration

### 5.1 Valetudo Configuration Generation

```bash
# Generate Valetudo configuration for Viomi V8
xvt valetudo generate \
  --model viomi.vacuum.v8 \
  --ip 10.0.0.103 \
  --mqtt-host mqtt.local \
  --mqtt-user valetudo \
  --mqtt-password secure_password \
  --output valetudo_config.yaml
```

### 5.2 Generated Valetudo Configuration (Example)

```yaml
# valetudo_config.yaml
mqtt:
  host: "mqtt.local"
  port: 1883
  user: "valetudo"
  password: "secure_password"
  topic_prefix: "valetudo/viomi_v8"
  
vacuum:
  model: "viomi.vacuum.v8"
  name: "Viomi V8"
  ip: "10.0.0.103"
  token: "ffffffffffffffffffffffffffffffff"
  
capabilities:
  - vacuum
  - map
  - zone_cleaning
  - segment_cleaning
  - go_to_location
  - fan_speed_control
  - water_grade_control
  
map:
  enabled: true
  persistence: true
  
valetudo:
  version: "2024.04.0"
  web_interface:
    enabled: true
    port: 80
```

### 5.3 Deploy Valetudo

```bash
# Deploy via SSH
scp valetudo_config.yaml root@10.0.0.103:/etc/valetudo/
ssh root@10.0.0.103 "systemctl restart valetudo"
```

---

## 6. Verification & Testing

### 6.1 Post-Exploitation Verification Checklist

| Check | Command | Expected Result |
|-------|---------|-----------------|
| SSH Access | `ssh root@10.0.0.103 "id"` | `uid=0(root) gid=0(root)` |
| Root Shell | `ssh root@10.0.0.103 "whoami"` | `root` |
| Dropbear Running | `ssh root@10.0.0.103 "ps | grep dropbear"` | Dropbear process visible |
| SSH Keys | `ssh root@10.0.0.103 "cat /etc/dropbear/authorized_keys"` | Your public key present |
| su Binary | `ssh root@10.0.0.103 "which su"` | `/bin/su` |
| Persistence | Reboot device, re-test SSH | SSH still works after reboot |
| Valetudo | `curl http://10.0.0.103` | Valetudo web UI loads |

### 6.2 Automated Verification Script

```bash
#!/bin/bash
# verify_exploit.sh
IP="10.0.0.103"
KEY="~/.ssh/xvt_viomi_v8"

echo "=== XVT Post-Exploitation Verification ==="
echo "Target: $IP"

# Test SSH
if ssh -i ~/.ssh/xvt_viomi_v8 -o ConnectTimeout=5 -o BatchMode=yes root@$IP "echo 'SSH OK'" 2>/dev/null; then
    echo "✅ SSH Access: OK"
else
    echo "❌ SSH Access: FAILED"
    exit 1
fi

# Test root
if ssh -i ~/.ssh/xvt_viomi_v8 root@$IP "id" | grep -q "uid=0(root)"; then
    echo "✅ Root Access: OK"
else
    echo "❌ Root Access: FAILED"
fi

# Test dropbear
if ssh -i ~/.ssh/xvt_viomi_v8 root@$IP "ps | grep -v grep | grep dropbear" >/dev/null; then
    echo "✅ Dropbear Running: OK"
else
    echo "⚠️  Dropbear: Not detected"
fi

# Test persistence (reboot test)
echo "Testing persistence (reboot)..."
ssh root@$IP "reboot" 2>/dev/null || true
sleep 30
if ssh -i ~/.ssh/xvt_viomi_v8 -o ConnectTimeout=10 root@$IP "echo 'Persistence OK'" 2>/dev/null; then
    echo "✅ Persistence: OK (survives reboot)"
else
    echo "❌ Persistence: FAILED (keys not persistent)"
fi

echo "=== Verification Complete ==="
```

---

## 7. Network Topology & Security

### 7.1 Network Isolation Recommendations

```bash
# Recommended: Isolate IoT devices on separate VLAN
# Example VLAN configuration:
# VLAN 10: IoT Devices (10.0.10.0/24)
# - No internet access (block WAN)
# - mDNS relay for discovery
# - MQTT broker on management VLAN
```

### 7.2 Firewall Rules

```bash
# Allow only necessary traffic
# Allow: MQTT (1883/8883) to MQTT broker
# Allow: SSH (22) from management host only
# Allow: HTTP (80) for Valetudo web UI from management VLAN
# Block: All other inbound/outbound
```

### 7.3 MQTT Security

```yaml
# Mosquitto configuration example
listener 1883
listener 8883
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
require_certificate true
use_identity_as_username true

# ACL file
topic readwrite valetudo/#
topic readwrite xvt/#
```

---

## 8. Troubleshooting Guide

### 8.1 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| SSH connection refused | Dropbear not running | Check init script, verify dropbear binary |
| SSH key rejected | Wrong key/permissions | Verify authorized_keys permissions (600), key format |
| Device unreachable | Wrong IP/VLAN | Verify network, ARP table, mDNS |
| OTA flash fails | Wrong token/firmware | Verify token, firmware compatibility |
| Device bricks | Power loss during flash | UART recovery via U-Boot |
| SSH key rejected | Wrong key format | Use Ed25519, OpenSSH format |

### 8.2 Recovery Procedures

#### 8.2.1 UART Recovery (Bricked Device)
```bash
# 1. Connect UART (115200 8N1)
# 2. Power on, interrupt U-Boot (Ctrl+C within 3s)
# 3. TFTP boot recovery image
# 4. Flash recovery firmware
```

#### 8.2.2 SSH Key Recovery
```bash
# If keys lost, re-inject via exploit vector
xvt inject --ip 10.0.0.103 --vector dustbin \
  --key ~/.ssh/new_key.pub --no-dry-run --confirm
```

---

## 9. Maintenance & Updates

### 9.1 Firmware Update Strategy

```bash
# Block automatic OTA updates (prevent losing root)
# Method 1: Block Xiaomi OTA domains
# Method 2: Disable OTA in Valetudo config
# Method 3: Block Xiaomi cloud IPs at firewall

# Manual update procedure:
# 1. Obtain new firmware
# 2. Patch with XVT tools
# 3. Flash via OTA/UART
# 4. Verify root persistence
```

### 9.2 Backup Strategy

```bash
# Backup critical files
ssh root@10.0.0.103 "tar czf /tmp/backup_$(date +%Y%m%d).tar.gz \
  /etc/dropbear/authorized_keys \
  /root/.ssh/authorized_keys \
  /etc/dropbear/dropbear_rsa_host_key \
  /etc/init.d/S50dropbear \
  /etc/valetudo/valetudo_config.yaml"
scp root@10.0.0.103:/tmp/backup_*.tar.gz ~/backups/
```

---

## 10. Appendix

### 10.1 Device Specifications (Viomi V8)

| Specification | Value |
|---------------|-------|
| Model | Viomi V8 / Viomi S7 (viomi.vacuum.v8) |
| Vendor | Viomi (Xiaomi ecosystem) |
| CPU | Quad-core ARM Cortex-A7 |
| RAM | 512 MB DDR3 |
| Flash | 128 MB NAND / 16 MB NOR |
| WiFi | 2.4 GHz 802.11 b/g/n |
| Sensors | LDS LiDAR, IMU, Cliff, Bumper, Dustbin |
| Battery | 5200 mAh Li-ion |
| Runtime | Up to 150 min |
| Suction | 2700 Pa |
| Dimensions | 350 × 350 × 97 mm |
| Weight | 3.6 kg |

### 10.2 Firmware Version History

| Version | Date | Notes |
|---------|------|-------|
| 30081 | 2023-Q2 | Last vulnerable (dustbin exploit works) |
| 30082+ | 2023-Q3+ | Patched dustbin exploit |
| Latest | 2024+ | OTA updates only |

### 10.3 Useful References

| Resource | URL |
|----------|-----|
| Valetudo Documentation | https://valetudo.cloud/docs/ |
| Xiaomi Vacuum Protocol | https://github.com/rytila3/python-miio |
| Xiaomi OTA Protocol | https://github.com/rytila3/python-miio/blob/master/docs/protocol.md |
| Valetudo Configuration | https://valetudo.cloud/docs/configuration/ |
| Xiaomi Vacuum Protocol | https://github.com/rytila3/python-miio/blob/master/docs/protocol.md |

---

## 11. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-09-19 | XVT Team | Initial documentation - Viomi V8 network exemplification |

---

## 12. Disclaimer

> **⚠️ IMPORTANT LEGAL NOTICE**
> 
> This documentation is provided for educational and research purposes only. Modifying device firmware may:
> - Void manufacturer warranty
> - Violate Terms of Service
> - Potentially brick the device permanently
> - Violate local laws or regulations
> 
> **USE AT YOUR OWN RISK.** The authors assume no liability for any damage, loss, or legal consequences resulting from the use of this information.
> 
> **Always:**
> - Obtain proper authorization before testing
> - Have physical access and recovery means ready
> - Backup critical data before proceeding
> - Test in controlled environment first
> - Respect intellectual property and licensing

---

**Document Control**
- **Project:** XVT (Xiaomi Vacuum/Vale Tudo)
- **Protocol:** AES (Ambrósio Engineering System) v4.8+
- **Classification:** Technical Documentation - Internal Use
- **Repository:** https://github.com/linuxkafe/xvt
- **Last Updated:** 2026-09-19

---

*End of Document*