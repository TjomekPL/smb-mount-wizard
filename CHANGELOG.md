# Changelog

All notable changes to this project are documented in this file.

## [0.14.2]

### Debugging
- `get_tailscale_hosts()` was silently returning early (with zero log
  output) when the `tailscale` binary wasn't found on PATH - added a
  print for that case plus an unconditional entry-point log, so a
  completely silent scan now clearly points at a PATH issue rather
  than looking indistinguishable from "the function was never called".

## [0.14.1]

### Fixed
- Unmounting now automatically falls back to a lazy unmount
  (`umount -l`) if a plain unmount fails - a share whose connection
  died silently (e.g. after suspend/resume) can leave a mount that a
  plain `umount` refuses to touch ("target is busy") even though it's
  actually dead. No more need to drop to a terminal to recover a
  stale mount.

### Debugging
- `core/tailscale.py` now prints per-peer diagnostics (Online status,
  whether an IP was found, whether port 445 responded) to help track
  down why a specific online peer isn't being picked up.

## [0.14.0]

### Added
- Tailscale devices are now discovered automatically alongside the
  regular LAN scan - quietly, with no separate button or toggle. If
  the `tailscale` CLI is present, `tailscale status --json` is queried
  for online peers (much lighter than trying to scan the huge
  100.64.0.0/10 range directly), and each one is checked for an open
  SMB port. If `tailscale` isn't installed, this is skipped silently.
- Discovery now shows a hostname next to the address when one is known
  - from Tailscale's device name, or from nmap's reverse-DNS lookup
  during a LAN scan when one resolves. The address itself (used for
  actually connecting) is unaffected; the hostname is purely a display
  label, stored separately so it can never get mistaken for the real
  host to connect to.

## [0.13.0] - Verified end-to-end on a fresh Debian install

This release bundles a full round of fixes found by installing and
testing the app on a genuinely fresh Debian machine, following its own
README/install.sh from scratch. Everything below was needed to get
from "clone the repo" to "scan, mount, and persist a share" working
without any manual workarounds.

### Fixed
- **Critical: persistent mounts failed with `mount error(22): Invalid
  argument`.** The "Persist" option finished by re-reading /etc/fstab
  and handing every option on that line straight to `mount.cifs` -
  including systemd/boot-only pseudo-options (`_netdev`, `nofail`,
  `x-systemd.automount`, `x-systemd.mount-timeout=10`) that
  `mount.cifs` doesn't understand. Mounting now always uses a direct
  `mount -t cifs ... -o <clean options>` call; the `/etc/fstab` entry
  (with the systemd-specific options) is written separately, purely so
  the share mounts itself automatically on *future* boots.
- `policykit-1` doesn't exist as a package name on Debian 13+ (split
  into `polkitd` + `pkexec`). Diagnostics and `install.sh` now detect
  which naming a system uses and install the right one automatically.
- Diagnostics could show a tool (notably `mount.cifs`) as still
  missing right after successfully installing it, because it only
  checked the regular PATH - cifs-utils installs mount.cifs under
  `/usr/sbin`, which isn't on a normal user's PATH even though root
  (via pkexec) already has it. check_tool() now also checks
  /sbin, /usr/sbin, and /usr/local/sbin.
- "Install missing" gave a raw Python `FileNotFoundError` when
  `pkexec` itself was one of the missing tools - it now explains
  clearly that this one has to be installed manually first (since
  installing anything via pkexec requires pkexec to already exist).
- `install.sh` now checks for (and installs) the Python `venv` module
  up front, instead of copying files to `/opt` first and only then
  failing partway through.
- Server list is now sorted numerically by IP address (e.g.
  `192.168.0.2` before `192.168.0.100`) instead of plain alphabetical
  string sorting, which ordered them incorrectly.
- Diagnostics: widened the Tool column so labels like
  "secret-tool (Recommended)" aren't clipped.

### Changed
- `install.sh` now installs **all** required system packages itself
  (nmap, smbclient, cifs-utils, libsecret-tools, python3-venv, and
  policykit-1/polkitd+pkexec) instead of just setting up the Python
  virtual environment - fixes a real case where a fresh Debian install
  had no `secret-tool`, so credentials silently weren't being
  remembered between sessions.
- `secret-tool` sits in its own "Recommended" tier in Diagnostics
  (shown in orange, not red, when missing). The single "Install
  missing" button installs required tools first; a second click
  installs recommended ones once required tools are satisfied.
- The listing (Discovery) and mounting credential caches now share
  with each other within a session: credentials entered to browse a
  host's shares are tried first when mounting one of them, and
  confirmed-working mount credentials are fed back for browsing other
  shares on that host - no more typing the same login twice in a row
  for the common case where it's the same account.

### Added
- Discovered servers now persist across app restarts, not just
  manually-added ones. Each host's origin (manual vs discovered) is
  tracked: manually added servers are never auto-removed; discovered
  ones stick around after closing the app, but get pruned
  automatically the next time a scan doesn't find them again.

## [0.12.0]

### Added
- Discovered servers now persist across app restarts, not just
  manually-added ones. `core/manual_servers.py` now tracks each host's
  origin (manual vs discovered): manually added servers are never
  auto-removed; discovered ones stick around after closing the app,
  but get pruned automatically the next time a scan doesn't find them
  again.

### Fixed
- Server list is now sorted numerically by IP address (e.g.
  `192.168.0.2` before `192.168.0.100`) instead of plain alphabetical
  sorting, which ordered them incorrectly as strings.
- Diagnostics: widened the Tool column so labels like
  "secret-tool (Recommended)" aren't clipped.

## [0.11.4]

### Changed
- `secret-tool` is back to its own "Recommended" tier in Diagnostics
  (shown in orange, not red, when missing) instead of being lumped in
  with the strictly-required tools. The single "Install missing"
  button now installs required tools first; once those are all
  present, clicking it again installs recommended ones - so it takes
  two clicks if both are missing, matching the distinction between
  "the app won't work without this" and "nice to have".

## [0.11.3]

### Changed
- `secret-tool` (libsecret-tools) moved from the "Optional" section in
  Diagnostics to the main required-tools list, matching install.sh now
  installing it by default. The "Optional" section stays in place
  (empty for now) for future genuinely-optional additions.

## [0.11.2]

### Changed
- `install.sh` now installs all required system packages itself
  (nmap, smbclient, cifs-utils, libsecret-tools, python3-venv, and
  policykit-1/polkitd+pkexec depending on Debian version) instead of
  just checking for the Python venv module and erroring out. Fixes a
  real case where a fresh Debian install had no `secret-tool`, so
  credentials silently weren't being remembered between sessions.
  README updated to note this step is now optional if using
  install.sh.

## [0.11.1]

### Changed
- The listing (Discovery) and mounting credential caches now share
  with each other within a session: credentials entered to browse a
  host's shares are tried first when mounting one of them, and
  credentials confirmed working for a mount are fed back for browsing
  other shares on that host - so you're no longer asked to type in the
  same login twice in a row for the common case where it's the same
  account. If a share genuinely needs different credentials, the
  existing retry/prompt flow still catches that and asks again.

## [0.11.0]

### Fixed
- **Persistent mounts failed with `mount error(22): Invalid argument`.**
  The "Persist" option finished by running `mount "{target}"`, which
  re-reads /etc/fstab and hands every option on that line straight to
  `mount.cifs` - including systemd/boot-only pseudo-options
  (`_netdev`, `nofail`, `x-systemd.automount`,
  `x-systemd.mount-timeout=10`) that `mount.cifs` doesn't understand
  and rejects. The immediate mount now always uses a direct
  `mount -t cifs ... -o <clean options>` call (uid/gid/file_mode/
  dir_mode/soft/vers/credentials only), regardless of whether
  "Persist" is checked. The `/etc/fstab` entry (with the
  systemd-specific options) is still written separately, purely so the
  share mounts itself automatically on *future* boots via systemd -
  it's no longer involved in the mount that happens right now.

## [0.10.5]

### Fixed
- Diagnostics could show a tool (notably `mount.cifs`) as still
  missing right after successfully installing it, because it only
  checked the regular PATH - but cifs-utils installs mount.cifs under
  `/usr/sbin`, which isn't on a normal user's PATH on Debian even
  though the binary works fine (root, via pkexec, already has it on
  PATH). check_tool() now also looks in /sbin, /usr/sbin, and
  /usr/local/sbin.

## [0.10.4]

### Fixed
- "Install missing" in Diagnostics now gives a clear, actionable
  message when `pkexec` itself is one of the missing tools (a raw
  Python `FileNotFoundError` was shown before). This case can't be
  fixed by the button itself - installing anything via pkexec requires
  pkexec to already exist - so the app now says exactly which manual
  command to run instead of failing cryptically.

## [0.10.3]

### Fixed
- `install.sh` now checks upfront whether the Python `venv` module is
  available (Debian ships it as a separate `python3-venv` package)
  and fails fast with a clear message, instead of copying files to
  `/opt` first and only then failing partway through. README updated
  to include `python3-venv` in the required packages.

## [0.10.2]

### Fixed
- `policykit-1` doesn't exist as a package name on newer Debian
  releases (split into `polkitd` + `pkexec`). Diagnostics now detects
  which naming a given system uses via `apt-cache show` and installs
  the right one automatically, instead of hardcoding `policykit-1`
  and failing on newer releases. README updated with the same note
  for the manual install path.

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
