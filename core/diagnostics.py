import os
import shutil
import subprocess

# Tools like mount.cifs commonly live in /sbin or /usr/sbin, which are
# usually NOT on a regular (non-root) user's PATH on Debian, even
# though the binary is genuinely installed and root (via pkexec) can
# run it fine. shutil.which() alone would report these as "missing"
# even right after a successful install - check these directories too.
EXTRA_PATH_DIRS = ["/usr/local/sbin", "/usr/sbin", "/sbin"]


def _resolve_pkexec_packages():
    """
    Different Debian versions name the polkit/pkexec package
    differently: older releases ship it as a single 'policykit-1'
    package, while newer ones split it into 'polkitd' (the daemon)
    and 'pkexec' (the CLI tool) as separate packages. Checks which one
    actually exists on this system instead of hardcoding either.
    """
    try:
        result = subprocess.run(
            ["apt-cache", "show", "policykit-1"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return ["policykit-1"]
    except Exception:
        pass

    return ["polkitd", "pkexec"]


REQUIRED_TOOLS = [
    {
        "binary": "nmap",
        "packages": ["nmap"],
        "purpose_key": "diagnostics.purpose.nmap",
    },
    {
        "binary": "smbclient",
        "packages": ["smbclient"],
        "purpose_key": "diagnostics.purpose.smbclient",
    },
    {
        "binary": "mount.cifs",
        "packages": ["cifs-utils"],
        "purpose_key": "diagnostics.purpose.cifs_utils",
    },
    {
        "binary": "pkexec",
        "packages": None,  # resolved lazily, see "resolver" below
        "resolver": _resolve_pkexec_packages,
        "purpose_key": "diagnostics.purpose.pkexec",
    },
]

# Not strictly required for the app to function - without secret-tool,
# credentials are simply kept in memory for the current session only
# instead of being remembered between runs. Installed by "Install
# missing" too, but only after everything in REQUIRED_TOOLS is
# already satisfied (see get_missing_packages()/diagnostics_tab.py).
RECOMMENDED_TOOLS = [
    {
        "binary": "secret-tool",
        "packages": ["libsecret-tools"],
        "purpose_key": "diagnostics.purpose.secret_tool",
    },
]

# Kept as an alias for compatibility with anything still referring to
# the old name.
OPTIONAL_TOOLS = RECOMMENDED_TOOLS


def check_tool(binary):
    if shutil.which(binary):
        return True

    for d in EXTRA_PATH_DIRS:
        candidate = os.path.join(d, binary)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return True

    return False


def _packages_for(tool):
    resolver = tool.get("resolver")
    if resolver:
        return resolver()
    return tool["packages"]


def get_dependency_status():
    status = []

    for tool in REQUIRED_TOOLS:
        packages = _packages_for(tool)
        status.append({
            "binary": tool["binary"],
            "package": ", ".join(packages),
            "packages": packages,
            "purpose_key": tool["purpose_key"],
            "installed": check_tool(tool["binary"]),
        })

    return status


def get_optional_status():
    status = []

    for tool in OPTIONAL_TOOLS:
        packages = _packages_for(tool)
        status.append({
            "binary": tool["binary"],
            "package": ", ".join(packages),
            "packages": packages,
            "purpose_key": tool["purpose_key"],
            "installed": check_tool(tool["binary"]),
        })

    return status


def get_missing_packages(include_optional=False):
    missing = []

    for t in get_dependency_status():
        if not t["installed"]:
            missing.extend(t["packages"])

    if include_optional:
        for t in get_optional_status():
            if not t["installed"]:
                missing.extend(t["packages"])

    return missing


def get_missing_optional_packages():
    missing = []
    for t in get_optional_status():
        if not t["installed"]:
            missing.extend(t["packages"])
    return missing


def install_packages(packages):
    """
    Installs the given apt packages through a single pkexec call
    (one admin-password prompt, regardless of how many packages).
    """
    if not packages:
        return {"success": True, "stdout": "Nothing to install.", "stderr": ""}

    if shutil.which("pkexec") is None:
        return {
            "success": False,
            "stdout": "",
            "stderr": (
                "pkexec itself is missing, so this app has no way to "
                "elevate privileges to install anything - including "
                "pkexec. This one has to be installed manually first:\n\n"
                "  sudo apt install policykit-1\n"
                "  (or on Debian 13+, where that package was split:)\n"
                "  sudo apt install polkitd pkexec\n\n"
                "Then click 'Install missing' again for the rest."
            ),
        }

    cmd = [
        "pkexec", "env", "DEBIAN_FRONTEND=noninteractive",
        "apt-get", "install", "-y",
    ] + packages

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}
