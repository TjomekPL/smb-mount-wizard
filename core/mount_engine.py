import subprocess
import os

MOUNT_BASE = "/mnt/smb"


def ensure_base():
    os.makedirs(MOUNT_BASE, exist_ok=True)


def build_path(host, share):
    return os.path.join(MOUNT_BASE, host, share)


def mount_share(host, share, username=None, password=None):

    ensure_base()

    target = build_path(host, share)
    os.makedirs(target, exist_ok=True)

    source = f"//{host}/{share}"

    cmd = ["mount", "-t", "cifs", source, target]

    if username:
        cmd += ["-o", f"username={username},password={password},vers=3.0"]
    else:
        cmd += ["-o", "guest"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return False, result.stderr

    return True, target


def unmount_share(path):

    result = subprocess.run(["umount", path], capture_output=True, text=True)

    if result.returncode != 0:
        return False, result.stderr

    return True, None


# =========================
# REAL STATE (NOWE)
# =========================

def get_real_mounts():

    result = subprocess.run(
        ["findmnt", "-rn", "-t", "cifs"],
        capture_output=True,
        text=True
    )

    mounts = []

    for line in result.stdout.splitlines():

        parts = line.split()

        if len(parts) >= 2:
            source = parts[0]
            target = parts[1]

            mounts.append({
                "source": source,
                "target": target
            })

    return mounts


def is_mounted(path):

    mounts = get_real_mounts()

    return any(m["target"] == path for m in mounts)
