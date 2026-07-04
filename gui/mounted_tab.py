from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget
)

from core.mount_engine import list_mounts, unmount_share


class MountedTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.list = QListWidget()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)

        self.unmount_btn = QPushButton("Unmount selected")
        self.unmount_btn.clicked.connect(self.unmount)

        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.list)
        layout.addWidget(self.unmount_btn)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        self.list.clear()

        mounts = list_mounts()

        for m in mounts:
            self.list.addItem(m)

    def unmount(self):
        item = self.list.currentItem()

        if not item:
            return

        line = item.text()

        path = line.split(" on ")[1].split(" type")[0]

        unmount_share(path)

        self.refresh()
