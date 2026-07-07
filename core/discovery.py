import shutil
import subprocess
import concurrent.futures
import ipaddress
import socket
from core.runtime import run

# Internal control-flow sentinels (NOT user-facing text - the GUI layer
# maps these to translated strings via core.i18n.tr()). Keep these as
# plain English constants so equality checks in the GUI stay stable
# regardless of the selected display language.
SENTINEL_LOGIN_REQUIRED = "Login required"
SENTINEL_UNAVAILABLE = "Unavailable"
SENTINEL_NO_SHARES = "No shares"


def get_local_subnet():
    """
    Detects the /24 prefix of the current local network, based on the
    IP address the system would use to route towards the internet.
    Does not send any real packets (the UDP connect() call only makes
    the kernel resolve a local source address via the routing table).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    return ".".join(local_ip.split(".")[:3])


def has_smb(ip):
    try:
        ip = str(ip)  # always a string

        p = run(["nmap", "-p", "445", ip])
        stdout, _ = p.communicate(timeout=2)

        return "445/tcp open" in stdout

    except Exception:
        return False


def scan_smb_hosts(ip_range=None):
    if shutil.which("nmap") is None:
        raise RuntimeError(
            "nmap not found - install it from the Diagnostics tab"
        )

    if ip_range is None:
        ip_range = get_local_subnet()

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


def share_accessible_as_guest(host, share):
    """
    Checks (without root, without pkexec) whether a share can be read
    anonymously. Used to decide BEFORE calling 'pkexec mount' whether
    login is needed at all - this avoids asking for the account
    password twice (once for a guest attempt, once for the real one).
    """
    try:
        result = subprocess.run(
            ["smbclient", f"//{host}/{share}", "-N", "-c", "ls"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_smb_shares(host, username=None, password=None):
    cmd = ["smbclient", "-L", host]

    if username:
        cmd += ["-U", f"{username}%{password}"]
    else:
        cmd += ["-N"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            return [SENTINEL_LOGIN_REQUIRED]

        shares = []

        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "Disk":
                shares.append(parts[0])

        return shares if shares else [SENTINEL_NO_SHARES]

    except Exception:
        return [SENTINEL_UNAVAILABLE]
