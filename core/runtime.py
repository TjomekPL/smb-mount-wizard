import subprocess

ACTIVE_PROCESSES = []


def run(cmd, timeout=None):
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    ACTIVE_PROCESSES.append(p)
    return p


def kill_all():
    global ACTIVE_PROCESSES

    for p in ACTIVE_PROCESSES:
        try:
            p.kill()
        except Exception:
            pass

    ACTIVE_PROCESSES = []
