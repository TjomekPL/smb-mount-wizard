import subprocess
import threading
import os
import signal

ACTIVE_PROCESSES = []
LOCK = threading.Lock()


def run(cmd, timeout=None):
    """
    Runs a process and registers it for cleanup.
    """

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid  # KEY: separate process group
    )

    with LOCK:
        # opportunistically drop already-finished processes so this
        # list doesn't grow without bound across many scans
        ACTIVE_PROCESSES[:] = [proc for proc in ACTIVE_PROCESSES if proc.poll() is None]
        ACTIVE_PROCESSES.append(p)

    return p


def kill_all():
    """
    Kills all tracked processes and their process groups.
    """

    global ACTIVE_PROCESSES

    with LOCK:
        for p in ACTIVE_PROCESSES:
            try:
                # kill the whole process group
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                pass

        ACTIVE_PROCESSES.clear()
