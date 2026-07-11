# Changelog

All notable changes to this project are documented in this file.

## [0.10.1]

### Fixed
- Mounted tab layout: the Mountpoint column now stretches to fill
  available width (previously disabling column auto-stretch left a
  dead empty area after the last column).
- Disk usage bar restyled - rounded corners, neutral groove
  background, right-aligned text - instead of the plain, blocky
  default Qt look.

## [0.10.0]

### Added
- Disk usage bar in the Mounted tab (used/total space per mounted
  share). Computed in a background thread, not the GUI thread - an
  unresponsive network mount can make `statvfs()` block for a few
  seconds even with 'soft', and the 3-second auto-refresh timer would
  otherwise have turned that into a recurring freeze.

### Fixed
- Regular (non-persistent) mounts now also use the `soft` option,
  matching persistent (fstab) mounts - previously only persistent
  mounts had it, so a session mount to a server that later went
  offline had no bound on how long file operations could hang.

## [0.9.0]

### Added
- `install.sh` / `uninstall.sh` - a proper install path under
  `/opt/smb-mount-wizard`, in its own virtual environment, with a
  desktop menu entry installed automatically. Previously the only
  option was running the app from wherever it happened to be cloned.
- README screenshots (`img/1.png`-`4.png`) for each tab.

## [0.8.1]

### Added
- Custom app icon (`resources/icon.svg`) - a network-share folder
  glyph, wired into the window title bar and the desktop launcher.

## [0.8.0]

### Added
- SMB protocol version override in Settings (default: Auto) - mounts
  no longer hardcode `vers=3.0`; `mount.cifs` auto-negotiates the best
  version with the server unless a specific one is forced, fixing
  compatibility with older NAS devices that don't support SMB 3.0.
- Version number shown in the Settings tab, plus a background
  (non-blocking) check against GitHub tags for a newer release.
- Filled in `README.md` and `requirements.txt` (both were empty).

## [0.7.0]

### Added
- KWallet credential storage (`kde/kwallet.py`, via `secret-tool` / the
  Secret Service API). Mount credentials are cached per `(host, share)`
  pair rather than per host, since different shares on the same server
  can need different logins. Saved only after a mount actually
  succeeds, so a typo is never persisted. A "Forget saved credentials"
  button in the login dialog clears a stale entry.
- `is_port_open()` reachability check before every mount attempt, so
  mounting a currently-offline server fails fast with a clear message
  instead of freezing the app for a long OS-level TCP timeout.
- Optional-tools section in Diagnostics (`secret-tool`).

### Changed
- Network scan now uses a single `nmap` invocation across the whole
  `/24` range instead of spawning 254 separate processes.
- Persistent (fstab) mounts add `soft` and `x-systemd.mount-timeout=10`
  so an offline server can no longer hang Dolphin/the desktop.

### Fixed
- Regular mounts and share listing no longer leak plaintext credentials
  via `ps aux` / `/proc/<pid>/cmdline` (temp credentials files instead
  of inline `-o username=...,password=...` / `-U user%pass`).
- `%` in a password no longer breaks `smbclient` share listing.
- Mounted shares default to `file_mode=0600,dir_mode=0700` (other local
  system users could previously read the contents).
- `core/runtime.py` no longer leaks finished processes into an
  ever-growing list.
- Mount button could get stuck disabled if the login dialog was
  cancelled.

## [0.6.0]

### Added
- Full EN/PL translation system (`core/i18n.py`), switchable live from
  Settings with no restart required.

## [0.5.0]

### Added
- Diagnostics tab: checks for `nmap`, `smbclient`, `cifs-utils`,
  `pkexec`, with one-click installation via a single `pkexec` call.

## [0.4.0]

### Added
- Desktop launcher (`packaging/smb-mount-wizard.desktop`) so the app
  can be started from the KDE app menu without a terminal.
- Remove ("\u2715") button per server in the Discovery list.

## [0.3.0]

### Added
- Persistent mounts: a "Persist" checkbox writes a proper `/etc/fstab`
  entry (credentials in a root-owned file, not inline) so a share
  survives a reboot.
- Configurable default mount location (Settings tab).

## [0.2.0]

### Fixed
- "Bad mount args: False" - a Qt `clicked` signal boolean argument was
  overwriting the intended host parameter in a closure.
- Mounting no longer blocks on an invisible terminal password prompt;
  falls back to a guest mount and only asks for credentials in the GUI
  when actually needed.
- Reduced double `pkexec` (admin password) prompts on a single mount
  down to one, by probing guest access before elevating.
- Automatic local subnet detection instead of a hardcoded `192.168.0.x`
  scan range.

## [0.1.0]

Initial working version: network discovery (scan or manually add a
server), SMB share listing and mounting, a Mounted tab to view/unmount
active shares, and a (then non-functional) Settings tab stub.
