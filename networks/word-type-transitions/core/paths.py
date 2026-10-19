"""
networks/word-type-transitions/core/paths.py

Rutas de datos, definición de condiciones y hash de archivos (sha256).

Diseño 2×2 por grupo lingüístico: {L1 nativo, L2 inglés} × {Q1, Q4} por
comprensión lectora (accuracy). Koreano excluido (sin sesión L2).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BENCH_DIR = REPO_ROOT / "data" / "benchmark"

# --- Fijaciones L1 (nativos) -----------------------------------------------
L1_W1_FIX_RDA = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-1"
    / "primary-data"
    / "eye tracking data"
    / "fixation report"
    / "joint_l1_fixation_report_2.1.rda"
)
L1_W2_FIX_RDA = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-2"
    / "primary-data"
    / "eye tracking data"
    / "joint_fix_trimmed_l1_wave2_version2.1.rda"
)
L1_FIX_EXPORT_DIR = BENCH_DIR / "word_type_transitions" / "l1_fixations"
L1_ACC_EXPORT = {
    "wave1": L1_FIX_EXPORT_DIR / "l1_wave1_acc.csv",
    "wave2": L1_FIX_EXPORT_DIR / "l1_wave2_ch_acc.csv",
}

# --- Fijaciones L2 (inglés) -------------------------------------------------
L2_W1_FIX_CSV = (
    REPO_ROOT
    / "data"
    / "MECO-L2_version-2.2"
    / "wave-1"
    / "primary-data"
    / "eye-tracking"
    / "joint_l2_fixation_trimmed_report_2.2.comprehension.clean.csv"
)
L2_W2_FIX_CSV = (
    REPO_ROOT
    / "data"
    / "MECO-L2_version-2.2"
    / "wave-2"
    / "primary-data"
    / "eye-tracking"
    / "joint_fix_trimmed_L2_wave2_version2.2.comprehension.clean.csv"
)

# --- Comprensión lectora (accuracy por uniform_id) --------------------------
L1_W1_ACC_RDA = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-1"
    / "primary-data"
    / "comprehension data"
    / "joint_l1_acc.rda"
)
L1_W2_ACC_RDA = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-2"
    / "primary-data"
    / "comprehension data"
    / "joint_comp_L1_Wave2_trimmed.rda"
)
L2_W1_ACC_CSV = (
    REPO_ROOT
    / "data"
    / "MECO-L2_version-2.2"
    / "wave-1"
    / "primary-data"
    / "comprehension"
    / "joint.comp.l2.csv"
)
L2_W2_ACC_CSV = (
    REPO_ROOT
    / "data"
    / "MECO-L2_version-2.2"
    / "wave-2"
    / "primary-data"
    / "comprehension"
    / "joint_comp_L2_Wave2_trimmed.csv"
)

# --- Mapeo itemid -> índice de texto L1 (generado por el clasificador) --------
ITEM_MAP_DIR = BENCH_DIR / "l1_tokens"          # wave 1 alfabético
ITEM_MAP_DIR_W2 = BENCH_DIR / "l1_tokens_w2"    # variantes wave 2

# --- Benchmarks de tipificación de palabras ----------------------------------
L1_BENCH = {
    lang: BENCH_DIR / f"words_classified_{lang}_l1.csv"
    for lang in ("du", "ee", "en", "fi", "ge", "gr", "he", "it", "no", "ru", "sp", "tr")
}
CH_BENCH = {
    "ch_s": BENCH_DIR / "words_classified_chinese_simplified_wave2.csv",
    "ch_t": BENCH_DIR / "words_classified_chinese_traditional_wave2.csv",
}
# Variantes L1 wave 2 (cada una es un GRUPO SEPARADO; sin fusiones)
W2_VARIANTS = [
    "ba", "bp", "da", "en_uk", "ge_po", "ge_zu", "hi_iiith", "hi_iitk",
    "ic", "ru_mo", "se", "sp_ch", "no_w2", "tr_w2",
]
L1_W2_BENCH = {code: BENCH_DIR / f"words_classified_{code}_w2l1.csv" for code in W2_VARIANTS}
L2_BENCH = BENCH_DIR / "words_classified.csv"  # textos ingleses (Morse…Smartphones)

# --- Condiciones --------------------------------------------------------------
# Grupos wave 1 (sesión nativa w1 + sesión inglés w1), chino y variantes wave 2
# (todas con sesión nativa w2 + sesión inglés w2).
LANGS_W1 = ["du", "ee", "en", "fi", "ge", "gr", "he", "it", "no", "ru", "sp", "tr"]
CH_VARIANTS = ["ch_s", "ch_t"]
CONDITION_LANGS = LANGS_W1 + CH_VARIANTS + W2_VARIANTS

# Código de GRUPO -> código de `lang` en los archivos crudos wave 2 (los cohortes
# noruego/turco de wave 2 aparecen como "no"/"tr" en los datos).
DATA_LANG_ALIAS = {"no_w2": "no", "tr_w2": "tr"}
# Códigos `lang` presentes en los archivos wave 2 (L1 rda y L2 csv).
W2_DATA_CODES = (
    "ba", "bp", "ch_s", "ch_t", "da", "en_uk", "ge_po", "ge_zu", "hi_iiith",
    "hi_iitk", "ic", "no", "ru_mo", "se", "sp_ch", "tr",
)


def data_lang(lang: str) -> str:
    """Código `lang` en los datos crudos para un código de grupo."""
    return DATA_LANG_ALIAS.get(lang, lang)

MIN_GROUP_N = 4  # n mínimo por celda para construir red / contraste
MIN_PAIRED_N = 5  # emparejamiento por sujeto requiere al menos 5 pares

QUARTILES = ("Q1", "Q4")  # Q1 = accuracy <= p25 (peor), Q4 = >= p75 (mejor)
SESSIONS = ("L1", "L2")

MODES = ("temporal", "regression")

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def lang_dir(lang: str) -> Path:
    """Directorio raíz de salidas de una lengua: output/<lang>/."""
    return OUTPUT_DIR / lang


def mode_dir(lang: str, mode: str) -> Path:
    """Directorio de un modo para una lengua: output/<lang>/<mode>/."""
    return lang_dir(lang) / mode


def figures_dir(lang: str, mode: str) -> Path:
    """output/<lang>/<mode>/figures/."""
    return mode_dir(lang, mode) / "figures"


def prepare_lang_dirs(lang: str, modes: "tuple[str, ...] | list[str]" = MODES) -> None:
    for mode in modes:
        figures_dir(lang, mode).mkdir(parents=True, exist_ok=True)


def all_conditions() -> list[str]:
    """IDs de condición: {L1|L2}-{lang}-Q{1,4} para todos los grupos."""
    conds = []
    for session in SESSIONS:
        for lang in CONDITION_LANGS:
            for q in QUARTILES:
                conds.append(f"{session}-{lang}-{q}")
    return conds


def l1_wave(lang: str) -> int:
    return 2 if lang in CH_VARIANTS or lang in W2_VARIANTS else 1


def l2_wave(lang: str) -> int:
    return 2 if lang in CH_VARIANTS or lang in W2_VARIANTS else 1


def file_sha256(path, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def short_sha(path) -> str:
    return file_sha256(path)[:16]
