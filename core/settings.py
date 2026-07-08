import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "smb-mount-wizard"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS = {
    "mount_base": "/mnt",
    "language": "en",
}


def _ensure():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=4))


def get_settings():
    _ensure()

    try:
        data = json.loads(CONFIG_FILE.read_text())
    except Exception:
        data = {}

    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save_settings(settings):
    _ensure()

    CONFIG_FILE.write_text(json.dumps(settings, indent=4))


def get_default_mount_base():
    return get_settings().get("mount_base", DEFAULTS["mount_base"])


def set_default_mount_base(path):
    settings = get_settings()
    settings["mount_base"] = path
    save_settings(settings)
