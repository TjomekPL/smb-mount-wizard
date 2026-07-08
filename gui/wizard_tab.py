from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame,
    QMessageBox
)

from core.discovery import (
    scan_smb_hosts,
    get_smb_shares,
    share_accessible_as_guest,
    is_port_open,
    SENTINEL_LOGIN_REQUIRED,
    SENTINEL_UNAVAILABLE,
    SENTINEL_NO_SHARES,
)
from core.auth import AuthDialog
from core.mount_engine import mount_share, get_real_mounts
from core.manual_servers import get_servers, add_server, remove_server
from core.i18n import tr
from kde import kwallet

SENTINEL_DISPLAY_KEYS = {
    SENTINEL_LOGIN_REQUIRED: "wizard.login_required",
    SENTINEL_UNAVAILABLE: "wizard.unavailable",
    SENTINEL_NO_SHARES: "wizard.no_shares",
}


def _wallet_key(host, share):
    return f"{host}::{share}"


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

        # Credentials used just to LIST shares on a host (smbclient -L
        # can't target a single share, so this stays host-scoped and
        # in-memory only for the current session).
        self.auth_cache = {}

        # Credentials used to actually MOUNT a specific share. Keyed
        # per (host, share) - different shares on the same server can
        # need different logins, so these must never be shared across
        # shares. Backed by the wallet (kde/kwallet.py) for persistence
        # across sessions; this dict is just this session's fast cache
        # on top of that.
        self.mount_auth_cache = {}

        layout = QVBoxLayout()

        top = QHBoxLayout()

        self.scan_btn = QPushButton(tr("wizard.scan_button"))
        self.scan_btn.clicked.connect(self.scan)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText(tr("wizard.host_placeholder"))

        self.add_btn = QPushButton(tr("wizard.add_button"))
        self.add_btn.clicked.connect(self.add_manual_server)

        top.addWidget(self.scan_btn)
        top.addWidget(self.host_input)
        top.addWidget(self.add_btn)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels([tr("wizard.tree_header"), ""])

        # fixed width for the first column, so IPs don't get clipped at startup
        self.tree.setColumnWidth(0, 350)

        self.tree.itemExpanded.connect(self.load_shares)

        layout.addLayout(top)
        layout.addWidget(self.tree)

        self.setLayout(layout)

        self.load_saved_servers()

    def add_host_row(self, host):
        host = str(host) if host is not None else ""

        item = QTreeWidgetItem([host])
        item.addChild(QTreeWidgetItem([tr("wizard.loading")]))
        self.tree.addTopLevelItem(item)

        remove_btn = QPushButton("\u2715")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setToolTip(tr("wizard.remove_tooltip"))

        def on_remove(_checked=False, h=host, item=item):
            remove_server(h)

            index = self.tree.indexOfTopLevelItem(item)
            if index != -1:
                self.tree.takeTopLevelItem(index)

        remove_btn.clicked.connect(on_remove)

        # wrapper widget so the button sticks to the right edge of the
        # column instead of stretching across its whole width
        remove_container = QFrame()
        remove_lay = QHBoxLayout(remove_container)
        remove_lay.setContentsMargins(0, 0, 4, 0)
        remove_lay.addStretch()
        remove_lay.addWidget(remove_btn)

        self.tree.setItemWidget(item, 1, remove_container)

        return item

    def load_saved_servers(self):
        self.tree.clear()

        hosts = get_servers()
        hosts = sorted(list(set(hosts)))

        for host in hosts:
            self.add_host_row(host)

    def scan(self):
        hosts = []
        warning = None

        try:
            hosts.extend(get_servers())
        except Exception:
            pass

        try:
            hosts.extend(scan_smb_hosts())
        except RuntimeError as e:
            warning = str(e)
        except Exception:
            pass

        hosts = sorted(list(set(hosts)))

        self.tree.clear()

        for host in hosts:
            self.add_host_row(host)

        if warning:
            QMessageBox.warning(self, tr("wizard.scan_warning_title"), warning)

    def add_manual_server(self):
        host = self.host_input.text().strip()

        if not host:
            return

        add_server(host)
        self.host_input.clear()
        self.load_saved_servers()

    def load_shares(self, item):
        if item.parent() is not None:
            return

        host = item.text(0)

        if not isinstance(host, str) or not host:
            return

        if item.childCount() == 0:
            return

        item.takeChildren()

        creds = self.auth_cache.get(host)

        try:
            if creds:
                shares = get_smb_shares(host, *creds)
            else:
                shares = get_smb_shares(host)
        except Exception:
            shares = [SENTINEL_UNAVAILABLE]

        if shares == [SENTINEL_LOGIN_REQUIRED]:
            dialog = AuthDialog(host)

            if dialog.exec():
                username, password = dialog.get_credentials()

                self.auth_cache[host] = (username, password)
                shares = get_smb_shares(host, username, password)

        try:
            active_sources = {m["source"].lower() for m in get_real_mounts()}
        except Exception:
            active_sources = set()

        for share in shares:
            share = str(share)

            display_text = tr(SENTINEL_DISPLAY_KEYS[share]) if share in SENTINEL_DISPLAY_KEYS else share

            child = QTreeWidgetItem([display_text])
            item.addChild(child)

            if share in SENTINEL_DISPLAY_KEYS:
                continue

            is_mounted = f"//{host}/{share}".lower() in active_sources

            btn = QPushButton(tr("wizard.mounted_button") if is_mounted else tr("wizard.mount_button"))
            btn.setEnabled(not is_mounted)

            persist_checkbox = QCheckBox(tr("wizard.persist_checkbox"))
            persist_checkbox.setToolTip(tr("wizard.persist_tooltip"))
            persist_checkbox.setEnabled(not is_mounted)

            container = QFrame()
            lay = QHBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(btn)
            lay.addWidget(persist_checkbox)

            def on_mount(_checked=False, h=host, s=share, btn=btn, persist_cb=persist_checkbox):

                # hard guard against garbage arguments coming from Qt
                if not isinstance(h, str) or not isinstance(s, str):
                    QMessageBox.critical(
                        self,
                        tr("wizard.invalid_data_title"),
                        tr("wizard.invalid_data_message", h=h, s=s)
                    )
                    return

                # disable immediately to guard against a fast double-click
                # firing two overlapping mount attempts for the same share
                btn.setEnabled(False)

                # Fail fast instead of letting `mount` itself block the
                # whole app for a long OS-level TCP timeout when the
                # server is simply offline right now.
                if not is_port_open(h):
                    btn.setEnabled(True)
                    QMessageBox.critical(
                        self,
                        tr("wizard.mount_failed_title"),
                        tr("wizard.host_unreachable", host=h)
                    )
                    return

                mount_key = (h, s)
                wallet_key = _wallet_key(h, s)
                persist = persist_cb.isChecked()

                # 1) already used this session?
                creds_local = self.mount_auth_cache.get(mount_key)

                # 2) saved from a previous session in the wallet?
                if not creds_local:
                    saved = kwallet.get_credentials(wallet_key)
                    if saved:
                        creds_local = saved

                # 3) nothing cached/saved - check BEFORE calling pkexec
                # whether login is needed at all, so pkexec (account
                # password) gets invoked only once instead of twice
                # (guest attempt + real one).
                if not creds_local and not share_accessible_as_guest(h, s):
                    dialog = AuthDialog(h)

                    if not dialog.exec():
                        btn.setEnabled(True)
                        return  # user cancelled the login dialog

                    username, password = dialog.get_credentials()
                    creds_local = (username, password)
                    # NOT saved to the wallet yet - only once the mount
                    # below actually succeeds with these values.

                if creds_local:
                    result = mount_share(h, s, *creds_local, persist=persist)
                else:
                    result = mount_share(h, s, persist=persist)

                # Auth retry: covers both "no creds at all yet" and
                # "we had cached/saved creds, but they turned out to be
                # wrong" (e.g. password changed on the server since).
                stderr = (result.get("stderr") or "").lower()
                needs_auth = (
                    not result.get("success")
                    and ("permission denied" in stderr or "error(13)" in stderr)
                )

                if needs_auth:
                    prev_username, prev_password = creds_local if creds_local else ("", "")

                    def forget(k=wallet_key, mk=mount_key):
                        kwallet.forget_credentials(k)
                        self.mount_auth_cache.pop(mk, None)

                    dialog = AuthDialog(
                        h,
                        prefill_username=prev_username,
                        prefill_password=prev_password,
                        on_forget=forget,
                    )

                    if dialog.exec():
                        username, password = dialog.get_credentials()
                        creds_local = (username, password)
                        result = mount_share(h, s, username, password, persist=persist)

                if result.get("success"):
                    btn.setText(tr("wizard.mounted_button"))
                    btn.setEnabled(False)
                    persist_cb.setEnabled(False)

                    # Only remember credentials once they are CONFIRMED
                    # to work - never persist an unverified attempt.
                    if creds_local:
                        self.mount_auth_cache[mount_key] = creds_local
                        kwallet.save_credentials(wallet_key, *creds_local)

                    QMessageBox.information(
                        self,
                        tr("wizard.mounted_title"),
                        tr("wizard.mounted_message", path=result.get("mountpoint"))
                    )
                else:
                    btn.setEnabled(True)
                    QMessageBox.critical(
                        self,
                        tr("wizard.mount_failed_title"),
                        result.get("stderr") or tr("wizard.unknown_error")
                    )

            btn.clicked.connect(on_mount)

            self.tree.setItemWidget(child, 1, container)
