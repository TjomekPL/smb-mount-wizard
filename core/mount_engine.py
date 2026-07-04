import subprocess
import os

# USER SPACE (FIX: no /mnt permission issues)
MOUNT_BASE = os.path.expanduser("~/mnt/smb-wizard")


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
        cmd += [
            "-o",
            f"username={username},password={password},vers=3.0"
        ]
    else:
        cmd += ["-o", "guest,vers=3.0"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return False, result.stderr

    return True, target


def unmount_share(path):

    cmd = ["umount", path]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return False, result.stderr

    return True, None


# =========================
# REAL SYSTEM STATE
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

    for m in get_real_mounts():
        if m["target"] == path:
            return True

    return False


# =========================
# TEST MOUNT (SANDBOX)
# =========================

def test_mount(host="127.0.0.1", share="test"):

    ensure_base()

    target = os.path.join(MOUNT_BASE, "_test")

    os.makedirs(target, exist_ok=True)

    source = f"//{host}/{share}"

    cmd = [
        "mount",
        "-t",
        "cifs",
        source,
        target,
        "-o",
        "guest,vers=3.0"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return {
            "mounted": False,
            "target": target,
            "error": result.stderr
        }

    return {
        "mounted": True,
        "target": target,
        "error": None
    }
