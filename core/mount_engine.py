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
        cmd += [
            "-o",
            f"username={username},password={password},vers=3.0"
        ]
    else:
        cmd += ["-o", "guest"]

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


def list_mounts():
    result = subprocess.run(["mount"], capture_output=True, text=True)

    mounts = []

    for line in result.stdout.splitlines():
        if "/mnt/smb" in line:
            mounts.append(line)

    return mounts
