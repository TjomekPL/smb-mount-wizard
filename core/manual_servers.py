import json
import ipaddress
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "smb-mount-wizard"
CONFIG_FILE = CONFIG_DIR / "manual_servers.json"

SOURCE_MANUAL = "manual"
SOURCE_DISCOVERED = "discovered"

# Tailscale's CGNAT range (RFC 6598) - used to tell a Tailscale address
# apart from a regular LAN one when the same device is reachable both
# ways, so we can prefer the (faster, VPN-independent) LAN address.
TAILSCALE_NET = ipaddress.ip_network("100.64.0.0/10")


def _looks_like_tailscale(host):
    try:
        return ipaddress.ip_address(host) in TAILSCALE_NET
    except ValueError:
        return False


def ensure():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text("[]")


def _load_raw():
    ensure()

    try:
        data = json.loads(CONFIG_FILE.read_text())
    except Exception:
        return []

    # Backward compatibility: older versions stored a flat list of
    # plain hostname/IP strings instead of {host, source, hostname}
    # objects. Anything found in that old format is treated as
    # manually added, since we have no way to know otherwise.
    entries = []
    for item in data:
        if isinstance(item, str):
            entries.append({"host": item, "source": SOURCE_MANUAL, "hostname": None})
        elif isinstance(item, dict) and item.get("host"):
            entries.append({
                "host": item["host"],
                "source": item.get("source", SOURCE_MANUAL),
                "hostname": item.get("hostname"),
            })

    return entries


def _save_raw(entries):
    ensure()

    # de-duplicate by host, preferring "manual" if any entry for that
    # host says so, and keeping whichever hostname is non-empty
    merged = {}
    for e in entries:
        host = e["host"]
        source = e.get("source", SOURCE_DISCOVERED)
        hostname = e.get("hostname")

        if host in merged:
            prev = merged[host]
            if prev["source"] == SOURCE_MANUAL:
                source = SOURCE_MANUAL
            if not hostname:
                hostname = prev.get("hostname")

        merged[host] = {"source": source, "hostname": hostname}

    result = [
        {"host": h, "source": v["source"], "hostname": v["hostname"]}
        for h, v in merged.items()
    ]
    CONFIG_FILE.write_text(json.dumps(result, indent=4))


def _sort_hosts(hosts):
    def sort_key(h):
        try:
            return (0, ipaddress.ip_address(h))
        except ValueError:
            return (1, h)

    try:
        return sorted(set(hosts), key=sort_key)
    except Exception:
        return sorted(set(hosts))


def get_servers():
    """
    Returns all known server hostnames/IPs (both manually added and
    previously discovered), sorted numerically by IP address where
    possible (falls back to plain alphabetical sorting for non-IP
    hostnames like 'nas.local').
    """
    hosts = [e["host"] for e in _load_raw()]
    return _sort_hosts(hosts)


def get_server_display_map():
    """
    Returns {host: hostname_or_None} - purely for showing a friendly
    name next to the address in the UI (e.g. "192.168.0.5 (nas)").
    Never used to actually connect to anything; the real address
    stays whatever is returned by get_servers().
    """
    return {e["host"]: e.get("hostname") for e in _load_raw()}


def add_server(server, hostname=None):
    """
    Adds (or upgrades) a server as manually added - manually added
    servers are never auto-removed by a scan that doesn't find them.
    """
    entries = _load_raw()

    for e in entries:
        if e["host"] == server:
            e["source"] = SOURCE_MANUAL
            if hostname:
                e["hostname"] = hostname
            _save_raw(entries)
            return

    entries.append({"host": server, "source": SOURCE_MANUAL, "hostname": hostname})
    _save_raw(entries)


def remove_server(server):
    entries = _load_raw()
    entries = [e for e in entries if e["host"] != server]
    _save_raw(entries)


def _dedupe_by_hostname(entries):
    """
    If the same device is reachable both on the LAN and via Tailscale
    (recognized by having the same hostname), keep only the LAN
    address - faster, and doesn't depend on the VPN being up - instead
    of showing what is obviously the same physical machine twice.
    Entries with no known hostname are left untouched (nothing to
    group them by).
    """
    by_hostname = {}
    result = []

    for e in entries:
        hostname = (e.get("hostname") or "").strip().lower()
        if not hostname:
            result.append(e)
            continue
        by_hostname.setdefault(hostname, []).append(e)

    for group in by_hostname.values():
        if len(group) == 1:
            result.append(group[0])
            continue

        manual = [e for e in group if e.get("source") == SOURCE_MANUAL]
        if manual:
            result.append(manual[0])
            continue

        lan_candidates = [e for e in group if not _looks_like_tailscale(e["host"])]
        result.append(lan_candidates[0] if lan_candidates else group[0])

    return result


def merge_discovered(entries):
    """
    Called after a network scan. 'entries' is a list of either plain
    host strings, or {"host": ..., "hostname": ... or None} dicts
    (accepted for backward compatibility - treated as no hostname).

    Adds newly-found hosts (marked as 'discovered' - these persist
    across app restarts), and removes any PREVIOUSLY discovered (not
    manually added) hosts that are no longer present in this scan.
    Manually added servers are never touched here, regardless of
    whether this scan found them.
    """
    normalized = []
    for e in entries:
        if isinstance(e, str):
            normalized.append({"host": e, "hostname": None})
        else:
            normalized.append({"host": e.get("host"), "hostname": e.get("hostname")})

    existing = _load_raw()
    hosts_set = {e["host"] for e in normalized}
    hostname_by_host = {
        e["host"]: e["hostname"] for e in normalized if e.get("hostname")
    }

    kept = [
        e for e in existing
        if e["source"] == SOURCE_MANUAL or e["host"] in hosts_set
    ]

    # refresh hostname for entries we still have, if this scan found one
    for e in kept:
        if e["host"] in hostname_by_host:
            e["hostname"] = hostname_by_host[e["host"]]

    existing_hosts = {e["host"] for e in kept}
    for e in normalized:
        if e["host"] not in existing_hosts:
            kept.append({
                "host": e["host"],
                "source": SOURCE_DISCOVERED,
                "hostname": e.get("hostname"),
            })

    kept = _dedupe_by_hostname(kept)

    _save_raw(kept)
