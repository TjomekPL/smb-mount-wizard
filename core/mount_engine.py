import os
import subprocess
from pathlib import Path

BASE_DIR = Path("/mnt/smb-mount-wizard")


def ensure_base_dir():
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def get_mount_path(server, share):

    ensure_base_dir()

    safe_server = server.replace(".", "_")
    safe_share = share.replace("/", "_")

    path = BASE_DIR / safe_server / safe_share

    path.mkdir(parents=True, exist_ok=True)

    return str(path)


def mount_share(server, share, username=None, password=None, smb_version="3.0"):

    target = get_mount_path(server, share)

    creds = ""

    if username:
        creds = (
            f"username={username},"
            f"password={password},"
        )
    else:
        creds = "guest,"

    cmd = [
        "pkexec",
        "mount",
        "-t",
        "cifs",
        f"//{server}/{share}",
        target,
        "-o",
        (
            creds +
            f"vers={smb_version},"
            f"uid={os.getuid()},"
            f"gid={os.getgid()},"
            "iocharset=utf8"
        )
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "mountpoint": target
    }


def unmount_share(path):

    result = subprocess.run(
        ["pkexec", "umount", path],
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def detect_mounts():

    try:
        out = subprocess.check_output(["mount"], text=True)
    except Exception:
        return []

    mounts = []

    for line in out.splitlines():

        if "type cifs" not in line:
            continue

        parts = line.split()

        mounts.append({
            "source": parts[0],
            "target": parts[2]
        })

    return mounts


def test_mount(server, share, username=None, password=None):

    res = mount_share(server, share, username, password)

    if not res["success"]:
        return {
            "ok": False,
            "error": res["stderr"] or res["stdout"]
        }

    # natychmiast unmount testowy
    subprocess.run(["pkexec", "umount", res["mountpoint"]])

    return {"ok": True}


def list_mounts():
    return detect_mounts()

# --- TEMP compatibility layer for GUI ---

def get_real_mounts():
    return detect_mounts()


def list_mounts():
    return detect_mounts()


def unmount_share(path):
    return unmount(path)
