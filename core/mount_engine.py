import os
import base64
import subprocess
import tempfile
from pathlib import Path

from core.settings import get_default_mount_base
from core.fstab import build_persist_fragment, remove_fstab_line


def get_mount_path(server, share):
    if not isinstance(server, str):
        raise ValueError(f"Invalid server: {server}")
    if not isinstance(share, str):
        raise ValueError(f"Invalid share: {share}")

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
                 smb_version="3.0", persist=False):
    target = get_mount_path(server, share)

    uid = os.getuid()
    gid = os.getgid()

    script = f'mkdir -p "{target}"\n'

    if persist:
        # persistent /etc/fstab entry (survives reboot) + credentials
        # in a separate file under /etc, then mount via fstab
        script += build_persist_fragment(
            server, share, target, uid, gid, username, password, smb_version
        )
        script += f'mount "{target}"\n'
    else:
        # regular, session-only mount
        opts = [
            f"vers={smb_version}",
            f"uid={uid}",
            f"gid={gid}",
            "file_mode=0600",
            "dir_mode=0700",
        ]

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
                'CRED_TMP=$(mktemp)\n'
                'trap \'rm -f "$CRED_TMP"\' EXIT\n'
                f'echo "{cred_b64}" | base64 -d > "$CRED_TMP"\n'
                'chmod 600 "$CRED_TMP"\n'
            )
            opts.append("credentials=$CRED_TMP")
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
        script = f'umount "{path}"\n' + remove_fstab_line(path)
        result = _run_privileged_script(script)
    else:
        try:
            result = subprocess.run(
                ["pkexec", "umount", path],
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
