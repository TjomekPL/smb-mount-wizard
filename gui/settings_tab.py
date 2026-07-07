from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
)

from core.settings import get_default_mount_base, set_default_mount_base
from core.i18n import tr, get_language, set_language, available_languages


class SettingsTab(QWidget):

    def __init__(self, on_language_changed=None):
        super().__init__()

        self.on_language_changed = on_language_changed

        layout = QVBoxLayout()

        layout.addWidget(QLabel(tr("settings.mount_location_label")))

        row = QHBoxLayout()

        self.path = QLineEdit()
        self.path.setText(get_default_mount_base())

        self.save_btn = QPushButton(tr("settings.save_button"))
        self.save_btn.clicked.connect(self.save)

        row.addWidget(self.path)
        row.addWidget(self.save_btn)

        layout.addLayout(row)

        layout.addWidget(QLabel(tr("settings.note")))

        layout.addWidget(QLabel(tr("settings.language_label")))

        self.language_combo = QComboBox()
        self.language_codes = []

        current_lang = get_language()
        current_index = 0

        for i, (code, name) in enumerate(available_languages()):
            self.language_combo.addItem(name)
            self.language_codes.append(code)
            if code == current_lang:
                current_index = i

        self.language_combo.setCurrentIndex(current_index)
        self.language_combo.currentIndexChanged.connect(self.change_language)

        layout.addWidget(self.language_combo)
        layout.addWidget(QLabel(tr("settings.language_note")))

        layout.addStretch()

        self.setLayout(layout)

    def save(self):
        path = self.path.text().strip()

        if not path:
            QMessageBox.warning(self, tr("settings.error_title"), tr("settings.path_empty"))
            return

        set_default_mount_base(path)
        QMessageBox.information(
            self,
            tr("settings.saved_title"),
            tr("settings.saved_message", path=path),
        )

    def change_language(self, index):
        code = self.language_codes[index]
        set_language(code)

        if self.on_language_changed:
            self.on_language_changed()
