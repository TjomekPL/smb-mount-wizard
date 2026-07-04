import sys
import signal
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    # pozwala Ctrl+C i poprawne SIGTERM
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # ważne: zamykanie całego procesu po zamknięciu okna
    app.lastWindowClosed.connect(app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
