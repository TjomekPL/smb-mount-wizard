import subprocess
import concurrent.futures


def has_smb(ip):

    try:

        result = subprocess.run(

            [
                "nmap",
                "-p",
                "445",
                ip
            ],

            capture_output=True,
            text=True,
            timeout=2

        )

        return "445/tcp open" in result.stdout

    except Exception:

        return False


def scan_smb_hosts(ip_range="192.168.0"):

    hosts = []

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=50) as ex:

        futures = {

            ex.submit(
                has_smb,
                f"{ip_range}.{i}"
            ): i

            for i in range(1, 255)

        }

        for f in concurrent.futures.as_completed(
                futures):

            i = futures[f]

            ip = f"{ip_range}.{i}"

            try:

                if f.result():

                    hosts.append(ip)

            except Exception:

                pass

    return sorted(hosts)


def get_smb_shares(host):

    try:

        result = subprocess.run(

            [
                "smbclient",
                "-L",
                host,
                "-N"
            ],

            capture_output=True,
            text=True,
            timeout=5

        )

        if result.returncode != 0:

            return ["Login required"]

        shares = []

        for line in result.stdout.splitlines():

            parts = line.split()

            if len(parts) >= 2:

                if parts[1] == "Disk":

                    shares.append(parts[0])

        return shares

    except Exception:

        return ["Unavailable"]
