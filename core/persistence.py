import subprocess


def get_fstab_mounts():
    mounts = []

    try:
        with open("/etc/fstab", "r") as f:
            for line in f.readlines():
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if "cifs" in line:
                    parts = line.split()

                    if len(parts) >= 2:
                        mounts.append({
                            "source": parts[0],
                            "target": parts[1],
                            "type": "fstab"
                        })

    except Exception:
        pass

    return mounts


def get_systemd_mounts():
    mounts = []

    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--type=mount", "--no-pager"],
            capture_output=True,
            text=True
        )

        for line in result.stdout.splitlines():
            if ".mount" in line and "/mnt" in line:
                mounts.append({
                    "unit": line.split()[0],
                    "raw": line,
                    "type": "systemd"
                })

    except Exception:
        pass

    return mounts


def get_persistent_mounts():
    return {
        "fstab": get_fstab_mounts(),
        "systemd": get_systemd_mounts()
    }
