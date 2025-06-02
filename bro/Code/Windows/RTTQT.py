from PyQt5 import QtWidgets, QtCore, QtGui
import mtranslate
from Code import Languages, TextProcess
import Code.WindowScreenshot as WindowScreenshot
import Code.Ocr as Ocr
from typing import List
from PIL import Image
import uuid
import sys
import ctypes
from ctypes import wintypes
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import Code.Rectangle as Rectangle

_window = None
_app = None
_thread = None
_exist = False
latest_data = None
latest_data_lock = threading.Lock()

can_translate = []

lang_code_from : str
lang_code_to : str

class SubImageText:
    def __init__(self, text: str, translated_text, cropped_img, pixmap_item: QtWidgets.QGraphicsPixmapItem, text_item: QtWidgets.QGraphicsTextItem, id_: str):
        self.text = text
        self.translated_text = translated_text
        self.cropped_img = cropped_img  # PIL Image
        self.pixmap_item = pixmap_item
        self.text_item = text_item
        self.id = id_

class UpdateThread(QtCore.QThread):
    updated = QtCore.pyqtSignal(object)

    def __init__(self, window_name, fps):
        super().__init__()
        self.window_name = window_name
        self.fps = fps
        self.running = True
        self.ocr_img_pil = None  # imagem compartilhada com a thread de OCR
        self.last_ocr_img_pil = None 

    def func_1(self):
        while self.running:
            # TODO: implemente algo aqui
            self.msleep(1000)

    def run(self):
        global _window, latest_data, lang_code_from
        # Ocr.create('en')
        # Ocr.create(lang_code_from)
        Ocr.create(Languages.get_model_by_lang_code(lang_code_from))

        # Iniciar a thread OCR
        self.ocr_thread = threading.Thread(target=self.ocr_worker, daemon=True)
        self.ocr_thread.start()

        while self.running:
            names = WindowScreenshot.getWindowsNames()
            names = [x for x in names if x != '' and not x.isspace()]
            if names[1] != self.window_name:
                print(names[1])
                print("Janela nao está 100% em foco ou foi fechada")
                _window.setWindowOpacity(0.0)
                self.msleep(int(1000 / self.fps))
                continue
            else:
                _window.setWindowOpacity(1.0)

            # result = WindowScreenshot.getWindowScreenshot(self.window_name)

            # img_pil = result[0]
            # rectangles = Ocr.get_rectangles_from_pil(img_pil, max_gap_distance=10)
            # cropped_imgs = Ocr.crop_regions_from_pil(img_pil, rectangles)
            # inpainted_imgs = Ocr.inpaint_area_regions_from_pil(img_pil, rectangles)

            # data = {
            #     'pos_dim': result[1:5],
            #     'rectangles': rectangles,
            #     'cropped_imgs': cropped_imgs,
            #     'inpainted_imgs': inpainted_imgs,
            #     'img_pil': img_pil
            # }

            # self.updated.emit(data)

            result = WindowScreenshot.getWindowScreenshot(self.window_name)

            img_pil = result[0]
            self.ocr_img_pil = img_pil  # passa a imagem para a thread OCR

            # Pega a última análise da thread OCR (caso esteja pronta)
            with latest_data_lock:
                data = latest_data

            if data:
                # Atualiza posição da janela e envia dados para GUI
                data['pos_dim'] = result[1:5]
                self.updated.emit(data)
            self.msleep(int(1000 / self.fps))

    def ocr_worker(self):
        global latest_data, can_translate

        while self.running:
            if self.ocr_img_pil is not None and self.ocr_img_pil != self.last_ocr_img_pil:
                img_pil = self.ocr_img_pil

                rectangles = Ocr.get_rectangles_from_pil(img_pil, max_gap_distance=10)
                cropped_imgs = Ocr.crop_regions_from_pil(img_pil, rectangles)
                inpainted_imgs = Ocr.inpaint_area_regions_from_pil(img_pil, rectangles)

                with latest_data_lock:
                    latest_data = {
                        'rectangles': rectangles,
                        'cropped_imgs': cropped_imgs,
                        'inpainted_imgs': inpainted_imgs,
                        'img_pil': img_pil
                    }
                self.last_ocr_img_pil = self.ocr_img_pil
                can_translate.append(True)

    def stop(self):
        self.running = False
        self.wait()

class RTTWindow(QtWidgets.QWidget):
    def __init__(self, window_name: str, x, y, width, height, fps):
        super().__init__()
        self.window_name = window_name
        self.fps = fps
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setGeometry(x, y, width, height)

        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background: transparent")
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.view.setGeometry(0, 0, width, height)

        self.sub_images: List[SubImageText] = []

        self.thread = UpdateThread(window_name, fps)
        self.thread.updated.connect(self.on_update)
        self.thread.start()

        self.show()

        # Torna a janela click-through no Windows (ignorar input mouse)
        if sys.platform == "win32":
            hwnd = self.winId().__int__()
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020

            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

    def on_update(self, data):
        global can_translate

        x, y, w, h = data['pos_dim']
        self.setGeometry(x, y, w, h)
        self.view.setGeometry(0, 0, w, h)

        img_pil = data['img_pil']
        img_width, img_height = img_pil.size
        scale_x = self.view.width() / img_width
        scale_y = self.view.height() / img_height
        self.scene.setSceneRect(0, 0, img_width, img_height)

        rectangles = data['rectangles']
        cropped_imgs = data['cropped_imgs']
        inpainted_imgs = data['inpainted_imgs']

        to_remove = []
        for sub_img in self.sub_images:
            pos = Ocr.find_subimage_exact(Ocr.pil_to_cv(img_pil), Ocr.pil_to_cv(sub_img.cropped_img))  # TODO
            # pos = Ocr.encontrar_subimagem_exata(Ocr.pil_to_cv(img_pil), Ocr.pil_to_cv(sub_img.cropped_img))
            if pos:
                print("hey")
                sub_img.pixmap_item.setPos(pos[0] * scale_x, pos[1] * scale_y)
                sub_img.text_item.setPos(pos[0] * scale_x, pos[1] * scale_y)
                new_data = []
                for rect, cropped, inpainted in zip(rectangles, cropped_imgs, inpainted_imgs):
                    if not any(are_images_equal(sub_img.cropped_img, cropped) for sub_img in self.sub_images):
                        new_data.append((rect, cropped, inpainted))
                
                # Atualize as listas com os dados filtrados corretamente
                rectangles, cropped_imgs, inpainted_imgs = zip(*new_data) if new_data else ([], [], [])
                # if sub_img.cropped_img in cropped_imgs:
                #     print("xoo")
                #     print("THE FUCKIN TEXT IS: ", sub_img.text)
                #     cropped_imgs.remove(sub_img.cropped_img)
            else:
                print("ho")
                to_remove.append(sub_img)
        print("-----------------------------")
        for sub_img in to_remove:
            self.scene.removeItem(sub_img.pixmap_item)
            self.scene.removeItem(sub_img.text_item)
            self.sub_images.remove(sub_img)

        # if len(can_translate) == 0:
        #     for sub_img in self.sub_images:
        #         pos = Ocr.find_subimage_exact(Ocr.pil_to_cv(img_pil), Ocr.pil_to_cv(sub_img.cropped_img))
        #         if pos:
        #             sub_img.pixmap_item.setPos(pos[0] * scale_x, pos[1] * scale_y)
        #             sub_img.text_item.setPos(pos[0] * scale_x, pos[1] * scale_y)
        #             sub_img.pixmap_item.show()
        #             sub_img.text_item.show()
        #         else:
        #             sub_img.pixmap_item.hide()
        #             sub_img.text_item.hide()
            
        #     print("=======================================================")
        #     return


        texts = [rectangles[i].text for i in range(len(cropped_imgs))]

        for i in range(len(texts)):
            if TextProcess.has_dictionary_loaded():
                print("Antes do correção: ", texts[i])
                texts[i] = TextProcess.correct_phrase(texts[i])
                print("Depois da correção: ", texts[i])

        if len(can_translate) > 0:
            translated_texts = [None] * len(texts)
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(translate, t): idx for idx, t in enumerate(texts)}
                for future in as_completed(futures):
                    idx = futures[future]
                    translated_texts[idx] = future.result()
            can_translate.remove(True)

            for i in range(len(cropped_imgs)):
                rect = rectangles[i]

                # Calcular retângulo original do novo item
                new_rect = Rectangle.Rectangle(
                    x=rect.x,
                    y=rect.y,
                    width=rect.width,
                    height=rect.height,
                    text=rect.text,
                    translated_text=''
                )

                # Remover sub-imagens que colidem
                to_remove = []
                for sub_img in self.sub_images:
                    existing_rect = Rectangle.Rectangle(
                        x=sub_img.pixmap_item.x() / scale_x,
                        y=sub_img.pixmap_item.y() / scale_y,
                        width=sub_img.cropped_img.width,
                        height=sub_img.cropped_img.height,
                        text='',
                        translated_text=''
                    )
                    if Rectangle.rectangles_intersect(new_rect, existing_rect):
                        to_remove.append(sub_img)

                for sub_img in to_remove:
                    self.scene.removeItem(sub_img.pixmap_item)
                    self.scene.removeItem(sub_img.text_item)
                    self.sub_images.remove(sub_img)

                # Criar imagem
                pixmap = pil2pixmap(inpainted_imgs[i])
                pixmap_item = self.scene.addPixmap(pixmap)
                pixmap_item.setPos(rect.x * scale_x, rect.y * scale_y)
                pixmap_item.setZValue(1)
                pixmap_item.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                pixmap_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
                pixmap_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)

                # Criar texto
                text_item = QtWidgets.QGraphicsTextItem(translated_texts[i])
                text_item.setDefaultTextColor(Ocr.get_contrast_color(inpainted_imgs[i]))
                font = QtGui.QFont("Arial", 12)
                text_item.setFont(font)
                text_item.setTextWidth(rect.width * scale_x)
                text_item.setPos(rect.x * scale_x, rect.y * scale_y)
                text_item.setZValue(2)
                text_item.setAcceptedMouseButtons(QtCore.Qt.NoButton)
                text_item.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
                text_item.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)

                self.scene.addItem(text_item)

                self.sub_images.append(SubImageText(
                    rect.text,
                    '',
                    cropped_imgs[i],
                    pixmap_item,
                    text_item,
                    str(uuid.uuid4())
                ))

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
    
def translate(text : str) -> str:
    global lang_code_to
    try:
        print("Antes da tradução: ", text)
        textx = mtranslate.translate(text, lang_code_to)
        print("Depois da tradução: ", textx)
        return textx
        # return mtranslate.translate(text, 'pt')
    except Exception as e:
        print(f"Erro: {e}")
        return text

def pil2pixmap(pil_img):
    pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    qimage = QtGui.QImage(data, pil_img.width, pil_img.height, QtGui.QImage.Format_RGBA8888)
    return QtGui.QPixmap.fromImage(qimage)

def are_images_equal(img1: Image.Image, img2: Image.Image) -> bool:
    return img1.size == img2.size and img1.tobytes() == img2.tobytes()

def create(window_name: str, x, y, width, height, fps: int, language_from: str, language_to: str):
    global _window, _app, _thread, _exist, lang_code_from, lang_code_to
    if _exist:
        quit()

    _app = QtWidgets.QApplication.instance()
    if not _app:
        _app = QtWidgets.QApplication(sys.argv)

    lang_code_from = Languages.get_lang_code(language_from)
    lang_code_to = Languages.get_lang_code(language_to)
    print("lang code from: ", lang_code_from)
    print("lang code to: ", lang_code_to)
    TextProcess.create(language_from)
    
    _window = RTTWindow(window_name, x, y, width, height, fps)
    _window.show()
    _exist = True

    if not QtWidgets.QApplication.instance().startingUp():
        pass
    else:
        _app.exec()

def exists() -> bool:
    return _exist

def quit() -> None:
    global _window, _app, _exist
    if _window is not None:
        _window.close()
        _window = None
    _exist = False
