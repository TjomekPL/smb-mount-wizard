import sys
import signal
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    # allows Ctrl+C and proper SIGTERM handling
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # important: quit the whole process once the window closes
    app.lastWindowClosed.connect(app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
