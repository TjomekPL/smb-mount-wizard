from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
)

from PyQt6.QtCore import QTimer

from core.mount_engine import get_real_mounts, unmount_share


class MountedTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # ---------------- TREE ----------------
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Source", "Mountpoint"])

        layout.addWidget(self.tree)

        # ---------------- BUTTONS ----------------
        btns = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_mounts)

        self.unmount_btn = QPushButton("Unmount selected")
        self.unmount_btn.clicked.connect(self.unmount_selected)

        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.unmount_btn)

        layout.addLayout(btns)

        self.setLayout(layout)

        # auto refresh (co 3s)
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_mounts)
        self.timer.start(3000)

        self.load_mounts()

    # ---------------- LOAD ----------------
    def load_mounts(self):

        self.tree.clear()

        try:
            mounts = get_real_mounts()
        except Exception:
            mounts = []

        for m in mounts:

            item = QTreeWidgetItem([
                m.get("source", ""),
                m.get("target", "")
            ])

            self.tree.addTopLevelItem(item)

    # ---------------- UNMOUNT ----------------
    def unmount_selected(self):

        selected = self.tree.selectedItems()

        if not selected:
            return

        path = selected[0].text(1)

        try:
            res = unmount_share(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        if isinstance(res, dict):
            ok = res.get("success", False)
            err = res.get("stderr", "")
        else:
            ok = bool(res)
            err = ""

        if not ok:
            QMessageBox.critical(self, "Unmount failed", err or "Unknown error")

        self.load_mounts()
