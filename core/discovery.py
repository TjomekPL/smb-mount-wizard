import socket
import subprocess
import concurrent.futures
import ipaddress
from core.runtime import run


def get_local_subnet():
    """
    Wykrywa prefiks /24 aktualnej sieci lokalnej na podstawie adresu IP,
    którego system użyłby do routingu w stronę internetu.
    Nie wysyła żadnych realnych pakietów (UDP connect() tylko ustala
    lokalny adres źródłowy na podstawie tablicy routingu).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    return ".".join(local_ip.split(".")[:3])


def has_smb(ip):
    try:
        ip = str(ip)  # FIX: zawsze string

        p = run(["nmap", "-p", "445", ip])
        stdout, _ = p.communicate(timeout=2)

        return "445/tcp open" in stdout

    except Exception:
        return False


def scan_smb_hosts(ip_range=None):
    if ip_range is None:
        ip_range = get_local_subnet()

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

    try:
        hosts.sort(key=lambda x: ipaddress.ip_address(x))
    except Exception:
        hosts.sort()

    return hosts


def share_accessible_as_guest(host, share):
    """
    Sprawdza (bez roota, bez pkexec) czy dany udział da się odczytać
    anonimowo. Używane, żeby ustalić PRZED wywołaniem 'pkexec mount'
    czy w ogóle trzeba pytać o dane logowania - dzięki temu unikamy
    podwójnego pytania o hasło do konta (raz na próbę-gościa,
    drugi raz na próbę z danymi).
    """
    try:
        result = subprocess.run(
            ["smbclient", f"//{host}/{share}", "-N", "-c", "ls"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_smb_shares(host, username=None, password=None):
    cmd = ["smbclient", "-L", host]

    if username:
        cmd += ["-U", f"{username}%{password}"]
    else:
        cmd += ["-N"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            return ["Login required"]

        shares = []

        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "Disk":
                shares.append(parts[0])

        return shares if shares else ["No shares"]

    except Exception:
        return ["Unavailable"]
