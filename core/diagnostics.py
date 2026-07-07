import shutil
import subprocess

REQUIRED_TOOLS = [
    {
        "binary": "nmap",
        "package": "nmap",
        "purpose_key": "diagnostics.purpose.nmap",
    },
    {
        "binary": "smbclient",
        "package": "smbclient",
        "purpose_key": "diagnostics.purpose.smbclient",
    },
    {
        "binary": "mount.cifs",
        "package": "cifs-utils",
        "purpose_key": "diagnostics.purpose.cifs_utils",
    },
    {
        "binary": "pkexec",
        "package": "policykit-1",
        "purpose_key": "diagnostics.purpose.pkexec",
    },
]


def check_tool(binary):
    return shutil.which(binary) is not None


def get_dependency_status():
    status = []

    for tool in REQUIRED_TOOLS:
        status.append({
            "binary": tool["binary"],
            "package": tool["package"],
            "purpose_key": tool["purpose_key"],
            "installed": check_tool(tool["binary"]),
        })

    return status


def get_missing_packages():
    return [t["package"] for t in get_dependency_status() if not t["installed"]]


def install_packages(packages):
    """
    Installs the given apt packages through a single pkexec call
    (one admin-password prompt, regardless of how many packages).
    """
    if not packages:
        return {"success": True, "stdout": "Nothing to install.", "stderr": ""}

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
