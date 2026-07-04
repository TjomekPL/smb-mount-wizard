from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QVBoxLayout
)


class SettingsTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel(
                "Default mount path"
            )
        )

        self.path = QLineEdit()

        self.path.setText(
            "/mnt/network"
        )

        layout.addWidget(
            self.path
        )

        self.setLayout(layout)
