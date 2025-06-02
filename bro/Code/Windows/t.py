import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui

def pil2pixmap(pil_img):
    pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    qimage = QtGui.QImage(data, pil_img.width, pil_img.height, QtGui.QImage.Format_RGBA8888)
    return QtGui.QPixmap.fromImage(qimage)

class ImageWindow(QtWidgets.QWidget):
    def __init__(self, image, x, y, width, height):
        super().__init__()

        # Ajuste de DPI (necessário para telas com escala diferente de 100%)
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

        # Configurações da janela
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowStaysOnTopHint  # Garante que fique por cima
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Tamanho e posição
        self.move(x, y)
        self.resize(width, height)

        # Exibir imagem
        pixmap = pil2pixmap(image)

        label = QtWidgets.QLabel(self)
        label.setPixmap(pixmap)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setGeometry(0, 0, width, height)

        self.show()

def show_image_window(image, x, y, width, height):
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    window = ImageWindow(image, x, y, width, height)
    app.exec_()
