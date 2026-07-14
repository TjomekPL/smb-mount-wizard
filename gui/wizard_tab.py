# gui/wizard_tab.py
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
from PyQt6.QtCore import Qt

from core.discovery import (
    scan_smb_hosts,
    get_smb_shares,
    share_accessible_as_guest,
    is_port_open,
    open_in_file_manager,
    open_local_path,
    can_browse_share,
    SENTINEL_LOGIN_REQUIRED,
    SENTINEL_UNAVAILABLE,
    SENTINEL_NO_SHARES,
)
from core.auth import AuthDialog
from core.mount_engine import mount_share, get_real_mounts
from core.manual_servers import (
    get_servers,
    add_server,
    remove_server,
    merge_discovered,
    get_server_display_map,
)
from core.tailscale import get_tailscale_hosts
from core.i18n import tr
from core.settings import get_smb_version_override
from core.session_cache import auth_cache, mount_auth_cache
from kde import kwallet

SENTINEL_DISPLAY_KEYS = {
    SENTINEL_LOGIN_REQUIRED: "wizard.login_required",
    SENTINEL_UNAVAILABLE: "wizard.unavailable",
    SENTINEL_NO_SHARES: "wizard.no_shares",
}


def _wallet_key(host, share, display_name=None):
    identity = (display_name or host).lower()
    return f"{identity}::{share}"


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

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

        self.tree.setColumnWidth(0, 350)

        self.tree.itemExpanded.connect(self.load_shares)

        layout.addLayout(top)
        layout.addWidget(self.tree)

        self.setLayout(layout)

        self.load_saved_servers()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_mount_states()

    def refresh_mount_states(self):
        try:
            active_sources = {m["source"].lower() for m in get_real_mounts()}
        except Exception:
            active_sources = set()

        for i in range(self.tree.topLevelItemCount()):
            host_item = self.tree.topLevelItem(i)

            if not host_item.isExpanded():
                continue

            host = host_item.data(0, Qt.ItemDataRole.UserRole)
            if not isinstance(host, str):
                continue

            for j in range(host_item.childCount()):
                child = host_item.child(j)
                container = self.tree.itemWidget(child, 1)

                if container is None or container.layout() is None:
                    continue

                lay = container.layout()
                if lay.count() < 1:
                    continue

                btn = lay.itemAt(0).widget()
                if not isinstance(btn, QPushButton):
                    continue

                share = child.text(0)
                is_mounted = f"//{host}/{share}".lower() in active_sources

                btn.setText(tr("wizard.mounted_button") if is_mounted else tr("wizard.mount_button"))
                btn.setEnabled(not is_mounted)

                if lay.count() > 1:
                    persist_cb = lay.itemAt(1).widget()
                    if isinstance(persist_cb, QCheckBox):
                        persist_cb.setEnabled(not is_mounted)

    def add_host_row(self, host, display_map=None):
        host = str(host) if host is not None else ""
        hostname = (display_map or {}).get(host)
        label = f"{host} ({hostname})" if hostname else host

        item = QTreeWidgetItem([label])
        item.setData(0, Qt.ItemDataRole.UserRole, host)

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

        remove_container = QFrame()
        remove_lay = QHBoxLayout(remove_container)
        remove_lay.setContentsMargins(0, 0, 8, 0)
        remove_lay.addStretch()
        remove_lay.addWidget(remove_btn)

        self.tree.setItemWidget(item, 1, remove_container)

        return item

    def load_saved_servers(self):
        self.tree.clear()

        hosts = get_servers()
        display_map = get_server_display_map()

        for host in hosts:
            self.add_host_row(host, display_map)

    def scan(self):
        warning = None
        scanned = None

        try:
            scanned = scan_smb_hosts()
        except RuntimeError as e:
            warning = str(e)
        except Exception:
            pass

        try:
            tailscale_hosts = get_tailscale_hosts()
        except Exception:
            tailscale_hosts = []

        if scanned is not None or tailscale_hosts:
            combined = (scanned or []) + tailscale_hosts
            try:
                merge_discovered(combined)
            except Exception:
                pass

        hosts = get_servers()
        display_map = get_server_display_map()

        self.tree.clear()

        for host in hosts:
            self.add_host_row(host, display_map)

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

        host = item.data(0, Qt.ItemDataRole.UserRole)

        if not isinstance(host, str) or not host:
            return

        if item.childCount() == 0:
            return

        item.takeChildren()

        creds = auth_cache.get(host)

        # Not cached in this session yet - but if any share on this
        # host is ALREADY mounted (e.g. via a persistent/fstab mount
        # from a previous run), its credentials are sitting in the
        # wallet under this host's identity. Try that before asking
        # the user to type in the same login yet again on every fresh
        # app start, purely to see the share list.
        if not creds:
            display_name = get_server_display_map().get(host)
            wallet_identity = (display_name or host).lower()

            try:
                existing_mounts = get_real_mounts()
            except Exception:
                existing_mounts = []

            for m in existing_mounts:
                source = m.get("source", "")
                if not source.lower().startswith(f"//{host}".lower() + "/"):
                    continue

                existing_share = source.split("/", 3)[-1]
                saved = kwallet.get_credentials(f"{wallet_identity}::{existing_share}")
                if saved:
                    creds = saved
                    break

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

                auth_cache[host] = (username, password)
                shares = get_smb_shares(host, username, password)
        elif creds:
            # The wallet-sourced credentials above worked - cache them
            # for the rest of this session so we don't repeat this
            # lookup on every expand of this host.
            auth_cache[host] = creds

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

            open_btn = QPushButton("\U0001F4C2")  # open folder emoji
            open_btn.setFixedSize(28, 28)
            open_btn.setToolTip(tr("wizard.open_tooltip"))

            def on_open(_checked=False, h=host, s=share):
                try:
                    mounts = get_real_mounts()
                except Exception:
                    mounts = []

                local_target = None
                for m in mounts:
                    if m.get("source", "").lower() == f"//{h}/{s}".lower():
                        local_target = m.get("target")
                        break

                if local_target:
                    if not open_local_path(local_target):
                        QMessageBox.warning(
                            self,
                            tr("wizard.open_failed_title"),
                            tr("wizard.open_failed_message")
                        )
                    return

                creds = mount_auth_cache.get((h, s))

                if not creds:
                    wallet_key = _wallet_key(h, s, display_name=get_server_display_map().get(h))
                    saved = kwallet.get_credentials(wallet_key)
                    if saved:
                        creds = saved

                if not creds:
                    creds = auth_cache.get(h)

                if not creds and not share_accessible_as_guest(h, s):
                    dialog = AuthDialog(h)

                    if not dialog.exec():
                        return

                    creds = dialog.get_credentials()

                username, password = creds if creds else (None, None)

                if not can_browse_share(h, s, username, password):
                    QMessageBox.warning(
                        self,
                        tr("wizard.open_failed_title"),
                        tr("wizard.open_encryption_warning")
                    )
                    return

                if not open_in_file_manager(h, s):
                    QMessageBox.warning(
                        self,
                        tr("wizard.open_failed_title"),
                        tr("wizard.open_failed_message")
                    )

            open_btn.clicked.connect(on_open)

            container = QFrame()
            lay = QHBoxLayout(container)
            lay.setContentsMargins(0, 0, 8, 0)
            lay.addWidget(btn)
            lay.addWidget(persist_checkbox)
            lay.addWidget(open_btn)

            def on_mount(_checked=False, h=host, s=share, btn=btn, persist_cb=persist_checkbox):

                if not isinstance(h, str) or not isinstance(s, str):
                    QMessageBox.critical(
                        self,
                        tr("wizard.invalid_data_title"),
                        tr("wizard.invalid_data_message", h=h, s=s)
                    )
                    return

                btn.setEnabled(False)

                if not is_port_open(h):
                    btn.setEnabled(True)
                    QMessageBox.critical(
                        self,
                        tr("wizard.mount_failed_title"),
                        tr("wizard.host_unreachable", host=h)
                    )
                    return

                mount_key = (h, s)
                display_name = get_server_display_map().get(h)
                wallet_key = _wallet_key(h, s, display_name=display_name)
                persist = persist_cb.isChecked()

                creds_local = mount_auth_cache.get(mount_key)

                if not creds_local:
                    saved = kwallet.get_credentials(wallet_key)
                    if saved:
                        creds_local = saved

                if not creds_local:
                    listing_creds = auth_cache.get(h)
                    if listing_creds:
                        creds_local = listing_creds

                if not creds_local and not share_accessible_as_guest(h, s):
                    dialog = AuthDialog(h)

                    if not dialog.exec():
                        btn.setEnabled(True)
                        return

                    username, password = dialog.get_credentials()
                    creds_local = (username, password)

                smb_version = get_smb_version_override() or None

                if creds_local:
                    result = mount_share(h, s, *creds_local, smb_version=smb_version, persist=persist, display_name=display_name)
                else:
                    result = mount_share(h, s, smb_version=smb_version, persist=persist, display_name=display_name)

                stderr = (result.get("stderr") or "").lower()
                needs_auth = (
                    not result.get("success")
                    and ("permission denied" in stderr or "error(13)" in stderr)
                )

                if needs_auth:
                    prev_username, prev_password = creds_local if creds_local else ("", "")

                    def forget(k=wallet_key, mk=mount_key):
                        kwallet.forget_credentials(k)
                        mount_auth_cache.pop(mk, None)

                    dialog = AuthDialog(
                        h,
                        prefill_username=prev_username,
                        prefill_password=prev_password,
                        on_forget=forget,
                    )

                    if dialog.exec():
                        username, password = dialog.get_credentials()
                        creds_local = (username, password)
                        result = mount_share(h, s, username, password, smb_version=smb_version, persist=persist, display_name=display_name)

                if result.get("success"):
                    btn.setText(tr("wizard.mounted_button"))
                    btn.setEnabled(False)
                    persist_cb.setEnabled(False)

                    if creds_local:
                        mount_auth_cache[mount_key] = creds_local
                        kwallet.save_credentials(wallet_key, *creds_local)

                        if not auth_cache.get(h):
                            auth_cache[h] = creds_local

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
