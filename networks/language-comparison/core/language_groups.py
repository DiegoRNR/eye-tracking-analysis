"""
language_groups.py

Mapeo de códigos L1 de MECO L2 a familias lingüísticas, y resolución de
grupos a partir del nombre de familia.
"""

LANG_TO_FAMILY = {
    # Germánica (Oeste y Norte)
    "du": "germanic",
    "en": "germanic",
    "ge": "germanic",
    "ge_po": "germanic",
    "ge_zu": "germanic",
    "en_uk": "germanic",
    "no": "germanic",
    "da": "germanic",
    "se": "germanic",
    "ic": "germanic",
    # Románica
    "it": "romance",
    "sp": "romance",
    "sp_ch": "romance",
    "bp": "romance",
    # Eslava
    "ru": "slavic",
    "ru_mo": "slavic",
    # Urálica
    "ee": "uralic",
    "fi": "uralic",
    # Túrquica
    "tr": "turkic",
    # Helénica
    "gr": "hellenic",
    # Semítica
    "he": "semitic",
    # Sino-Tibetana
    "ch_s": "sino-tibetan",
    "ch_t": "sino-tibetan",
    # Indo-Aria
    "hi_iiith": "indo-aryan",
    "hi_iitk": "indo-aryan",
    # Aislada (Euskera)
    "ba": "isolate",
}

FAMILY_LABELS = {
    "germanic": "Germánica",
    "romance": "Románica",
    "slavic": "Eslava",
    "uralic": "Urálica",
    "turkic": "Túrquica",
    "hellenic": "Helénica",
    "semitic": "Semítica",
    "sino-tibetan": "Sino-Tibetana",
    "indo-aryan": "Indo-Aria",
    "isolate": "Aislada (Euskera)",
}

ALL_FAMILIES = tuple(LANG_TO_FAMILY.values()) if False else tuple(
    dict.fromkeys(LANG_TO_FAMILY.values())
)

# Códigos L1 por ola (verificados sobre los CSVs de fijación/comprensión).
WAVE_LANGS = {
    1: ["du", "ee", "en", "fi", "ge", "gr", "he", "it", "no", "ru", "sp", "tr"],
    2: [
        "ba",
        "bp",
        "ch_s",
        "ch_t",
        "da",
        "en_uk",
        "ge_po",
        "ge_zu",
        "hi_iiith",
        "hi_iitk",
        "ic",
        "no",
        "ru_mo",
        "se",
        "sp_ch",
        "tr",
    ],
}

# Lenguas sin datos de pupila (ps = NA en todas sus fijaciones). No aportan
# aristas a la red de carga cognitiva.
LANGS_WITHOUT_PS = {"ch_s"}


def resolve_group(group, wave="both"):
    """
    Devuelve la lista de códigos L1 de la familia `group` presentes en la
    ola(s) `wave`.

    group puede ser un nombre de familia ('germanic') o 'all'. Si group no es
    una familia conocida, se interpreta como un código L1 individual.
    """
    if group == "all":
        return all_langs(wave)

    if group in LANG_TO_FAMILY.values() or group in FAMILY_LABELS:
        family = group if group in FAMILY_LABELS else group
        langs = [l for l, f in LANG_TO_FAMILY.items() if f == family]
    elif group in LANG_TO_FAMILY:
        # Permite pasar un código L1 directo como grupo de 1 lengua.
        langs = [group]
    else:
        raise ValueError(
            f"Grupo de lenguas desconocido: {group!r}. "
            f"Familias disponibles: {', '.join(ALL_FAMILIES)}; o usa 'all'."
        )

    if wave == "both":
        return sorted(langs)
    wave_langs = set(WAVE_LANGS[int(wave)])
    return sorted(l for l in langs if l in wave_langs)


def all_langs(wave="both"):
    """Todos los códigos L1 disponibles en la ola solicitada."""
    if wave == "both":
        return sorted(set(WAVE_LANGS[1]) | set(WAVE_LANGS[2]))
    return list(WAVE_LANGS[int(wave)])


def family_of(lang):
    """Familia de un código L1, o None si es desconocido."""
    return LANG_TO_FAMILY.get(lang)


def langs_without_ps(wave="both"):
    """Códigos L1 sin datos de pupila en la ola solicitada."""
    wl = set(all_langs(wave))
    return sorted(l for l in LANGS_WITHOUT_PS if l in wl)
