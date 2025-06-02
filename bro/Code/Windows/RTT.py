import tkinter as tk
import Code.WindowScreenshot as WindowScreenshot
import Code.Ocr as Ocr
from typing import List
from PIL import Image, ImageTk
import Code.Rectangle as Rectangle
import uuid

_window_name: str
_fps: int
_root: tk.Tk = None
_exist: bool = False
_after_id = None  # ID do after para cancelamento
_canvas : tk.Canvas
_dimension : tuple

class _SubImageText():
    text: str
    translated_text: str
    cropped_img: Image
    photo_img: ImageTk.PhotoImage
    id: str

    def __init__(self, text : str, translated_text : str, cropped_img: Image.Image, inpainted_img: Image.Image, id:str):
        self.text = text
        self.translated_text = translated_text
        self.cropped_img = cropped_img
        self.photo_img = ImageTk.PhotoImage(inpainted_img)
        self.id = id

_last_sub_images: List[_SubImageText] = []

def create(window_name: str, x, y, width, height, FPS: int) -> None:
    global _root, _fps, _exist, _after_id, _window_name, _dimension, _canvas
    Ocr.create('en')
    _fps = FPS
    _window_name = window_name
    _dimension = (x, y, width, height)

    if _exist:
        quit()
    else:
        _exist = True

    _root = tk.Tk()
    _root.wm_title("RTT")
    _root.overrideredirect(True)
    # _root.attributes("-transparentcolor", "white")  # habilite se quiser transparência
    _root.attributes("-topmost", True)
    _root.attributes("-disabled", True)
    _root.geometry(f"{width}x{height}+{x}+{y}")

    _canvas = tk.Canvas(_root, width=width, height=height, bg="white", highlightthickness=0)
    _canvas.pack()

    _update()
    try:
        _root.mainloop()
    except:
        pass

def exists() -> bool:
    global _exist
    return _exist

def quit() -> None:
    global _root, _exist, _after_id

    if _root is not None:
        if _after_id is not None:
            try:
                _root.after_cancel(_after_id)
            except:
                pass  # Pode já estar destruída

        try:
            _root.quit()
            _root.destroy()
        except:
            pass

    _exist = False
    _root = None
    _after_id = None

def _update() -> None:
    global _fps, _root, _after_id

    if _root is None:
        return

    #!

    _frame()

    #!

    try:
        _after_id = _root.after(int(1000 / _fps), _update)
    except:
        _after_id = None  # Falha ao agendar, provavelmente já destruída

def _frame() -> None:
    global _window_name, _root, _dimension, _canvas, _last_sub_images
    print("oi")
    result = WindowScreenshot.getWindowScreenshot(_window_name)
    if not result:
        print("A janela não está sendo encontrada!")

    if result[1] != _dimension[0] or result[2] != _dimension[1] or result[3] != _dimension[2] or result[4] != _dimension[3]:
        _root.geometry(f"{result[3]}x{result[4]}+{result[1]}+{result[2]}")
        _dimension = (result[1], result[2], result[3], result[4])
        _canvas.config(width=result[3], height=result[4])
    
    rectangles = Ocr.get_rectangles_from_pil(result[0], max_gap_distance=10)
    cropped_imgs = Ocr.crop_regions_from_pil(result[0], rectangles)
    inpainted_imgs = Ocr.inpaint_area_regions_from_pil(result[0], rectangles)
    
    sub_img: _SubImageText
    for sub_img in _last_sub_images:
        pos = Ocr.find_subimage(result[0], Ocr.pil_to_cv(sub_img.cropped_img), 0.97)
        if pos:
            _canvas.move(sub_img.id, pos[0], pos[1])
            if sub_img.cropped_img in cropped_imgs:
                cropped_imgs.remove(sub_img.cropped_img)
                print("tinha")
        else:
            _canvas.delete(sub_img.id)
    
    for i in range(len(cropped_imgs)):
        new_sub_img = _SubImageText(rectangles[i].text, '', cropped_imgs[i], inpainted_imgs[i],_get_id())
        _canvas.create_image(rectangles[i].x, rectangles[i].y, image=new_sub_img.photo_img, tags=new_sub_img.id)

def _get_id() -> str:
    return str(uuid.uuid4())