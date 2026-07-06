from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)

from core.settings import get_default_mount_base, set_default_mount_base


class SettingsTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Domyślna lokalizacja montowania"))

        row = QHBoxLayout()

        self.path = QLineEdit()
        self.path.setText(get_default_mount_base())

        self.save_btn = QPushButton("Zapisz")
        self.save_btn.clicked.connect(self.save)

        row.addWidget(self.path)
        row.addWidget(self.save_btn)

        layout.addLayout(row)

        layout.addWidget(
            QLabel(
                "Uwaga: zmiana dotyczy nowo montowanych udziałów.\n"
                "Już zamontowane zostają tam, gdzie są."
            )
        )

        layout.addStretch()

        self.setLayout(layout)

    def save(self):
        path = self.path.text().strip()

        if not path:
            QMessageBox.warning(self, "Błąd", "Ścieżka nie może być pusta")
            return

        set_default_mount_base(path)
        QMessageBox.information(self, "Zapisano", f"Domyślna lokalizacja: {path}")
