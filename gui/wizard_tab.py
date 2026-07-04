from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem
)

from core.discovery import (
    scan_smb_hosts,
    get_smb_shares
)

from core.auth import AuthDialog


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

        self.auth_cache = {}

        layout = QVBoxLayout()

        top = QHBoxLayout()

        self.scan_btn = QPushButton("Scan network")
        self.scan_btn.clicked.connect(self.scan)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText(
            "192.168.0.201 / nas.tailnet.ts.net"
        )

        self.add_btn = QPushButton("Add server")
        self.add_btn.clicked.connect(self.add_server)

        top.addWidget(self.scan_btn)
        top.addWidget(self.host_input)
        top.addWidget(self.add_btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["SMB Hosts"])

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

        item.takeChildren()

        creds = self.auth_cache.get(host, None)

        shares = None

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
            item.addChild(QTreeWidgetItem([share]))
