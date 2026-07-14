from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel
)

from core.i18n import tr


class AuthDialog(QDialog):

    def __init__(self, host, prefill_username="", prefill_password="", on_forget=None):
        super().__init__()

        self.setWindowTitle(tr("auth.title", host=host))
        self.resize(320, 170)

        self.username = QLineEdit()
        self.username.setPlaceholderText(tr("auth.username_placeholder"))
        self.username.setText(prefill_username)

        self.password = QLineEdit()
        self.password.setPlaceholderText(tr("auth.password_placeholder"))
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setText(prefill_password)

        self.ok_btn = QPushButton(tr("auth.login_button"))
        self.ok_btn.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(host))
        layout.addWidget(self.username)
        layout.addWidget(self.password)

        # Only offer "forget" if there's actually something prefilled
        # (i.e. this dialog was opened because a saved credential
        # exists and either the user wants to clear it, or it just
        # failed and needs replacing).
        if on_forget and (prefill_username or prefill_password):
            forget_row = QHBoxLayout()
            forget_btn = QPushButton(tr("auth.forget_button"))

            def do_forget():
                on_forget()
                self.username.clear()
                self.password.clear()

            forget_btn.clicked.connect(do_forget)
            forget_row.addWidget(forget_btn)
            layout.addLayout(forget_row)

        layout.addWidget(self.ok_btn)

        self.setLayout(layout)

    def get_credentials(self):
        return self.username.text(), self.password.text()
