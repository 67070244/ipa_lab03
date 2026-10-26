import pytest
from netmiko import ConnectHandler

USER, PASS = "admin", "cisco"
DEVICES = {"R1": "172.31.47.4", "R2": "172.31.47.5", "S1": "172.31.47.3"}

EXPECTED = {
    "R1": {"GigabitEthernet0/1": "Connect to PC",
           "GigabitEthernet0/2": "Connect to Gi0/1 of R2"},
    "R2": {"GigabitEthernet0/1": "Connect to Gi0/2 of R1",
           "GigabitEthernet0/2": "Connect to Gi0/1 of S1",
           "GigabitEthernet0/3": "Connect to WAN"},
    "S1": {"GigabitEthernet0/1": "Connect to Gi0/2 of R2",
           "GigabitEthernet1/1": "Connect to PC"},
}


def get_descriptions(ip):
    with ConnectHandler(device_type="cisco_ios_telnet", host=ip,
                        username=USER, password=PASS) as c:
        rows = c.send_command("show interfaces description",
                              use_textfsm=True, read_timeout=30)
    return {r["port"]: r["description"] for r in rows}


@pytest.mark.parametrize("dev,intf,expected", [
    (d, i, e) for d, m in EXPECTED.items() for i, e in m.items()
])
def test_description(dev, intf, expected):
    descs = get_descriptions(DEVICES[dev])
    # `show interfaces description` ย่อชื่อเป็น Gi0/1
    short = intf.replace("GigabitEthernet", "Gi")
    assert descs.get(short) == expected