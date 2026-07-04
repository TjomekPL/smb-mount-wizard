from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QMessageBox
)

from core.mount_engine import (
    get_real_mounts,
    unmount_share,
    test_mount
)

from core.persistence import get_persistent_mounts


class MountedTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # --- BUTTONS ---
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)

        self.test_btn = QPushButton("Test mount")
        self.test_btn.clicked.connect(self.run_test_mount)

        self.unmount_btn = QPushButton("Unmount selected")
        self.unmount_btn.clicked.connect(self.unmount)

        # --- LISTS ---
        self.active_list = QListWidget()
        self.persistent_list = QListWidget()

        # --- LAYOUT ---
        layout.addWidget(QLabel("Active mounts"))
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.test_btn)
        layout.addWidget(self.active_list)
        layout.addWidget(self.unmount_btn)

        layout.addWidget(QLabel("Persistent mounts (fstab/systemd)"))
        layout.addWidget(self.persistent_list)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):

        self.active_list.clear()
        self.persistent_list.clear()

        # ACTIVE mounts (kernel state)
        for m in get_real_mounts():
            self.active_list.addItem(
                f"{m['source']} -> {m['target']}"
            )

        # PERSISTENT mounts
        persistent = get_persistent_mounts()

        for m in persistent["fstab"]:
            self.persistent_list.addItem(
                f"[fstab] {m['source']} -> {m['target']}"
            )

        for m in persistent["systemd"]:
            self.persistent_list.addItem(
                f"[systemd] {m['unit']}"
            )

    def unmount(self):

        item = self.active_list.currentItem()

        if not item:
            return

        line = item.text()

        try:
            path = line.split("->")[1].strip()
        except Exception:
            return

        ok, err = unmount_share(path)

        if not ok:
            QMessageBox.critical(self, "Unmount error", err)

        self.refresh()

    def run_test_mount(self):

        result = test_mount()

        if result["mounted"]:
            QMessageBox.information(
                self,
                "Test mount",
                f"OK mounted at {result['target']}"
            )
        else:
            QMessageBox.critical(
                self,
                "Test mount failed",
                result["error"]
            )

        self.refresh()
