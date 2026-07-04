from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget
)

from core.mount_engine import get_real_mounts, unmount_share
from core.persistence import get_persistent_mounts


class MountedTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)

        self.active_list = QListWidget()
        self.persistent_list = QListWidget()

        layout.addWidget(QLabel("Active mounts"))
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.active_list)

        layout.addWidget(QLabel("Persistent mounts (fstab/systemd)"))
        layout.addWidget(self.persistent_list)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):

        self.active_list.clear()
        self.persistent_list.clear()

        # ACTIVE
        for m in get_real_mounts():
            self.active_list.addItem(
                f"{m['source']} -> {m['target']}"
            )

        # PERSISTENT
        persistent = get_persistent_mounts()

        for m in persistent["fstab"]:
            self.persistent_list.addItem(
                f"[fstab] {m['source']} -> {m['target']}"
            )

        for m in persistent["systemd"]:
            self.persistent_list.addItem(
                f"[systemd] {m['unit']}"
            )
