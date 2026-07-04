from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QFrame,
)

from PyQt6.QtCore import Qt

from core.discovery import scan_smb_hosts, get_smb_shares
from core.auth import AuthDialog
from core.mount_engine import mount_share
from core.manual_servers import (
    get_servers,
    add_server,
    remove_server,
)


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

        self.auth_cache = {}

        layout = QVBoxLayout()

        # ---------------- TOP BAR ----------------
        top = QHBoxLayout()

        self.scan_btn = QPushButton("Scan network")
        self.scan_btn.clicked.connect(self.scan)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText(
            "192.168.0.201 / nas.tailnet.ts.net"
        )

        self.add_btn = QPushButton("Add server")
        self.add_btn.clicked.connect(self.add_manual_server)

        self.remove_btn = QPushButton("Remove server")
        self.remove_btn.clicked.connect(self.remove_manual_server)

        top.addWidget(self.scan_btn)
        top.addWidget(self.host_input)
        top.addWidget(self.add_btn)
        top.addWidget(self.remove_btn)

        # ---------------- TREE ----------------
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["SMB Hosts / Shares"])

        self.tree.setSelectionMode(
            QTreeWidget.SelectionMode.SingleSelection
        )

        self.tree.itemExpanded.connect(self.load_shares)

        layout.addLayout(top)
        layout.addWidget(self.tree)

        self.setLayout(layout)

        self.load_saved_servers()

    # ---------------- LOAD ROOT ----------------
    def load_saved_servers(self):

        self.tree.clear()

        hosts = sorted(set(get_servers()))

        for host in hosts:

            item = QTreeWidgetItem([host])
            item.setData(0, Qt.ItemDataRole.UserRole, "manual")

            item.addChild(QTreeWidgetItem(["Loading..."]))

            self.tree.addTopLevelItem(item)

    # ---------------- SCAN ----------------
    def scan(self):
        self.load_saved_servers()

    # ---------------- ADD SERVER ----------------
    def add_manual_server(self):

        host = self.host_input.text().strip()

        if not host:
            return

        add_server(host)

        self.host_input.clear()

        self.load_saved_servers()

    # ---------------- REMOVE SERVER (FIXED) ----------------
    def remove_manual_server(self):

        selected = self.tree.selectedItems()

        if not selected:
            return

        item = selected[0]
        host = item.text(0)

        remove_server(host)

        self.load_saved_servers()

    # ---------------- LOAD SHARES ----------------
    def load_shares(self, item):

        if item.parent() is not None:
            return

        host = item.text(0)

        if item.childCount() == 0:
            return

        item.takeChildren()

        creds = self.auth_cache.get(host)

        if creds:
            shares = get_smb_shares(host, *creds)
        else:
            shares = get_smb_shares(host)

        if shares == ["Login required"]:

            dialog = AuthDialog(host)

            if dialog.exec():
                username, password = dialog.get_credentials()

                self.auth_cache[host] = (username, password)

                shares = get_smb_shares(host, username, password)

        for share in shares:

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
                creds_local = self.auth_cache.get(h)

                if creds_local:
                    mount_share(h, s, *creds_local)
                else:
                    mount_share(h, s)

            btn.clicked.connect(on_mount)

            self.tree.setItemWidget(child, 1, container)
