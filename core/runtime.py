import subprocess
import threading
import os
import signal

ACTIVE_PROCESSES = []
LOCK = threading.Lock()


def run(cmd, timeout=None):
    """
    Uruchamia proces i rejestruje go do cleanupu.
    """

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid  # KLUCZOWE: osobna grupa procesów
    )

    with LOCK:
        ACTIVE_PROCESSES.append(p)

    return p


def kill_all():
    """
    Zabija wszystkie procesy + ich grupy.
    """

    global ACTIVE_PROCESSES

    with LOCK:
        for p in ACTIVE_PROCESSES:
            try:
                # zabija całą grupę procesu
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                pass

        ACTIVE_PROCESSES.clear()
