import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "smb-mount-wizard"
CONFIG_FILE = CONFIG_DIR / "manual_servers.json"


def ensure():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text("[]")


def get_servers():
    ensure()

    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return []


def save_servers(servers):
    ensure()

    servers = sorted(list(set(servers)))

    CONFIG_FILE.write_text(
        json.dumps(servers, indent=4)
    )


def add_server(server):
    servers = get_servers()

    if server not in servers:
        servers.append(server)

    save_servers(servers)


def remove_server(server):
    servers = get_servers()
    servers = [s for s in servers if s != server]
    save_servers(servers)
