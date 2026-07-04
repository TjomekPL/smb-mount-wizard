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
