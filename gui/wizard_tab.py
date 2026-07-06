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

from core.discovery import scan_smb_hosts, get_smb_shares, share_accessible_as_guest
from core.auth import AuthDialog
from core.mount_engine import mount_share, get_real_mounts
from core.manual_servers import get_servers, add_server


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

        self.auth_cache = {}

        layout = QVBoxLayout()

        top = QHBoxLayout()

        self.scan_btn = QPushButton("Scan network")
        self.scan_btn.clicked.connect(self.scan)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("adres IP lub nazwa hosta (np. nas.local)")

        self.add_btn = QPushButton("Add server")
        self.add_btn.clicked.connect(self.add_manual_server)

        top.addWidget(self.scan_btn)
        top.addWidget(self.host_input)
        top.addWidget(self.add_btn)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["SMB Hosts / Shares", ""])

        self.tree.setColumnWidth(0, 350)

        self.tree.itemExpanded.connect(self.load_shares)

        layout.addLayout(top)
        layout.addWidget(self.tree)

        self.setLayout(layout)

        self.load_saved_servers()

    def load_saved_servers(self):
        self.tree.clear()

        hosts = get_servers()
        hosts = sorted(list(set(hosts)))

        for host in hosts:
            host = str(host) if host is not None else ""

            item = QTreeWidgetItem([host])
            item.addChild(QTreeWidgetItem(["Loading..."]))
            self.tree.addTopLevelItem(item)

    def scan(self):
        hosts = []

        try:
            hosts.extend(get_servers())
            hosts.extend(scan_smb_hosts())
        except Exception:
            pass

        hosts = sorted(list(set(hosts)))

        self.tree.clear()

        for host in hosts:
            host = str(host) if host is not None else ""

            item = QTreeWidgetItem([host])
            item.addChild(QTreeWidgetItem(["Loading..."]))
            self.tree.addTopLevelItem(item)

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
            shares = ["Unavailable"]

        if shares == ["Login required"]:
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

            child = QTreeWidgetItem([share])
            item.addChild(child)

            if share in ["Login required", "Unavailable", "No shares"]:
                continue

            is_mounted = f"//{host}/{share}".lower() in active_sources

            btn = QPushButton("Mounted" if is_mounted else "Mount")
            btn.setEnabled(not is_mounted)

            persist_checkbox = QCheckBox("Na stałe")
            persist_checkbox.setToolTip(
                "Dodaje trwały wpis w /etc/fstab - udział zamontuje się "
                "sam po restarcie systemu."
            )
            persist_checkbox.setEnabled(not is_mounted)

            container = QFrame()
            lay = QHBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(btn)
            lay.addWidget(persist_checkbox)

            def on_mount(_checked=False, h=host, s=share, btn=btn, persist_cb=persist_checkbox):

                # twarda ochrona przed śmieciami z Qt
                if not isinstance(h, str) or not isinstance(s, str):
                    QMessageBox.critical(
                        self,
                        "Invalid data",
                        f"Bad mount args:\n{h}\n{s}"
                    )
                    return

                creds_local = self.auth_cache.get(h)
                persist = persist_cb.isChecked()

                # Sprawdzamy PRZED wywołaniem pkexec, czy w ogóle trzeba się
                # logować - dzięki temu pkexec (hasło do konta) woła się
                # tylko raz, zamiast dwa razy (próba-gościa + próba z danymi).
                if not creds_local and not share_accessible_as_guest(h, s):
                    dialog = AuthDialog(h)

                    if not dialog.exec():
                        return  # użytkownik anulował logowanie

                    username, password = dialog.get_credentials()
                    creds_local = (username, password)
                    self.auth_cache[h] = creds_local

                if creds_local:
                    result = mount_share(h, s, *creds_local, persist=persist)
                else:
                    result = mount_share(h, s, persist=persist)

                # Fallback na wszelki wypadek: gdyby próba gościa mimo
                # wszystko wywaliła się permission-denied.
                stderr = (result.get("stderr") or "").lower()
                needs_auth = (
                    not result.get("success")
                    and not creds_local
                    and ("permission denied" in stderr or "error(13)" in stderr)
                )

                if needs_auth:
                    dialog = AuthDialog(h)

                    if dialog.exec():
                        username, password = dialog.get_credentials()

                        self.auth_cache[h] = (username, password)
                        result = mount_share(h, s, username, password, persist=persist)

                if result.get("success"):
                    btn.setText("Mounted")
                    btn.setEnabled(False)
                    persist_cb.setEnabled(False)

                    QMessageBox.information(
                        self,
                        "Mounted",
                        f"Mounted:\n\n{result.get('mountpoint')}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Mount failed",
                        result.get("stderr", "Unknown error")
                    )

            btn.clicked.connect(on_mount)

            self.tree.setItemWidget(child, 1, container)
