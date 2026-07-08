import base64

CREDENTIALS_DIR = "/etc/smb-mount-wizard-credentials"


def _credentials_filename(server, share):
    safe_server = server.replace(".", "_")
    safe_share = share.replace("/", "_")
    return f"{safe_server}_{safe_share}.credentials"


def build_persist_fragment(server, share, mountpoint, uid, gid,
                            username=None, password=None, smb_version="3.0"):
    cred_lines = []
    if username:
        cred_lines.append(f"username={username}")
        if password:
            cred_lines.append(f"password={password}")
    else:
        cred_lines.append("guest")

    cred_content = "\n".join(cred_lines) + "\n"
    cred_b64 = base64.b64encode(cred_content.encode()).decode()

    cred_path = f"{CREDENTIALS_DIR}/{_credentials_filename(server, share)}"

    fstab_opts = ",".join([
        f"credentials={cred_path}",
        f"vers={smb_version}",
        f"uid={uid}",
        f"gid={gid}",
        "file_mode=0600",
        "dir_mode=0700",
        "soft",
        "_netdev",
        "x-systemd.automount",
        "x-systemd.mount-timeout=10",
        "nofail",
    ])

    fstab_line = f"//{server}/{share} {mountpoint} cifs {fstab_opts} 0 0"

    return (
        f'mkdir -p "{CREDENTIALS_DIR}"\n'
        f'echo "{cred_b64}" | base64 -d > "{cred_path}"\n'
        f'chmod 600 "{cred_path}"\n'
        f'chown root:root "{cred_path}"\n'
        f"grep -qxF '{fstab_line}' /etc/fstab || echo '{fstab_line}' >> /etc/fstab\n"
    )


def remove_fstab_line(mountpoint):
    return (
        f'grep -v " {mountpoint} cifs " /etc/fstab > /etc/fstab.tmp '
        f"&& mv /etc/fstab.tmp /etc/fstab\n"
    )
