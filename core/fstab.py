import base64

CREDENTIALS_DIR = "/etc/smb-mount-wizard-credentials"


def _credentials_filename(server, share):
    safe_server = server.replace(".", "_")
    safe_share = share.replace("/", "_")
    return f"{safe_server}_{safe_share}.credentials"


def build_persist_fragment(server, share, mountpoint, uid, gid,
                            username=None, password=None, smb_version=None):
    """
    Builds a shell script fragment (executed as root via pkexec) that:
      - writes the login credentials to a file under /etc (root:root,
        chmod 600) instead of keeping them in plain text in /etc/fstab
        (which every user can read)
      - appends a line to /etc/fstab, if it isn't already there

    Does not do the actual mounting - that's mount_engine.mount_share,
    which combines this fragment with a 'mount' command in a SINGLE
    pkexec call, so it doesn't multiply admin-password prompts.
    """
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

    fstab_opt_list = [
        f"credentials={cred_path}",
        f"uid={uid}",
        f"gid={gid}",
        "file_mode=0600",
        "dir_mode=0700",
        "soft",
        "_netdev",
        "x-systemd.automount",
        "x-systemd.mount-timeout=10",
        "nofail",
    ]

    if smb_version:
        # explicit override - otherwise omit 'vers=' and let mount.cifs
        # auto-negotiate the best protocol version with the server
        # (needed for older NAS devices that don't support SMB 3.0)
        fstab_opt_list.insert(0, f"vers={smb_version}")

    fstab_opts = ",".join(fstab_opt_list)

    fstab_line = f"//{server}/{share} {mountpoint} cifs {fstab_opts} 0 0"

    return (
        f'mkdir -p "{CREDENTIALS_DIR}"\n'
        f'echo "{cred_b64}" | base64 -d > "{cred_path}"\n'
        f'chmod 600 "{cred_path}"\n'
        f'chown root:root "{cred_path}"\n'
        f"grep -qxF '{fstab_line}' /etc/fstab || echo '{fstab_line}' >> /etc/fstab\n"
    )


def remove_fstab_line(mountpoint):
    """
    Returns a script fragment that removes the fstab line for this
    mountpoint (matched by the target path). The credentials file is
    intentionally left behind - it's harmless without a matching
    fstab entry.
    """
    return (
        f'grep -v " {mountpoint} cifs " /etc/fstab > /etc/fstab.tmp '
        f"&& mv /etc/fstab.tmp /etc/fstab\n"
    )
