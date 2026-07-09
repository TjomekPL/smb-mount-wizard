# SMB Mount Wizard

A small PyQt6 desktop app for Debian/KDE Plasma to discover and mount
SMB/CIFS network shares, without editing `/etc/fstab` by hand or
digging through Dolphin's network browser every time.


## Features

- **Discovery** - scans the local subnet for SMB hosts (or add one
  manually by IP/hostname), lists shares, mounts with one click.
- **Guest and authenticated mounts** - detects whether a share needs a
  login before asking, and only prompts for credentials when actually
  required.
- **Persistent mounts** - optionally writes a proper `/etc/fstab` entry
  (`x-systemd.automount`, credentials in a root-owned file) so a share
  survives a reboot, instead of requiring a manual re-mount every time.
- **Saved credentials** - remembers login details per (host, share)
  pair via the system keyring (KWallet / Secret Service), only after a
  mount has actually succeeded.
- **Mounted** tab - view and unmount active shares.
- **Diagnostics** tab - checks for required system tools (`nmap`,
  `smbclient`, `cifs-utils`, `pkexec`) and installs anything missing.
- **Settings** - default mount location, SMB protocol version override,
  and a live-switchable EN/PL interface language.


## Requirements

Python dependency (see `requirements.txt`):

pip install -r requirements.txt --break-system-packages

System packages (Debian):

sudo apt install nmap smbclient cifs-utils policykit-1 libsecret-tools

The app's own **Diagnostics** tab can check for and install these
(except `libsecret-tools`, which is optional - without it, credentials
just aren't remembered between sessions).


## Running

python3 main.py

To launch it from the KDE application menu instead of a terminal, see
`packaging/smb-mount-wizard.desktop`.


## Notes

- Mounting and any `/etc/fstab` changes go through `pkexec`, so you'll
  be prompted for your account password (not the share's) once per
  action.
- Mounted shares default to `file_mode=0600,dir_mode=0700` - only the
  mounting user can read the contents locally.
