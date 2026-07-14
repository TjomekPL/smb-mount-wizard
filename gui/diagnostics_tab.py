from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QTextEdit,
)
from PyQt6.QtGui import QColor

from core.diagnostics import (
    get_dependency_status,
    get_optional_status,
    get_missing_packages,
    get_missing_optional_packages,
    install_packages,
)
from core.i18n import tr


class DiagnosticsTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel(tr("diagnostics.title")))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            tr("diagnostics.header_tool"),
            tr("diagnostics.header_package"),
            tr("diagnostics.header_status"),
            tr("diagnostics.header_purpose"),
        ])
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 60)

        layout.addWidget(self.tree)

        btns = QHBoxLayout()

        self.refresh_btn = QPushButton(tr("diagnostics.refresh_button"))
        self.refresh_btn.clicked.connect(self.refresh)

        self.install_btn = QPushButton(tr("diagnostics.install_button"))
        self.install_btn.clicked.connect(self.install_missing)

        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.install_btn)

        layout.addLayout(btns)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(120)
        self.output.setPlaceholderText(tr("diagnostics.output_placeholder"))

        layout.addWidget(self.output)

        self.setLayout(layout)

        self.refresh()

    def _add_row(self, tool, recommended=False):
        ok = tool["installed"]
        state = tr("diagnostics.status_ok") if ok else tr("diagnostics.status_missing")
        purpose = tr(tool["purpose_key"])

        label = tool["binary"]
        if recommended:
            label += f" ({tr('diagnostics.optional_title')})"

        item = QTreeWidgetItem([
            label,
            tool["package"],
            state,
            purpose,
        ])

        if ok:
            color = QColor("darkgreen")
        elif recommended:
            color = QColor("darkorange")
        else:
            color = QColor("red")

        for col in range(4):
            item.setForeground(col, color)

        self.tree.addTopLevelItem(item)

    def refresh(self):
        self.tree.clear()

        for tool in get_dependency_status():
            self._add_row(tool, recommended=False)

        for tool in get_optional_status():
            self._add_row(tool, recommended=True)

        # Button stays enabled as long as anything (required or
        # recommended) is still missing - clicking it always tackles
        # required first, then recommended, one tier per click.
        any_missing = bool(get_missing_packages()) or bool(get_missing_optional_packages())
        self.install_btn.setEnabled(any_missing)

    def install_missing(self):
        # Required tools first; only move on to recommended ones once
        # nothing required is missing anymore, so a second click of
        # the same button is what installs those.
        missing = get_missing_packages()

        if not missing:
            missing = get_missing_optional_packages()

        if not missing:
            QMessageBox.information(
                self,
                tr("tab.diagnostics"),
                tr("diagnostics.already_installed")
            )
            return

        confirm = QMessageBox.question(
            self,
            tr("diagnostics.confirm_title"),
            tr("diagnostics.confirm_message", packages="\n".join(missing)),
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        result = install_packages(missing)

        self.output.setPlainText(
            (result.get("stdout") or "") + "\n" + (result.get("stderr") or "")
        )

        if result.get("success"):
            QMessageBox.information(self, tr("tab.diagnostics"), tr("diagnostics.done"))
        else:
            QMessageBox.critical(self, tr("tab.diagnostics"), tr("diagnostics.failed"))

        self.refresh()
