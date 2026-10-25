import os
import paramiko

USERNAME = "admin"
KEY_FILE = os.path.expanduser("~/.ssh/id_rsa")

devices = {
    "R0": "172.31.47.1",
    "S0": "172.31.47.2",
    "S1": "172.31.47.3",
    "R1": "172.31.47.4",
    "R2": "172.31.47.5",
}

for name, ip in devices.items():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=ip,
            username=USERNAME,
            key_filename=KEY_FILE,
            look_for_keys=False,
            allow_agent=False,
            timeout=10,
        )
        stdin, stdout, stderr = client.exec_command("show ip interface brief")
        print(f"===== {name} ({ip}) connected with public key =====")
        print(stdout.read().decode())

        if name == "R0":
            client.close()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ip,
                username=USERNAME,
                key_filename=KEY_FILE,
                look_for_keys=False,
                allow_agent=False,
                timeout=10,
            )
            stdin, stdout, stderr = client.exec_command("show running-config")
            with open("R0-running-config.txt", "w") as f:
                f.write(stdout.read().decode())
            print("Saved R0-running-config.txt")
    except Exception as e:
        print(f"===== {name} ({ip}) FAILED: {e}")
    finally:
        client.close()