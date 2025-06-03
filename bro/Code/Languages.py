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
    "ch": "Chinês Simplificado",
    "korean": "Coreano",
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
    "japan": "Japonês",
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
    "pt-BR": "Português",
    "pt-PT": "Português (Portugal)",
    "ro": "Romeno",
    "ru": "Russo",
    "rs_cyrillic": "Sérvio (Cirílico)",
    "rs_latin": "Sérvio (Latim)",
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

_alphabet_groups = {
    "Latim": {
        "sq", "de", "af", "az", "eu", "bs", "ca", "hr", "cs", "da", "nl", "en", "eo", "et",
        "fi", "fr", "ga", "hu", "id", "is", "it", "lt", "lv", "ms", "mt", "no", "pl", "pt",
        "pt-BR", "pt-PT", "ro", "rs_latin", "sk", "sl", "es", "sv", "tl", "tr", "vi"
    },
    "Cirílico": {
        "be", "bg", "mk", "ru", "rs_cyrillic", "uk"
    },
    "Árabe": {
        "ar", "fa", "ug", "ur"
    },
    "Devanágari": {
        "hi", "mr", "ne"
    },
    "Chinês": {
        "ch"
    },
    "Japonês": {
        "japan"
    },
    "Coreano": {
        "korean"
    },
    "Grego": {
        "el"
    }
}

def get_language_name(lang_code):
    return _lang_map.get(lang_code, "Idioma desconhecido")

def get_lang_code(language_name):
    if language_name in ("Português", "Português (Portugal)"):
        return "pt"
    for code, name in _lang_map.items():
        if name == language_name:
            return code
    return "Código desconhecido"

def get_all_language_codes():
    return list(_lang_map.keys())

def get_all_language_names():
    return list(set(_lang_map.values()))

def get_alphabet_group(lang_code: str) -> str:
    global _alphabet_groups
    for alphabet, lang_codes in _alphabet_groups.items():
        if lang_code in lang_codes:
            return alphabet
    return "Desconhecido"

def get_model_by_lang_code(lang_code: str) -> str:
    match get_alphabet_group(lang_code):
        case "Latim":
            return "en"
        case "Cirílico":
            return "ru"
        case "Árabe":
            return "arabic"
        case "Devanágari":
            return "devanagari"
        case "Chinês":
            return "ch"
        case "Japonês":
            return "japan"
        case "Coreano":
            return "korean"
        case "Grego":
            return "greek"
        case _:
            return lang_code


#! From the PaddleOcr
# def parse_lang(lang):
#     latin_lang = [
#         "af",
#         "az",
#         "bs",
#         "cs",
#         "cy",
#         "da",
#         "de",
#         "es",
#         "et",
#         "fr",
#         "ga",
#         "hr",
#         "hu",
#         "id",
#         "is",
#         "it",
#         "ku",
#         "la",
#         "lt",
#         "lv",
#         "mi",
#         "ms",
#         "mt",
#         "nl",
#         "no",
#         "oc",
#         "pi",
#         "pl",
#         "pt",
#         "ro",
#         "rs_latin",
#         "sk",
#         "sl",
#         "sq",
#         "sv",
#         "sw",
#         "tl",
#         "tr",
#         "uz",
#         "vi",
#         "french",
#         "german",
#     ]
#     arabic_lang = ["ar", "fa", "ug", "ur"]
#     cyrillic_lang = [
#         "ru",
#         "rs_cyrillic",
#         "be",
#         "bg",
#         "uk",
#         "mn",
#         "abq",
#         "ady",
#         "kbd",
#         "ava",
#         "dar",
#         "inh",
#         "che",
#         "lbe",
#         "lez",
#         "tab",
#     ]
#     devanagari_lang = [
#         "hi",
#         "mr",
#         "ne",
#         "bh",
#         "mai",
#         "ang",
#         "bho",
#         "mah",
#         "sck",
#         "new",
#         "gom",
#         "sa",
#         "bgc",
#     ]

# _lang_map = {
#     # Latin
#     "af": "Africâner",
#     "az": "Azerbaijano",
#     "bs": "Bósnio",
#     "ca": "Catalão",
#     "cs": "Tcheco",
#     "cy": "Galês",
#     "da": "Dinamarquês",
#     "de": "Alemão",
#     "es": "Espanhol",
#     "et": "Estoniano",
#     "eu": "Basco",
#     "fi": "Finlandês",
#     "fr": "Francês",
#     "ga": "Irlandês",
#     "hr": "Croata",
#     "hu": "Húngaro",
#     "id": "Indonésio",
#     "is": "Islandês",
#     "it": "Italiano",
#     "lt": "Lituano",
#     "lv": "Letão",
#     "mt": "Maltês",
#     "nl": "Holandês",
#     "no": "Norueguês",
#     "pl": "Polonês",
#     "pt": "Português",
#     "ro": "Romeno",
#     "rs_latin": "Sérvio (Latim)",
#     "sk": "Eslovaco",
#     "sl": "Esloveno",
#     "sq": "Albanês",
#     "sv": "Sueco",
#     "tr": "Turco",
#     "vi": "Vietnamita",
#     "en": "Inglês",
#     # Arabic
#     "ar": "Árabe",
#     "fa": "Persa",
#     "ug": "Uigur",
#     "ur": "Urdu",
#     # Cyrillic
#     "ru": "Russo",
#     "rs_cyrillic": "Sérvio (Cirílico)",
#     "be": "Bielorrusso",
#     "bg": "Búlgaro",
#     "uk": "Ucraniano",
#     "mk": "Macedônio",
#     # Devanagari
#     "hi": "Hindi",
#     "mr": "Marathi",
#     "ne": "Nepalês",
#     # Outros
#     "japan": "Japonês",
#     "korean": "Coreano",
#     "ch": "Chinês Simplificado",
# }