import os
import base64
import subprocess
import tempfile
from pathlib import Path

from core.settings import get_default_mount_base
from core.fstab import build_persist_fragment, remove_fstab_line


def get_mount_path(server, share):
    # zabezpieczenie przed "False", None itd.
    if not isinstance(server, str):
        raise ValueError(f"Invalid server: {server}")
    if not isinstance(share, str):
        raise ValueError(f"Invalid share: {share}")

    safe_server = server.replace(".", "_")
    safe_share = share.replace("/", "_")

    base = get_default_mount_base()

    return str(Path(base) / safe_server / safe_share)


class _FailedResult:
    """
    Minimal stand-in for subprocess.CompletedProcess, used when the
    command itself can't even be launched (e.g. pkexec missing) so
    calling code can keep reading .returncode/.stdout/.stderr the
    same way regardless of what went wrong.
    """
    def __init__(self, message):
        self.returncode = 1
        self.stdout = ""
        self.stderr = message


def _run_privileged_script(script_body):
    """
    Zapisuje skrypt do tymczasowego pliku i uruchamia go JEDNYM
    wywolaniem pkexec - dzieki temu niezaleznie od tego, ile krokow
    wymaga uprawnien roota (mkdir, mount, zapis fstab), uzytkownik
    jest pytany o haslo administratora tylko raz.
    """
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
                 smb_version=None, persist=False):
    target = get_mount_path(server, share)

    uid = os.getuid()
    gid = os.getgid()

    script = f'mkdir -p "{target}"\n'

    if persist:
        # Write the /etc/fstab entry (with its own separate credentials
        # file and the systemd-specific options like _netdev, nofail,
        # x-systemd.automount) so this share mounts itself automatically
        # on FUTURE boots. This does NOT do the actual mount below -
        # kept deliberately separate, see the comment further down.
        script += build_persist_fragment(
            server, share, target, uid, gid, username, password, smb_version
        )

    # Real, cifs.ko-level mount options for the mount happening RIGHT
    # NOW - used whether or not we're also persisting to fstab. Kept
    # deliberately separate from the fstab-only pseudo-options above
    # (_netdev, nofail, x-systemd.*): those are meaningful to systemd's
    # boot-time fstab processing, but are NOT valid mount.cifs
    # arguments. Mounting via `mount "{target}"` (which re-reads fstab
    # and hands ALL of its options straight to mount.cifs) caused
    # 'mount error(22): Invalid argument' because of exactly that -
    # so the immediate mount always uses this clean option set instead
    # of going through fstab.
    opts = [
        f"uid={uid}",
        f"gid={gid}",
        "file_mode=0600",
        "dir_mode=0700",
        "soft",
    ]

    if smb_version:
        # explicit override - otherwise omit 'vers=' entirely and
        # let mount.cifs auto-negotiate the best protocol version
        # with the server (needed for older NAS devices that don't
        # support SMB 3.0)
        opts.append(f"vers={smb_version}")

    if username:
        # Write credentials to a throwaway temp file instead of
        # embedding them inline in '-o username=...,password=...'.
        # Inline credentials show up in plain text in `ps aux` /
        # /proc/<pid>/cmdline for the duration of the mount call,
        # readable by ANY local user on the machine - not just the
        # one doing the mounting. The temp file is root-owned,
        # chmod 600, and removed immediately after (via trap, so
        # it's cleaned up even if the mount command itself fails).
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
        # Try a normal unmount first, then fall back to a lazy one
        # (-l) if that fails - a share whose connection died silently
        # (e.g. after suspend/resume) can leave a mount that a plain
        # `umount` refuses to touch ("target is busy") even though
        # it's actually dead. Lazy unmount detaches it immediately
        # regardless.
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
    """
    Returns (used_bytes, total_bytes) for the filesystem mounted at
    path, or None if it can't be determined right now (share went
    offline, stale mount, etc). Note: on an unresponsive network
    mount this call CAN block for a few seconds even with the 'soft'
    mount option - callers should run this off the GUI thread.
    """
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
