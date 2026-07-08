from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
)

from PyQt6.QtCore import QTimer

from core.mount_engine import get_real_mounts, unmount_share
from core.i18n import tr


class MountedTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # ---------------- TREE ----------------
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            tr("mounted.header_source"),
            tr("mounted.header_target"),
        ])

        # fixed width for the source column, so full //ip/share paths
        # aren't clipped (same fix as the Discovery tab)
        self.tree.setColumnWidth(0, 350)

        layout.addWidget(self.tree)

        # ---------------- BUTTONS ----------------
        btns = QHBoxLayout()

        self.refresh_btn = QPushButton(tr("mounted.refresh_button"))
        self.refresh_btn.clicked.connect(self.load_mounts)

        self.remove_fstab_checkbox = QCheckBox(tr("mounted.remove_fstab_checkbox"))
        self.remove_fstab_checkbox.setToolTip(tr("mounted.remove_fstab_tooltip"))

        self.unmount_btn = QPushButton(tr("mounted.unmount_button"))
        self.unmount_btn.clicked.connect(self.unmount_selected)

        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.remove_fstab_checkbox)
        btns.addWidget(self.unmount_btn)

        layout.addLayout(btns)

        self.setLayout(layout)

        # auto refresh every 3s
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
        remove_fstab = self.remove_fstab_checkbox.isChecked()

        try:
            res = unmount_share(path, remove_fstab=remove_fstab)
        except Exception as e:
            QMessageBox.critical(self, tr("mounted.error_title"), str(e))
            return

        if isinstance(res, dict):
            ok = res.get("success", False)
            err = res.get("stderr", "")
        else:
            ok = bool(res)
            err = ""

        if not ok:
            QMessageBox.critical(
                self,
                tr("mounted.unmount_failed_title"),
                err or tr("mounted.unknown_error")
            )

        self.load_mounts()
