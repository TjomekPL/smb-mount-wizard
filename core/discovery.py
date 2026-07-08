import shutil
import subprocess
import os
import tempfile
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


def is_port_open(host, port=445, timeout=2):
    """
    Quick, bounded reachability check - used right before mounting to
    fail fast with a clear message instead of letting `mount` itself
    block the whole app for a long OS-level TCP timeout (which can be
    tens of seconds to minutes) when the server is simply offline.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def scan_smb_hosts(ip_range=None):
    if shutil.which("nmap") is None:
        raise RuntimeError(
            "nmap not found - install it from the Diagnostics tab"
        )

    if ip_range is None:
        ip_range = get_local_subnet()

    cidr = f"{ip_range}.0/24"

    hosts = []

    try:
        # One nmap process scanning the whole /24 range for the SMB
        # port, instead of spawning a separate nmap process per host
        # (254 processes) - nmap already parallelizes this internally,
        # so a single invocation is both faster and much lighter on
        # the system.
        p = run(["nmap", "-p", "445", "--open", "-oG", "-", cidr])
        stdout, _ = p.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            p.kill()
        except Exception:
            pass
        return hosts
    except Exception:
        return hosts

    for line in stdout.splitlines():
        if not line.startswith("Host:") or "445/open" not in line:
            continue

        parts = line.split()
        if len(parts) >= 2:
            hosts.append(parts[1])

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
    auth_file = None

    try:
        cmd = ["smbclient", "-L", host]

        if username:
            # Use an auth file instead of '-U user%pass': smbclient
            # treats '%' as the user/password separator in -U, so a
            # password containing a literal '%' would be mangled.
            # An auth file also avoids the credentials showing up in
            # plain text via `ps aux` / /proc/<pid>/cmdline while
            # smbclient is running.
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
