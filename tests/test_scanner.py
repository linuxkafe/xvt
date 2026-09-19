"""Tests for XVT scanner module."""

from src.xvt.scanner import DeviceInfo, NetworkScanner


def test_device_info_json():
    device = DeviceInfo(
        ip="192.168.1.100",
        mac="AA:BB:CC:DD:EE:FF",
        model="rockrobo.vacuum.s5",
        firmware="1.2.3_4567",
        hardware_rev="S5",
        token="deadbeefdeadbeefdeadbeefdeadbeef",
    )
    json_str = device.to_json()
    assert '"ip": "192.168.1.100"' in json_str
    assert '"model": "rockrobo.vacuum.s5"' in json_str


def test_xiaomi_oui_detection():
    scanner = NetworkScanner()
    # Known Xiaomi OUIs
    assert scanner._is_xiaomi_mac("28:6c:07:12:34:56")
    assert scanner._is_xiaomi_mac("9c:9c:1f:12:34:56")
    assert scanner._is_xiaomi_mac("1c:90:ff:12:34:56")
    assert scanner._is_xiaomi_mac("60:1d:9d:12:34:56")
    assert scanner._is_xiaomi_mac("58:b6:23:12:34:56")
    # Non-Xiaomi
    assert not scanner._is_xiaomi_mac("00:11:22:33:44:55")
    assert not scanner._is_xiaomi_mac("aa:bb:cc:dd:ee:ff")


def test_scan_arp_returns_list():
    scanner = NetworkScanner()
    result = scanner.scan_arp()
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, DeviceInfo)


def test_scan_mdns_returns_list():
    scanner = NetworkScanner()
    result = scanner.scan_mdns()
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, DeviceInfo)


def test_probe_miio_returns_deviceinfo_or_none():
    scanner = NetworkScanner()
    # Test with a non-existent IP (should return None quickly)
    result = scanner.probe_miio("10.255.255.254")
    assert result is None or isinstance(result, DeviceInfo)


def test_discover_all_returns_list():
    scanner = NetworkScanner(timeout=1.0)
    result = scanner.discover_all()
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, DeviceInfo)
        assert item.ip
        assert item.mac


def test_scan_ssdp_returns_list():
    scanner = NetworkScanner(timeout=1.0)
    result = scanner.scan_ssdp()
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, DeviceInfo)


def test_device_info_equality():
    d1 = DeviceInfo(
        ip="1.2.3.4", mac="aa:bb:cc:dd:ee:ff",
        model="test", firmware="1.0", hardware_rev="hw"
    )
    d2 = DeviceInfo(
        ip="1.2.3.4", mac="aa:bb:cc:dd:ee:ff",
        model="test", firmware="1.0", hardware_rev="hw"
    )
    d3 = DeviceInfo(
        ip="5.6.7.8", mac="aa:bb:cc:dd:ee:ff",
        model="test", firmware="1.0", hardware_rev="hw"
    )
    assert d1 == d2
    assert d1 != d3


def test_device_info_with_token():
    d = DeviceInfo(
        ip="1.2.3.4", mac="aa:bb:cc:dd:ee:ff",
        model="test", firmware="1.0", hardware_rev="hw",
        token="abc123"
    )
    assert d.token == "abc123"
    json_str = d.to_json()
    assert "abc123" in json_str
