# core/session_cache.py
"""
In-memory-only credential caches for the current running session.
NEVER written to disk - that's what the wallet (kde/kwallet.py) is
for. Kept here at module level, rather than as instance attributes of
WizardTab, specifically so they survive a full tab rebuild - which
happens whenever the display language is changed (MainWindow.build_tabs()
discards the old WizardTab instance and creates a fresh one). A plain
instance attribute would have been wiped out by that; a module-level
dict is shared by whichever WizardTab instance is currently alive.

Cleared only by the process exiting - never persisted, never survives
an app restart, by design.
"""

# host -> (username, password) - used just to LIST shares on a host
# (smbclient -L can't target a single share, so this stays host-scoped).
auth_cache = {}

# (host, share) -> (username, password) - used to actually MOUNT a
# specific share. Kept separate from auth_cache since different shares
# on the same server can need different logins.
mount_auth_cache = {}
