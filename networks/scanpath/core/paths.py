"""
networks/scanpath/core/paths.py

Rutas de datos, grupos lingüísticos y salidas para las redes de scanpath
POR TEXTO (sesión L2 inglés únicamente).

Estructura de salida:
output/<lang>/<Q1|Q4>/
├── network.html               # wrapper: iframes de network/<t>.html
├── network/<tN>.html          # red estática por texto
├── network_anim.html          # wrapper: iframes de network_anim/<t>.html
└── network_anim/<tN>.html     # red animada por texto
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# --- Fijaciones L2 (inglés), CSVs limpios con palabra, ps y sentnum ---------
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

# --- Grupos lingüísticos (misma convención que word-type-transitions) -------
LANGS_W1 = ["du", "ee", "en", "fi", "ge", "gr", "he", "it", "no", "ru", "sp", "tr"]
CH_VARIANTS = ["ch_s", "ch_t"]
W2_VARIANTS = [
    "ba", "bp", "da", "en_uk", "ge_po", "ge_zu", "hi_iiith", "hi_iitk",
    "ic", "ru_mo", "se", "sp_ch", "no_w2", "tr_w2",
]
CONDITION_LANGS = LANGS_W1 + CH_VARIANTS + W2_VARIANTS

DATA_LANG_ALIAS = {"no_w2": "no", "tr_w2": "tr"}
W2_DATA_CODES = (
    "ba", "bp", "ch_s", "ch_t", "da", "en_uk", "ge_po", "ge_zu", "hi_iiith",
    "hi_iitk", "ic", "no", "ru_mo", "se", "sp_ch", "tr",
)

MIN_GROUP_N = 4
TEXTS = tuple(range(1, 13))
QUARTILES = ("Q1", "Q4")

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def data_lang(lang: str) -> str:
    """Código `lang` en los datos crudos para un código de grupo."""
    return DATA_LANG_ALIAS.get(lang, lang)


def l2_wave(lang: str) -> int:
    return 2 if lang in CH_VARIANTS or lang in W2_VARIANTS else 1


def l2_fix_csv(lang: str) -> Path:
    return l2_fix_csv_for_wave(l2_wave(lang))


def l2_fix_csv_for_wave(wave: int) -> Path:
    return L2_W1_FIX_CSV if wave == 1 else L2_W2_FIX_CSV


def l2_acc_csv(lang: str) -> Path:
    return L2_W1_ACC_CSV if l2_wave(lang) == 1 else L2_W2_ACC_CSV


def quartile_dir(lang: str, quartile: str) -> Path:
    """output/<lang>/<Q1|Q4>/."""
    return OUTPUT_DIR / lang / quartile


def network_dir(lang: str, quartile: str) -> Path:
    return quartile_dir(lang, quartile) / "network"


def network_anim_dir(lang: str, quartile: str) -> Path:
    return quartile_dir(lang, quartile) / "network_anim"
