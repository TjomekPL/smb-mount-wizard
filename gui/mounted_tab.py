from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QTreeWidget,
    QTreeWidgetItem,
    QProgressBar,
    QMessageBox,
)

from PyQt6.QtCore import QTimer, QThread, pyqtSignal

from core.mount_engine import get_real_mounts, unmount_share, get_disk_usage, format_bytes
from core.i18n import tr


class _DiskUsageThread(QThread):
    """
    Computes disk usage for a list of mountpoints off the GUI thread.
    os.statvfs() can block for a few seconds on an unresponsive
    network mount even with the 'soft' option - this must never run
    directly in a Qt slot handler on the main thread.
    """
    result_ready = pyqtSignal(dict)  # {target: (used, total) or None}

    def __init__(self, targets):
        super().__init__()
        self.targets = targets

    def run(self):
        results = {}
        for target in self.targets:
            results[target] = get_disk_usage(target)
        self.result_ready.emit(results)


class MountedTab(QWidget):

    def __init__(self):
        super().__init__()

        self._current_mounts = []
        self._usage_cache = {}
        self._usage_thread = None

        layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            tr("mounted.header_source"),
            tr("mounted.header_target"),
            tr("mounted.header_usage"),
        ])

        self.tree.setColumnWidth(0, 350)
        self.tree.setColumnWidth(2, 160)

        layout.addWidget(self.tree)

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_mounts)
        self.timer.start(3000)

        self.load_mounts()

    def load_mounts(self):
        try:
            mounts = get_real_mounts()
        except Exception:
            mounts = []

        self._current_mounts = mounts
        self._render_tree()

        if self._usage_thread is None or not self._usage_thread.isRunning():
            targets = [m.get("target") for m in mounts if m.get("target")]
            if targets:
                self._usage_thread = _DiskUsageThread(targets)
                self._usage_thread.result_ready.connect(self._on_usage_result)
                self._usage_thread.start()

    def _on_usage_result(self, results):
        self._usage_cache.update(results)
        self._render_tree()

    def _render_tree(self):
        self.tree.clear()

        for m in self._current_mounts:
            target = m.get("target", "")

            item = QTreeWidgetItem([m.get("source", ""), target])
            self.tree.addTopLevelItem(item)

            bar = QProgressBar()
            bar.setTextVisible(True)

            usage = self._usage_cache.get(target)

            if usage and usage[1] > 0:
                used, total = usage
                percent = min(100, int(used / total * 100))
                bar.setValue(percent)
                bar.setFormat(f"{format_bytes(used)} / {format_bytes(total)}")
            else:
                bar.setValue(0)
                bar.setFormat(tr("mounted.usage_unknown"))

            self.tree.setItemWidget(item, 2, bar)

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

        self._usage_cache.pop(path, None)
        self.load_mounts()
