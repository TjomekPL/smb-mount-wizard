from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame
)

from PyQt6.QtCore import Qt

from core.discovery import scan_smb_hosts, get_smb_shares
from core.auth import AuthDialog
from core.mount_engine import mount_share


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

        self.auth_cache = {}

        layout = QVBoxLayout()

        # --- TOP BAR ---
        top = QHBoxLayout()

        self.scan_btn = QPushButton("Scan network")
        self.scan_btn.clicked.connect(self.scan)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.0.201 / nas.tailnet.ts.net")

        self.add_btn = QPushButton("Add server")
        self.add_btn.clicked.connect(self.add_server)

        top.addWidget(self.scan_btn)
        top.addWidget(self.host_input)
        top.addWidget(self.add_btn)

        # --- TREE ---
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["SMB Hosts / Shares"])

        self.tree.itemExpanded.connect(self.load_shares)

        layout.addLayout(top)
        layout.addWidget(self.tree)

        self.setLayout(layout)

    def scan(self):
        self.tree.clear()

        hosts = scan_smb_hosts()

        for host in hosts:
            item = QTreeWidgetItem([host])
            item.addChild(QTreeWidgetItem(["Loading..."]))
            self.tree.addTopLevelItem(item)

    def add_server(self):
        host = self.host_input.text().strip()

        if not host:
            return

        item = QTreeWidgetItem([host])
        item.addChild(QTreeWidgetItem(["Loading..."]))
        self.tree.addTopLevelItem(item)

        self.host_input.clear()

    def load_shares(self, item):
        if item.parent() is not None:
            return

        host = item.text(0)

        # jeśli już załadowane
        if item.childCount() == 0:
            return

        item.takeChildren()

        creds = self.auth_cache.get(host)

        if creds:
            shares = get_smb_shares(host, *creds)
        else:
            shares = get_smb_shares(host)

        # login flow
        if shares == ["Login required"]:
            dialog = AuthDialog(host)

            if dialog.exec():
                username, password = dialog.get_credentials()

                self.auth_cache[host] = (username, password)

                shares = get_smb_shares(host, username, password)

        for share in shares:

            child = QTreeWidgetItem([share])
            item.addChild(child)

            # system messages
            if share in ["Login required", "Unavailable", "No shares"]:
                continue

            btn = QPushButton("Mount")

            container = QFrame()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            layout.addWidget(btn)

            def on_mount(h=host, s=share):
                creds_local = self.auth_cache.get(h)

                if creds_local:
                    mount_share(h, s, *creds_local)
                else:
                    mount_share(h, s)

            btn.clicked.connect(on_mount)

            self.tree.setItemWidget(child, 1, container)
