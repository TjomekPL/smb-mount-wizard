import subprocess
import concurrent.futures


from core.runtime import run


def has_smb(ip):
    try:
        p = run(["nmap", "-p", "445", ip])

        stdout, _ = p.communicate(timeout=2)

        return "445/tcp open" in stdout

    except Exception:
        return False

def scan_smb_hosts(ip_range="192.168.0"):
    hosts = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = {
            ex.submit(has_smb, f"{ip_range}.{i}"): i
            for i in range(1, 255)
        }

        for f in concurrent.futures.as_completed(futures):
            ip = f"{ip_range}.{futures[f]}"
            try:
                if f.result():
                    hosts.append(ip)
            except Exception:
                pass

    return sorted(hosts)


def get_smb_shares(host):
    """
    Proste SMB listing przez smbclient.
    Jeśli brak dostępu → zwraca 'Login required'
    """

    try:
        result = subprocess.run(
            ["smbclient", "-L", host, "-N"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return ["Login required"]

        shares = []

        for line in result.stdout.splitlines():
            parts = line.split()

            if len(parts) >= 2 and parts[1] == "Disk":
                shares.append(parts[0])

        if not shares:
            return ["No shares"]

        return shares

    except Exception:
        return ["Unavailable"]
