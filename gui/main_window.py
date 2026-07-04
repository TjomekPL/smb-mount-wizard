from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget
)

from gui.wizard_tab import WizardTab
from gui.mounted_tab import MountedTab
from gui.settings_tab import SettingsTab


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SMB Mount Wizard")
        self.resize(900, 700)

        tabs = QTabWidget()

        tabs.addTab(WizardTab(), "Discovery")
        tabs.addTab(MountedTab(), "Mounted")
        tabs.addTab(SettingsTab(), "Settings")

        self.setCentralWidget(tabs)
