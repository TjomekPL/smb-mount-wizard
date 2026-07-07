from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtCore import QTimer

from gui.wizard_tab import WizardTab
from gui.mounted_tab import MountedTab
from gui.settings_tab import SettingsTab
from gui.diagnostics_tab import DiagnosticsTab
from core.runtime import kill_all
from core.i18n import tr


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SMB Mount Wizard")
        self.resize(900, 700)

        self.tabs = QTabWidget()
        self.build_tabs()

        self.setCentralWidget(self.tabs)

    def build_tabs(self):
        self.tabs.clear()

        self.tabs.addTab(WizardTab(), tr("tab.discovery"))
        self.tabs.addTab(MountedTab(), tr("tab.mounted"))
        self.tabs.addTab(
            SettingsTab(on_language_changed=self.on_language_changed),
            tr("tab.settings"),
        )
        self.tabs.addTab(DiagnosticsTab(), tr("tab.diagnostics"))

    def on_language_changed(self):
        QTimer.singleShot(0, self.build_tabs)

    def closeEvent(self, event):
        kill_all()
        event.accept()
