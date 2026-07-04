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


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # --- TOP BAR ---
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

        # --- TREE ---
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
        # tylko top-level hosty
        if item.parent() is not None:
            return

        # jeśli już załadowane → nie rób drugi raz
        if item.childCount() == 1 and item.child(0).text(0) != "Loading...":
            return

        item.takeChildren()

        shares = get_smb_shares(item.text(0))

        for share in shares:
            item.addChild(QTreeWidgetItem([share]))
