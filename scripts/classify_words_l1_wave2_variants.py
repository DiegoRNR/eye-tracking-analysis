#!/usr/bin/env python3
"""
scripts/classify_words_l1_wave2_variants.py

Clasificación de palabras para las VARIANTES wave 2 de MECO-L1 no cubiertas por
`classify_words_l1_all_languages.py` (que procesó las 12 lenguas wave 1 + chino
ch_s/ch_t). Cada variante es un GRUPO SEPARADO (sin fusiones):

    ba=Vasco, bp=Portugués (Brasil), da=Danés, en_uk=Inglés UK,
    ge_po=Alemán (Potsdam), ge_zu=Alemán (Zúrich), hi_iiith=Hindi (IIITH),
    hi_iitk=Hindi (IITK), ic=Islandés, ru_mo=Ruso (wave 2), se=Serbio,
    sp_ch=Español (Chile), no_w2=Noruego (cohorte wave 2), tr_w2=Turco (cohorte wave 2)

Metodología idéntica a la wave 1 (`classify_words_l1_all_languages.py`):
1. Tokens = interest areas reales del experimento: columna `word` del
   `joint_data_trimmed_wave2_version2.1.rda`, clave (lang, itemid, wordnum).
2. Identidad de texto = `itemid` mapeado a índice 1..12 (columnas de
   `supp texts_wave2.xlsx`) por alineación de secuencias; ic y en_uk rotan el
   orden de presentación entre sujetos. Los textos de ge_po y ge_zu son
   idénticos (nota en Sheet2 del xlsx) pero cada variante recibe su propio
   benchmark y grupo.
3. POS: spaCy (pt, da, de, en, es, ru, nb) y Stanza (eu, hi, is, sr, tr) —
   IA etiquetado aislado, regla del segmento más largo si sub-divide.
4. Frecuencia: Zipf de `wordfreq` (sr y eu sin lista → frecuencia interna del
   corpus, documentada); techo/suelo [1.0, 7.6].
5. Sílabas: pyphen (pt_BR, da, is, sr, eu) donde hay diccionario; CMUdict
   (en_uk); conteo de vocales (ru, tr); agrupación de vocales (de, es, nb);
   aksharas devanágari (hi, aproximación documentada).
6. Predictibilidad/Surprisal: trigram interpolado (Jelinek-Mercer) por variante
   sobre sus 12 textos; mismos umbrales que el benchmark chino/L1.
7. Medidas humanas del mismo .rda (skip rate, gaze, total) fusionadas por
   (lang, texto, wordnum).

Salidas:
- data/benchmark/words_classified_<code>_w2l1.csv   (14 variantes)
- data/benchmark/l1_tokens_w2/                      (tokens por texto + mapeos itemid)
- data/CLASIFICACION_PALABRAS_L1_WAVE2.md           (reporte combinado)
"""

from __future__ import annotations

import difflib
import logging
import math
import re
import subprocess
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import classify_words_l1_all_languages as base
from classify_words_l1_all_languages import (
    clean_token,
    build_ngram_model,
    classify_frequency_category,
    classify_predictability_category,
    classify_universal_pos,
    is_punct_only,
    tag_token_spacy,
    tag_token_stanza,
    zipf_wordfreq,
)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("classify_l1_w2")

REPO_ROOT = Path(__file__).resolve().parent.parent
RDA_W2 = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-2"
    / "primary-data"
    / "eye tracking data"
    / "joint_data_trimmed_wave2_version2.1.rda"
)
XLSX_W2 = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-2"
    / "auxiliary files"
    / "reading task materials"
    / "supp texts_wave2.xlsx"
)
BENCH_DIR = REPO_ROOT / "data" / "benchmark"
TOKENS_DIR = BENCH_DIR / "l1_tokens_w2"
HUMAN_CSV = TOKENS_DIR / "human_measures_w2l1.csv"
REPORT_PATH = REPO_ROOT / "data" / "CLASIFICACION_PALABRAS_L1_WAVE2.md"

N_TEXTS = 12

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

# Fila del xlsx wave 2 → código de variante (etiqueta EXACTA, sin prefijos)
XLSX_ROW_TO_LANG = {
    "Basque": "ba",
    "Danish": "da",
    "English (uk)": "en_uk",
    "German Wave 2": "ge_po",
    "German Wave 2 Zurich": "ge_zu",
    "Hindi iiith": "hi_iiith",
    "Hindi iitk": "hi_iitk",
    "Icelandic": "ic",
    "Norwegian Wave 2": "no_w2",
    "Portuguese(Brazil)": "bp",
    "Russian Wave 2": "ru_mo",
    "Serbian": "se",
    "Spanish(Chile)": "sp_ch",
    "Turkish Wave 2": "tr_w2",
}

LANG_CONFIG: Dict[str, Dict] = {
    "ba": dict(nombre="Vasco", engine="stanza", model="eu", wf=None, syl="pyphen", pyphen="eu"),
    "bp": dict(nombre="Portugués (Brasil)", engine="spacy", model="pt_core_news_sm", wf="pt", syl="pyphen", pyphen="pt_BR"),
    "da": dict(nombre="Danés", engine="spacy", model="da_core_news_sm", wf="da", syl="pyphen", pyphen="da"),
    "en_uk": dict(nombre="Inglés UK", engine="spacy", model="en_core_web_sm", wf="en", syl="cmudict"),
    "ge_po": dict(nombre="Alemán (Potsdam)", engine="spacy", model="de_core_news_sm", wf="de", syl="cluster", vowels="aeiouäöü"),
    "ge_zu": dict(nombre="Alemán (Zúrich)", engine="spacy", model="de_core_news_sm", wf="de", syl="cluster", vowels="aeiouäöü"),
    "hi_iiith": dict(nombre="Hindi (IIITH)", engine="stanza", model="hi", wf="hi", syl="akshara"),
    "hi_iitk": dict(nombre="Hindi (IITK)", engine="stanza", model="hi", wf="hi", syl="akshara"),
    "ic": dict(nombre="Islandés", engine="stanza", model="is", wf="is", syl="pyphen", pyphen="is"),
    "ru_mo": dict(nombre="Ruso (wave 2)", engine="spacy", model="ru_core_news_sm", wf="ru", syl="count", vowels="аеёиоуыэюя"),
    "se": dict(nombre="Serbio", engine="stanza", model="sr", wf=None, syl="cluster", vowels="aeiou"),
    "sp_ch": dict(nombre="Español (Chile)", engine="spacy", model="es_core_news_sm", wf="es", syl="cluster", vowels="aeiouáéíóúü"),
    "no_w2": dict(nombre="Noruego (wave 2)", engine="spacy", model="nb_core_news_sm", wf="nb", syl="cluster", vowels="aeiouyæøå"),
    "tr_w2": dict(nombre="Turco (wave 2)", engine="stanza", model="tr", wf="tr", syl="count", vowels="aeıioöuü"),
}

# Códigos crudos en el .rda (no_w2/tr_w2 son cohortes wave 2 de no/tr)
RAW_LANG = {code: code.removesuffix("_w2") for code in LANG_CONFIG}

# Artículos adicionales para DET → 'Artículo' (pt/da/is)
base.ARTICLES_ALL |= {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "ao", "à", "aos", "às",
    "hinn", "hin", "hið", "hinir", "hinar",
}

def _is_edge_punct(ch: str) -> bool:
    """Puntuación/símbolo/espacio para recorte de bordes (conserva Mn/Mc: matras)."""
    import unicodedata

    return ch and unicodedata.category(ch)[0] in ("P", "S", "Z")


def clean_token_w2(raw: str) -> str:
    """
    Token limpio: recorta puntuación/símbolos de los bordes por categoría
    Unicode (P*/S*/Z*), lo que preserva las matras devanágari (Mn/Mc) — \W las
    clasificaría como no-palabra y las eliminaría (के → क).
    """
    w = str(raw).strip()
    while w and _is_edge_punct(w[0]):
        w = w[1:]
    while w and _is_edge_punct(w[-1]):
        w = w[:-1]
    return w


# ---------------------------------------------------------------------------
# Exportación R (tokens por itemid + medidas humanas)
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
h <- merge(a1, a2, by = c("lang", "itemid", "wordnum"))
h <- merge(h, a3, by = c("lang", "itemid", "wordnum"), all.x = TRUE)
h <- merge(h, a4, by = c("lang", "itemid", "wordnum"), all.x = TRUE)
h <- h[order(h$lang, h$itemid, h$wordnum), ]
write.csv(h, {human!r}, row.names = FALSE, fileEncoding = "UTF-8")
cat("exported\\n")
"""


def export_r_tokens() -> None:
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    code = R_EXPORT_CODE.format(
        rda=str(RDA_W2),
        langs=", ".join(f'"{RAW_LANG[c]}"' for c in LANG_CONFIG),
        outdir=str(TOKENS_DIR),
        human=str(HUMAN_CSV),
    )
    res = subprocess.run(["Rscript", "-e", code], capture_output=True, text=True, timeout=1800)
    if "exported" not in res.stdout:
        raise RuntimeError(f"Falló la exportación R:\n{res.stdout}\n{res.stderr}")
    logger.info("Tokens y medidas humanas wave 2 exportados a %s", TOKENS_DIR)


@lru_cache(maxsize=None)
def load_r_tokens(lang: str) -> Dict[int, List[Dict]]:
    raw = RAW_LANG[lang]
    result: Dict[int, List[Dict]] = {}
    for csv_path in sorted(TOKENS_DIR.glob(f"{raw}_item*.csv")):
        itemid = int(csv_path.stem.split("_item")[1])
        df = pd.read_csv(csv_path, encoding="utf-8")
        result[itemid] = [
            {"sentnum": int(r["sentnum"]), "wordnum": int(r["wordnum"]), "word": str(r["word"])}
            for _, r in df.iterrows()
        ]
    if not result:
        raise FileNotFoundError(f"Sin tokens R para {lang} en {TOKENS_DIR}")
    return result


def normalize_seq(tokens: List[str]) -> List[str]:
    out = []
    for t in tokens:
        c = clean_token_w2(t).lower()
        if c:
            out.append(c)
    return out


@lru_cache(maxsize=None)
def load_xlsx_texts() -> Dict[str, Dict[int, str]]:
    """{variante: {text_index: texto}} desde supp texts_wave2.xlsx (Sheet1)."""
    import openpyxl

    wb = openpyxl.load_workbook(XLSX_W2, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = list(ws.iter_rows(min_row=1, max_row=20, max_col=13, values_only=True))
    wb.close()

    texts: Dict[str, Dict[int, str]] = {}
    for row in rows:
        label = row[0]
        if label is None:
            continue
        label = str(label).strip()
        lang = XLSX_ROW_TO_LANG.get(label)
        if lang is None:
            continue
        texts[lang] = {}
        for idx, cell in enumerate(row[1 : N_TEXTS + 1], start=1):
            t = str(cell) if cell else ""
            t = t.replace("\\n", "\n").replace("\u200b", "").replace("\n", " ")
            t = re.sub(r"\s+", " ", t).strip()
            texts[lang][idx] = t
    missing = set(LANG_CONFIG) - set(texts)
    if missing:
        raise RuntimeError(f"Variantes ausentes en supp texts_wave2.xlsx: {missing}")
    return texts


def map_itemid_to_text(lang: str) -> Dict[int, int]:
    """itemid → índice de texto (1..12) por alineación difflib contra el xlsx."""
    tokens_by_item = load_r_tokens(lang)
    ref_texts = load_xlsx_texts()[lang]
    ref_seqs = {idx: normalize_seq(re.findall(r"\S+", txt)) for idx, txt in ref_texts.items()}
    mapping: Dict[int, int] = {}
    for itemid, entries in tokens_by_item.items():
        seq = normalize_seq([e["word"] for e in entries])
        best_idx, best_ratio = None, -1.0
        for idx, rseq in ref_seqs.items():
            ratio = difflib.SequenceMatcher(None, seq, rseq, autojunk=False).ratio()
            if ratio > best_ratio:
                best_ratio, best_idx = ratio, idx
        if best_idx is None or best_ratio < 0.5:
            raise RuntimeError(f"{lang}: itemid {itemid} sin texto (best={best_ratio:.2f})")
        if best_idx in mapping.values():
            raise RuntimeError(f"{lang}: texto {best_idx} mapeado dos veces (itemid {itemid})")
        mapping[itemid] = best_idx
    if sorted(mapping.values()) != list(range(1, N_TEXTS + 1)):
        raise RuntimeError(f"{lang}: mapeo incompleto: {sorted(mapping.values())}")
    return mapping


# ---------------------------------------------------------------------------
# POS / frecuencia / sílabas (despacho local sobre la config wave 2)
# ---------------------------------------------------------------------------

def tag_token(lang: str, token: str) -> Tuple[str, str]:
    cfg = LANG_CONFIG[lang]
    if cfg["engine"] == "spacy":
        return tag_token_spacy(cfg["model"], token)
    return tag_token_stanza(cfg["model"], token)


@lru_cache(maxsize=200000)
def zipf_w2(word_lower: str, wf_lang: Optional[str]) -> Optional[float]:
    if wf_lang is None:
        return None  # señal de frecuencia interna (sr, eu)
    return zipf_wordfreq(word_lower, wf_lang)


def count_syllables_pyphen(word: str, dic: str) -> int:
    import pyphen

    d = pyphen.Pyphen(lang=dic)
    parts = [p for p in d.inserted(word.lower()).replace("-", " ").split() if p]
    return max(1, len(parts))


def count_syllables_cluster(word: str, vowels: str) -> int:
    n, prev = 0, False
    for ch in word.lower():
        if ch in vowels:
            if not prev:
                n += 1
            prev = True
        else:
            prev = False
    return max(1, n)


def count_syllables_count(word: str, vowels: str) -> int:
    return max(1, sum(1 for ch in word.lower() if ch in vowels))


_DEV_CONSONANTS = set(
    chr(c) for c in list(range(0x0915, 0x093A)) + [0x0958, 0x0959, 0x095A, 0x095B, 0x095C, 0x095D, 0x095E, 0x095F, 0x0979, 0x097A, 0x097B, 0x097C, 0x097E, 0x097F]
)  # क..ह + consonantes con nukta
_DEV_IND_VOWELS = set(chr(c) for c in range(0x0905, 0x0915))  # अ..ए+ओ etc.
_DEV_HALANT = "\u094D"


def count_syllables_akshara(word: str) -> int:
    """
    Devanágari: número de AKSHARAS (unidad ortográfica: consonante(+halant+...)
    con su matra/inherent-a, o vocal independiente). Consonante inicia akshara
    nuevo salvo que el carácter anterior sea halant (forma clúster con el
    anterior). Aproximación documentada: sobre-cuenta codas finales (कार = 2).
    """
    n = 0
    prev_halant = False
    for ch in word:
        if "\u0900" <= ch <= "\u097F":
            if ch in _DEV_IND_VOWELS:
                n += 1
                prev_halant = False
            elif ch in _DEV_CONSONANTS:
                if not prev_halant:
                    n += 1
                prev_halant = False
            elif ch == _DEV_HALANT:
                prev_halant = True
            # matras y otros signos: núcleo del akshara en curso, sin efecto
        else:
            prev_halant = False
    return max(1, n)


def count_syllables(word_clean: str, lang: str) -> int:
    cfg = LANG_CONFIG[lang]
    if not word_clean:
        return 0
    method = cfg["syl"]
    if method == "cmudict":
        from classify_words_l1_all_languages import count_syllables_en

        return count_syllables_en(word_clean)
    if method == "pyphen":
        try:
            return count_syllables_pyphen(word_clean, cfg["pyphen"])
        except Exception:
            return count_syllables_cluster(word_clean, "aeiouáéíóúæøåäöü")
    if method == "cluster":
        return count_syllables_cluster(word_clean, cfg["vowels"])
    if method == "count":
        return count_syllables_count(word_clean, cfg["vowels"])
    if method == "akshara":
        return count_syllables_akshara(word_clean)
    raise ValueError(method)


def classify_length(clean_word: str, lang: str) -> Tuple[int, int, str]:
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
# Pipeline por variante
# ---------------------------------------------------------------------------

def classify_variant(lang: str) -> Tuple[pd.DataFrame, Dict[str, object]]:
    cfg = LANG_CONFIG[lang]
    logger.info("=== %s (%s): clasificación wave 2 ===", lang, cfg["nombre"])
    mapping = map_itemid_to_text(lang)
    pd.DataFrame(
        {"itemid": sorted(mapping), "text_index": [mapping[i] for i in sorted(mapping)]}
    ).to_csv(TOKENS_DIR / f"itemid_to_text_{lang}.csv", index=False, encoding="utf-8")
    tokens_by_item = load_r_tokens(lang)
    supp_texts = load_xlsx_texts()[lang]

    texts: Dict[int, List[Dict]] = {}
    for itemid, textidx in mapping.items():
        entries = sorted(tokens_by_item[itemid], key=lambda e: e["wordnum"])
        texts[textidx] = [
            {"sentnum": e["sentnum"], "wordnum": e["wordnum"], "word": e["word"],
             "word_clean": clean_token_w2(e["word"])}
            for e in entries
        ]

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

                if is_punct_only(clean_word):
                    records.append({
                        "lang": lang, "trialid": textidx, "text_name": TEXT_NAMES[textidx],
                        "sentnum": entry["sentnum"], "ianum": entry["wordnum"], "wordnum": entry["wordnum"],
                        "word": raw_word, "word_clean": "",
                        "largo_caracteres": 0, "num_silabas": 0, "categoria_largo": "Puntuación",
                        "freq_corpus": None, "zipf_freq": None, "categoria_frecuencia": None,
                        "categoria_gramatical": "Puntuación", "tipo_lexico": None,
                        "subtipo_gramatical": "Puntuación", "pos_tag_universal": "PUNCT",
                        "pos_tag_native": "PUNCT",
                        "predictibilidad_prob": None, "surprisal_bits": None,
                        "categoria_predictibilidad": None,
                    })
                    continue

                len_chars, syls, len_cat = classify_length(clean_word, lang)
                zipf_val = zipf_w2(lower, cfg["wf"])
                if zipf_val is None:
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

                records.append({
                    "lang": lang, "trialid": textidx, "text_name": TEXT_NAMES[textidx],
                    "sentnum": entry["sentnum"], "ianum": entry["wordnum"], "wordnum": entry["wordnum"],
                    "word": raw_word, "word_clean": clean_word,
                    "largo_caracteres": len_chars, "num_silabas": syls, "categoria_largo": len_cat,
                    "freq_corpus": int(corpus_counter.get(lower, 0)), "zipf_freq": zipf_val,
                    "categoria_frecuencia": freq_cat,
                    "categoria_gramatical": pos_cat, "tipo_lexico": tipo_lex,
                    "subtipo_gramatical": subtipo, "pos_tag_universal": pos_univ,
                    "pos_tag_native": fine,
                    "predictibilidad_prob": round(prob, 6), "surprisal_bits": round(surprisal, 3),
                    "categoria_predictibilidad": pred_cat,
                })
    df = pd.DataFrame(records)

    human = pd.read_csv(HUMAN_CSV, encoding="utf-8")
    human = human[human["lang"] == RAW_LANG[lang]].copy()
    human["trialid"] = human["itemid"].map(mapping)
    human = human[["trialid", "wordnum", "human_skip_rate", "human_firstpass_dur_ms",
                   "human_total_dur_ms", "n_human_observations"]]
    human["human_skip_rate"] = human["human_skip_rate"].round(4)
    human["human_firstpass_dur_ms"] = human["human_firstpass_dur_ms"].round(1)
    human["human_total_dur_ms"] = human["human_total_dur_ms"].round(1)
    df = df.merge(human, on=["trialid", "wordnum"], how="left", validate="one_to_one")

    n_et = sum(len(v) for v in texts.values())
    pairs = set(zip(df["trialid"], df["wordnum"]))
    missing_ia = sum(
        1 for t in range(1, N_TEXTS + 1) for e in texts[t] if (t, e["wordnum"]) not in pairs
    )
    concord = []
    for textidx in range(1, N_TEXTS + 1):
        seq_r = " ".join(normalize_seq([e["word"] for e in texts[textidx]]))
        seq_c = " ".join(normalize_seq(re.findall(r"\S+", supp_texts[textidx])))
        concord.append(difflib.SequenceMatcher(None, seq_r, seq_c, autojunk=False).ratio())
    checks = {
        "lang": lang, "nombre": cfg["nombre"], "tokens_et": n_et,
        "tokens_benchmark": len(df), "tokens_match": n_et == len(df),
        "ias_sin_categoria": missing_ia,
        "ias_sin_medidas_humanas": int(df["n_human_observations"].isna().sum()),
        "zipf_rango": [float(df["zipf_freq"].min()), float(df["zipf_freq"].max())],
        "concordancia_media": round(sum(concord) / len(concord) * 100, 1),
        "concordancia_min": round(min(concord) * 100, 1),
        "item_map": {str(k): v for k, v in sorted(mapping.items())},
    }
    return df, checks


# ---------------------------------------------------------------------------
# Reporte combinado
# ---------------------------------------------------------------------------

def language_section(df: pd.DataFrame, checks: Dict[str, object]) -> List[str]:
    cfg = LANG_CONFIG[checks["lang"]]
    dfValid = df[df["n_human_observations"].notna()]
    lines = [
        f"## {cfg['nombre']} (`{checks['lang']}`)",
        "",
        f"- **Tokens (IAs):** {len(df):,} | **Textos:** {df['trialid'].nunique()} | "
        f"**Oraciones:** {df.groupby(['trialid', 'sentnum']).ngroups} | "
        f"**Vocabulario único:** {df['word_clean'].nunique():,}",
        f"- **Verificación:** tokens ET {checks['tokens_et']} vs benchmark {checks['tokens_benchmark']} → "
        f"{'OK' if checks['tokens_match'] else 'MISMATCH'}; "
        f"IAs sin categoría: {checks['ias_sin_categoria']}; "
        f"IAs sin medidas humanas: {checks['ias_sin_medidas_humanas']}",
        f"- **Rango Zipf:** {checks['zipf_rango'][0]:.2f} – {checks['zipf_rango'][1]:.2f} | "
        f"**Concordancia con supp texts_wave2.xlsx:** media {checks['concordancia_media']}%, "
        f"mínima {checks['concordancia_min']}%",
    ]
    if checks["lang"] in ("ic", "en_uk"):
        lines.append(
            f"- **Mapeo itemid → texto:** {checks['item_map']} (rotación de orden de presentación entre sujetos)"
        )
    if checks["lang"] in ("ba", "se"):
        lines.append(
            "- **Nota de frecuencia:** sin lista en `wordfreq`; Zipf derivado de la frecuencia interna del corpus (aproximación grosera)."
        )
    if checks["lang"].startswith("hi"):
        lines.append(
            "- **Nota de sílabas:** número de aksharas devanágari (aproximación documentada; sobre-cuenta codas finales)."
        )
    lines.append("")

    lines += ["### Categorías gramaticales", "",
              "| Categoría | Tokens | % | Ejemplos |", "| :--- | :--- | :--- | :--- |"]
    for cat, c in df["categoria_gramatical"].value_counts().items():
        pct = round(c / len(df) * 100, 1)
        ex = ", ".join(df[df["categoria_gramatical"] == cat]["word_clean"].dropna().drop_duplicates().head(5).tolist())
        lines.append(f"| {cat} | {c} | {pct}% | {ex} |")

    lines += ["", "### Funcional vs. contenido", "", "| Tipo léxico | Tokens | % |", "| :--- | :--- | :--- |"]
    for lex, c in df["tipo_lexico"].value_counts().items():
        lines.append(f"| {lex} | {c} | {round(c / len(df) * 100, 1)}% |")

    lines += ["", "### Longitud y frecuencia", "", "| Categoría | Tokens | % |", "| :--- | :--- | :--- |"]
    for col in ("categoria_largo", "categoria_frecuencia"):
        for cat, c in df[col].value_counts().items():
            lines.append(f"| {cat} | {c} | {round(c / len(df) * 100, 1)}% |")
        lines.append("")

    lines += [
        "### Medidas humanas observadas (eye-tracking L1 wave 2)",
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
        "# Clasificación Integral de Palabras — Variantes L1 wave 2 de MECO (14 grupos separados)",
        "",
        "Extensión de `CLASIFICACION_PALABRAS_L1.md` a las variantes wave 2 (cada variante es un",
        "GRUPO SEPARADO, sin fusiones): `ba` Vasco, `bp` Portugués-Brasil, `da` Danés, `en_uk`",
        "Inglés UK, `ge_po` Alemán Potsdam, `ge_zu` Alemán Zúrich, `hi_iiith`/`hi_iitk` Hindi,",
        "`ic` Islandés, `ru_mo` Ruso wave 2, `se` Serbio, `sp_ch` Español Chile, `no_w2` Noruego",
        "wave 2, `tr_w2` Turco wave 2. Chino (`ch_s`/`ch_t`) ya estaba clasificado",
        "(`words_classified_chinese_*_wave2.csv`).",
        "",
        "Metodología idéntica a la wave 1; decisiones específicas:",
        "",
        "1. Tokens = IAs reales del `joint_data_trimmed_wave2_version2.1.rda`; textos de",
        "   `supp texts_wave2.xlsx`. **`itemid` mapeado a índice de texto** (ic y en_uk rotan).",
        "2. POS: spaCy (pt, da, de, en, es, ru, nb) y Stanza (eu, hi, is, sr, tr).",
        "3. Frecuencia Zipf de `wordfreq`; **sr y eu sin lista → Zipf interno del corpus**",
        "   (documentado). Sílabas: pyphen (pt_BR, da, is, sr, eu), CMUdict (en_uk), vocales",
        "   (ru, tr), clústeres vocálicos (de, es, nb), aksharas devanágari (hi).",
        "4. Medidas humanas del mismo .rda fusionadas por (variante, texto, wordnum).",
        "",
        "## Resumen de verificación de calidad",
        "",
        "| Variante | Código | Tokens ET | Benchmark | Match | IAs sin human | Zipf mín–máx | Concordancia xlsx (%) |",
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
        df = pd.read_csv(BENCH_DIR / f"words_classified_{checks['lang']}_w2l1.csv")
        lines += language_section(df, checks)
    lines.append("Fin del reporte.")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Reporte guardado en %s", REPORT_PATH)


# ---------------------------------------------------------------------------

def main() -> None:
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    if not any(TOKENS_DIR.glob("*_item*.csv")) or not HUMAN_CSV.exists():
        export_r_tokens()

    all_checks = []
    for lang in LANG_CONFIG:
        df, checks = classify_variant(lang)
        csv_path = BENCH_DIR / f"words_classified_{lang}_w2l1.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("%s: dataset guardado en %s (%d registros)", lang, csv_path, len(df))

        # Archivos de tokens por texto (patrón tidNN)
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
    print("CLASIFICACIÓN L1 WAVE 2 (14 VARIANTES) COMPLETADA")
    for c in all_checks:
        print(
            f"  {c['lang']}: ET={c['tokens_et']} bench={c['tokens_benchmark']} "
            f"match={c['tokens_match']} humanNA={c['ias_sin_medidas_humanas']} "
            f"concord={c['concordancia_media']}%"
        )
    print("=" * 72)


if __name__ == "__main__":
    main()
