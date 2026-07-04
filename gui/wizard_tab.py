from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem
)

from core.discovery import scan_smb_hosts


class WizardTab(QWidget):

    def __init__(self):
        super().__init__()

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

        self.tree.setHeaderLabels([
            "Server"
        ])

        layout.addLayout(top)
        layout.addWidget(self.tree)

        self.setLayout(layout)

    def scan(self):

        self.tree.clear()

        hosts = scan_smb_hosts()

        for host in hosts:
            QTreeWidgetItem(
                self.tree,
                [host]
            )

    def add_server(self):

        host = self.host_input.text().strip()

        if not host:
            return

        QTreeWidgetItem(
            self.tree,
            [host]
        )

        self.host_input.clear()
