"""
networks/reading-pattern-mds/core/paths.py

Rutas y registro de condiciones para el MDS de patrones de lectura.

Espacio de características: distribuciones de transición entre tipos de palabra
(NOUN->VERB, ...) calculadas con la MISMA lógica que networks/word-type-transitions
(se reutiliza su core: data_io, label_map, grouping). Cohortes nativos de inglés:
- en_ca  -> código de grupo "en"   (wave 1)
- en_uk  -> código de grupo "en_uk" (wave 2)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WTT_ROOT = REPO_ROOT / "networks" / "word-type-transitions"

if str(WTT_ROOT) not in sys.path:
    sys.path.insert(0, str(WTT_ROOT))

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"

# Cohortes nativos de inglés (etiqueta de figura -> código de grupo)
EN_REFS = {"en_ca": "en", "en_uk": "en_uk"}

# Grupos no ingleses = todas las Conditioning langs menos los cohortes en*
TARGET_LANGS: list[str] = []


def target_langs() -> list[str]:
    """Grupos no ingleses (lazy: CONDITION_LANGS vive en el core reutilizado)."""
    global TARGET_LANGS
    if not TARGET_LANGS:
        from ._wtt import shared

        _, _, _, _, wtt_paths = shared()
        TARGET_LANGS = [lg for lg in wtt_paths.CONDITION_LANGS if lg not in EN_REFS.values()]
    return TARGET_LANGS


QUARTILES = ("Q1", "Q4")

FIG_LABEL = {  # etiqueta corta por lengua para figuras
    "du": "du", "ee": "ee", "fi": "fi", "ge": "ge", "gr": "gr", "he": "he",
    "it": "it", "no": "no", "ru": "ru", "sp": "sp", "tr": "tr",
    "ch_s": "zh-s", "ch_t": "zh-t",
    "ba": "ba", "bp": "bp", "da": "da", "ge_po": "ge-po", "ge_zu": "ge-zu",
    "hi_iiith": "hi-iith", "hi_iitk": "hi-itk", "ic": "ic", "ru_mo": "ru-md",
    "se": "se", "sp_ch": "sp-ch", "no_w2": "no2", "tr_w2": "tr2",
}


def fig_label(code: str) -> str:
    return FIG_LABEL.get(code, code)


def profiles_dir(mode: str) -> Path:
    return OUTPUT_DIR / mode / "profiles"


def distances_dir(mode: str) -> Path:
    return OUTPUT_DIR / mode / "distances"


def figures_dir(mode: str) -> Path:
    return OUTPUT_DIR / mode / "figures"


def ensure_dirs(mode: str) -> None:
    for d in (profiles_dir(mode), distances_dir(mode), figures_dir(mode)):
        d.mkdir(parents=True, exist_ok=True)
