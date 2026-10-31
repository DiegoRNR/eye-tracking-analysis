"""
networks/word-type-transitions/core/label_map.py

Espacio de etiquetas FUSED unificado entre el benchmark L2 (inglés), los
benchmarks L1 alfabéticos (UPOS de spaCy/Stanza) y los benchmarks chino wave 2.
Cada etiqueta original → nodo fused; orden canónico para matrices.
"""

from __future__ import annotations

# Mapa etiqueta original -> nodo fused
_LABEL_MAP: dict[str, str] = {
    # UPOS común (L1 alfabético, L2 inglés, chino wave 2)
    "NOUN": "NOUN",
    "VERB": "VERB",
    "ADJ": "ADJ",
    "ADV": "ADV",
    "ADP": "ADP",
    "PRON": "PRON",
    "NUM": "NUM",
    "PROPN": "NOUN",
    "AUX": "VERB",
    "SCONJ": "CONJ",
    "CCONJ": "CONJ",
    "DET": "PTCL",
    "PART": "PTCL",
    "PUNCT": "PUNCT",
    "INTJ": "X",
    # etiquetas Penn del benchmark L2 legacy (words_classified.csv)
    "CONJ": "CONJ",
    "PRT": "PTCL",
}

# Orden canónico de nodos (matrices determinísticas)
FUSED_ORDER = ["NOUN", "VERB", "ADJ", "ADV", "PRON", "ADP", "PTCL", "CONJ", "NUM", "X", "PUNCT"]

# Nodos de contenido vs funcionales (para agrupar en figuras si se requiere)
CONTENT_NODES = {"NOUN", "VERB", "ADJ", "ADV", "NUM"}
FUNCTION_NODES = {"PRON", "ADP", "PTCL", "CONJ", "X", "PUNCT"}


def map_label(label) -> str | None:
    """Mapea etiqueta original a nodo fused; None/nulo/desconocido -> None."""
    if label is None or (isinstance(label, float) and label != label):
        return None
    return _LABEL_MAP.get(str(label).strip())
