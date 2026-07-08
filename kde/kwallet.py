import shutil
import subprocess

# We talk to the freedesktop Secret Service API (via secret-tool) rather
# than a KWallet-specific CLI. On a stock KDE Plasma system, kwalletd
# registers itself as the Secret Service provider, so entries saved here
# show up in KWalletManager under the hood - without depending on
# kwallet-specific command syntax that's harder to verify ahead of time.

SERVICE_ATTR = "smb-mount-wizard"


def available():
    return shutil.which("secret-tool") is not None


def _attrs(key):
    return ["service", SERVICE_ATTR, "entry", key]


def get_credentials(key):
    """
    Returns (username, password) if something is stored for this key,
    or None if nothing is stored, secret-tool is unavailable, or the
    keyring is locked/unreachable.

    'key' should uniquely identify what the credentials are for -
    e.g. "192.168.0.50::Downloads" for a specific host+share pair.
    """
    if not available():
        return None

    try:
        result = subprocess.run(
            ["secret-tool", "lookup"] + _attrs(key),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as e:
        print(f"[kwallet] get_credentials exception for key={key!r}: {e}")
        return None

    if result.returncode != 0:
        # not necessarily an error - just means nothing is stored yet
        return None

    raw = result.stdout.strip("\n")

    if not raw or "\x1f" not in raw:
        return None

    username, _, password = raw.partition("\x1f")
    return username, password


def save_credentials(key, username, password, label=None):
    """
    Saves credentials for this key, OVERWRITING any previous entry.

    IMPORTANT: only call this after a mount has actually succeeded
    with these credentials. Never save on an unverified login attempt -
    that would risk permanently caching a typo.
    """
    if not available():
        print("[kwallet] secret-tool not found - cannot save credentials")
        return False

    payload = f"{username}\x1f{password}"
    label = label or f"SMB Mount Wizard - {key}"

    try:
        result = subprocess.run(
            ["secret-tool", "store", "--label", label] + _attrs(key),
            input=payload,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            print(
                f"[kwallet] save_credentials FAILED for key={key!r}: "
                f"rc={result.returncode} stderr={result.stderr!r} stdout={result.stdout!r}"
            )
        else:
            print(f"[kwallet] saved credentials for key={key!r}")
        return result.returncode == 0
    except Exception as e:
        print(f"[kwallet] save_credentials exception for key={key!r}: {e}")
        return False


def forget_credentials(key):
    """
    Deletes any stored entry for this key - used when the user knows
    the saved credentials are wrong or stale.
    """
    if not available():
        return False

    try:
        result = subprocess.run(
            ["secret-tool", "clear"] + _attrs(key),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            print(
                f"[kwallet] forget_credentials FAILED for key={key!r}: "
                f"rc={result.returncode} stderr={result.stderr!r}"
            )
        return result.returncode == 0
    except Exception as e:
        print(f"[kwallet] forget_credentials exception for key={key!r}: {e}")
        return False
