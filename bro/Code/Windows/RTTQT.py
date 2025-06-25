from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
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

FULLSCREEN = "7935093159g1821-0814-0"

_window = None
_app = None
_thread = None
_exist = False
latest_data = None
latest_data_lock = threading.Lock()

can_translate = []

lang_code_from : str
lang_code_to : str

is_fullscreen_mode = False

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

    def __init__(self, hwnd, fps):
        super().__init__()
        self.hwnd = hwnd
        self.fps = fps
        self.running = True
        # self.ocr_img_pil = None  # imagem compartilhada com a thread de OCR
        # self.last_ocr_img_pil = None
        self.result = None
        self.last_result = None
        self.updated_screen = True

    # def func_1(self):
    #     while self.running:
    #         # TODO: implemente algo aqui
    #         self.msleep(1000)

    def run(self):
        global _window, latest_data, lang_code_from
        # Ocr.create('en')
        # Ocr.create(lang_code_from)
        Ocr.create(Languages.get_model_by_lang_code(lang_code_from))

        # Iniciar a thread OCR
        self.ocr_thread = threading.Thread(target=self.ocr_worker, daemon=True)
        self.ocr_thread.start()

        while self.running:
            if is_fullscreen_mode:
                image = WindowScreenshot.getFullScreenshot([FULLSCREEN])
                if not image:
                    self.result = None
                else:
                    self.result = (image, 0, 0, image.size[0], image.size[1])
            else:
                # print(WindowScreenshot.getAllVisibleWindows())
                if not any(window == self.hwnd for window, title in WindowScreenshot.getAllVisibleWindows()):
                    print("Janela foi fechada")
                    return
                elif not WindowScreenshot.isWindowInFullFocus(self.hwnd, [FULLSCREEN]):
                    print("Janela não está 100% em em foco")
                    _window.setWindowOpacity(0.0)
                    self.msleep(int(1000 / self.fps))
                    continue
                else:
                    _window.setWindowOpacity(1.0)

                self.result = WindowScreenshot.getWindowScreenshot(self.hwnd)

            if not self.result:
                print("RESULT NAO EXISTE!")
                return
            elif self.last_result and self.updated_screen:
                print("CHECKING...")
                if are_images_equal(self.last_result[0], self.result[0]) and self.last_result[1] == self.result[1] and self.last_result[2] == self.result[2]:
                    print("IMAGENS SAO IGUAIS E EM POSIÇÃO IGUAIS!")
                    self.msleep(int(1000 / self.fps))
                    continue
            
            # last_result = result

            # img_pil = result[0]
            # self.ocr_img_pil = img_pil  # passa a imagem para a thread OCR

            # Pega a última análise da thread OCR (caso esteja pronta)
            with latest_data_lock:
                data = latest_data

            if data:
                # Atualiza posição da janela e envia dados para GUI
                data['pos_dim'] = self.result[1:5]
                self.updated.emit(data)
                self.updated_screen = True
                self.last_result = self.result
            self.msleep(int(1000 / self.fps))

    def ocr_worker(self):
        global latest_data, can_translate

        while self.running:

            if self.result and self.result[0]:
                if self.last_result and self.result[0] == self.last_result[0]:
                    continue
            # if self.ocr_img_pil is not None and self.ocr_img_pil != self.last_ocr_img_pil:
                # img_pil = self.ocr_img_pil
                img_pil = self.result[0]

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
                self.last_result = self.result
                self.updated_screen = False
                # self.last_ocr_img_pil = self.ocr_img_pil
                can_translate.append(True)

    def stop(self):
        self.running = False
        self.wait()

class TranslationWorkerSignals(QObject):
    result = pyqtSignal(list, list, list, list)  # rects, cropped_imgs, inpainted_imgs, translated_texts

class TranslationWorker(QRunnable):
    def __init__(self, rectangles, cropped_imgs, inpainted_imgs, scale_x, scale_y):
        super().__init__()
        self.rectangles = rectangles
        self.cropped_imgs = cropped_imgs
        self.inpainted_imgs = inpainted_imgs
        self.signals = TranslationWorkerSignals()
        self.scale_x = scale_x
        self.scale_y = scale_y

    def run(self):
        from Code import TextProcess  # evita problemas de thread com import
        texts = [r.text for r in self.rectangles]
        
        for i in range(len(texts)):
            if TextProcess.has_dictionary_loaded():
                print("Texto ANTES da correção: ", texts[i])
                texts[i] = TextProcess.correct_phrase(texts[i])
                print("Texto DEPOIS da correção: ", texts[i])
        
        translated_texts = [None] * len(texts)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(translate, t): idx for idx, t in enumerate(texts)}
            for future in as_completed(futures):
                idx = futures[future]
                translated_texts[idx] = future.result()

        # translated_texts = texts

        #! PODE OCORRER DOS 3 PRIMEIROS ARGUMENTOS SEREM PASSADOS COMO TUPLA
        self.signals.result.emit(list(self.rectangles), list(self.cropped_imgs), list(self.inpainted_imgs), translated_texts)

class RTTWindow(QtWidgets.QWidget):
    def __init__(self, hwnd: int, x, y, width, height, fps):
        super().__init__()
        self.hwnd = hwnd
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

        self.thread = UpdateThread(hwnd, fps)
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
            else:
                print("ho")
                to_remove.append(sub_img)
        print("-----------------------------")
        for sub_img in to_remove:
            self.scene.removeItem(sub_img.pixmap_item)
            self.scene.removeItem(sub_img.text_item)
            self.sub_images.remove(sub_img)

        if len(can_translate) > 0:
            can_translate.remove(True)
            worker = TranslationWorker(rectangles, cropped_imgs, inpainted_imgs, scale_x, scale_y)
            worker.signals.result.connect(self.handle_translation_result)
            QThreadPool.globalInstance().start(worker)
    
    def handle_translation_result(self, rectangles, cropped_imgs, inpainted_imgs, translated_texts):
        img_pil = next((s['img_pil'] for s in [latest_data] if s), None)
        if not img_pil:
            return

        img_width, img_height = img_pil.size
        scale_x = self.view.width() / img_width
        scale_y = self.view.height() / img_height

        for i in range(len(cropped_imgs)):
            rect = rectangles[i]
            new_rect = Rectangle.Rectangle(rect.x, rect.y, rect.width, rect.height, rect.text, '')

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

            pixmap = pil2pixmap(inpainted_imgs[i])
            pixmap_item = self.scene.addPixmap(pixmap)
            pixmap_item.setPos(rect.x * scale_x, rect.y * scale_y)
            pixmap_item.setZValue(1)

            text_item = QtWidgets.QGraphicsTextItem(translated_texts[i])
            text_item.setDefaultTextColor(Ocr.get_contrast_color(inpainted_imgs[i]))
            font = QtGui.QFont("Arial", 12)
            text_item.setFont(font)
            text_item.setTextWidth(rect.width * scale_x)
            text_item.setPos(rect.x * scale_x, rect.y * scale_y)
            text_item.setZValue(2)

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

def create(hwnd: int, x, y, width, height, fps: int, language_from: str, language_to: str, is_fullscreen: bool):
    global _window, _app, _thread, _exist, lang_code_from, lang_code_to, is_fullscreen_mode
    if _exist:
        quit()

    is_fullscreen_mode = is_fullscreen

    _app = QtWidgets.QApplication.instance()
    if not _app:
        _app = QtWidgets.QApplication(sys.argv)

    lang_code_from = Languages.get_lang_code(language_from)
    lang_code_to = Languages.get_lang_code(language_to)
    print("lang code from: ", lang_code_from)
    print("lang code to: ", lang_code_to)
    TextProcess.create(language_from)
    
    _window = RTTWindow(hwnd, x, y, width, height, fps)
    _window.setWindowTitle(FULLSCREEN)
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
