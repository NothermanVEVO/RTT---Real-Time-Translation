from unidecode import unidecode
from collections import defaultdict
import re

# Caminho para o dicionário original
entrada = "dictionary\\2018\\vi\\vi_50k.txt"
# Caminho para o novo dicionário sem acento
saida = "dictionary\\2018\\vi\\vi_no_accent_50k.txt"

dicionario_sem_acento = defaultdict(int)

with open(entrada, "r", encoding="utf-8") as arquivo:
    for linha in arquivo:
        partes = linha.strip().split()

        if len(partes) != 2:
            continue

        palavra, freq = partes
        palavra = re.sub(r"^[^\w]+|[^\w]+$", "", palavra)

        try:
            freq = int(freq)
        except ValueError:
            continue

        palavra_sem_acento = unidecode(palavra).lower()

        if palavra_sem_acento.isalpha() and len(palavra_sem_acento) > 1:
            dicionario_sem_acento[palavra_sem_acento] += freq

# Ordenar por frequência decrescente
with open(saida, "w", encoding="utf-8") as out:
    for palavra, freq in sorted(dicionario_sem_acento.items(), key=lambda x: x[1], reverse=True):
        out.write(f"{palavra} {freq}\n")

print("Dicionário ordenado por frequência gerado com sucesso!")