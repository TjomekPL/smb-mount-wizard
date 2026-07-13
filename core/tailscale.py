import json
import shutil
import subprocess

from core.discovery import is_port_open


def is_available():
    return shutil.which("tailscale") is not None


def get_tailscale_hosts():
    """
    Returns a list of {"host": ip, "hostname": name_or_None} for
    Tailscale peers that are currently online AND have SMB (port 445)
    reachable. This is folded silently into the regular network scan -
    if tailscale isn't installed, isn't logged in, or the query fails
    for any reason, this just returns an empty list rather than
    surfacing an error (it's an optional extra discovery source, not
    a hard requirement).

    Uses `tailscale status --json`, which already knows every device
    in the tailnet and its 100.x.x.x address - much lighter than
    trying to scan the huge 100.64.0.0/10 range directly.
    """
    print("[tailscale] get_tailscale_hosts() called")

    if not is_available():
        print("[tailscale] 'tailscale' binary not found on PATH")
        return []

    try:
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            print(f"[tailscale] status --json failed: rc={result.returncode} stderr={result.stderr!r}")
            return []

        data = json.loads(result.stdout)
    except Exception as e:
        print(f"[tailscale] status --json exception: {e}")
        return []

    found = []

    peers = data.get("Peer") or {}
    for peer in peers.values():
        name = peer.get("HostName") or peer.get("DNSName") or "?"

        if not peer.get("Online"):
            print(f"[tailscale] skipping {name}: Online={peer.get('Online')!r}")
            continue

        ips = peer.get("TailscaleIPs") or []
        if not ips:
            print(f"[tailscale] skipping {name}: no TailscaleIPs")
            continue

        ip = ips[0]

        hostname = peer.get("HostName")
        if not hostname:
            dns_name = peer.get("DNSName") or ""
            hostname = dns_name.rstrip(".") or None

        port_open = is_port_open(ip, timeout=3)
        print(f"[tailscale] {name} ({ip}): Online=True, port 445 open={port_open}")

        if port_open:
            found.append({"host": ip, "hostname": hostname})

    return found
