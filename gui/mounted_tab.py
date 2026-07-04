
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout
)


class MountedTab(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel(
                "No mounted shares"
            )
        )

        self.setLayout(layout)
