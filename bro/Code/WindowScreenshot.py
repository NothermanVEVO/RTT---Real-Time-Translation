import pygetwindow
import ctypes, win32con, win32gui
import win32clipboard as w32clip
from struct import pack, calcsize
from ctypes import windll
from PIL import Image
from typing import List

# _user32,_gdi32 = windll.user32,windll.gdi32
# _PW_RENDERFULLCONTENT = 2

# # if you use a high DPI display or >100% scaling size
# try:
#     windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
# except Exception:
#     windll.user32.SetProcessDPIAware()  # fallback

# def get_window_area_precise(hwnd):
#     left, top, right, bottom = win32gui.GetWindowRect(hwnd)
#     win_width = right - left
#     win_height = bottom - top

#     client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
#     client_rect = win32gui.GetClientRect(hwnd)
#     client_width = client_rect[2]
#     client_height = client_rect[3]

#     border_left = client_x - left
#     # border_top = client_y - top  # Não usado diretamente

#     corrected_left = left + border_left
#     corrected_top = top
#     corrected_height = client_height + (client_y - top)

#     return corrected_left, corrected_top, client_width, corrected_height

# def _getWindowBMAP(hwnd,returnImage=False):
#     # usa a nova função para pegar posição e tamanho corretos
#     x, y, w, h = get_window_area_precise(hwnd)

#     # Cria DCs e bitmaps
#     dc = _user32.GetWindowDC(hwnd)
#     dc1 = _gdi32.CreateCompatibleDC(dc)
#     dc2 = _gdi32.CreateCompatibleDC(dc)
#     bmp1 = _gdi32.CreateCompatibleBitmap(dc, w, h)
#     bmp2 = _gdi32.CreateCompatibleBitmap(dc, w, h)

#     # Renderiza a janela para dc1
#     obj1 = _gdi32.SelectObject(dc1, bmp1)
#     _user32.PrintWindow(hwnd, dc1, _PW_RENDERFULLCONTENT)

#     # Copia a imagem renderizada para dc2 (bitmap final)
#     obj2 = _gdi32.SelectObject(dc2, bmp2)
#     _gdi32.BitBlt(dc2, 0, 0, w, h, dc1, 0, 0, win32con.SRCCOPY)

#     # Restaura os objetos selecionados
#     _gdi32.SelectObject(dc1, obj1)
#     _gdi32.SelectObject(dc2, obj2)

#     if returnImage:
#         data = ctypes.create_string_buffer((w*4)*h)
#         bmi = ctypes.c_buffer(pack("IiiHHIIiiII", calcsize("IiiHHIIiiII"), w, -h, 1, 32, 0, 0, 0, 0, 0, 0))
#         _gdi32.GetDIBits(dc2, bmp2, 0, h, ctypes.byref(data), ctypes.byref(bmi), win32con.DIB_RGB_COLORS)
#         img = Image.frombuffer('RGB', (w, h), data, 'raw', 'BGRX')
#     else:
#         img = None

#     # Limpeza
#     _gdi32.DeleteObject(bmp1)
#     _gdi32.DeleteObject(bmp2)
#     _gdi32.DeleteDC(dc1)
#     _gdi32.DeleteDC(dc2)
#     _user32.ReleaseDC(hwnd, dc)

#     return (bmp2, w, h, img) if returnImage else (bmp2, w, h)

# def _copyBitmap(hbmp):
#     w32clip.OpenClipboard()
#     w32clip.EmptyClipboard()
#     w32clip.SetClipboardData(w32clip.CF_BITMAP, hbmp)
#     w32clip.CloseClipboard()

# def _copySnapshot(hwnd):
#     hbmp, w, h = _getWindowBMAP(hwnd)
#     _copyBitmap(hbmp)
#     _gdi32.DeleteObject(hbmp)

# def _getSnapshot(hwnd):
#     hbmp, w, h, img = _getWindowBMAP(hwnd, True)
#     _gdi32.DeleteObject(hbmp)
#     return img

# def getWindowScreenshot(window_name: str):
#     hwnd = _user32.FindWindowW(None, window_name)
#     if not hwnd:
#         return None
#     elif _user32.IsIconic(hwnd):
#         return None
#     else:
#         img = _getSnapshot(hwnd)
#         x, y, w, h = get_window_area_precise(hwnd)
#         return img, x, y, w, h

# def getWindowsNames() -> List[str]:
#     return pygetwindow.getAllTitles()

##! ANTIGO

_user32,_gdi32 = windll.user32,windll.gdi32
_PW_RENDERFULLCONTENT = 2

_X = 0
_Y = 0
_WIDTH = 0
_HEIGHT = 0

# if you use a high DPI display or >100% scaling size
# windll.user32.SetProcessDPIAware()
try:
    windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
except Exception:
    windll.user32.SetProcessDPIAware()  # fallback

# ADAPTED
## https://stackoverflow.com/questions/19695214/screenshot-of-inactive-window-printwindow-win32gui

def _getWindowBMAP(hwnd,returnImage=False):
    global _X, _Y, _WIDTH, _HEIGHT
    # get Window size and crop pos/size
    L,T,R,B = win32gui.GetWindowRect(hwnd); W,H = R-L,B-T
    
    _X = L
    _Y = T

    x,y,w,h = (8,8,W-16,H-16) if _user32.IsZoomed(hwnd) else (7,0,W-14,H-7)
    _WIDTH = w
    _HEIGHT = h

    if w <= 0 or h <= 0:
        # print(f"[ERRO] Tamanho inválido: w={w}, h={h} (Window: {win32gui.GetWindowText(hwnd)})")
        return (None, w, h, None) if returnImage else (None, w, h)

    # create dc's and bmp's
    dc = _user32.GetWindowDC(hwnd)
    dc1,dc2 = _gdi32.CreateCompatibleDC(dc),_gdi32.CreateCompatibleDC(dc)
    bmp1,bmp2 = _gdi32.CreateCompatibleBitmap(dc,W,H),_gdi32.CreateCompatibleBitmap(dc,w,h)

    # render dc1 and dc2 (bmp1 and bmp2) (uncropped and cropped)
    obj1,obj2 = _gdi32.SelectObject(dc1,bmp1),_gdi32.SelectObject(dc2,bmp2) # select bmp's into dc's
    _user32.PrintWindow(hwnd,dc1,_PW_RENDERFULLCONTENT) # render window to dc1
    _gdi32.BitBlt(dc2,0,0,w,h,dc1,x,y,win32con.SRCCOPY) # copy dc1 (x,y,w,h) to dc2 (0,0,w,h)
    _gdi32.SelectObject(dc1,obj1); _gdi32.SelectObject(dc2,obj2) # restore dc's default obj's

    if returnImage: # create Image from bmp2
        data = ctypes.create_string_buffer((w*4)*h)
        bmi = ctypes.c_buffer(pack("IiiHHIIiiII",calcsize("IiiHHIIiiII"),w,-h,1,32,0,0,0,0,0,0))
        _gdi32.GetDIBits(dc2,bmp2,0,h,ctypes.byref(data),ctypes.byref(bmi),win32con.DIB_RGB_COLORS)
        img = Image.frombuffer('RGB',(w,h),data,'raw','BGRX')

    # clean up
    _gdi32.DeleteObject(bmp1) # delete bmp1 (uncropped)
    _gdi32.DeleteDC(dc1); _gdi32.DeleteDC(dc2) # delete created dc's
    _user32.ReleaseDC(hwnd,dc) # release retrieved dc

    return (bmp2,w,h,img) if returnImage else (bmp2,w,h)

def _copyBitmap(hbmp): # copy HBITMAP to clipboard
    w32clip.OpenClipboard(); w32clip.EmptyClipboard()
    w32clip.SetClipboardData(w32clip.CF_BITMAP,hbmp); w32clip.CloseClipboard()

def _copySnapshot(hwnd): # copy Window HBITMAP to clipboard
    hbmp,w,h = _getWindowBMAP(hwnd); _copyBitmap(hbmp); _gdi32.DeleteObject(hbmp)

def _getSnapshot(hwnd): # get Window HBITMAP as Image
    hbmp,w,h,img = _getWindowBMAP(hwnd,True); _gdi32.DeleteObject(hbmp); return img

# def getWindowScreenshot(window_name : str):

#     hwnd = None
#     if not hwnd: hwnd = _user32.FindWindowW(None, window_name)      # 1 Argument: ClassName | 2 Argument: WindowName

#     if not hwnd:
#         # print("Couldn't find Window")
#         return None
#     elif _user32.IsIconic(hwnd):
#         # print("Window is minimized")
#         return None
#     else:
#         # print(win32gui.GetWindowText(hwnd))
#         # print(win32gui.GetClassName(hwnd))
#         # _copySnapshot(hwnd) #? TIRA UM PRINT DA TELA E DEIXA NO CLIPBOARD!
#         img = _getSnapshot(hwnd)
#         x, y, w, h = _get_full_window(hwnd)
#         # return img, _X, _Y, _WIDTH, _HEIGHT
#         return img, x, y, w, h
def isWindowIconic(hwnd: int) -> bool:
    return win32gui.IsIconic(hwnd)

def isWindowInFullFocus(hwnd: int, exceptions: List[str] = []) -> bool:
    visible_windows = getAllVisibleWindows()
    to_remove = []
    for exception in exceptions:
        for _hwnd, title in visible_windows:
            if title == exception:
                to_remove.append((_hwnd, title))

    for item in to_remove:
        visible_windows.remove(item)
    
    _hwnd, _title = visible_windows[0]
    # print("INPUT: ", hwnd, " | ACHADO: ", _hwnd)
    return _hwnd == hwnd

def getAllVisibleWindows():
    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            title = win32gui.GetWindowText(hwnd)
            windows.append((hwnd, title))

    win32gui.EnumWindows(callback, None)
    return windows

def getWindowScreenshotByName(window_name: str, ignore_titles : List[str] = []):
    hwnds = find_all_windows_by_title(window_name)

    if not hwnds:
        return None

    ignore_titles_copy = ignore_titles.copy()
    to_remove = []
    for window in hwnds:
        if window_name in ignore_titles_copy:
            to_remove.append(window)
            ignore_titles_copy.remove(window_name)
    for window in to_remove:
        hwnds.remove(window)
    
    hwnd = hwnds[0]

    if win32gui.IsIconic(hwnd):
        return None

    img = _getSnapshot(hwnd)
    x, y, w, h = _get_full_window(hwnd)
    return img, x, y, w, h

def getWindowScreenshot(hwnd: int):
    if win32gui.IsIconic(hwnd):
        return None

    img = _getSnapshot(hwnd)
    x, y, w, h = _get_full_window(hwnd)
    return img, x, y, w, h

def getFullScreenshot(exceptions: List[str] = []):
    names = getWindowsNames()
    name: str
    results = []

    ignore_titles = []
    for name in reversed(names):
        if name in exceptions:
            continue
        if not len(name) == 0 and not name.isspace():
            result = getWindowScreenshotByName(name, ignore_titles)
            if result and result[0]:
                results.append(result)
                ignore_titles.append(name)

    if len(results) != 0:
        image = results[0][0]
        for result in results[1:]:
            overlay = result[0].convert("RGBA")
            # print("position: ", (result[1], result[2]))
            image.paste(overlay, (result[1], result[2]), overlay)

        # if len(exceptions) != 0: image.show()
        return image
    return None

def getWindowsNames() -> List:
    return pygetwindow.getAllTitles()

def enum_windows_callback(hwnd, results):
    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
        results.append(hwnd)

def find_all_windows_by_title(title):
    hwnds = []
    win32gui.EnumWindows(enum_windows_callback, hwnds)
    return [hwnd for hwnd in hwnds if win32gui.GetWindowText(hwnd) == title]

def _get_full_window(hwnd):
    # Retângulo da janela (inclui bordas e título)
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)

    # Posição da área cliente na tela
    client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
    client_rect = win32gui.GetClientRect(hwnd)
    client_width = client_rect[2]
    client_height = client_rect[3]

    # Cálculo das bordas
    border_left = client_x - left

    # Correções
    corrected_left = left + border_left  # Ajusta X
    corrected_top = top                  # Usa top diretamente
    corrected_height = client_height + (client_y - top)  # Soma altura do título/borda

    return corrected_left, corrected_top, client_width, corrected_height

def _get_no_border_window(hwnd):
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.GetClientRect(hwnd)[2:]
    width = right
    height = bottom
    return left, top, width, height

# # print(pygetwindow.getAllTitles())
# # img = getWindowScreenshot("Pip install win32gui : r/learnpython - Google Chrome")
# # if img != -1 and img != None:
# #     img[0].show()
# #     print(type(img[0]))
# #     print(img[1])
# #     print(img[2])