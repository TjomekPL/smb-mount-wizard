from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QTreeWidget,
    QTreeWidgetItem,
    QProgressBar,
    QHeaderView,
    QMessageBox,
)

from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt

from core.mount_engine import get_real_mounts, unmount_share, get_disk_usage, format_bytes
from core.manual_servers import get_server_display_map
from core.i18n import tr


def _usage_color(percent):
    if percent >= 90:
        return "#e74c3c"  # red - almost full
    elif percent >= 70:
        return "#f39c2d"  # orange - getting full
    else:
        return "#2a8fd8"  # blue - plenty of room


def _split_source(source):
    """
    '//192.168.0.201/storage' -> ('192.168.0.201', 'storage')
    Falls back to (source, '') if it doesn't look like that shape.
    """
    if source.startswith("//"):
        rest = source[2:]
        if "/" in rest:
            server, share = rest.split("/", 1)
            return server, share
        return rest, ""
    return source, ""


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

        # ---------------- TREE ----------------
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            tr("mounted.header_source"),
            tr("mounted.header_target"),
            tr("mounted.header_usage"),
        ])

        # Source and Usage get a sensible fixed-ish width (still
        # user-resizable); Mountpoint absorbs whatever space is left,
        # so there's no dead empty area after the last column.
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)

        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(2, 150)

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
        try:
            mounts = get_real_mounts()
        except Exception:
            mounts = []

        self._current_mounts = mounts
        self._render_tree()

        # Kick off a background usage check, but only if the previous
        # one has finished - avoids piling up threads if a share is
        # slow/unresponsive.
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
        # Remember what's currently selected (by mountpoint) before
        # wiping the tree - _render_tree() runs on every periodic
        # refresh (every 3s) as well as after user actions, and
        # clear() creates entirely new item objects, silently losing
        # any selection made in between. Restored after rebuilding
        # below so "Unmount selected" keeps working on what the user
        # actually clicked, even if a refresh happens in between.
        selected_target = None
        selected = self.tree.selectedItems()
        if selected and selected[0].childCount() == 0:
            selected_target = selected[0].text(1)

        self.tree.clear()

        display_map = get_server_display_map()

        # group mounts by which server they came from, preserving the
        # order servers first appear in
        groups = {}
        order = []

        for m in self._current_mounts:
            server, share = _split_source(m.get("source", ""))

            if server not in groups:
                groups[server] = []
                order.append(server)

            groups[server].append((share, m))

        for server in order:
            hostname = display_map.get(server)
            label = f"{server} ({hostname})" if hostname else server

            parent = QTreeWidgetItem([label, "", ""])
            self.tree.addTopLevelItem(parent)
            parent.setExpanded(True)

            for share, m in groups[server]:
                target = m.get("target", "")

                child = QTreeWidgetItem([share, target, ""])
                parent.addChild(child)

                if selected_target and target == selected_target:
                    child.setSelected(True)
                    self.tree.setCurrentItem(child)

                bar = QProgressBar()
                bar.setTextVisible(True)
                bar.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                bar.setFixedHeight(20)

                usage = self._usage_cache.get(target)

                if usage and usage[1] > 0:
                    used, total = usage
                    percent = min(100, int(used / total * 100))
                    bar.setValue(percent)
                    bar.setFormat(f"{format_bytes(used)} / {format_bytes(total)}  ")
                    bar.setStyleSheet(
                        "QProgressBar {"
                        "  border: 1px solid palette(mid);"
                        "  border-radius: 8px;"
                        "  background-color: palette(alternate-base);"
                        "  padding: 1px;"
                        "}"
                        "QProgressBar::chunk {"
                        f"  background-color: {_usage_color(percent)};"
                        "  border-radius: 7px;"
                        "}"
                    )
                else:
                    bar.setValue(0)
                    bar.setFormat(tr("mounted.usage_unknown"))

                self.tree.setItemWidget(child, 2, bar)

    # ---------------- UNMOUNT ----------------
    def unmount_selected(self):
        selected = self.tree.selectedItems()

        if not selected:
            return

        item = selected[0]

        if item.childCount() > 0:
            # this is a server group row, not an individual share
            QMessageBox.information(
                self,
                tr("mounted.error_title"),
                tr("mounted.select_share_not_server")
            )
            return

        path = item.text(1)
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
