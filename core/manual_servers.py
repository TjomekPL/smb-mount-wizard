import json
import ipaddress
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "smb-mount-wizard"
CONFIG_FILE = CONFIG_DIR / "manual_servers.json"

SOURCE_MANUAL = "manual"
SOURCE_DISCOVERED = "discovered"


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

    entries = []
    for item in data:
        if isinstance(item, str):
            entries.append({"host": item, "source": SOURCE_MANUAL})
        elif isinstance(item, dict) and item.get("host"):
            entries.append({
                "host": item["host"],
                "source": item.get("source", SOURCE_MANUAL),
            })

    return entries


def _save_raw(entries):
    ensure()

    merged = {}
    for e in entries:
        host = e["host"]
        source = e.get("source", SOURCE_DISCOVERED)

        if merged.get(host) == SOURCE_MANUAL:
            continue

        merged[host] = source

    result = [{"host": h, "source": s} for h, s in merged.items()]
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


def add_server(server):
    """
    Adds (or upgrades) a server as manually added - manually added
    servers are never auto-removed by a scan that doesn't find them.
    """
    entries = _load_raw()

    for e in entries:
        if e["host"] == server:
            e["source"] = SOURCE_MANUAL
            _save_raw(entries)
            return

    entries.append({"host": server, "source": SOURCE_MANUAL})
    _save_raw(entries)


def remove_server(server):
    entries = _load_raw()
    entries = [e for e in entries if e["host"] != server]
    _save_raw(entries)


def merge_discovered(hosts):
    """
    Called after a network scan. Adds newly-found hosts (marked as
    'discovered' - these persist across app restarts, showing up in
    Discovery next time it's opened), and removes any PREVIOUSLY
    discovered (not manually added) hosts that are no longer present
    in this scan. Manually added servers are never touched here,
    regardless of whether this scan found them.
    """
    entries = _load_raw()
    hosts_set = set(hosts)

    kept = [
        e for e in entries
        if e["source"] == SOURCE_MANUAL or e["host"] in hosts_set
    ]

    existing_hosts = {e["host"] for e in kept}
    for h in hosts_set:
        if h not in existing_hosts:
            kept.append({"host": h, "source": SOURCE_DISCOVERED})

    _save_raw(kept)
