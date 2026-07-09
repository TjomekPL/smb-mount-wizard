from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal

from core.settings import (
    get_default_mount_base,
    set_default_mount_base,
    get_smb_version_override,
    set_smb_version_override,
)
from core.i18n import tr, get_language, set_language, available_languages
from core.version import __version__
from core.update_check import get_latest_version_tag, is_newer


def _separator():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


class _UpdateCheckThread(QThread):
    """
    Runs the GitHub tag lookup off the GUI thread - a network call
    blocking the main thread is exactly the kind of freeze we already
    fixed elsewhere in this app, so it must not happen here either.
    """
    result_ready = pyqtSignal(object)  # str (version) or None

    def run(self):
        self.result_ready.emit(get_latest_version_tag())


class SettingsTab(QWidget):

    def __init__(self, on_language_changed=None):
        super().__init__()

        self.on_language_changed = on_language_changed
        self._update_thread = None

        layout = QVBoxLayout()

        # ---------------- version / updates (top, most visible) ----------------
        version_row = QHBoxLayout()
        version_row.addWidget(QLabel(tr("settings.version_label", version=__version__)))
        version_row.addStretch()

        layout.addLayout(version_row)

        update_row = QHBoxLayout()

        self.check_updates_btn = QPushButton(tr("settings.check_updates_button"))
        self.check_updates_btn.clicked.connect(self.check_for_updates)

        self.update_status_label = QLabel("")

        update_row.addWidget(self.check_updates_btn)
        update_row.addWidget(self.update_status_label)
        update_row.addStretch()

        layout.addLayout(update_row)

        layout.addWidget(_separator())

        # ---------------- mount location ----------------
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

        layout.addWidget(_separator())

        # ---------------- language ----------------
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

        layout.addWidget(_separator())

        # ---------------- SMB protocol version ----------------
        layout.addWidget(QLabel(tr("settings.smb_version_label")))

        self.smb_version_combo = QComboBox()
        self.smb_version_options = ["", "1.0", "2.0", "2.1", "3.0", "3.1.1"]
        labels = [tr("settings.smb_version_auto")] + self.smb_version_options[1:]

        for label in labels:
            self.smb_version_combo.addItem(label)

        current_version = get_smb_version_override()
        try:
            self.smb_version_combo.setCurrentIndex(
                self.smb_version_options.index(current_version)
            )
        except ValueError:
            self.smb_version_combo.setCurrentIndex(0)

        self.smb_version_combo.currentIndexChanged.connect(self.change_smb_version)

        layout.addWidget(self.smb_version_combo)
        layout.addWidget(QLabel(tr("settings.smb_version_note")))

        layout.addStretch()

        self.setLayout(layout)

        # silent check on load - no popups, just fills in the label
        # if/when it completes
        self.check_for_updates()

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

    def change_smb_version(self, index):
        set_smb_version_override(self.smb_version_options[index])

    def check_for_updates(self):
        self.update_status_label.setText(tr("settings.checking_updates"))
        self.check_updates_btn.setEnabled(False)

        self._update_thread = _UpdateCheckThread()
        self._update_thread.result_ready.connect(self._on_update_result)
        self._update_thread.start()

    def _on_update_result(self, latest):
        self.check_updates_btn.setEnabled(True)

        if not latest:
            self.update_status_label.setText(tr("settings.update_check_failed"))
            return

        if is_newer(latest, __version__):
            self.update_status_label.setText(
                tr("settings.update_available", version=latest)
            )
        else:
            self.update_status_label.setText(tr("settings.up_to_date"))
