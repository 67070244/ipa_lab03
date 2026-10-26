import re
from netmiko import ConnectHandler

USER, PASS = "admin", "cisco"
ROUTERS = {"R1": "172.31.47.4", "R2": "172.31.47.5"}

BRIEF_RE = re.compile(
    r"^(\S+)\s+(\S+)\s+\S+\s+\S+\s+(up|down|administratively down)\s+(up|down)\s*$",
    re.MULTILINE,
)
UPTIME_RE = re.compile(r"uptime is (.+)")
LOG_RE = re.compile(
    r"^(\*?\w{3}\s+\d+\s+[\d:.]+):\s+%LINEPROTO-5-UPDOWN: Line protocol on "
    r"Interface (\S+), changed state to up",
    re.MULTILINE,
)

for name, ip in ROUTERS.items():
    with ConnectHandler(device_type="cisco_ios_telnet", host=ip,
                        username=USER, password=PASS) as conn:
        brief = conn.send_command("show ip interface brief", read_timeout=30)
        ver = conn.send_command("show version | include uptime", read_timeout=30)
        log = conn.send_command("show logging", read_timeout=30)

        r_up = UPTIME_RE.search(ver)
        up_since = {}
        for m in LOG_RE.finditer(log):
            up_since[m.group(2)] = m.group(1)  # เก็บครั้งล่าสุด

        print(f"===== {name} ({ip}) | router uptime: "
              f"{r_up.group(1) if r_up else 'n/a'} =====")
        for m in BRIEF_RE.finditer(brief):
            intf, addr, status, proto = m.groups()
            if intf.startswith("NVI"):
                continue
            if status == "up" and proto == "up":
                print(f"{intf:<22} {addr:<15} up since: "
                      f"{up_since.get(intf, 'no log entry')}")