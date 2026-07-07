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
    get_missing_packages,
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
        self.tree.setColumnWidth(0, 100)
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

    def refresh(self):
        self.tree.clear()

        status = get_dependency_status()
        any_missing = False

        for tool in status:
            ok = tool["installed"]
            state = tr("diagnostics.status_ok") if ok else tr("diagnostics.status_missing")
            purpose = tr(tool["purpose_key"])

            item = QTreeWidgetItem([
                tool["binary"],
                tool["package"],
                state,
                purpose,
            ])

            color = QColor("darkgreen") if ok else QColor("red")
            for col in range(4):
                item.setForeground(col, color)

            if not ok:
                any_missing = True

            self.tree.addTopLevelItem(item)

        self.install_btn.setEnabled(any_missing)

    def install_missing(self):
        missing = get_missing_packages()

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
