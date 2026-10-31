#!/usr/bin/env python3
"""
scripts/classify_words_l1_all_languages.py

Clasificación de palabras para los 12 textos MECO (Janus … Vehicle Registration
Plate) en TODAS las lenguas L1 alfabéticas del corpus MECO-L1 wave 1, siguiendo
la metodología de `classify_words_chinese.py` / `classify_words_chinese_wave2.py`
y el formato del benchmark (`data/benchmark/words_classified*.csv`).

Lenguas incluidas (código MECO L1 → estándar):
    du=Neerlandés, ee=Estonio, en=Inglés, fi=Finés, ge=Alemán, gr=Griego,
    he=Hebreo, it=Italiano, no=Noruego, ru=Ruso, sp=Español, tr=Turco.
    KOREANO (ko) SE OMITE a petición del usuario: solo existe en L1, sin
    comparación posible con MECO-L2.

Decisiones metodológicas (documentadas):
1. FUENTE DE TOKENS: igual que en wave-2 chino (ver `wave2_chinese_texts.py`),
   la columna `word` del .rda wave 1 L1 es la fuente autoritativa de
   segmentación (interest areas reales), clave (lang, itemid, wordnum).
   `supp texts.csv` (L1 wave 1) se usa como referencia de verificación
   (concordancia reportada).
2. IDENTIDAD DE TEXTO = `itemid`, NO `trialid`: en Estonio y Ruso el orden de
   presentación rotaba entre sujetos (22 y 20 pares trialid-itemid), por lo que
   un mismo trialid puede contener textos distintos. El itemid de cada lengua se
   mapea al índice de texto (1..12 = columnas de `supp texts.csv`) mediante
   alineación de secuencias (difflib). Ruso usa itemids 2..13 (offset +1).
3. POS: spaCy (modelos `*_core_news_sm`) para 9 lenguas; Stanza
   (procesadores tokenize+pos) para Estonio, Hebreo y Turco, sin modelo spaCy
   disponible. Cada IA se etiqueta como token aislado; si el tagger sub-divide
   el token (p. ej. prefijos del hebreo), se toma el UPOS del segmento más
   largo (misma regla que `tag_fixed_token()` en chino).
4. FRECUENCIA: escala Zipf de `wordfreq` (van Heuven et al. 2014) por lengua.
   Estonio no tiene lista en wordfreq → se usa frecuencia interna del corpus
   (documentada como aproximación grosera). Techo/suelo [1.0, 7.6] igual que
   el benchmark chino.
5. SÍLABAS: CMUdict para inglés (como `classify_words.py`); conteo de letras
   vocálicas mediales (ו/י) para hebreo (aproximación documentada); conteo de
   vocales para ruso y turco; agrupación de vocales consecutivas (diptongos)
   para el resto. Aproximaciones heurísticas, documentadas en el reporte.
6. PREDICTIBILIDAD/SURPRISAL: mismo modelo trigram interpolado
   (Jelinek-Mercer 0.55/0.30/0.15) del script chino, entrenado por lengua sobre
   sus 12 textos (tokens limpios, frontera de oración = sentnum).
7. MEDIDAS HUMANAS: merge por (lang, itemid=trialid de texto, wordnum) desde el
   mismo .rda (skip rate, gaze duration de primera pasada, tiempo total), igual
   que el benchmark wave-2 chino.

Salidas:
- data/benchmark/words_classified_<lang>_l1.csv      (una por lengua, 12)
- data/benchmark/l1_tokens/tid<NN>_<lang>.csv        (secuencia de IAs por texto)
- data/CLASIFICACION_PALABRAS_L1.md                  (reporte combinado)
"""

from __future__ import annotations

import difflib
import logging
import math
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("classify_l1_all")

REPO_ROOT = Path(__file__).resolve().parent.parent
RDA_PATH = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-1"
    / "primary-data"
    / "eye tracking data"
    / "joint_l1_data_trimmed_version2.1.rda"
)
SUPP_TEXTS_CSV = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-1"
    / "auxiliary files"
    / "reading task materials"
    / "supp texts.csv"
)
BENCH_DIR = REPO_ROOT / "data" / "benchmark"
TOKENS_DIR = BENCH_DIR / "l1_tokens"
REPORT_PATH = REPO_ROOT / "data" / "CLASIFICACION_PALABRAS_L1.md"

N_TEXTS = 12

# Nombres de los textos (orden = índice de texto 1..12, columnas del supp texts.csv)
TEXT_NAMES: Dict[int, str] = {
    1: "Janus",
    2: "Shaka",
    3: "Doping",
    4: "Thylacine",
    5: "World Environment Day",
    6: "Monocle",
    7: "Wine Tasting",
    8: "Orange Juice",
    9: "Beekeeping",
    10: "National Flag",
    11: "IUCN",
    12: "Vehicle Registration Plate",
}

# ---------------------------------------------------------------------------
# Configuración por lengua
# ---------------------------------------------------------------------------

LANG_CONFIG: Dict[str, Dict] = {
    "du": dict(nombre="Neerlandés", engine="spacy", model="nl_core_news_sm", wf="nl", syl="cluster"),
    "ee": dict(nombre="Estonio", engine="stanza", model="et", wf=None, syl="cluster"),
    "en": dict(nombre="Inglés", engine="spacy", model="en_core_web_sm", wf="en", syl="cmudict"),
    "fi": dict(nombre="Finés", engine="spacy", model="fi_core_news_sm", wf="fi", syl="cluster"),
    "ge": dict(nombre="Alemán", engine="spacy", model="de_core_news_sm", wf="de", syl="cluster"),
    "gr": dict(nombre="Griego", engine="spacy", model="el_core_news_sm", wf="el", syl="cluster"),
    "he": dict(nombre="Hebreo", engine="stanza", model="he", wf="he", syl="hebrew"),
    "it": dict(nombre="Italiano", engine="spacy", model="it_core_news_sm", wf="it", syl="cluster"),
    "no": dict(nombre="Noruego", engine="spacy", model="nb_core_news_sm", wf="nb", syl="cluster"),
    "ru": dict(nombre="Ruso", engine="spacy", model="ru_core_news_sm", wf="ru", syl="count"),
    "sp": dict(nombre="Español", engine="spacy", model="es_core_news_sm", wf="es", syl="cluster"),
    "tr": dict(nombre="Turco", engine="stanza", model="tr", wf="tr", syl="count"),
}

# Vocales por lengua para la heurística silábica
VOWELS: Dict[str, str] = {
    "du": "aeiouyàáèéëêìíïòóöùúü",
    "ee": "aeiouyõäöüàáèéìíòóùú",
    "fi": "aeiouyäö",
    "ge": "aeiouäöü",
    "gr": "αεηιουώάέήίόύώϊϋΐΰ",
    "it": "aeiouàèéìíòóùú",
    "no": "aeiouyæøå",
    "sp": "aeiouáéíóúü",
    "ru": "аеёиоуыэюя",
    "tr": "aeıioöuü",
}

# Fila del supp texts.csv → código MECO (Korean omitido a propósito)
ROW_TO_LANG = {
    "Dutch": "du",
    "English": "en",
    "Estonian": "ee",
    "Finnish": "fi",
    "German": "ge",
    "Greek": "gr",
    "Hebrew": "he",
    "Italian": "it",
    "Norwegian": "no",
    "Russian": "ru",
    "Spanish": "sp",
    "Turkish": "tr",
}

# Conjunto de puntuación Unicode (para limpieza de tokens)
_PUNCT_STRIP_RE = re.compile(r"^[\W_\u00b7\u2013\u2014\u2018\u2019\u201c\u201d\u00ab\u00bb\u2026]+|[\W_\u00b7\u2013\u2014\u2018\u2019\u201c\u201d\u00ab\u00bb\u2026]+$")


def clean_token(raw: str) -> str:
    """Token limpio: sin puntuación inicial/final (se conservan guiones y apóstrofos internos)."""
    w = str(raw).strip()
    clean = _PUNCT_STRIP_RE.sub("", w)
    return clean


def is_punct_only(clean: str) -> bool:
    return clean == ""


# ---------------------------------------------------------------------------
# Exportación desde R (tokens por itemid + medidas humanas)
# ---------------------------------------------------------------------------

R_EXPORT_CODE = """
e <- new.env()
load({rda!r}, envir = e)
d <- e$joint.data
d <- d[!is.na(d$wordnum) & !is.na(d$itemid) & d$lang %in% c({langs}), ]
outdir <- {outdir!r}
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

for (lg in c({langs})) {{
  sub <- d[d$lang == lg, ]
  w <- sub[!duplicated(sub[, c("itemid", "wordnum")]),
           c("itemid", "sentnum", "wordnum", "word")]
  w <- w[order(w$itemid, w$wordnum), ]
  for (it in unique(w$itemid)) {{
    wi <- w[w$itemid == it, c("sentnum", "wordnum", "word")]
    write.csv(wi, file.path(outdir, sprintf("%s_item%02d.csv", lg, as.integer(it))),
              row.names = FALSE, fileEncoding = "UTF-8")
  }}
}}

a1 <- aggregate(skip ~ lang + itemid + wordnum, data = d, FUN = length)
names(a1)[4] <- "n_human_observations"
a2 <- aggregate(skip ~ lang + itemid + wordnum, data = d, FUN = mean)
names(a2)[4] <- "human_skip_rate"
a3 <- aggregate(firstrun.dur ~ lang + itemid + wordnum, data = d,
                FUN = function(x) mean(x[!is.na(x)]))
names(a3)[4] <- "human_firstpass_dur_ms"
a4 <- aggregate(dur ~ lang + itemid + wordnum, data = d,
                FUN = function(x) mean(x[!is.na(x)]))
names(a4)[4] <- "human_total_dur_ms"
h <- Merge <- merge(a1, a2, by = c("lang", "itemid", "wordnum"))
h <- merge(h, a3, by = c("lang", "itemid", "wordnum"), all.x = TRUE)
h <- merge(h, a4, by = c("lang", "itemid", "wordnum"), all.x = TRUE)
h <- h[order(h$lang, h$itemid, h$wordnum), ]
write.csv(h, file.path(outdir, "human_measures_l1.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
cat("exported\\n")
"""


def export_r_tokens() -> None:
    """Exporta tokens únicos por (lang, itemid) y medidas humanas agregadas."""
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    code = R_EXPORT_CODE.format(
        rda=str(RDA_PATH),
        langs=", ".join(f'"{lg}"' for lg in LANG_CONFIG),
        outdir=str(TOKENS_DIR),
    )
    res = subprocess.run(["Rscript", "-e", code], capture_output=True, text=True, timeout=900)
    if "exported" not in res.stdout:
        raise RuntimeError(f"Falló la exportación R:\n{res.stdout}\n{res.stderr}")
    logger.info("Tokens y medidas humanas exportados a %s", TOKENS_DIR)


@lru_cache(maxsize=None)
def load_r_tokens(lang: str) -> Dict[int, List[Dict]]:
    """{itemid: [{sentnum, wordnum, word}, ...]} ordenado por wordnum."""
    result: Dict[int, List[Dict]] = {}
    for csv_path in sorted(TOKENS_DIR.glob(f"{lang}_item*.csv")):
        itemid = int(csv_path.stem.split("_item")[1])
        df = pd.read_csv(csv_path, encoding="utf-8")
        entries = [
            {
                "sentnum": int(r["sentnum"]),
                "wordnum": int(r["wordnum"]),
                "word": str(r["word"]),
            }
            for _, r in df.iterrows()
        ]
        result[itemid] = entries
    if not result:
        raise FileNotFoundError(f"Sin tokens R para {lang} en {TOKENS_DIR}")
    return result


@lru_cache(maxsize=None)
def load_human_measures() -> pd.DataFrame:
    return pd.read_csv(TOKENS_DIR / "human_measures_l1.csv", encoding="utf-8")


# ---------------------------------------------------------------------------
# Textos de referencia (supp texts.csv)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def load_supp_texts() -> Dict[str, Dict[int, str]]:
    """{lang_code: {text_index(1..12): texto plano}} desde supp texts.csv."""
    import csv as _csv

    texts: Dict[str, Dict[int, str]] = {}
    with open(SUPP_TEXTS_CSV, newline="", encoding="utf-8-sig") as f:
        rows = list(_csv.reader(f))
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        lang = ROW_TO_LANG.get(row[0].strip())
        if lang is None:
            continue
        texts[lang] = {}
        for idx, cell in enumerate(row[1 : N_TEXTS + 1], start=1):
            t = str(cell) if cell else ""
            t = re.sub(r"\s+", " ", t).strip()
            texts[lang][idx] = t
    missing = set(ROW_TO_LANG.values()) - set(texts)
    if missing:
        raise RuntimeError(f"Lenguas ausentes en supp texts.csv: {missing}")
    return texts


def normalize_seq(tokens: List[str]) -> List[str]:
    """Tokens limpios y en minúsculas, sin elementos vacíos (para alineación)."""
    out = []
    for t in tokens:
        c = clean_token(t).lower()
        if c:
            out.append(c)
    return out


def map_itemid_to_text(lang: str) -> Dict[int, int]:
    """
    Mapea itemid → índice de texto (1..12) alineando la secuencia de tokens del
    .rda con los textos del supp texts.csv (difflib sobre tokens normalizados).
    """
    tokens_by_item = load_r_tokens(lang)
    ref_texts = load_supp_texts()[lang]
    ref_seqs = {idx: normalize_seq([txt]) and normalize_seq(re.findall(r"\S+", txt)) for idx, txt in ref_texts.items()}
    mapping: Dict[int, int] = {}
    for itemid, entries in tokens_by_item.items():
        seq = normalize_seq([e["word"] for e in entries])
        best_idx, best_ratio = None, -1.0
        for idx, rseq in ref_seqs.items():
            sm = difflib.SequenceMatcher(None, seq, rseq, autojunk=False)
            ratio = sm.quick_ratio()
            if ratio < best_ratio:
                continue
            ratio = sm.ratio() if ratio > 0.5 else ratio
            if ratio > best_ratio:
                best_ratio, best_idx = ratio, idx
        if best_idx is None or best_ratio < 0.5:
            raise RuntimeError(f"{lang}: itemid {itemid} no pudo mapearse a ningún texto (best={best_ratio:.2f})")
        if best_idx in mapping.values():
            raise RuntimeError(f"{lang}: texto {best_idx} mapeado dos veces (itemid {itemid})")
        mapping[itemid] = best_idx
    if sorted(mapping.values()) != list(range(1, N_TEXTS + 1)):
        raise RuntimeError(f"{lang}: mapeo incompleto de textos: {sorted(mapping.values())}")
    return mapping


# ---------------------------------------------------------------------------
# POS tagging (spaCy / Stanza), token aislado con regla del segmento más largo
# ---------------------------------------------------------------------------

_SPACY_NLPS: Dict[str, object] = {}
_STANZA_NLPS: Dict[str, object] = {}


def get_spacy_nlp(model: str):
    if model not in _SPACY_NLPS:
        import spacy

        logger.info("Cargando spaCy %s ...", model)
        _SPACY_NLPS[model] = spacy.load(model, disable=["parser", "ner", "lemmatizer"])
    return _SPACY_NLPS[model]


def get_stanza_nlp(lang: str):
    if lang not in _STANZA_NLPS:
        import stanza

        logger.info("Cargando Stanza %s ...", lang)
        stanza.download(lang, processors="tokenize,pos", verbose=False)
        _STANZA_NLPS[lang] = stanza.Pipeline(
            lang, processors="tokenize,pos", verbose=False, use_gpu=False
        )
    return _STANZA_NLPS[lang]


@lru_cache(maxsize=200000)
def tag_token_spacy(model: str, token: str) -> Tuple[str, str]:
    """(upos, tag_fino) para un token aislado con spaCy."""
    nlp = get_spacy_nlp(model)
    doc = nlp(token)
    if len(doc) == 0:
        return "X", "X"
    upos = doc[0].pos_ or "X"
    fine = doc[0].tag_ or upos
    return upos, fine


@lru_cache(maxsize=200000)
def tag_token_stanza(lang: str, token: str) -> Tuple[str, str]:
    """(upos, tag_fino) con Stanza; si sub-divide el token, gana el segmento más largo."""
    nlp = get_stanza_nlp(lang)
    doc = nlp(token)
    words = [w for s in doc.sentences for w in s.words]
    if not words:
        return "X", "X"
    if len(words) == 1:
        return words[0].upos or "X", (words[0].xpos or words[0].upos or "X")
    head = max(words, key=lambda w: len(w.text))
    return head.upos or "X", (head.xpos or head.upos or "X")


def tag_token(lang: str, token: str) -> Tuple[str, str]:
    cfg = LANG_CONFIG[lang]
    if cfg["engine"] == "spacy":
        return tag_token_spacy(cfg["model"], token)
    return tag_token_stanza(cfg["model"], token)


def classify_universal_pos(upos: str, word_clean_lower: str) -> Tuple[str, str, str, str]:
    """
    UPOS → (categoria_gramatical, tipo_lexico, subtipo_gramatical, pos_tag_universal).
    Misma taxonomía española que `classify_words.py` (L2) y `classify_words_chinese.py`.
    """
    if upos == "NOUN":
        return "Sustantivo", "Palabra de Contenido", "Sustantivo común", "NOUN"
    if upos == "PROPN":
        return "Sustantivo", "Palabra de Contenido", "Nombre propio", "PROPN"
    if upos == "VERB":
        return "Verbo", "Palabra de Contenido", "Verbo léxico/principal", "VERB"
    if upos == "AUX":
        return "Verbo", "Palabra Funcional", "Verbo auxiliar o cópula", "AUX"
    if upos == "ADJ":
        return "Adjetivo", "Palabra de Contenido", "Adjetivo calificativo", "ADJ"
    if upos == "ADV":
        return "Adverbio", "Palabra Funcional", "Adverbio de modo/grado/tiempo", "ADV"
    if upos == "PRON":
        return "Pronombre", "Palabra Funcional", "Pronombre personal o demostrativo", "PRON"
    if upos == "DET":
        sub = "Artículo" if word_clean_lower in ARTICLES_ALL else "Determinante"
        return "Determinante", "Palabra Funcional", sub, "DET"
    if upos == "ADP":
        return "Preposición", "Palabra Funcional", "Preposición o postposición", "ADP"
    if upos == "CCONJ":
        return "Conjunción", "Palabra Funcional", "Conjunción coordinante", "CCONJ"
    if upos == "SCONJ":
        return "Conjunción", "Palabra Funcional", "Conjunción subordinante", "SCONJ"
    if upos == "NUM":
        return "Numeral", "Palabra de Contenido", "Numeral cardinal", "NUM"
    if upos == "PART":
        return "Partícula", "Palabra Funcional", "Partícula gramatical", "PART"
    if upos == "INTJ":
        return "Interjección", "Palabra de Contenido", "Interjección", "INTJ"
    if upos == "PUNCT":
        return "Puntuación", None, "Puntuación", "PUNCT"
    return "Otro", "Palabra de Contenido", "Elemento léxico general", "X"


# Artículos (DET que son artículos) para las lenguas con artículos definidos/indefinidos
ARTICLES_ALL = {
    # du
    "de", "het", "een",
    # en
    "the", "a", "an",
    # ge
    "der", "die", "das", "ein", "eine", "einen", "einem", "einer", "eines",
    "den", "dem", "des",
    # gr
    "ο", "η", "το", "οι", "οι", "τα", "του", "της", "των", "τον", "την", "το",
    "ένας", "μία", "ένα",
    # it
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una",
    # no
    "en", "ei", "et", "den", "det", "de",
    # sp
    "el", "la", "los", "las", "un", "una", "unos", "unas", "lo",
}


# ---------------------------------------------------------------------------
# Silabas
# ---------------------------------------------------------------------------

def ensure_nltk_cmu() -> dict:
    import nltk

    try:
        nltk.data.find("corpora/cmudict")
    except LookupError:
        nltk.download("cmudict", quiet=True)
    from nltk.corpus import cmudict

    return cmudict.dict()


_CMU: Optional[dict] = None


def count_syllables_en(word: str) -> int:
    global _CMU
    if _CMU is None:
        _CMU = ensure_nltk_cmu()
    clean = re.sub(r"[^a-zA-Z]", "", word).lower()
    if not clean:
        return 1
    if clean in _CMU:
        return [len([y for y in x if y[-1].isdigit()]) for x in _CMU[clean]][0]
    clean = re.sub(r"(?:[^laeiouy]|ed|es|e)$", "", clean)
    clean = re.sub(r"^y", "", clean)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", clean)))


def count_syllables_cluster(word: str, vowels: str) -> int:
    """Agrupa vocales consecutivas (diptongos) en una sílaba."""
    clean = word.lower()
    n = 0
    prev_vowel = False
    for ch in clean:
        if ch in vowels:
            if not prev_vowel:
                n += 1
            prev_vowel = True
        else:
            prev_vowel = False
    return max(1, n)


def count_syllables_count(word: str, vowels: str) -> int:
    """Cada vocal es una sílaba (ruso, turco)."""
    n = sum(1 for ch in word.lower() if ch in vowels)
    return max(1, n)


def count_syllables_hebrew(word: str) -> int:
    """Aproximación: 1 + letras vocálicas mediales (ו, י) sin punto de vocal escrito."""
    letters = [ch for ch in word if "\u0590" <= ch <= "\u05FF"]
    if not letters:
        return 1
    medial = 0
    for i, ch in enumerate(letters):
        if ch in ("ו", "י") and 0 < i < len(letters) - 1:
            medial += 1
    prefix_ve = 1 if letters[0] == "ו" else 0  # conjunción ו- ("y-") = onset silábico
    return max(1, 1 + medial + prefix_ve)


def count_syllables(word_clean: str, lang: str) -> int:
    cfg = LANG_CONFIG[lang]
    if not word_clean:
        return 0
    method = cfg["syl"]
    if method == "cmudict":
        return count_syllables_en(word_clean)
    if method == "hebrew":
        return count_syllables_hebrew(word_clean)
    if method == "count":
        return count_syllables_count(word_clean, VOWELS[lang])
    return count_syllables_cluster(word_clean, VOWELS[lang])


def classify_length(clean_word: str, lang: str) -> Tuple[int, int, str]:
    """Longitud en letras, sílabas y categoría (mismas bandas que words_classified.csv L2)."""
    length = len(clean_word)
    if length == 0:
        return 0, 0, "Puntuación"
    syls = count_syllables(clean_word, lang)
    if length <= 4:
        cat = "Corta (1-4 letras)"
    elif length <= 8:
        cat = "Media (5-8 letras)"
    else:
        cat = "Larga (9+ letras)"
    return length, syls, cat


# ---------------------------------------------------------------------------
# Frecuencia
# ---------------------------------------------------------------------------

@lru_cache(maxsize=200000)
def zipf_wordfreq(word_lower: str, wf_lang: str) -> float:
    from wordfreq import zipf_frequency

    z = zipf_frequency(word_lower, wf_lang)
    if z <= 0:
        return 1.0
    return round(float(min(7.6, z)), 4)


def classify_frequency_category(zipf_freq: float) -> str:
    if zipf_freq >= 6.0:
        return "Muy Alta Frecuencia"
    elif zipf_freq >= 5.0:
        return "Alta Frecuencia"
    elif zipf_freq >= 4.0:
        return "Media Frecuencia"
    else:
        return "Baja Frecuencia"


# ---------------------------------------------------------------------------
# Modelo n-gram (idéntico a classify_words_chinese.build_chinese_ngram_model)
# ---------------------------------------------------------------------------

def build_ngram_model(all_sents_tokenized: List[List[str]]):
    """Modelo trigram interpolado (Jelinek-Mercer) → get_predictability(w, prev1, prev2)."""
    uni_counts: Counter = Counter()
    bi_counts: Counter = Counter()
    tri_counts: Counter = Counter()
    context_bi: Counter = Counter()
    context_tri: Counter = Counter()

    for s in all_sents_tokenized:
        padded = ["<s>", "<s>"] + s + ["</s>"]
        for i in range(2, len(padded)):
            w = padded[i]
            prev1 = padded[i - 1]
            prev2 = padded[i - 2]
            uni_counts[w] += 1
            bi_counts[(prev1, w)] += 1
            context_bi[prev1] += 1
            tri_counts[(prev2, prev1, w)] += 1
            context_tri[(prev2, prev1)] += 1

    total_words = sum(uni_counts.values())

    def get_predictability(w: str, prev1: str, prev2: str) -> Tuple[float, float]:
        p_uni = uni_counts[w] / total_words if total_words > 0 else 1e-5
        p_bi = bi_counts[(prev1, w)] / context_bi[prev1] if context_bi[prev1] > 0 else p_uni
        p_tri = tri_counts[(prev2, prev1, w)] / context_tri[(prev2, prev1)] if context_tri[(prev2, prev1)] > 0 else p_bi
        p_interp = 0.55 * p_tri + 0.30 * p_bi + 0.15 * p_uni
        p_interp = max(1e-8, min(1.0, p_interp))
        surprisal = -math.log2(p_interp)
        return p_interp, surprisal

    return get_predictability


def classify_predictability_category(prob: float, surprisal: float) -> str:
    if prob >= 0.08 or surprisal < 3.65:
        return "Alta Predictibilidad"
    elif prob >= 0.008 or surprisal < 7.0:
        return "Media Predictibilidad"
    else:
        return "Baja Predictibilidad"


# ---------------------------------------------------------------------------
# Pipeline por lengua
# ---------------------------------------------------------------------------

def classify_language(lang: str) -> Tuple[pd.DataFrame, Dict[str, object]]:
    cfg = LANG_CONFIG[lang]
    logger.info("=== %s (%s): clasificación ===", lang, cfg["nombre"])
    mapping = map_itemid_to_text(lang)
    # Persistencia del mapeo itemid → índice de texto (necesario para unir
    # fijaciones wave 1, donde la identidad del texto es itemid; ee/ru rotan).
    pd.DataFrame(
        {"itemid": sorted(mapping), "text_index": [mapping[i] for i in sorted(mapping)]}
    ).to_csv(TOKENS_DIR / f"itemid_to_text_{lang}.csv", index=False, encoding="utf-8")
    tokens_by_item = load_r_tokens(lang)
    supp_texts = load_supp_texts()[lang]

    # Secuencia de textos en orden 1..12
    texts: Dict[int, List[Dict]] = {}
    for itemid, textidx in mapping.items():
        entries = sorted(tokens_by_item[itemid], key=lambda e: e["wordnum"])
        texts[textidx] = [
            {
                "sentnum": e["sentnum"],
                "wordnum": e["wordnum"],
                "word": e["word"],
                "word_clean": clean_token(e["word"]),
            }
            for e in entries
        ]

    # Corpus para n-gramas y frecuencia interna
    corpus_tokens: List[List[str]] = []
    corpus_counter: Counter = Counter()
    for textidx in range(1, N_TEXTS + 1):
        by_sent: Dict[int, List[Dict]] = {}
        for e in texts[textidx]:
            by_sent.setdefault(e["sentnum"], []).append(e)
        for sn in sorted(by_sent):
            toks = [e["word_clean"].lower() for e in by_sent[sn] if e["word_clean"]]
            corpus_tokens.append(toks)
            corpus_counter.update(toks)
    predict_fn = build_ngram_model(corpus_tokens)
    corpus_total = sum(corpus_counter.values())

    records = []
    for textidx in range(1, N_TEXTS + 1):
        by_sent: Dict[int, List[Dict]] = {}
        for e in texts[textidx]:
            by_sent.setdefault(e["sentnum"], []).append(e)
        for sn in sorted(by_sent):
            sent = by_sent[sn]
            sent_clean = [e["word_clean"].lower() for e in sent]
            for i, entry in enumerate(sent):
                raw_word = entry["word"]
                clean_word = entry["word_clean"]
                lower = clean_word.lower()
                punct = is_punct_only(clean_word)

                if punct:
                    records.append(
                        {
                            "lang": lang,
                            "trialid": textidx,
                            "text_name": TEXT_NAMES[textidx],
                            "sentnum": entry["sentnum"],
                            "ianum": entry["wordnum"],
                            "wordnum": entry["wordnum"],
                            "word": raw_word,
                            "word_clean": "",
                            "largo_caracteres": 0,
                            "num_silabas": 0,
                            "categoria_largo": "Puntuación",
                            "freq_corpus": None,
                            "zipf_freq": None,
                            "categoria_frecuencia": None,
                            "categoria_gramatical": "Puntuación",
                            "tipo_lexico": None,
                            "subtipo_gramatical": "Puntuación",
                            "pos_tag_universal": "PUNCT",
                            "pos_tag_native": "PUNCT",
                            "predictibilidad_prob": None,
                            "surprisal_bits": None,
                            "categoria_predictibilidad": None,
                        }
                    )
                    continue

                len_chars, syls, len_cat = classify_length(clean_word, lang)

                if cfg["wf"]:
                    zipf_val = zipf_wordfreq(lower, cfg["wf"])
                else:
                    # Estonio: sin lista en wordfreq → frecuencia interna del corpus
                    count = corpus_counter.get(lower, 0)
                    pm = max(0.01, (count / corpus_total) * 1e6) if corpus_total else 0.01
                    zipf_val = round(max(1.0, min(7.6, math.log10(pm) + 3.0)), 4)
                freq_cat = classify_frequency_category(zipf_val)

                upos, fine = tag_token(lang, raw_word.strip())
                pos_cat, tipo_lex, subtipo, pos_univ = classify_universal_pos(upos, lower)

                prev1 = sent_clean[i - 1] if i >= 1 else "<s>"
                prev2 = sent_clean[i - 2] if i >= 2 else "<s>"
                prob, surprisal = predict_fn(lower, prev1, prev2)
                pred_cat = classify_predictability_category(prob, surprisal)

                records.append(
                    {
                        "lang": lang,
                        "trialid": textidx,
                        "text_name": TEXT_NAMES[textidx],
                        "sentnum": entry["sentnum"],
                        "ianum": entry["wordnum"],
                        "wordnum": entry["wordnum"],
                        "word": raw_word,
                        "word_clean": clean_word,
                        "largo_caracteres": len_chars,
                        "num_silabas": syls,
                        "categoria_largo": len_cat,
                        "freq_corpus": int(corpus_counter.get(lower, 0)),
                        "zipf_freq": zipf_val,
                        "categoria_frecuencia": freq_cat,
                        "categoria_gramatical": pos_cat,
                        "tipo_lexico": tipo_lex,
                        "subtipo_gramatical": subtipo,
                        "pos_tag_universal": pos_univ,
                        "pos_tag_native": fine,
                        "predictibilidad_prob": round(prob, 6),
                        "surprisal_bits": round(surprisal, 3),
                        "categoria_predictibilidad": pred_cat,
                    }
                )
    df = pd.DataFrame(records)

    # ---- Medidas humanas (merge por lang + itemid→trialid + wordnum) ----
    human = load_human_measures()
    human = human[human["lang"] == lang].copy()
    human["trialid"] = human["itemid"].map(mapping)
    human = human.rename(
        columns={
            "human_skip_rate": "human_skip_rate",
            "human_firstpass_dur_ms": "human_firstpass_dur_ms",
            "human_total_dur_ms": "human_total_dur_ms",
            "n_human_observations": "n_human_observations",
        }
    )
    human = human[
        [
            "trialid",
            "wordnum",
            "human_skip_rate",
            "human_firstpass_dur_ms",
            "human_total_dur_ms",
            "n_human_observations",
        ]
    ]
    human["human_skip_rate"] = human["human_skip_rate"].round(4)
    human["human_firstpass_dur_ms"] = human["human_firstpass_dur_ms"].round(1)
    human["human_total_dur_ms"] = human["human_total_dur_ms"].round(1)
    df = df.merge(human, on=["trialid", "wordnum"], how="left", validate="one_to_one")

    # ---- QA ----
    n_et = sum(len(v) for v in texts.values())
    pairs = set(zip(df["trialid"], df["wordnum"]))
    missing_ia = sum(
        1
        for textidx in range(1, N_TEXTS + 1)
        for e in texts[textidx]
        if (textidx, e["wordnum"]) not in pairs
    )
    # Concordancia con supp texts.csv (razón de similitud sobre texto normalizado)
    concord = []
    for textidx in range(1, N_TEXTS + 1):
        seq_r = " ".join(normalize_seq([e["word"] for e in texts[textidx]]))
        seq_c = " ".join(normalize_seq(re.findall(r"\S+", supp_texts[textidx])))
        ratio = difflib.SequenceMatcher(None, seq_r, seq_c, autojunk=False).ratio()
        concord.append(ratio)

    checks = {
        "lang": lang,
        "nombre": cfg["nombre"],
        "tokens_et": n_et,
        "tokens_benchmark": len(df),
        "tokens_match": n_et == len(df),
        "ias_sin_categoria": missing_ia,
        "ias_sin_medidas_humanas": int(df["n_human_observations"].isna().sum()),
        "zipf_rango": [float(df["zipf_freq"].min()), float(df["zipf_freq"].max())],
        "concordancia_media": round(sum(concord) / len(concord) * 100, 1),
        "concordancia_min": round(min(concord) * 100, 1),
        "item_map": {str(k): v for k, v in sorted(mapping.items())},
    }
    return df, checks


# ---------------------------------------------------------------------------
# Reporte Markdown combinado
# ---------------------------------------------------------------------------

def language_section(df: pd.DataFrame, checks: Dict[str, object]) -> List[str]:
    lang = checks["lang"]
    cfg = LANG_CONFIG[lang]
    dfValid = df[df["n_human_observations"].notna()]
    lines = [
        f"## {cfg['nombre']} (`{lang}`)",
        "",
        f"- **Tokens (IAs):** {len(df):,} | **Textos:** {df['trialid'].nunique()} | "
        f"**Oraciones:** {df.groupby(['trialid', 'sentnum']).ngroups} | "
        f"**Vocabulario único:** {df['word_clean'].nunique():,}",
        f"- **Verificación:** tokens ET {checks['tokens_et']} vs benchmark {checks['tokens_benchmark']} → "
        f"{'OK' if checks['tokens_match'] else 'MISMATCH'}; "
        f"IAs sin categoría: {checks['ias_sin_categoria']}; "
        f"IAs sin medidas humanas: {checks['ias_sin_medidas_humanas']}",
        f"- **Rango Zipf:** {checks['zipf_rango'][0]:.2f} – {checks['zipf_rango'][1]:.2f} | "
        f"**Concordancia con supp texts.csv:** media {checks['concordancia_media']}%, "
        f"mínima {checks['concordancia_min']}%",
    ]
    if lang in ("ee", "ru"):
        lines.append(
            f"- **Mapeo itemid → texto:** {checks['item_map']} (rotación de orden de presentación entre sujetos)"
        )
    if lang == "ee":
        lines.append(
            "- **Nota de frecuencia:** Estonio sin lista en `wordfreq`; Zipf derivado de la frecuencia interna del corpus (aproximación grosera)."
        )
    lines.append("")

    # Categorías gramaticales
    lines += [
        "### Categorías gramaticales",
        "",
        "| Categoría | Tokens | % | Ejemplos |",
        "| :--- | :--- | :--- | :--- |",
    ]
    pos_counts = df["categoria_gramatical"].value_counts()
    for cat, c in pos_counts.items():
        pct = round(c / len(df) * 100, 1)
        ex = ", ".join(df[df["categoria_gramatical"] == cat]["word_clean"].dropna().drop_duplicates().head(5).tolist())
        lines.append(f"| {cat} | {c} | {pct}% | {ex} |")

    # Funcional vs contenido
    lines += ["", "### Funcional vs. contenido", "", "| Tipo léxico | Tokens | % |", "| :--- | :--- | :--- |"]
    lex_counts = df["tipo_lexico"].value_counts()
    for lex, c in lex_counts.items():
        lines.append(f"| {lex} | {c} | {round(c / len(df) * 100, 1)}% |")

    # Largo
    lines += ["", "### Longitud y frecuencia", "", "| Categoría | Tokens | % |", "| :--- | :--- | :--- |"]
    for col in ("categoria_largo", "categoria_frecuencia"):
        counts = df[col].value_counts()
        for cat, c in counts.items():
            lines.append(f"| {cat} | {c} | {round(c / len(df) * 100, 1)}% |")
        lines.append("")

    # Medidas humanas
    lines += [
        "### Medidas humanas observadas (eye-tracking L1 wave 1)",
        "",
        "| Medida | Media | Mediana |",
        "| :--- | :--- | :--- |",
        f"| Skip rate | {dfValid['human_skip_rate'].mean():.3f} | {dfValid['human_skip_rate'].median():.3f} |",
        f"| Gaze duration primera pasada (ms) | {dfValid['human_firstpass_dur_ms'].mean():.1f} | {dfValid['human_firstpass_dur_ms'].median():.1f} |",
        f"| Tiempo total de lectura (ms) | {dfValid['human_total_dur_ms'].mean():.1f} | {dfValid['human_total_dur_ms'].median():.1f} |",
        "",
        "Correlaciones (Pearson) con medidas humanas:",
        "",
    ]
    corrs = {
        "zipf_freq ~ human_firstpass_dur_ms": df["zipf_freq"].corr(df["human_firstpass_dur_ms"]),
        "zipf_freq ~ human_skip_rate": df["zipf_freq"].corr(df["human_skip_rate"]),
        "surprisal_bits ~ human_firstpass_dur_ms": df["surprisal_bits"].corr(df["human_firstpass_dur_ms"]),
        "surprisal_bits ~ human_skip_rate": df["surprisal_bits"].corr(df["human_skip_rate"]),
        "largo_caracteres ~ human_firstpass_dur_ms": df["largo_caracteres"].corr(df["human_firstpass_dur_ms"]),
    }
    for k, v in corrs.items():
        lines.append(f"- {k}: **{v:.3f}**" if pd.notna(v) else f"- {k}: NA")
    lines.append("")
    return lines


def generate_report(all_checks: List[Dict[str, object]]) -> None:
    lines = [
        "# Clasificación Integral de Palabras — Lenguas L1 MECO (12 lenguas alfabéticas)",
        "",
        "Adaptación de la metodología china (`scripts/classify_words_chinese.py`,",
        "`classify_words_chinese_wave2.py`) a las lenguas L1 de MECO-L1 wave 1 con los",
        "12 textos Janus … Vehicle Registration Plate. **Koreano omitido** (solo L1, sin",
        "comparación posible con MECO-L2).",
        "",
        "Decisiones metodológicas clave:",
        "",
        "1. **Tokens = interest areas reales** (columna `word` del `.rda` wave 1 L1),",
        "   clave (lang, itemid, wordnum); `supp texts.csv` usado como verificación",
        "   (concordancia por texto reportada abajo).",
        "2. **Identidad de texto = `itemid`** (en Estonio y Ruso el orden de presentación",
        "   rotaba entre sujetos; el `trialid` no identifica el texto). El CSV de cada",
        "   lengua usa `trialid` = índice de texto 1..12 (columnas del supp texts.csv).",
        "3. **POS**: spaCy `*_core_news_sm` (9 lenguas) y Stanza tokenize+pos (Estonio,",
        "   Hebreo, Turco). IA etiquetado como token aislado; si el tagger sub-divide,",
        "   se toma el UPOS del segmento más largo (regla idéntica al script chino).",
        "4. **Frecuencia**: Zipf de `wordfreq` por lengua (Estonio: frecuencia interna",
        "   del corpus, sin lista disponible), categorías iguales al benchmark chino/L2.",
        "5. **Predictibilidad/Surprisal**: trigram interpolado (Jelinek-Mercer",
        "   0.55/0.30/0.15) entrenado por lengua sobre sus 12 textos; mismos umbrales",
        "   que el benchmark chino.",
        "6. **Sílabas**: CMUdict (inglés); vocales mediales ו/י (hebreo); conteo de",
        "   vocales (ruso, turco); agrupación de vocales consecutivas (resto).",
        "7. **Medidas humanas** fusionadas por (lang, texto, wordnum): skip rate, gaze",
        "   duration de primera pasada y tiempo total de lectura del .rda wave 1 L1.",
        "",
        "Salidas: `data/benchmark/words_classified_<lang>_l1.csv` (12 archivos) y",
        "`data/benchmark/l1_tokens/tid<NN>_<lang>.csv` (secuencias de IAs por texto).",
        "",
        "## Resumen de verificación de calidad",
        "",
        "| Lengua | Código | Tokens ET | Benchmark | Match | IAs sin human | Zipf mín–máx | Concordancia supp (%) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for checks in all_checks:
        zmin, zmax = checks["zipf_rango"]
        lines.append(
            f"| {checks['nombre']} | {checks['lang']} | {checks['tokens_et']} | "
            f"{checks['tokens_benchmark']} | {'OK' if checks['tokens_match'] else 'MISMATCH'} | "
            f"{checks['ias_sin_medidas_humanas']} | {zmin:.2f}–{zmax:.2f} | {checks['concordancia_media']} |"
        )
    lines.append("")
    for checks in all_checks:
        df = pd.read_csv(BENCH_DIR / f"words_classified_{checks['lang']}_l1.csv")
        lines += language_section(df, checks)
    lines.append("Fin del reporte.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Reporte guardado en %s", REPORT_PATH)


# ---------------------------------------------------------------------------

def main() -> None:
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    if not any(TOKENS_DIR.glob("*_item*.csv")) or not (TOKENS_DIR / "human_measures_l1.csv").exists():
        export_r_tokens()

    all_checks = []
    for lang in LANG_CONFIG:
        df, checks = classify_language(lang)
        csv_path = BENCH_DIR / f"words_classified_{lang}_l1.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("%s: dataset guardado en %s (%d registros)", lang, csv_path, len(df))

        # Archivos de tokens por texto (patrón wave-2 chino)
        mapping = {int(k): v for k, v in checks["item_map"].items()}
        tokens_by_item = load_r_tokens(lang)
        for itemid, entries in tokens_by_item.items():
            textidx = mapping[itemid]
            out = TOKENS_DIR / f"tid{textidx:02d}_{lang}.csv"
            pd.DataFrame(entries, columns=["sentnum", "wordnum", "word"]).to_csv(
                out, index=False, encoding="utf-8"
            )

        all_checks.append(checks)

    generate_report(all_checks)

    print("\n" + "=" * 72)
    print("CLASIFICACIÓN L1 (12 LENGUAS) COMPLETADA")
    for c in all_checks:
        print(
            f"  {c['lang']}: ET={c['tokens_et']} bench={c['tokens_benchmark']} "
            f"match={c['tokens_match']} humanNA={c['ias_sin_medidas_humanas']} "
            f"concord={c['concordancia_media']}%"
        )
    print("=" * 72)


if __name__ == "__main__":
    main()
