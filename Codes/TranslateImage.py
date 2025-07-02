from symspellpy import SymSpell

from dataclasses import dataclass
from typing import List, Tuple, Set
import math

import mtranslate
from paddleocr import PaddleOCR
import cv2
from matplotlib import pyplot as plt
from PIL import Image
import time
import numpy as np

import textwrap
import re

@dataclass
class Rectangle:
    x: float
    y: float
    width: float
    height: float
    text: str
    translated_text: str

    def right(self):
        return self.x + self.width

    def bottom(self):
        return self.y + self.height

def resize_image(image_path : str, image_scale : float) -> str:
    print("Redimensionando imagem...")
    img = Image.open(image_path)
    img_resized = img.resize((int(img.width // image_scale), int(img.height // image_scale)))
    img_resized_path = "imgs\\imagem_reduzida.png"
    img_resized.save(img_resized_path)
    print("Imagem redimensionada!")
    return img_resized_path

def get_rectangles(ocr : PaddleOCR, img_resized_path : str, image_scale : float = 1.0, max_gap_distance : int = 10) -> List[Rectangle]:
    rectangles = []
    inicio = time.time()
    print("Lendo imagem...")
    # Ler o texto da imagem com paddleocr
    resultados = ocr.ocr(img_resized_path, cls=True)[0]
    print("Imagem lida!")

    fim = time.time()
    print("Tempo de execução: ", fim - inicio, " segundos")

    for resultado in resultados:
        bbox, (texto, confianca) = resultado

        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x_min = int(min(x_coords) * image_scale)
        y_min = int(min(y_coords) * image_scale)
        x_max = int(max(x_coords) * image_scale)
        y_max = int(max(y_coords) * image_scale)

        rect = Rectangle(x_min, y_min, x_max - x_min, y_max - y_min, texto, '')
        rectangles.append(rect)

    return find_and_merge_close_rectangles(rectangles, max_distance=max_gap_distance)

def distance_between_rects(r1: Rectangle, r2: Rectangle) -> float:
    dx = max(r2.x - r1.right(), r1.x - r2.right(), 0)
    dy = max(r2.y - r1.bottom(), r1.y - r2.bottom(), 0)
    return math.hypot(dx, dy)

def ordenar_por_linha_e_coluna(rects: List[Rectangle], linha_tolerancia: float = 15.0) -> List[Rectangle]:
    linhas: List[List[Rectangle]] = []
    for rect in sorted(rects, key=lambda r: r.y):
        colocado = False
        for linha in linhas:
            if abs(linha[0].y - rect.y) <= linha_tolerancia:
                linha.append(rect)
                colocado = True
                break
        if not colocado:
            linhas.append([rect])
    for linha in linhas:
        linha.sort(key=lambda r: r.x)
    ordenados = []
    for linha in linhas:
        ordenados.extend(linha)
    return ordenados

def merge_rectangles_list(rects: List[Rectangle]) -> Rectangle:
    ordenados = ordenar_por_linha_e_coluna(rects)
    frase = ' '.join(r.text for r in ordenados)
    x_min = min(r.x for r in rects)
    y_min = min(r.y for r in rects)
    x_max = max(r.right() for r in rects)
    y_max = max(r.bottom() for r in rects)
    return Rectangle(x_min, y_min, x_max - x_min, y_max - y_min, frase, '')

def find_connected_groups(rectangles: List[Rectangle], max_distance: float) -> List[Set[int]]:
    n = len(rectangles)
    visited = [False] * n
    groups = []
    def dfs(i, group):
        visited[i] = True
        group.add(i)
        for j in range(n):
            if not visited[j] and distance_between_rects(rectangles[i], rectangles[j]) <= max_distance:
                dfs(j, group)
    for i in range(n):
        if not visited[i]:
            group = set()
            dfs(i, group)
            groups.append(group)
    return groups

def find_and_merge_close_rectangles(rectangles: List[Rectangle], max_distance: float) -> List[Rectangle]:
    groups = find_connected_groups(rectangles, max_distance)
    merged = [merge_rectangles_list([rectangles[i] for i in group]) for group in groups]
    return merged

def inpaint_area(image_path: str, rectangles: List[Rectangle]) -> str:
    # Carrega a imagem
    imagem = cv2.imread(image_path)
    altura, largura = imagem.shape[:2]

    # Cria uma máscara em branco (mesmo tamanho da imagem)
    mascara = np.zeros((altura, largura), dtype=np.uint8)

    # Preenche a máscara com os retângulos das regiões de texto
    for rect in rectangles:
        x1 = int(rect.x)
        y1 = int(rect.y)
        x2 = int(rect.x + rect.width)
        y2 = int(rect.y + rect.height)
        cv2.rectangle(mascara, (x1, y1), (x2, y2), 255, thickness=cv2.FILLED)

    # Aplica o inpainting para remover o texto
    imagem_sem_texto = cv2.inpaint(imagem, mascara, 3, cv2.INPAINT_TELEA)

    font = cv2.FONT_HERSHEY_COMPLEX
    font_size = 0.7
    font_thickness = 1

    for rect in rectangles:
        org = (rect.x, rect.y)
        # print("texto: ", rect.translated_text)
        largura_char = cv2.getTextSize("A", font, font_size, font_thickness)[0][0]
        max_chars_por_linha = int(rect.width // largura_char)
        wrapped_text = textwrap.wrap(rect.translated_text, width=max_chars_por_linha)
        for i, line in enumerate(wrapped_text):
            textsize = cv2.getTextSize(line, font, font_size, font_thickness)[0]

            gap = textsize[1] + 10

            y = rect.y + (i * gap)
            x = rect.x

            cv2.putText(imagem_sem_texto, line, (x, y), font,
                        font_size, 
                        (0,0,255), 
                        font_thickness, 
                        cv2.LINE_AA)

    # Salva ou exibe o resultado
    cv2.imwrite('imgs\\inpainted.png', imagem_sem_texto)
    return 'imgs\\inpainted.png'

# def force_split(word: str, sym_spell: SymSpell, min_freq: int = 10):
#     word = word.lower()

#     # Se a palavra já existe no dicionário, não precisa segmentar
#     if word in sym_spell._words:
#         return word

#     best = (word, 0)

#     for i in range(1, len(word)):
#         left = word[:i]
#         right = word[i:]
#         freq_left = sym_spell._words.get(left, 0)
#         freq_right = sym_spell._words.get(right, 0)

#         if freq_left >= min_freq and freq_right >= min_freq:
#             total_freq = freq_left + freq_right
#             if total_freq > best[1]:
#                 best = (f"{left} {right}", total_freq)

#     return best[0]

# def correct_phrase(text: str) -> str:
#     words = text.lower().split()
#     corrected_parts = []

#     for word in words:
#         # Primeiro tenta separar se não existir
#         possibly_split = force_split(word, sym_spell)
#         print("Possibly split: ", possibly_split)

#         # Depois corrige com lookup_compound
#         suggestions = sym_spell.lookup_compound(possibly_split, max_edit_distance=2)
#         if suggestions:
#             corrected_parts.append(suggestions[0].term)
#         else:
#             corrected_parts.append(possibly_split)

#     return ' '.join(corrected_parts)

############################################?

# def is_expression(word: str) -> bool:
#     return bool(re.fullmatch(r'[\d]+([\+\-\*/=][\d]+)+', word))

# def force_split(word: str, sym_spell: SymSpell, min_freq: int = 10) -> str:
#     word = word.lower()

#     # Se for expressão matemática, não dividir
#     if is_expression(word):
#         return word

#     # Se for algo como "equals2" → "equals 2"
#     match = re.match(r"^([a-zA-Z]+)([0-9]+)$", word)
#     if match:
#         return f"{match.group(1)} {match.group(2)}"

#     if word in sym_spell._words:
#         return word

#     best = (word, 0)

#     for i in range(1, len(word)):
#         left = word[:i]
#         right = word[i:]
#         freq_left = sym_spell._words.get(left, 0)
#         freq_right = sym_spell._words.get(right, 0)

#         if left in sym_spell._words and right in sym_spell._words:
#             if freq_left >= min_freq and freq_right >= min_freq:
#                 total_freq = freq_left + freq_right
#                 if total_freq > best[1]:
#                     best = (f"{left} {right}", total_freq)

#     return best[0]

# def correct_phrase(text: str) -> str:
#     tokens = re.findall(r'\w+[^\w\s]*|\S', text.lower())
#     corrected_parts = []

#     for token in tokens:
#         # separa palavra da pontuação (ex: "equals2." → "equals2", ".")
#         match = re.match(r"^([a-zA-Z0-9]+)([^\w\s]*)$", token)
#         if match:
#             word, punct = match.groups()
#         else:
#             word, punct = token, ""

#         if is_expression(word) or word.isdigit():
#             corrected = word
#         else:
#             possibly_split = force_split(word, sym_spell)

#             if any(char.isdigit() for char in possibly_split):
#                 corrected = possibly_split
#             else:
#                 suggestions = sym_spell.lookup_compound(possibly_split, max_edit_distance=2)
#                 corrected = suggestions[0].term if suggestions else possibly_split

#         corrected_parts.append(corrected + punct)

#     return ' '.join(corrected_parts).replace(" .", ".").replace(" ,", ",").replace(" !", "!").replace(" ?", "?")

################################################?

# Lista de sufixos japoneses que devem manter o hífen
JAPANESE_SUFFIXES = {"-san", "-kun", "-chan", "-sama", "-sensei"}

def is_expression(word: str) -> bool:
    return bool(re.fullmatch(r'[\d]+([\+\-\*/=][\d]+)+', word))

def force_split(word: str, sym_spell: SymSpell, min_freq: int = 10) -> str:
    word = word.lower()

    if is_expression(word):
        return word

    match = re.match(r"^([a-zA-Z]+)([0-9]+)$", word)
    if match:
        return f"{match.group(1)} {match.group(2)}"

    if word in sym_spell._words:
        return word

    best = (word, 0)

    for i in range(1, len(word)):
        left = word[:i]
        right = word[i:]
        freq_left = sym_spell._words.get(left, 0)
        freq_right = sym_spell._words.get(right, 0)

        if left in sym_spell._words and right in sym_spell._words:
            if freq_left >= min_freq and freq_right >= min_freq:
                total_freq = freq_left + freq_right
                if total_freq > best[1]:
                    best = (f"{left} {right}", total_freq)

    return best[0]

def correct_phrase(text: str) -> str:
    # Divide mantendo pontuação e hífen em palavras
    tokens = re.findall(r'\w+(?:-\w+)?[^\w\s]*|\S', text.lower())
    corrected_parts = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # Tenta unir palavras com hífen no meio (ex: sur- + prised → surprised)
        match_hyphen = re.match(r"^(\w+)-$", token)
        if match_hyphen and i + 1 < len(tokens):
            prefix = match_hyphen.group(1)
            next_token = tokens[i + 1]

            japanese_combined = f"{prefix}-{next_token}"
            if f"-{next_token}" in JAPANESE_SUFFIXES:
                corrected_parts.append(japanese_combined)
                i += 2
                continue
            else:
                token = prefix + next_token
                i += 2  # Já lidou com os dois tokens

        else:
            i += 1  # avança normalmente caso não seja caso de hífen

        # separa palavra da pontuação (ex: "equals2." → "equals2", ".")
        match = re.match(r"^([a-zA-Z0-9\-]+)([^\w\s]*)$", token)
        if match:
            word, punct = match.groups()
        else:
            word, punct = token, ""

        # Preserva palavras com sufixos japoneses como estão (ex: "kamikawa-san")
        if any(word.endswith(suffix) for suffix in JAPANESE_SUFFIXES):
            corrected_parts.append(word + punct)
            continue

        if is_expression(word) or word.isdigit():
            corrected = word
        else:
            possibly_split = force_split(word, sym_spell)

            if any(char.isdigit() for char in possibly_split):
                corrected = possibly_split
            else:
                suggestions = sym_spell.lookup_compound(possibly_split, max_edit_distance=2)
                corrected = suggestions[0].term if suggestions else possibly_split

        corrected_parts.append(corrected + punct)

    # Corrige espaços antes de pontuação
    result = ' '.join(corrected_parts)
    result = re.sub(r"\s+([.,!?])", r"\1", result)

    return result

#! THE BEGGINING

# Inicializa com capacidade máxima de edição e tamanho do prefixo
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

# Carrega o dicionário (formato: palavra [tab] frequência)
success = sym_spell.load_dictionary("dictionary\\2018\\en\\en_50k.txt", term_index=0, count_index=1, encoding="utf-8")

print("Criando leitor...")
ocr = PaddleOCR(use_angle_cls=True,
                det_model_dir='models\\ch_ppocr_server_v2.0_det_infer',
                rec_model_dir='models\\ch_ppocr_server_v2.0_rec_infer',
                cls_model_dir='models\\ch_ppocr_mobile_v2.0_cls_infer',
                ocr_version='PP-OCRv4',
                use_space_char=True,
                unclip_ratio= 0.8,
                use_dilation= True,
                det_db_box_thresh=0.6,
                det_db_unclip_ratio=1.6, #TODO # No "imgs\\dialogue.png" o 1.6 funfa melhor, 
                                         # já no "imgs\\chrono.png" o 1.0 funfa melhor,
                                         # e no jjk funfa melhor o 1.0, mas no jjk1 funfa melhor o 1.6
                lang='en')  # pode trocar para 'en' ou 'en+pt'
# ocr = PaddleOCR(use_angle_cls=True, 
#                 det_model_dir='models\\ch_ppocr_server_v2.0_det_infer',
#                 rec_model_dir='models\\ch_ppocr_server_v2.0_rec_infer',
#                 cls_model_dir='models\\ch_ppocr_mobile_v2.0_cls_infer',
#                 use_space_char=True,
#                 unclip_ratio= 0.8,
#                 det_db_thresh = 0.4, 
#                 det_db_box_thresh = 0.6,
#                 det_db_unclip_ratio = 1.6, 
#                 max_batch_size = 32,
#                 det_limit_side_len = 1000, 
#                 det_db_score_mode = "slow", 
#                 dilation = False, 
#                 lang='en', 
#                 rec_char_type='en',
#                 ocr_version = "PP-OCRv4")
print("Leitor criado!")

image_path = "imgs\\ifny.jpg"
image_scale = 1.0  # Fator de escala para redimensionamento

beggining = time.time()

img_resized_path = resize_image(image_path, image_scale)

resultado = get_rectangles(ocr, img_resized_path, image_scale, max_gap_distance=20)

pseudo_end = time.time()

print("Tempo de execução antes da tradução: ", pseudo_end - beggining, " segundos")

imagem = cv2.imread(image_path)

for rect in resultado:
    top_left = (int(rect.x), int(rect.y))
    bottom_right = (int(rect.x + rect.width), int(rect.y + rect.height))
    cv2.rectangle(imagem, top_left, bottom_right, (0, 255, 0), 2)
    print("Text: ", rect.text)
    corrected_text = correct_phrase(rect.text)
    print("Adjusted Text: ", corrected_text)
    rect.translated_text = mtranslate.translate(corrected_text, "pt")
    print(rect.translated_text)
    print()
    # print(mtranslate.translate(rect.text, "pt"))

end = time.time()
print("Tempo de execução após tradução: ", end - beggining, " segundos")

# imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
# plt.imshow(imagem_rgb)
# plt.axis('off')
# plt.show()
cv2.imshow("Antes", imagem)

img = cv2.imread(inpaint_area(image_path, resultado))
cv2.imshow("Resultado", img)
cv2.waitKey(0)
cv2.destroyAllWindows()