from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame,
    QMessageBox
)

from core.discovery import scan_smb_hosts, get_smb_shares
from core.auth import AuthDialog
from core.mount_engine import mount_share
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
        self.host_input.setPlaceholderText("192.168.0.201 / nas.local")

        self.add_btn = QPushButton("Add server")
        self.add_btn.clicked.connect(self.add_manual_server)

        top.addWidget(self.scan_btn)
        top.addWidget(self.host_input)
        top.addWidget(self.add_btn)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["SMB Hosts / Shares", ""])

        # stała szerokość pierwszej kolumny (żeby IP nie ucinało się przy starcie)
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

        for share in shares:
            share = str(share)

            child = QTreeWidgetItem([share])
            item.addChild(child)

            if share in ["Login required", "Unavailable", "No shares"]:
                continue

            btn = QPushButton("Mount")

            container = QFrame()
            lay = QHBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(btn)

            def on_mount(h=host, s=share):

                # twarda ochrona przed śmieciami z Qt
                if not isinstance(h, str) or not isinstance(s, str):
                    QMessageBox.critical(
                        self,
                        "Invalid data",
                        f"Bad mount args:\n{h}\n{s}"
                    )
                    return

                creds_local = self.auth_cache.get(h)

                if creds_local:
                    result = mount_share(h, s, *creds_local)
                else:
                    result = mount_share(h, s)

                if result.get("success"):
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
