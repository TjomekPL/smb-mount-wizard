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
        data = json.loads(CONFIG_FILE.read_text())

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_servers(servers):
    ensure()

    # deduplikacja + sortowanie
    servers = sorted(list(set(servers)))

    tmp_file = CONFIG_FILE.with_suffix(".tmp")

    try:
        tmp_file.write_text(
            json.dumps(servers, indent=4)
        )

        tmp_file.replace(CONFIG_FILE)

    except Exception:
        # fallback – nie psuj istniejącego pliku
        if tmp_file.exists():
            tmp_file.unlink()


def add_server(server):
    servers = get_servers()

    if server not in servers:
        servers.append(server)

    save_servers(servers)


def remove_server(server):
    servers = get_servers()

    servers = [
        s for s in servers if s != server
    ]

    save_servers(servers)
