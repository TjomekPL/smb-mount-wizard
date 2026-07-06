import os
import subprocess
from pathlib import Path


BASE_DIR = Path.home() / ".local/share/smb-mount-wizard/mounts"


def ensure_base_dir():
    BASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def get_mount_path(server, share):

    ensure_base_dir()

    safe_server = server.replace(".", "_")
    safe_share = share.replace("/", "_")

    path = BASE_DIR / safe_server / safe_share

    path.mkdir(
        parents=True,
        exist_ok=True
    )

    return str(path)


def mount_share(
        server,
        share,
        username=None,
        password=None,
        smb_version="3.0"
):

    target = get_mount_path(
        server,
        share
    )

    opts = [

        f"vers={smb_version}",

        f"uid={os.getuid()}",

        f"gid={os.getgid()}"

    ]

    if username:
        opts.append(

            f"username={username}"

        )

    if password:
        opts.append(

            f"password={password}"

        )

    cmd = [

        "pkexec",

        "mount",

        "-t",

        "cifs",

        f"//{server}/{share}",

        target,

        "-o",

        ",".join(opts)

    ]

    result = subprocess.run(

        cmd,

        capture_output=True,

        text=True

    )

    return {

        "success":

            result.returncode == 0,

        "stdout":

            result.stdout,

        "stderr":

            result.stderr,

        "mountpoint":

            target

    }


def unmount_share(path):

    result = subprocess.run(

        [

            "pkexec",

            "umount",

            path

        ],

        capture_output=True,

        text=True

    )

    return {

        "success":

            result.returncode == 0,

        "stdout":

            result.stdout,

        "stderr":

            result.stderr

    }


def detect_mounts():

    mounts = []

    try:

        output = subprocess.check_output(

            ["mount"],

            text=True

        )

        for line in output.splitlines():

            if " type cifs " not in line:
                continue

            parts = line.split()

            mounts.append(

                {

                    "source":

                        parts[0],

                    "target":

                        parts[2]

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

    ensure_base_dir()

    active = {

        m["target"]

        for m in detect_mounts()

    }

    for root, dirs, files in os.walk(

            BASE_DIR,

            topdown=False

    ):

        if root == str(BASE_DIR):
            continue

        if root not in active:

            try:

                os.rmdir(root)

            except Exception:

                pass
