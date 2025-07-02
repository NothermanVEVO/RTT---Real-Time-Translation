from symspellpy import SymSpell

def correct_phrase(text : str) -> str:
    suggestions = sym_spell.lookup_compound(input_phrase.lower(), max_edit_distance=2)
    if not suggestions:
        return text
    else:
        return suggestions[0].term

# Inicializa com capacidade máxima de edição e tamanho do prefixo
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

# Carrega o dicionário (formato: palavra [tab] frequência)
success = sym_spell.load_dictionary("dictionary\\2018\\id\\id_50k.txt", term_index=0, count_index=1, encoding="utf-8")

# Corrige uma frase
input_phrase = "DAN KARENA HUBUINGAN KITA ADALAH HUBUINGAN GURU DAN MURID"
print(correct_phrase(input_phrase))