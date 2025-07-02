from dataclasses import dataclass
from typing import List, Tuple, Set
import math

import mtranslate
from paddleocr import PaddleOCR
import cv2
from matplotlib import pyplot as plt
from PIL import Image
import time

@dataclass
class Rectangle:
    x: float
    y: float
    width: float
    height: float
    text: str

    def right(self):
        return self.x + self.width

    def bottom(self):
        return self.y + self.height

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
    return Rectangle(x_min, y_min, x_max - x_min, y_max - y_min, frase)

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

rectangles = []
distance_limit = 10

# Caminho da imagem
caminho_imagem = 'imgs\\3.png'  # Substitua pelo caminho da sua imagem

print("Criando leitor...")
# Inicializar o leitor com suporte ao idioma indonésio (por padrão o PaddleOCR é multilinguagem, se necessário altere o lang)
ocr = PaddleOCR(use_angle_cls=True,
                det_model_dir='models\\ch_ppocr_server_v2.0_det_infer',
                rec_model_dir='models\\ch_ppocr_server_v2.0_rec_infer',
                cls_model_dir='models\\ch_ppocr_mobile_v2.0_cls_infer',
                ocr_version='PP-OCRv4',
                use_space_char=True,
                unclip_ratio= 0.8,
                use_dilation= True,
                det_db_box_thresh=0.6,
                det_db_unclip_ratio=1.6, # No "imgs\\dialogue.png" o 1.6 funfa melhor, 
                                         # já no "imgs\\chrono.png" o 1.0 funfa melhor,
                                         # e no jjk funfa melhor o 1.0, mas no jjk1 funfa melhor o 1.6
                lang='en')  # pode trocar para 'en' ou 'en+pt'
print("Leitor criado!")

image_scale = 1.0  # Fator de escala para redimensionamento

print("Redimensionando imagem...")
img = Image.open(caminho_imagem)
img_resized = img.resize((int(img.width // image_scale), int(img.height // image_scale)))
img_resized_path = "imgs\\imagem_reduzida.png"
img_resized.save(img_resized_path)
print("Imagem redimensionada!")

inicio = time.time()

print("Lendo imagem...")
# Ler o texto da imagem com paddleocr
resultados = ocr.ocr(img_resized_path, cls=True)[0]
print("Imagem lida!")

fim = time.time()
print("Tempo de execução: ", fim - inicio, " segundos")

imagem = cv2.imread(caminho_imagem)

for resultado in resultados:
    bbox, (texto, confianca) = resultado

    x_coords = [p[0] for p in bbox]
    y_coords = [p[1] for p in bbox]
    x_min = int(min(x_coords) * image_scale)
    y_min = int(min(y_coords) * image_scale)
    x_max = int(max(x_coords) * image_scale)
    y_max = int(max(y_coords) * image_scale)

    rect = Rectangle(x_min, y_min, x_max - x_min, y_max - y_min, texto)
    rectangles.append(rect)

resultado = find_and_merge_close_rectangles(rectangles, max_distance=10)

for rect in resultado:
    top_left = (int(rect.x), int(rect.y))
    bottom_right = (int(rect.x + rect.width), int(rect.y + rect.height))
    cv2.rectangle(imagem, top_left, bottom_right, (0, 255, 0), 2)
    print(rect.text)
    # print(mtranslate.translate(rect.text, "pt"))

imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
plt.imshow(imagem_rgb)
plt.axis('off')
plt.show()
