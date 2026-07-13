import shutil
import subprocess
import os
import tempfile
import ipaddress
import socket
import re
from core.runtime import run

SENTINEL_LOGIN_REQUIRED = "Login required"
SENTINEL_UNAVAILABLE = "Unavailable"
SENTINEL_NO_SHARES = "No shares"


def get_local_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    return ".".join(local_ip.split(".")[:3])


def is_port_open(host, port=445, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


HOST_LINE_RE = re.compile(r'^Host:\s+(\S+)\s+\(([^)]*)\)')


def get_netbios_name(ip, timeout=3):
    """
    Resolves a host's actual NetBIOS/computer name via `nmblookup`.
    Reverse DNS is rarely configured for home-network devices, but an
    SMB server almost always has a NetBIOS name - this is a much more
    reliable source for a display hostname on a LAN. Best effort:
    returns None if nmblookup isn't installed (samba-common-bin) or
    the lookup fails for any reason.
    """
    if shutil.which("nmblookup") is None:
        return None

    try:
        result = subprocess.run(
            ["nmblookup", "-A", ip],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None

        for line in result.stdout.splitlines():
            line = line.strip()
            if "<00>" in line and "<GROUP>" not in line:
                return line.split()[0]
    except Exception:
        return None

    return None


def scan_smb_hosts(ip_range=None):
    """
    Returns a list of {"host": ip, "hostname": name_or_None}.
    """
    if shutil.which("nmap") is None:
        raise RuntimeError(
            "nmap not found - install it from the Diagnostics tab"
        )

    if ip_range is None:
        ip_range = get_local_subnet()

    cidr = f"{ip_range}.0/24"

    results = []

    try:
        p = run(["nmap", "-p", "445", "--open", "-oG", "-", cidr])
        stdout, _ = p.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            p.kill()
        except Exception:
            pass
        return results
    except Exception:
        return results

    for line in stdout.splitlines():
        if not line.startswith("Host:") or "445/open" not in line:
            continue

        match = HOST_LINE_RE.match(line)
        if not match:
            continue

        ip = match.group(1)
        hostname = match.group(2).strip() or None

        results.append({"host": ip, "hostname": hostname})

    try:
        results.sort(key=lambda r: ipaddress.ip_address(r["host"]))
    except Exception:
        results.sort(key=lambda r: r["host"])

    for r in results:
        if not r["hostname"]:
            r["hostname"] = get_netbios_name(r["host"])

    return results


def share_accessible_as_guest(host, share):
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
    auth_file = None

    try:
        cmd = ["smbclient", "-L", host]

        if username:
            auth_content = f"username={username}\npassword={password or ''}\n"

            with tempfile.NamedTemporaryFile(
                "w", suffix=".authfile", delete=False
            ) as f:
                f.write(auth_content)
                auth_file = f.name

            os.chmod(auth_file, 0o600)
            cmd += ["-A", auth_file]
        else:
            cmd += ["-N"]

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

    finally:
        if auth_file:
            try:
                os.remove(auth_file)
            except Exception:
                pass
