import math
from typing import List, Set

class Rectangle:
    x: float
    y: float
    width: float
    height: float
    text: str
    translated_text: str

    def __init__(self, x :float, y :float, width :float, height :float, text : str, translated_text : str):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.translated_text = translated_text

    def right(self) -> float:
        return self.x + self.width

    def bottom(self) -> float:
        return self.y + self.height

def rectangles_intersect(r1: Rectangle, r2: Rectangle) -> bool:
    return not (r1.x + r1.width < r2.x or r1.x > r2.x + r2.width or
                r1.y + r1.height < r2.y or r1.y > r2.y + r2.height)

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