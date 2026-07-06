import subprocess
import concurrent.futures
import ipaddress
from core.runtime import run


def has_smb(ip):
    try:
        p = run(["nmap", "-p", "445", ip])
        stdout, _ = p.communicate(timeout=2)
        return "445/tcp open" in stdout
    except Exception:
        return False


def scan_smb_hosts(ip_range="192.168.0"):
    hosts = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = {
            ex.submit(has_smb, f"{ip_range}.{i}"): i
            for i in range(1, 255)
        }

        for f in concurrent.futures.as_completed(futures):
            ip = f"{ip_range}.{futures[f]}"
            try:
                if f.result():
                    hosts.append(ip)
            except Exception:
                pass

    try:
        hosts.sort(key=lambda x: ipaddress.ip_address(x))
    except Exception:
        hosts.sort()

    return hosts


def get_smb_shares(host, username=None, password=None):
    cmd = ["smbclient", "-L", host]

    if username:
        cmd += ["-U", f"{username}%{password}"]
    else:
        cmd += ["-N"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            return ["Login required"]

        shares = []

        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "Disk":
                shares.append(parts[0])

        return shares if shares else ["No shares"]

    except Exception:
        return ["Unavailable"]
