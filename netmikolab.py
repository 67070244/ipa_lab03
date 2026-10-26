from netmiko import ConnectHandler

USER, PASS = "admin", "cisco"
LAB306 = "10.30.6.0"          # wildcard 0.0.1.255 (10.30.6.0/23)
MGMT = "172.31.47.0"          # wildcard 0.0.0.15

def dev(ip):
    return {"device_type": "cisco_ios_telnet", "host": ip,
            "username": USER, "password": PASS, "secret": "cisco"}

acl = [
    "ip access-list standard VTY-ACCESS",
    f"permit {MGMT} 0.0.0.15",
    f"permit {LAB306} 0.0.1.255",
    "deny any log",
    "line vty 0 4",
    "access-class VTY-ACCESS in vrf-also",
]

config = {
    "S1": ("172.31.47.3", [
        "vlan 101", "name CONTROL-DATA", "exit",
        "interface g0/1", "switchport mode access",
        "switchport access vlan 101", "no shutdown", "exit",
        "interface g1/1", "switchport mode access",
        "switchport access vlan 101", "no shutdown", "exit",
    ] + acl),

    "R1": ("172.31.47.4", [
        "interface g0/1", "ip address 10.47.1.1 255.255.255.0", "exit",
        "interface g0/2", "ip address 10.47.12.1 255.255.255.252", "exit",
        "interface loopback0", "vrf forwarding control-data",
        "ip address 1.1.1.1 255.255.255.255", "exit",
        "router ospf 1 vrf control-data", "router-id 1.1.1.1",
        "network 10.47.1.0 0.0.0.255 area 0",
        "network 10.47.12.0 0.0.0.3 area 0",
        "network 1.1.1.1 0.0.0.0 area 0", "exit",
    ] + acl),

    "R2": ("172.31.47.5", [
        "interface g0/2", "ip address 10.47.23.1 255.255.255.0", "exit",
        "interface loopback0", "vrf forwarding control-data",
        "ip address 2.2.2.2 255.255.255.255", "exit",
        "interface g0/3", "vrf forwarding control-data",
        "ip address dhcp", "ip nat outside", "no shutdown", "exit",
        "interface g0/1", "ip nat inside", "exit",
        "interface g0/2", "ip nat inside", "exit",
        "ip access-list standard NAT-LIST",
        "permit 10.47.0.0 0.0.255.255", "exit",
        "ip nat inside source list NAT-LIST interface g0/3 vrf control-data overload",
        "router ospf 1 vrf control-data", "router-id 2.2.2.2",
        "network 10.47.12.0 0.0.0.3 area 0",
        "network 10.47.23.0 0.0.0.255 area 0",
        "network 2.2.2.2 0.0.0.0 area 0",
        "default-information originate always", "exit",
    ] + acl),
}

for name, (ip, cmds) in config.items():
    with ConnectHandler(**dev(ip)) as c:
        c.enable()
        print(f"== {name} ==")
        print(c.send_config_set(cmds, read_timeout=30))
        c.save_config()