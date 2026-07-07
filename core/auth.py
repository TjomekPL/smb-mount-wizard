from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel
)

from core.i18n import tr


class AuthDialog(QDialog):

    def __init__(self, host):
        super().__init__()

        self.setWindowTitle(tr("auth.title", host=host))
        self.resize(300, 150)

        self.username = QLineEdit()
        self.username.setPlaceholderText(tr("auth.username_placeholder"))

        self.password = QLineEdit()
        self.password.setPlaceholderText(tr("auth.password_placeholder"))
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        self.ok_btn = QPushButton(tr("auth.login_button"))
        self.ok_btn.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(host))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.ok_btn)

        self.setLayout(layout)

    def get_credentials(self):
        return self.username.text(), self.password.text()
