from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt

window : QWidget = None

class Window(QWidget):
    def __init__(self, x, y, w, h):
        super().__init__()

        # Disable input
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint  # Avoid window manager control (Linux)
        )

        # Optional: make the window transparent with content
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0); color: white; font-size: 24px;")

        self.setGeometry(x, y, w, h)

def create():
    global window
    app = QApplication([])

    # Create a Qt widget, which will be our window.
    window = Window(0, 0, 100, 100)
    window.show()  # IMPORTANT!!!!! Windows are hidden by default.

    # Start the event loop.
    app.exec()

    # Your application won't reach here until you exit and the event
    # loop has stopped.