from symspellpy import SymSpell, Verbosity
import re

_sym_spell: SymSpell
_has_dict_loaded : bool

# Lista de sufixos japoneses que devem manter o hífen
JAPANESE_SUFFIXES = {"-san", "-kun", "-chan", "-sama", "-sensei"}

def create(language: str) -> None:
    global _sym_spell, _has_dict_loaded
    _sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    _has_dict_loaded = False
    path = get_dict_path(language)
    if path:
        load_dictionary(path)

def load_dictionary(txt_path : str) -> None:
    global _has_dict_loaded
    found = _sym_spell.load_dictionary(txt_path, term_index=0, count_index=1, encoding="utf-8")
    if found:
        print("Dictonary found!")
        _has_dict_loaded = True

def has_dictionary_loaded() -> bool:
    return _has_dict_loaded

CHAR_SUBSTITUTIONS = {
    '1': 'i',
    '!': 'i',
    '0': 'o',
    '@': 'a',
    '$': 's',
    '3': 'e',
    '5': 's',
    '6': 'g',
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

def remove_unwanted_chars(text: str) -> str:
    unwanted = set(CHAR_SUBSTITUTIONS.keys()) | set('0123456789')
    return ''.join(c for c in text if c not in unwanted)

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
    global _sym_spell
    # Etapa 1: variantes de substituição
    variants = generate_variants(word)
    higher_frequency = -1
    _variant = None
    for variant in variants:# VAI SE FUDER, PENSEI NA PORRA DA SOLUÇÃO EM 1 SEGUNDO
        variant = remove_unwanted_chars(variant)
        frequency = _sym_spell.words.get(variant, 0)
        # print("VARIANTE: ", variant, " | FREQUENCY: ", frequency)
        if frequency >= higher_frequency:
            higher_frequency = frequency
            _variant = variant
    if frequency >= min_frequency:
        return _variant

    # Etapa 0: divisão por número no início/final
    split_number = split_numbers_edge(word)
    if split_number:
        return split_number

    # Etapa 2: fallback com sugestões
    for variant in variants:
        suggestions = _sym_spell.lookup(variant, Verbosity.ALL, max_edit_distance=2)
        if suggestions:
            best = max(suggestions, key=lambda s: s.count)
            if best.count >= min_frequency:
                return best.term

    return word  # nada deu certo

def is_expression(word: str) -> bool:
    return bool(re.fullmatch(r'[\d]+([\+\-\*/=][\d]+)+', word))

def force_split(word: str, min_freq: int = 10) -> str:
    global _sym_spell
    word = word.lower()

    if is_expression(word):
        return word

    match = re.match(r"^([a-zA-Z]+)([0-9]+)$", word)
    if match:
        suggestion = _sym_spell.lookup_compound(match.group(1), 2)
        p_word = suggestion[0].term if suggestion else match.group(1)
        return f"{p_word} {match.group(2)}"
    else:
        match = re.match(r"^([0-9]+)([a-zA-Z]+)$", word)
        if match:
            suggestion = _sym_spell.lookup_compound(match.group(2), 2)
            p_word = suggestion[0].term if suggestion else match.group(2)
            return f"{match.group(1)} {p_word}"
        else:
            match = re.match(r"^([0-9]+)([a-zA-Z]+)([0-9]+)$", word)
            if match:
                suggestion = _sym_spell.lookup_compound(match.group(2), 2)
                p_word = suggestion[0].term if suggestion else match.group(2)
                return f"{match.group(1)} {p_word} {match.group(3)}"

    if word in _sym_spell._words:
        return word

    # best = (word, 0) #TODO MELHORAR ISSO, SE TIVER 3 PALAVRAS JUNTAS OU MAIS, N ADIANTA MT KKKK

    # for i in range(1, len(word)):
    #     left = word[:i]
    #     right = word[i:]
    #     freq_left = _sym_spell._words.get(left, 0)
    #     freq_right = _sym_spell._words.get(right, 0)

    #     if left in _sym_spell._words and right in _sym_spell._words:
    #         if freq_left >= min_freq and freq_right >= min_freq:
    #             total_freq = freq_left + freq_right
    #             if total_freq > best[1]:
    #                 best = (f"{left} {right}", total_freq)

    # return best[0]
    return word

def correct_phrase(text: str) -> str:
    global _sym_spell
    # Divide mantendo pontuação e hífen em palavras
    tokens = re.findall(r'\w+(?:-\w+)?[^\w\s]*|\S', text.lower())
    corrected_parts = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        #! MELHORA ISSO AQ: Exs: I -> I, M -> , I'M -> I'
        # if len(token) == 1 and token not in "aeiouAEIOU": #TODO ISSO FUNCIONA SOH NO ALFABETO LATINO
        #     i += 1
        #     continue

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
        # match = re.match(r"^([a-zA-Z0-9\-]+)([^\w\s]*)$", token) #! OLD
        # if match:
        #     word, punct = match.groups()
        # else:
        #     word, punct = token, ""

        did = False
        match = re.match(r"^([a-zA-Z0-9\-]+)([^\w\s]*)$", token)
        if match:
            word, punct = match.groups()
            if punct in CHAR_SUBSTITUTIONS:
                # print("punct: ", punct)
                # print("Antes: ", word)
                old_word = word
                word = correct_word(word + punct)
                # print("Depois: ", word)
                if word == old_word + punct:
                    word = old_word
                else:
                    punct = ""
                did = True
        else:
            word, punct = token, ""
        
        if not did and not word.isdigit() and any(char in CHAR_SUBSTITUTIONS for char in word):
            # print("Antes: ", word)
            word = correct_word(word)
            # print("Depois: ", word)

        # Preserva palavras com sufixos japoneses como estão (ex: "kamikawa-san")
        if any(word.endswith(suffix) for suffix in JAPANESE_SUFFIXES):
            corrected_parts.append(word + punct)
            continue

        if is_expression(word) or word.isdigit():
            corrected = word
        else:
            possibly_split = force_split(word)

            if any(char.isdigit() for char in possibly_split):
                corrected = possibly_split
            elif any(char.isalpha() for char in possibly_split):
                # suggestions = _sym_spell.lookup_compound(possibly_split, max_edit_distance=2)
                # corrected = suggestions[0].term if suggestions else possibly_split
                corrected_words = []
                segmented = _sym_spell.word_segmentation(possibly_split, max_edit_distance=2)
                for w in segmented.corrected_string.split():
                    suggestions = _sym_spell.lookup(w, Verbosity.TOP, max_edit_distance=2)
                    if suggestions:
                        corrected_words.append(suggestions[0].term)
                    else:
                        corrected_words.append(w)
                corrected = " ".join(corrected_words)
            else:
                corrected = " " + possibly_split

        corrected_parts.append(corrected + punct)

    # Corrige espaços antes de pontuação
    result = ' '.join(corrected_parts)
    result = re.sub(r"\s+([.,!?])", r"\1", result)

    return result

def get_dict_path(lang: str) -> str:
    lang_code = _get_lang_code(lang)
    before = "dictionary\\2018\\"
    after = ""
    additional = ""
    match lang_code:
        case "af" | "br"| "eo" | "hi" | "ja" | "tl" | "ur":
            after = lang_code + "\\" + lang_code + additional + "_full.txt"
        case "ar" | "bg" | "bs" | "ca" | "cs" | "da" | "de" | "el" | "en" | "es" | "et"  | "eu" | "fa"  | "fi" | "fr" | "hr" | "hu" | "id" | "is" | "it" | "ko" | "lt" | "lv" | "mk" | "ms" | "nl" | "no" | "pl" | "pt" | "pt_br" | "ro" | "ru" | "sk" | "sl" | "sq" | "sv" | "tr" | "uk" | "zh_cn" | "vi":
            if lang_code == "vi":
                additional = "_no_accent"
            after = lang_code + "\\" + lang_code + additional + "_50k.txt"
        case _:
            print("Não achou o dicionário")
            return None
    print(before + after)
    return before + after

_lang_map = {
    "sq": "Albanês",
    "de": "Alemão",
    "af": "Africâner",
    "ar": "Árabe",
    "az": "Azerbaijano",
    "eu": "Basco",
    "be": "Bielorrusso",
    "bg": "Búlgaro",
    "bs": "Bósnio",
    "ca": "Catalão",
    "ko": "Coreano",
    "hr": "Croata",
    "cs": "Tcheco",
    "da": "Dinamarquês",
    "nl": "Holandês",
    "en": "Inglês",
    "eo": "Esperanto",
    "et": "Estoniano",
    "fi": "Finlandês",
    "fr": "Francês",
    "ga": "Irlandês",
    "el": "Grego",
    "hi": "Hindi",
    "hu": "Húngaro",
    "id": "Indonésio",
    "is": "Islandês",
    "it": "Italiano",
    "ja": "Japonês",
    "lt": "Lituano",
    "lv": "Letão",
    "mk": "Macedônio",
    "mr": "Marathi",
    "ms": "Malaio",
    "mt": "Maltês",
    "ne": "Nepalês",
    "no": "Norueguês",
    "fa": "Persa",
    "pl": "Polonês",
    "pt_br": "Português",
    "pt": "Português (Portugal)",
    "ro": "Romeno",
    "ru": "Russo",
    # "rs": "Sérvio (Cirílico)",
    "rs": "Sérvio (Latim)",
    "sk": "Eslovaco",
    "sl": "Esloveno",
    "es": "Espanhol",
    "sv": "Sueco",
    "tl": "Tagalo",
    "tr": "Turco",
    "ug": "Uigur",
    "uk": "Ucraniano",
    "ur": "Urdu",
    "vi": "Vietnamita",
}

def _get_lang_code(language_name):
    global _lang_map
    for code, name in _lang_map.items():
        if name == language_name:
            return code
    return "Código desconhecido"