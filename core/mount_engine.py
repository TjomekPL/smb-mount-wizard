# core/mount_engine.py
import os
import re
import base64
import subprocess
import tempfile
from pathlib import Path

from core.settings import get_default_mount_base
from core.fstab import build_persist_fragment, remove_fstab_line


def _sanitize_path_component(s):
    """
    Turns a hostname/label into something safe to use as a single
    directory name - keeps letters, digits, dots, dashes and
    underscores, replaces anything else with '_', and lowercases it
    (so an all-caps NetBIOS name like TORRENTSERVER becomes a normal-
    looking directory name instead of shouting).
    """
    cleaned = re.sub(r'[^A-Za-z0-9_.-]', '_', s).strip('_')
    return cleaned.lower() or "_"


def get_mount_path(server, share, display_name=None):
    if not isinstance(server, str):
        raise ValueError(f"Invalid server: {server}")
    if not isinstance(share, str):
        raise ValueError(f"Invalid share: {share}")

    if display_name:
        safe_server = _sanitize_path_component(display_name)
    else:
        safe_server = server.replace(".", "_")

    safe_share = share.replace("/", "_")

    base = get_default_mount_base()

    return str(Path(base) / safe_server / safe_share)


class _FailedResult:
    def __init__(self, message):
        self.returncode = 1
        self.stdout = ""
        self.stderr = message


def _run_privileged_script(script_body):
    script = "#!/bin/bash\nset -e\n" + script_body

    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
        f.write(script)
        script_path = f.name

    os.chmod(script_path, 0o700)

    try:
        result = subprocess.run(
            ["pkexec", "bash", script_path],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        result = _FailedResult(
            "pkexec not found - install policykit-1 (see Diagnostics tab)"
        )
    except Exception as e:
        result = _FailedResult(str(e))
    finally:
        try:
            os.remove(script_path)
        except Exception:
            pass

    return result


def mount_share(server, share, username=None, password=None,
                 smb_version=None, persist=False, display_name=None):
    target = get_mount_path(server, share, display_name=display_name)

    uid = os.getuid()
    gid = os.getgid()

    script = f'mkdir -p "{target}"\n'

    if persist:
        script += build_persist_fragment(
            server, share, target, uid, gid, username, password, smb_version
        )

    opts = [
        f"uid={uid}",
        f"gid={gid}",
        "file_mode=0600",
        "dir_mode=0700",
        "soft",
    ]

    if smb_version:
        opts.append(f"vers={smb_version}")

    if username:
        cred_lines = [f"username={username}"]
        if password:
            cred_lines.append(f"password={password}")
        cred_content = "\n".join(cred_lines) + "\n"
        cred_b64 = base64.b64encode(cred_content.encode()).decode()

        script += (
            'MOUNT_CRED_TMP=$(mktemp)\n'
            'trap \'rm -f "$MOUNT_CRED_TMP"\' EXIT\n'
            f'echo "{cred_b64}" | base64 -d > "$MOUNT_CRED_TMP"\n'
            'chmod 600 "$MOUNT_CRED_TMP"\n'
        )
        opts.append("credentials=$MOUNT_CRED_TMP")
    else:
        opts.append("guest")

    script += (
        f'mount -t cifs "//{server}/{share}" "{target}" -o {",".join(opts)}\n'
    )

    result = _run_privileged_script(script)

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "mountpoint": target,
    }


def unmount_share(path, remove_fstab=False):
    if not isinstance(path, str):
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Invalid path type: {type(path)}",
        }

    if remove_fstab:
        script = (
            f'umount "{path}" || umount -l "{path}"\n'
        ) + remove_fstab_line(path)
        result = _run_privileged_script(script)
    else:
        try:
            result = subprocess.run(
                ["pkexec", "umount", path],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                result = subprocess.run(
                    ["pkexec", "umount", "-l", path],
                    capture_output=True,
                    text=True,
                )
        except FileNotFoundError:
            result = _FailedResult(
                "pkexec not found - install policykit-1 (see Diagnostics tab)"
            )
        except Exception as e:
            result = _FailedResult(str(e))

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def get_disk_usage(path):
    try:
        stat = os.statvfs(path)
        total = stat.f_frsize * stat.f_blocks
        free = stat.f_frsize * stat.f_bavail
        return total - free, total
    except Exception:
        return None


def format_bytes(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} {unit}"
        n /= 1024


def detect_mounts():
    mounts = []

    try:
        output = subprocess.check_output(["mount"], text=True)

        for line in output.splitlines():
            if " type cifs " not in line:
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            mounts.append(
                {
                    "source": parts[0],
                    "target": parts[2],
                }
            )

    except Exception:
        pass

    return mounts


def get_real_mounts():
    return detect_mounts()


def get_mounts():
    return detect_mounts()


def list_mounts():
    return detect_mounts()


def cleanup_unused_dirs():
    base = Path(get_default_mount_base())
    active = {m["target"] for m in detect_mounts()}

    for root, dirs, files in os.walk(base, topdown=False):
        if str(root) == str(base):
            continue

        if str(root) not in active:
            try:
                os.rmdir(root)
            except Exception:
                pass
