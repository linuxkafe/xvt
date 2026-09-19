"""Network scanner for discovering Xiaomi vacuum devices."""

import asyncio
import json
import socket
import struct
from dataclasses import dataclass

try:
    import zeroconf
    HAS_ZEROCONF = True
except ImportError:
    HAS_ZEROCONF = False

try:
    import importlib.util
    HAS_SCAPY = importlib.util.find_spec("scapy") is not None
except ImportError:
    HAS_SCAPY = False


@dataclass
class DeviceInfo:
    """Discovered device information."""
    ip: str
    mac: str
    model: str
    firmware: str
    hardware_rev: str
    token: str | None = None

    def to_json(self) -> str:
        return json.dumps(self.__dict__)


class NetworkScanner:
    """Scans network for Xiaomi vacuum devices via ARP, mDNS, SSDP, and MiIO."""

    # Known Xiaomi MAC prefixes (OUI)
    XIAOMI_OUIS = {
        "00:9e:c8", "00:c3:0a", "00:ec:0a", "04:10:6b", "04:7a:0b",
        "04:b1:67", "04:c8:07", "04:cf:8c", "04:d1:3a", "04:e5:98",
        "08:1c:6e", "08:25:25", "0c:1d:af", "0c:98:38", "0c:c6:fd",
        "0c:f3:46", "10:2a:b3", "10:3f:44", "14:49:d4", "14:f6:5a",
        "18:01:f1", "18:59:36", "18:87:40", "18:f0:e4", "1c:cc:d6",
        "20:34:fb", "20:47:da", "20:82:c0", "20:a6:0c", "20:f4:78",
        "24:0a:c4", "24:5e:be", "24:7f:20", "24:a2:c1", "24:ec:99",
        "28:6c:07", "28:c2:dd", "28:f0:76", "2c:aa:8e", "2c:f4:c5",
        "30:8c:fb", "30:de:4b", "34:ce:00", "38:01:95", "38:f9:d3",
        "3c:ec:ef", "40:31:3c", "40:5a:9b", "40:b0:34", "40:f3:08",
        "44:6d:57", "44:e4:d9", "48:02:2a", "48:3f:da", "48:d6:d5",
        "4c:0f:6e", "4c:49:e3", "4c:66:41", "50:1a:a5", "50:c7:bf",
        "54:14:f3", "54:48:10", "54:9f:13", "54:b2:03", "58:2f:42",
        "58:b6:23", "5c:0e:8b", "5c:63:bf", "60:1d:9d", "60:38:e0",
        "1c:90:ff",
        "64:09:80", "64:e4:a5", "68:3e:34", "68:ff:7b", "6c:59:40",
        "6c:83:36", "6c:ad:f8", "70:62:b8", "70:b3:d5", "74:da:88",
        "78:11:dc", "78:44:76", "78:a2:a0", "78:d7:5f", "7c:49:eb",
        "7c:7a:53", "7c:9e:bd", "80:19:34", "80:3f:5d", "84:0d:8e",
        "84:b5:9c", "84:f7:03", "88:3f:4a", "88:ad:43", "8c:4d:4e",
        "8c:85:80", "90:e8:68", "94:b3:4e", "94:e6:f7", "98:48:27",
        "9c:9c:1f", "a0:86:c6", "a4:02:b0", "a4:c1:38", "a8:4e:3f",
        "ac:37:43", "ac:9e:17", "b0:4e:26", "b0:5a:da", "b0:fc:36",
        "b4:3a:28", "b4:5d:50", "b4:7c:9c", "b8:27:eb", "b8:86:87",
        "bc:ff:4d", "c0:3c:59", "c4:01:7a", "c4:1b:82", "c4:93:00",
        "c4:ad:34", "c8:3d:97", "c8:d3:ff", "cc:2d:21", "cc:96:c2",
        "d0:17:c2", "d0:5f:b8", "d4:3d:7e", "d4:61:9d", "d4:f4:be",
        "d8:1f:12", "d8:63:75", "dc:4f:22", "dc:71:44", "e0:63:da",
        "e4:3e:d7", "e4:5f:01", "e4:95:6e", "e8:18:63", "e8:ab:fa",
        "ec:43:f6", "ec:62:60", "f0:27:65", "f0:b4:29", "f4:0f:24",
        "f4:f5:db", "f8:1a:67", "f8:d0:bd", "fc:67:1f",
    }

    def __init__(self, interface: str | None = None, timeout: float = 5.0):
        self.interface = interface
        self.timeout = timeout

    def _is_xiaomi_mac(self, mac: str) -> bool:
        """Check if MAC address belongs to Xiaomi OUI."""
        prefix = mac.lower()[:8]
        return prefix in self.XIAOMI_OUIS

    def scan_arp(self) -> list[DeviceInfo]:
        """Scan local subnet via ARP table (/proc/net/arp fallback)."""
        devices = []
        try:
            with open("/proc/net/arp") as f:
                lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    ip, _, _, mac, _, iface = parts[:6]
                    if self.interface and iface != self.interface:
                        continue
                    if self._is_xiaomi_mac(mac):
                        devices.append(DeviceInfo(
                            ip=ip, mac=mac, model="unknown",
                            firmware="unknown", hardware_rev="unknown"
                        ))
        except Exception:
            pass
        return devices

    async def _mdns_browse(self) -> list[DeviceInfo]:
        """Discover via mDNS (_miio._udp.local)."""
        devices = []
        if not HAS_ZEROCONF:
            return devices

        class Listener(zeroconf.ServiceListener):
            def __init__(self):
                self.found = []

            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if info and info.parsed_addresses():
                    ip = info.parsed_addresses()[0]
                    props = info.properties or {}
                    # MiIO mDNS properties (often empty, model in service name)
                    model_b = props.get(b'model', props.get(b'md', b'unknown'))
                    model = model_b.decode('utf-8', errors='ignore')
                    fw_b = props.get(b'firmware', props.get(b'fv', b'unknown'))
                    firmware = fw_b.decode('utf-8', errors='ignore')
                    hw_b = props.get(b'hw', props.get(b'hv', b'unknown'))
                    hw = hw_b.decode('utf-8', errors='ignore')
                    mac_b = props.get(b'mac', props.get(b'ma', b'unknown'))
                    mac = mac_b.decode('utf-8', errors='ignore')
                    # Extract model from service name: viomi-vacuum-v8_miioXXXXXXXX
                    if model == "unknown":
                        model = name.split('_')[0].split('.')[0]
                    self.found.append(DeviceInfo(
                        ip=ip, mac=mac, model=model, firmware=firmware, hardware_rev=hw
                    ))

            def remove_service(self, zc, type_, name):
                pass
            def update_service(self, zc, type_, name):
                pass

        zc = zeroconf.Zeroconf()
        listener = Listener()
        _ = zeroconf.ServiceBrowser(zc, '_miio._udp.local.', listener=listener)
        await asyncio.sleep(3)
        zc.close()
        return listener.found

    def scan_mdns(self) -> list[DeviceInfo]:
        """Discover via mDNS (_miio._udp.local)."""
        return asyncio.run(self._mdns_browse())

    def scan_ssdp(self) -> list[DeviceInfo]:
        """Discover via SSDP M-SEARCH."""
        devices = []
        msg = (
            b'M-SEARCH * HTTP/1.1\r\n'
            b'HOST: 239.255.255.250:1900\r\n'
            b'MAN: "ssdp:discover"\r\n'
            b'ST: urn:miio-com:device:basic:1\r\n'
            b'MX: 3\r\n\r\n'
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(self.timeout)
        try:
            sock.sendto(msg, ('239.255.255.250', 1900))
            while True:
                data, addr = sock.recvfrom(65507)
                # Parse SSDP response for Xiaomi devices
                text = data.decode(errors='ignore')
                is_xiaomi = ('xiaomi' in text.lower()
                             or 'miio' in text.lower()
                             or 'viomi' in text.lower())
                if is_xiaomi:
                    # Extract IP from response
                    ip = addr[0]
                    devices.append(DeviceInfo(
                        ip=ip, mac="unknown", model="ssdp-discovered",
                        firmware="unknown", hardware_rev="unknown"
                    ))
        except TimeoutError:
            pass
        except Exception:
            pass
        finally:
            sock.close()
        return devices

    def probe_miio(self, ip: str) -> DeviceInfo | None:
        """Probe device via MiIO handshake."""
        try:
            # MiIO handshake packet
            handshake = bytes.fromhex(
                '21310020ffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
            )
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            sock.sendto(handshake, (ip, 54321))
            data, _ = sock.recvfrom(1024)
            sock.close()

            if len(data) >= 32:
                # Parse response
                _device_id = struct.unpack('<I', data[4:8])[0]
                token = data[16:32].hex()
                # Device responded to handshake - it's a MiIO device
                return DeviceInfo(
                    ip=ip, mac="unknown", model="miio-device",
                    firmware="unknown", hardware_rev="unknown", token=token
                )
        except Exception:
            pass
        return None

    def discover_all(self) -> list[DeviceInfo]:
        """Run all discovery methods and deduplicate by MAC/IP."""
        all_devices = {}

        # ARP scan - primary source for MAC addresses
        for d in self.scan_arp():
            key = d.mac.lower()
            all_devices[key] = d

        # mDNS
        for d in self.scan_mdns():
            # Try to find matching ARP entry by IP
            matched = False
            for _existing_key, existing in all_devices.items():
                if existing.ip == d.ip:
                    # Merge mDNS info into ARP entry
                    if d.model != "unknown":
                        existing.model = d.model
                    if d.firmware != "unknown":
                        existing.firmware = d.firmware
                    if d.hardware_rev != "unknown":
                        existing.hardware_rev = d.hardware_rev
                    matched = True
                    break
            if not matched:
                key = d.mac.lower() if d.mac != "unknown" else d.ip
                all_devices[key] = d

        # SSDP
        for d in self.scan_ssdp():
            key = d.ip
            if key not in all_devices:
                all_devices[key] = d

# MiIO probe for all discovered IPs
        ips_to_probe = {d.ip for d in all_devices.values()}
        for ip in ips_to_probe:
            miio_info = self.probe_miio(ip)
            if miio_info:
                # Find existing by IP
                matched = False
                for _existing_key, existing in all_devices.items():
                    if existing.ip == ip:
                        if miio_info.token:
                            existing.token = miio_info.token
                        matched = True
                        break
                if not matched:
                    key = miio_info.mac.lower() if miio_info.mac != "unknown" else ip
                    all_devices[key] = miio_info

        return list(all_devices.values())

