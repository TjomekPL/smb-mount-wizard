from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from pathlib import Path

from gui.wizard_tab import WizardTab
from gui.mounted_tab import MountedTab
from gui.settings_tab import SettingsTab
from gui.diagnostics_tab import DiagnosticsTab
from core.runtime import kill_all
from core.i18n import tr
from core.version import __version__

ICON_PATH = Path(__file__).resolve().parent.parent / "resources" / "icon.svg"


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"SMB Mount Wizard v{__version__}")

        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(900, 700)

        self.tabs = QTabWidget()
        self.build_tabs()

        self.setCentralWidget(self.tabs)

    def build_tabs(self):
        # deferred via QTimer when called from within a widget that is
        # itself about to be torn down (e.g. a language change
        # triggered from inside SettingsTab's own click handler)
        self.tabs.clear()

        self.tabs.addTab(WizardTab(), tr("tab.discovery"))
        self.tabs.addTab(MountedTab(), tr("tab.mounted"))
        self.tabs.addTab(
            SettingsTab(on_language_changed=self.on_language_changed),
            tr("tab.settings"),
        )
        self.tabs.addTab(DiagnosticsTab(), tr("tab.diagnostics"))

    def on_language_changed(self):
        # deferred so the SettingsTab click handler that triggered this
        # finishes running before its own widget gets torn down
        QTimer.singleShot(0, self.build_tabs)

    def closeEvent(self, event):
        kill_all()
        event.accept()
