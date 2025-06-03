from paddleocr import PaddleOCR
import numpy as np
from typing import List
from PIL import Image
import cv2
import Code.Rectangle as Rectangle
from typing import List, Tuple, Optional
from PyQt5 import QtGui

_ocr: PaddleOCR

def create(lang: str, use_model: bool = True, det_db_unclip_ratio: float = 1.6) -> None:
    global _ocr
    if use_model:
        _ocr = PaddleOCR(use_angle_cls=True,
                        #  det_model_dir='models\\ch_ppocr_server_v2.0_det_infer',
                        #  rec_model_dir='models\\ch_ppocr_server_v2.0_rec_infer',
                         det_model_dir='models\\en_PP-OCRv3_det_infer',
                         rec_model_dir='models\\en_PP-OCRv3_rec_infer',
                         cls_model_dir='models\\ch_ppocr_mobile_v2.0_cls_infer',
                         ocr_version='PP-OCRv4',
                         use_space_char=True,
                         unclip_ratio=0.8,
                         use_dilation=True,
                         det_db_box_thresh=0.6,
                         det_db_unclip_ratio=det_db_unclip_ratio,
                         lang=lang)
    else:
        _ocr = PaddleOCR(use_angle_cls=True,
                         ocr_version='PP-OCRv4',
                         use_space_char=True,
                         unclip_ratio=0.8,
                         use_dilation=True,
                         det_db_box_thresh=0.6,
                         det_db_unclip_ratio=det_db_unclip_ratio,
                         lang=lang)
    print("OCR CRIADO COM O LANG = \"", lang, "\"")

def pil_to_cv(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)

def cv_to_pil(image: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

def get_rectangles_from_pil(image: Image.Image, image_scale: float = 1.0, max_gap_distance: int = 10) -> List[Rectangle.Rectangle]:
    image_cv = pil_to_cv(image)
    rectangles = []

    resultados = _ocr.ocr(image_cv, cls=True)[0]

    for resultado in resultados:
        bbox, (texto, confianca) = resultado

        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x_min = int(min(x_coords) * image_scale)
        y_min = int(min(y_coords) * image_scale)
        x_max = int(max(x_coords) * image_scale)
        y_max = int(max(y_coords) * image_scale)

        rect = Rectangle.Rectangle(x_min, y_min, x_max - x_min, y_max - y_min, texto, '')
        rectangles.append(rect)

    return Rectangle.find_and_merge_close_rectangles(rectangles, max_distance=max_gap_distance)

def inpaint_area_regions_from_pil(image: Image.Image, rectangles: List[Rectangle.Rectangle]) -> List[Image.Image]:
    image_cv = pil_to_cv(image)
    altura, largura = image_cv.shape[:2]
    mascara = np.zeros((altura, largura), dtype=np.uint8)

    for rect in rectangles:
        x1 = int(rect.x)
        y1 = int(rect.y)
        x2 = int(rect.x + rect.width)
        y2 = int(rect.y + rect.height)
        cv2.rectangle(mascara, (x1, y1), (x2, y2), 255, thickness=cv2.FILLED)

    image_inpainted = cv2.inpaint(image_cv, mascara, 3, cv2.INPAINT_TELEA)

    regioes = []
    for rect in rectangles:
        x1 = int(rect.x)
        y1 = int(rect.y)
        x2 = int(rect.x + rect.width)
        y2 = int(rect.y + rect.height)
        crop = image_inpainted[y1:y2, x1:x2]
        regioes.append(cv_to_pil(crop))

    return regioes

def crop_regions_from_pil(image: Image.Image, rectangles: List[Rectangle.Rectangle]) -> List[Image.Image]:
    """
    Recorta regiões da imagem original com base em uma lista de retângulos.

    Args:
        image: imagem PIL original.
        rectangles: lista de objetos Rectangle com as áreas a serem recortadas.

    Returns:
        Lista de imagens PIL recortadas.
    """
    image_cv = pil_to_cv(image)
    regioes = []

    for rect in rectangles:
        x1 = int(rect.x)
        y1 = int(rect.y)
        x2 = int(rect.x + rect.width)
        y2 = int(rect.y + rect.height)
        crop = image_cv[y1:y2, x1:x2]
        regioes.append(cv_to_pil(crop))

    return regioes

def find_subimage(image: np.ndarray, subimage: np.ndarray, threshold: float = 0.95) -> List[Tuple[int, int]]:
    """
    Encontra todas as ocorrências de uma subimagem dentro de uma imagem maior.

    Args:
        image: imagem onde procurar (np.ndarray)
        subimage: imagem a ser procurada (np.ndarray)
        threshold: valor de similaridade (0.0 a 1.0), mais alto = mais exato

    Returns:
        Lista de coordenadas (x, y) do canto superior esquerdo das ocorrências
    """
    # Converte para escala de cinza
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(subimage, cv2.COLOR_BGR2GRAY)

    # Aplica a correspondência de template
    resultado = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)

    # Encontra todas as localizações onde a similaridade excede o limiar
    locais = np.where(resultado >= threshold)

    # Converte para lista de tuplas (x, y)
    posicao = list(zip(locais[1], locais[0]))  # (coluna, linha) → (x, y)

    if not posicao:
        return None

    return posicao[0]

def find_subimage_exact(image: np.ndarray, subimage: np.ndarray, tolerance: float = 1e-1) -> Optional[Tuple[int, int]]:
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if len(subimage.shape) == 3:
        subimage = cv2.cvtColor(subimage, cv2.COLOR_BGR2GRAY)

    image = image.astype(np.float32)
    subimage = subimage.astype(np.float32)

    resultado = cv2.matchTemplate(image, subimage, cv2.TM_SQDIFF_NORMED)
    min_val, _, min_loc, _ = cv2.minMaxLoc(resultado)

    if min_val <= tolerance:
        return min_loc
    else:
        return None

def get_contrast_color(pil_image: Image.Image) -> QtGui.QColor:
    # Reduz o tamanho da imagem para acelerar o processamento
    small_img = pil_image.resize((50, 50))
    small_img = small_img.convert('RGB')
    
    # Pega todos os pixels e calcula a média R, G, B
    pixels = list(small_img.getdata())
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)

    # Cálculo da luminância perceptual (ITU-R BT.709)
    luminance = 0.2126 * avg_r + 0.7152 * avg_g + 0.0722 * avg_b

    # Se a luminância for alta, retorna preto. Caso contrário, branco.
    return QtGui.QColor('black') if luminance > 128 else QtGui.QColor('white')


# from numba import njit

# @njit
# def _buscar_subimagem_gray(maior, menor):
#     ih, iw = maior.shape
#     sh, sw = menor.shape

#     for y in range(ih - sh + 1):
#         for x in range(iw - sw + 1):
#             match = True
#             for dy in range(sh):
#                 for dx in range(sw):
#                     if maior[y + dy, x + dx] != menor[dy, dx]:
#                         match = False
#                         break
#                 if not match:
#                     break
#             if match:
#                 return x, y
#     # print("not found")
#     return -1, -1

# def encontrar_subimagem_exata(imagem_maior, subimagem):
#     """
#     Busca por correspondência exata da subimagem na imagem maior.
#     Converte ambas para escala de cinza (uint8) antes da comparação.

#     Parâmetros:
#         imagem_maior (np.ndarray): Imagem principal (qualquer formato).
#         subimagem (np.ndarray): Subimagem (template).

#     Retorna:
#         tuple | None: (x, y) da posição onde a subimagem foi encontrada, ou None.
#     """
#     # Converte para escala de cinza se for colorido
#     if len(imagem_maior.shape) == 3:
#         imagem_maior = cv2.cvtColor(imagem_maior, cv2.COLOR_BGR2GRAY)
#     if len(subimagem.shape) == 3:
#         subimagem = cv2.cvtColor(subimagem, cv2.COLOR_BGR2GRAY)

#     # Garante o tipo uint8
#     imagem_maior = imagem_maior.astype(np.uint8)
#     subimagem = subimagem.astype(np.uint8)

#     x, y = _buscar_subimagem_gray(imagem_maior, subimagem)

#     return (x, y) if x != -1 else None
