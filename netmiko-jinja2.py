from jinja2 import Template
from netmiko import ConnectHandler

USER, PASS = "admin", "cisco"

VTY_ACL = """
ip access-list standard VTY-ACCESS
{% for net in vty_permit %}
 permit {{ net.addr }} {{ net.wild }}
{% endfor %}
 deny any log
line vty 0 4
 access-class VTY-ACCESS in vrf-also
"""

SWITCH_TPL = """
vlan {{ vlan_id }}
 name {{ vlan_name }}
{% for p in access_ports %}
interface {{ p }}
 switchport mode access
 switchport access vlan {{ vlan_id }}
 no shutdown
{% endfor %}
""" + VTY_ACL

ROUTER_TPL = """
{% for i in interfaces %}
interface {{ i.name }}
{% if i.vrf %} vrf forwarding {{ i.vrf }}
{% endif %}
{% if i.ip == 'dhcp' %} ip address dhcp
{% else %} ip address {{ i.ip }} {{ i.mask }}
{% endif %}
{% if i.nat %} ip nat {{ i.nat }}
{% endif %}
 no shutdown
{% endfor %}
{% if nat %}
ip access-list standard NAT-LIST
 permit {{ nat.net }} {{ nat.wild }}
ip nat inside source list NAT-LIST interface {{ nat.outside }} vrf {{ vrf }} overload
{% endif %}
router ospf 1 vrf {{ vrf }}
 router-id {{ router_id }}
{% for n in ospf_networks %}
 network {{ n.net }} {{ n.wild }} area 0
{% endfor %}
{% if default_originate %} default-information originate always
{% endif %}
""" + VTY_ACL

VTY_PERMIT = [
    {"addr": "172.31.47.0", "wild": "0.0.0.15"},
    {"addr": "10.30.6.0", "wild": "0.0.1.255"},
]

DEVICES = {
    "S1": {
        "ip": "172.31.47.3", "tpl": SWITCH_TPL,
        "data": {"vlan_id": 101, "vlan_name": "CONTROL-DATA",
                 "access_ports": ["g0/1", "g1/1"],
                 "vty_permit": VTY_PERMIT},
    },
    "R1": {
        "ip": "172.31.47.4", "tpl": ROUTER_TPL,
        "data": {
            "vrf": "control-data", "router_id": "1.1.1.1",
            "interfaces": [
                {"name": "g0/1", "vrf": "control-data", "ip": "10.47.1.1", "mask": "255.255.255.0"},
                {"name": "g0/2", "vrf": "control-data", "ip": "10.47.12.1", "mask": "255.255.255.252"},
                {"name": "loopback0", "vrf": "control-data", "ip": "1.1.1.1", "mask": "255.255.255.255"},
            ],
            "ospf_networks": [
                {"net": "10.47.1.0", "wild": "0.0.0.255"},
                {"net": "10.47.12.0", "wild": "0.0.0.3"},
                {"net": "1.1.1.1", "wild": "0.0.0.0"},
            ],
            "vty_permit": VTY_PERMIT,
        },
    },
    "R2": {
        "ip": "172.31.47.5", "tpl": ROUTER_TPL,
        "data": {
            "vrf": "control-data", "router_id": "2.2.2.2",
            "default_originate": True,
            "interfaces": [
                {"name": "g0/1", "vrf": "control-data", "ip": "10.47.12.2", "mask": "255.255.255.252", "nat": "inside"},
                {"name": "g0/2", "vrf": "control-data", "ip": "10.47.23.1", "mask": "255.255.255.0", "nat": "inside"},
                {"name": "g0/3", "vrf": "control-data", "ip": "dhcp", "nat": "outside"},
                {"name": "loopback0", "vrf": "control-data", "ip": "2.2.2.2", "mask": "255.255.255.255"},
            ],
            "nat": {"net": "10.47.0.0", "wild": "0.0.255.255", "outside": "g0/3"},
            "ospf_networks": [
                {"net": "10.47.12.0", "wild": "0.0.0.3"},
                {"net": "10.47.23.0", "wild": "0.0.0.255"},
                {"net": "2.2.2.2", "wild": "0.0.0.0"},
            ],
            "vty_permit": VTY_PERMIT,
        },
    },
}

for name, d in DEVICES.items():
    template = Template(d["tpl"], trim_blocks=True, lstrip_blocks=True)
    rendered = template.render(**d["data"])
    cmds = [l for l in rendered.splitlines() if l.strip()]
    print(f"== {name}: {len(cmds)} commands ==")
    conn = ConnectHandler(device_type="cisco_ios_telnet", host=d["ip"],
                          username=USER, password=PASS, secret="cisco")
    conn.enable()
    print(conn.send_config_set(cmds, read_timeout=30))
    conn.save_config()
    conn.disconnect()