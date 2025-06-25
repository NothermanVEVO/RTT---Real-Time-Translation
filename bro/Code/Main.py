# import TextProcess
# import mtranslate

# TextProcess.create("Vietnamita")

# """
# Antes do correção:  TEN TOILA CHAARI YASUMI
# Depois da correção:  ten to ila cha ari ya sumi
# Antes do correção:  TOI DEP CHOI TRAI, THE THAO HOC TOT, DA GIOI vAy CON GIAU co
# Depois da correção:  toi dep choi trai, the thao hoc tot, da gi oi vay con gia u co
# Antes do correção:  TOI 15 TUOI vA LA1 HOC SINH CAO TRUNG
# Depois da correção:  toi 15 tu oi va la 1 hoc sinh cao trung
# Antes do correção:  KHONG CHi co vAy, TOI CON CO 2 NGUOI CH! EM CUC XINH DEP LUON
# Depois da correção:  khong chi co vay, toi con co 2 ngu oi ch! em cuc xinh dep lu on
# Antes do correção:  TOI DUNG CHUAN NOO, NHA
# Depois da correção:  toi dung chuan no o, nha
# Antes do correção:  NGOAI TRU 1 NHUOC DIEM NHO NHO: TOI VAN CHUA
# Depois da correção:  ngoai tru 1 nhục diem nho nho: toi van chua
# """

# print(TextProcess.correct_phrase("TEN TOILA CHAARI YASUMI"))
# print(TextProcess.correct_phrase("TOI DEP CHOI TRAI, THE THAO HOC TOT, DA GIOI vAy CON GIAU co"))
# print(TextProcess.correct_phrase("TOI 15 TUOI vA LA1 HOC SINH CAO TRUNG"))
# print(TextProcess.correct_phrase("KHONG CHi co vAy, TOI CON CO 2 NGUOI CH! EM CUC XINH DEP LUON"))
# print(TextProcess.correct_phrase("TOI DUNG CHUAN NOO, NHA"))
# print(TextProcess.correct_phrase("NGOAI TRU 1 NHUOC DIEM NHO NHO: TOI VAN CHUA"))

# print(mtranslate.translate(TextProcess.correct_phrase("TOI 15 TUOI vA LA1 HOC SINH CAO TRUNG"), "en"))
import re
from symspellpy.symspellpy import SymSpell, Verbosity

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
sym_spell.load_dictionary("dictionary\\2018\\en\\en_50k.txt", term_index=0, count_index=1, encoding="utf-8")

print(sym_spell.word_segmentation("sowhydo", max_edit_distance=0).corrected_string)

CHAR_SUBSTITUTIONS = {
    '1': 'i',
    '!': 'i',
    '0': 'o',
    '@': 'a',
    '$': 's',
    '3': 'e',
    '5': 's',
    '7': 't',
    '8': 'b',
    '|': 'l',
}

def generate_variants(word):
    variants = {word}
    for i, c in enumerate(word):
        if c in CHAR_SUBSTITUTIONS:
            new_word = word[:i] + CHAR_SUBSTITUTIONS[c] + word[i+1:]
            variants.add(new_word)
    return variants

def split_numbers_edge(word):
    """
    Separa números no início ou fim da palavra.
    Ex: 12c1sco -> 12 c1sco, depois corrige 'c1sco'
        cisco12 -> cisco 12, corrige 'cisco'
    """
    match = re.match(r'^(\d+)([a-zA-Z@!$|0-9]+)$', word)
    if match:
        prefix, rest = match.groups()
        corrected_rest = correct_word(rest)
        return f"{prefix} {corrected_rest}"

    match = re.match(r'^([a-zA-Z@!$|0-9]+)(\d+)$', word)
    if match:
        body, suffix = match.groups()
        corrected_body = correct_word(body)
        return f"{corrected_body} {suffix}"

    return None

def correct_word(word, min_frequency=10):
    # Etapa 1: variantes de substituição
    variants = generate_variants(word)
    for variant in variants:
        if sym_spell.words.get(variant, 0) >= min_frequency:
            return variant

    # Etapa 0: divisão por número no início/final
    split_number = split_numbers_edge(word)
    if split_number:
        return split_number

    # Etapa 2: fallback com sugestões
    for variant in variants:
        suggestions = sym_spell.lookup(variant, Verbosity.ALL, max_edit_distance=2)
        if suggestions:
            best = max(suggestions, key=lambda s: s.count)
            if best.count >= min_frequency:
                return best.term

    return word  # nada deu certo

def correct_text(text, min_frequency=10):
    words = text.split()
    return ' '.join(correct_word(word, min_frequency) for word in words)

# # 🔍 Teste
# ocr_text = "I th1nk she is ch! and 1nhuoc and ngon1 and @ngon and c1sco or 12cisco or 12c1sco or 12cisco12"
# # ocr_text = "12cisco12cisco12cisco or 12c1sco12c1sco12c1sco12c1sco"
# corrected = correct_text(ocr_text, min_frequency=10)
# print("Original :", ocr_text)
# print("Corrigido:", corrected)
# print("segment", sym_spell.word_segmentation(corrected).segmented_string)

import TextProcess
TextProcess.create("Vietnamita")
print(TextProcess.correct_phrase("CONCO2"))
print(TextProcess.correct_phrase("2CONCO"))
print(TextProcess.correct_phrase("2CONCO2"))
# print("TextProcess: ", TextProcess.correct_phrase(ocr_text))
# print(TextProcess.correct_phrase("TEN TOILA CHAARI YASUMI"))
# print(TextProcess.correct_phrase("TOI DEP CHOI TRAI, THE THAO HOC TOT, DA GIOI vAy CON GIAU co"))
# print(TextProcess.correct_phrase("TOI 15 TUOI vA LA1 HOC SINH CAO TRUNG"))
# print(TextProcess.correct_phrase("KHONG CHi co vAy, TOI CON CO 2 NGUOI CH! EM CUC XINH DEP LUON"))
# print(TextProcess.correct_phrase("TOI DUNG CHUAN NOO, NHA"))
# print(TextProcess.correct_phrase("NGOAI TRU 1 NHUOC DIEM NHO NHO: TOI VAN CHUA"))
# print(TextProcess.correct_phrase("I th1nk she is ch! and 1nhuoc and ngon1 and @ngon and c1sco or 12cisco or 12c1sco or 12cisco12"))
# print(TextProcess.correct_phrase("Caramba!"))