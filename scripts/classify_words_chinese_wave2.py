#!/usr/bin/env python3
"""
scripts/classify_words_chinese_wave2.py

Clasificación de palabras para los textos Wave 2 de MECO-L1 en Chino Mandarín
(Simplificado ch_s y Tradicional ch_t), siguiendo la metodología de
`classify_words_chinese.py` (wave 1) y el formato del benchmark L2
(`data/benchmark/words_classified_chinese_*.csv`).

Diferencias clave respecto a la wave 1:
1. LOS TEXTOS NO ESTÁN HARDCODEADOS: se cargan dinámicamente mediante
   `wave2_chinese_texts.py` (12 textos nuevos: Janus, Shaka, Doping, Thylacine,
   World Environment Day, Monocle, Wine Tasting, Orange Juice, Beekeeping,
   National Flag, IUCN, Vehicle Registration Plate).
2. SEGMENTACIÓN FIJA (ver decisión documentada en wave2_chinese_texts.py):
   no se re-segmenta con jieba; se usan los tokens reales (interest areas) del
   experimento, clave (trialid, wordnum), lo que permite:
   - Variantes simplificada Y tradicional (el xlsx no tiene límites de palabra
     en la fila tradicional).
   - Fusionar medidas oculares humanas (skip rate, gaze duration, total
     reading time) por palabra, igual que el benchmark L2.
3. Jieba se usa SOLO para etiquetado morfosintáctico (POS) y para el léxico de
   frecuencias (SUBTLEX-CH compatible), no para segmentar.
4. Entidades nombradas de la wave 2 añadidas al diccionario de jieba para que
   el POS de los tokens multi-carácter sea estable.

Salidas:
- data/benchmark/words_classified_chinese_simplified_wave2.csv
- data/benchmark/words_classified_chinese_traditional_wave2.csv
- data/CLASIFICACION_PALABRAS_CHINO_SIMPLIFICADO_WAVE2.md
- data/CLASIFICACION_PALABRAS_CHINO_TRADICIONAL_WAVE2.md
"""

from __future__ import annotations

import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jieba
import jieba.posseg as pseg

# Snapshot del léxico ORIGINAL de jieba (antes de inyectar entidades): las
# frecuencias se consultan contra este léxico para que las entidades añadidas
# con freq=20000 no contaminen la estimación de Zipf.
_ORIG_FREQ = None
_ORIG_TOTAL = None
_lemmas_initialized = False
from classify_words_chinese import (
    build_chinese_ngram_model,
    classify_chinese_pos,
    classify_frequency_category,
    classify_length,
    classify_predictability_category,
)
from wave2_chinese_texts import (
    N_TEXTS,
    TEXT_NAMES,
    VARIANT_BY_LANG,
    clean_token,
    flatten_text,
    load_et_tokens,
    load_xlsx_star_tokens,
    load_xlsx_texts,
    sentences_from_tokens,
)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("classify_chinese_wave2")

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = REPO_ROOT / "data" / "benchmark"
TOKENS_DIR = BENCH_DIR / "wave2_chinese_tokens"
OBS_CSV = TOKENS_DIR / "joint_ch_wave2_obs.csv"

# ---------------------------------------------------------------------------
# Entidades nombradas específicas de los textos Wave 2 (para POS de jieba)
# ---------------------------------------------------------------------------

MECO_WAVE2_ENTITIES_SIMP = [
    ("雅努斯", "nr"),
    ("古罗马", "ns"),
    ("夏威夷", "ns"),
    ("袋狼", "nz"),
    ("塔斯马尼亚虎", "nz"),
    ("塔斯马尼亚狼", "nz"),
    ("塔斯马尼亚", "ns"),
    ("世界环境日", "nz"),
    ("联合国", "nt"),
    ("国际自然保护联盟", "nt"),
    ("国际奥林匹克委员会", "nt"),
    ("单片眼镜", "n"),
    ("维生素C", "n"),
    ("新几内亚", "ns"),
    ("澳大利亚", "ns"),
    ("瑞士", "ns"),
    ("梵蒂冈", "ns"),
    ("印度", "ns"),
    ("法国", "ns"),
    ("埃及", "ns"),
    ("大祭司", "n"),
]

MECO_WAVE2_ENTITIES_TRAD = [
    ("雅努斯", "nr"),
    ("古羅馬", "ns"),
    ("夏威夷", "ns"),
    ("袋狼", "nz"),
    ("塔斯馬尼亞虎", "nz"),
    ("塔斯馬尼亞狼", "nz"),
    ("塔斯馬尼亞", "ns"),
    ("世界環境日", "nz"),
    ("聯合國", "nt"),
    ("國際自然保護聯盟", "nt"),
    ("國際奧林匹克委員會", "nt"),
    ("單片眼鏡", "n"),
    ("維生素C", "n"),
    ("新幾內亞", "ns"),
    ("澳大利亞", "ns"),
    ("瑞士", "ns"),
    ("梵蒂岡", "ns"),
    ("印度", "ns"),
    ("法國", "ns"),
    ("埃及", "ns"),
    ("大祭司", "n"),
]

_JIEBA_WAVE2_READY = False


def setup_jieba_wave2():
    """Inicializa jieba una sola vez y registra las entidades de la wave 2."""
    global _JIEBA_WAVE2_READY, _ORIG_FREQ, _ORIG_TOTAL
    if _JIEBA_WAVE2_READY:
        return
    jieba.initialize()
    _ORIG_FREQ = dict(jieba.dt.FREQ)
    _ORIG_TOTAL = jieba.dt.total
    for word, tag in MECO_WAVE2_ENTITIES_SIMP + MECO_WAVE2_ENTITIES_TRAD:
        jieba.add_word(word, freq=20000, tag=tag)
    _JIEBA_WAVE2_READY = True


def get_wave2_word_frequency(clean_word: str) -> Tuple[int, float]:
    """
    Frecuencia absoluta y Zipf usando SOLO el léxico original de jieba
    (compatible SUBTLEX-CH), con el mismo fallback por caracteres que wave 1.
    """
    import re as _re
    from opencc import OpenCC

    tw2s = OpenCC("tw2sp")
    s2tw = OpenCC("s2twp")
    total = _ORIG_TOTAL if _ORIG_TOTAL and _ORIG_TOTAL > 0 else 60101967
    clean = _re.sub(r"[^\w\u4e00-\u9fff]", "", clean_word)
    if not clean:
        return 0, 1.0

    count = _ORIG_FREQ.get(clean, 0)
    if count == 0:
        count = _ORIG_FREQ.get(tw2s.convert(clean), 0)
    if count == 0:
        count = _ORIG_FREQ.get(s2tw.convert(clean), 0)
    if count == 0:
        char_freqs = [f for c, f in ((c, _ORIG_FREQ.get(c)) for c in clean if "\u4e00" <= c <= "\u9fff") if f]
        if char_freqs:
            count = max(1, int(min(char_freqs) * 0.05))
        else:
            count = 10

    per_million = max(0.01, (count / total) * 1e6)
    zipf_val = math.log10(per_million) + 3.0
    zipf_val = round(max(1.0, min(7.6, zipf_val)), 4)
    return count, zipf_val


def tag_fixed_token(clean_word: str) -> str:
    """
    Etiqueta POS de un token FIJO (ya segmentado por el experimento).
    Se usa pseg sobre el token limpio; si jieba lo sub-divide, se devuelve la
    etiqueta del segmento más largo (cabeza sintáctica del IA).
    """
    clean_word = clean_word.strip()
    if not clean_word:
        return "x"
    segs = list(pseg.cut(clean_word))
    if not segs:
        return "x"
    if len(segs) == 1:
        return segs[0].flag
    head = max(segs, key=lambda s: len(s.word))
    return head.flag


# ---------------------------------------------------------------------------
# Medidas oculares humanas (merge estilo benchmark L2)
# ---------------------------------------------------------------------------

def load_human_measures(variant: str) -> pd.DataFrame:
    """
    Agrega, por (lang, trialid, wordnum), las medidas de eye-tracking humanas:
      - human_skip_rate: proporción de lectores que saltearon el IA (skip==1)
      - human_firstpass_dur_ms: gaze duration media en primera pasada
        (firstrun.dur, solo IAs fijadas en primera pasada)
      - human_total_dur_ms: tiempo total de lectura medio (dur, solo IAs fijadas)
      - n_human_observations: número de lectores con el IA presentado
    """
    lang = "ch_s" if variant == "simplified" else "ch_t"
    if not OBS_CSV.exists():
        raise FileNotFoundError(
            f"No existe {OBS_CSV}. Exportar primero las observaciones con R "
            "(ver data/benchmark/wave2_chinese_tokens/)."
        )
    obs = pd.read_csv(OBS_CSV, encoding="utf-8", low_memory=False)
    if "firstrun.dur" in obs.columns:
        obs = obs.rename(columns={"firstrun.dur": "firstrun_dur"})
    obs = obs[obs["lang"] == lang].copy()

    grouped = obs.groupby(["trialid", "wordnum"], sort=True)
    human = grouped.agg(
        n_human_observations=("skip", "size"),
        human_skip_rate=("skip", "mean"),
        human_firstpass_dur_ms=("firstrun_dur", lambda s: s[s.notna()].mean()),
        human_total_dur_ms=("dur", lambda s: s[s.notna()].mean()),
    ).reset_index()
    human["human_skip_rate"] = human["human_skip_rate"].round(4)
    human["human_firstpass_dur_ms"] = human["human_firstpass_dur_ms"].round(1)
    human["human_total_dur_ms"] = human["human_total_dur_ms"].round(1)
    return human


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def classify_wave2_corpus(variant: str) -> pd.DataFrame:
    """Clasifica los 12 textos wave 2 de la variante dada y fusiona measures humanas."""
    logger.info("Iniciando clasificación wave 2 para %s", variant)
    setup_jieba_wave2()
    all_tokens = load_et_tokens(variant)

    # 1. Modelo n-gram entrenado sobre TODO el corpus wave 2 de la variante
    corpus_tokens: List[List[str]] = []
    for tid in range(1, N_TEXTS + 1):
        for sent in sentences_from_tokens(all_tokens[tid]):
            corpus_tokens.append([e["word_clean"] for e in sent if e["word_clean"]])
    predict_fn = build_chinese_ngram_model(corpus_tokens)

    # 2. Clasificar token a token (ialigned con el experimento)
    records = []
    for tid in range(1, N_TEXTS + 1):
        for sent in sentences_from_tokens(all_tokens[tid]):
            sent_clean = [e["word_clean"] for e in sent]
            for i, entry in enumerate(sent):
                raw_word = entry["word"]
                clean_word = entry["word_clean"]
                if not clean_word:
                    # IA puramente puntuación (p. ej. "。" en ch_s tid7): se
                    # conserva con métricas léxicas vacías para mantener
                    # cobertura 1:1 con los interest areas del experimento.
                    records.append(
                        {
                            "trialid": tid,
                            "text_name": TEXT_NAMES[tid],
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
                            "subtipo_gramatical": None,
                            "pos_tag_universal": "PUNCT",
                            "pos_tag_chinese": "x",
                            "predictibilidad_prob": None,
                            "surprisal_bits": None,
                            "categoria_predictibilidad": None,
                        }
                    )
                    continue

                len_chars, syls, len_cat = classify_length(clean_word)
                freq_count, zipf_val = get_wave2_word_frequency(clean_word)
                freq_cat = classify_frequency_category(zipf_val)

                tag = tag_fixed_token(clean_word)
                pos_cat, tipo_lex, subtipo, pos_univ = classify_chinese_pos(clean_word, tag)

                prev1 = sent_clean[i - 1] if i >= 1 else "<s>"
                prev2 = sent_clean[i - 2] if i >= 2 else "<s>"
                prob, surprisal = predict_fn(clean_word, prev1, prev2)
                pred_cat = classify_predictability_category(prob, surprisal)

                records.append(
                    {
                        "trialid": tid,
                        "text_name": TEXT_NAMES[tid],
                        "sentnum": entry["sentnum"],
                        "ianum": entry["wordnum"],
                        "wordnum": entry["wordnum"],
                        "word": raw_word,
                        "word_clean": clean_word,
                        "largo_caracteres": len_chars,
                        "num_silabas": syls,
                        "categoria_largo": len_cat,
                        "freq_corpus": freq_count,
                        "zipf_freq": zipf_val,
                        "categoria_frecuencia": freq_cat,
                        "categoria_gramatical": pos_cat,
                        "tipo_lexico": tipo_lex,
                        "subtipo_gramatical": subtipo,
                        "pos_tag_universal": pos_univ,
                        "pos_tag_chinese": tag,
                        "predictibilidad_prob": round(prob, 6),
                        "surprisal_bits": round(surprisal, 3),
                        "categoria_predictibilidad": pred_cat,
                    }
                )
    df = pd.DataFrame(records)

    # 3. Fusionar medidas humanas
    human = load_human_measures(variant)
    df = df.merge(human, on=["trialid", "wordnum"], how="left", validate="one_to_one")
    if df["n_human_observations"].isna().any():
        missing = df[df["n_human_observations"].isna()][["trialid", "wordnum"]]
        logger.warning("IAs sin observaciones humanas: %s", missing.to_dict("records")[:10])

    logger.info("Clasificación completada para %s: %d palabras.", variant, len(df))
    return df


# ---------------------------------------------------------------------------
# Validación / QA
# ---------------------------------------------------------------------------

def star_concordance_stats() -> pd.DataFrame:
    """
    Control de concordancia: proporción de los límites '*' del xlsx (solo
    simplificado) que son también límites de jieba sobre el texto plano.
    Sirve como sanity-check del léxico de jieba para este corpus.
    """
    setup_jieba_wave2()
    star = load_xlsx_star_tokens()
    rows = []
    for tid in range(1, N_TEXTS + 1):
        toks = [t for t in star[tid] if t.strip()]
        if not toks:
            continue
        n_match = 0
        for tok in toks:
            clean = clean_token(tok)[1]
            if not clean:
                continue
            cut = [w for w, _ in pseg.cut(clean)]
            n_match += int(len(cut) == 1)
        rows.append({"trialid": tid, "star_tokens": len(toks), "jieba_single_token": n_match})
    df = pd.DataFrame(rows)
    if len(df):
        df["pct_agreement"] = (df["jieba_single_token"] / df["star_tokens"] * 100).round(1)
    return df


def run_validation(df: pd.DataFrame, variant: str) -> Dict[str, object]:
    """Verificaciones de QA sobre el benchmark generado."""
    tokens = load_et_tokens(variant)
    n_et = sum(len(v) for v in tokens.values())
    n_bench = len(df)
    # cobertura de IAs
    pairs = set(zip(df["trialid"], df["wordnum"]))
    missing = [
        (tid, e["wordnum"]) for tid in range(1, N_TEXTS + 1) for e in tokens[tid] if (tid, e["wordnum"]) not in pairs
    ]
    human_missing = int(df["n_human_observations"].isna().sum())
    zipf_min, zipf_max = df["zipf_freq"].min(), df["zipf_freq"].max()
    checks = {
        "variant": variant,
        "tokens_et": n_et,
        "tokens_benchmark": n_bench,
        "tokens_match": n_et == n_bench,
        "ias_sin_categoria": len(missing),
        "ias_sin_medidas_humanas": human_missing,
        "zipf_rango": [zipf_min, zipf_max],
    }
    return checks


# ---------------------------------------------------------------------------
# Reporte Markdown
# ---------------------------------------------------------------------------

def generate_report(df: pd.DataFrame, checks: Dict[str, object], concord: pd.DataFrame, variant: str, out_path: Path):
    title = "Chino Mandarín Simplificado (简体中文 / ch_s)" if variant == "simplified" else "Chino Mandarín Tradicional (繁體中文 / ch_t)"
    dfValid = df[df["n_human_observations"].notna()]
    lines = [
        f"# Clasificación Integral de Palabras Wave 2 — {title}",
        "",
        "adaptación wave 2 de la metodología del corpus MECO; tokens = interest areas reales del experimento",
        "(ver `scripts/wave2_chinese_texts.py` para la decisión documentada).",
        "",
        "## 1. Resumen del Corpus",
        "",
        f"- **Tokens (IAs):** {len(df):,} | **Textos:** {df['trialid'].nunique()} | **Oraciones:** {df.groupby(['trialid','sentnum']).ngroups}",
        f"- **Vocabulario único:** {df['word_clean'].nunique():,}",
        f"- **Caracteres chinos totales:** {df['largo_caracteres'].sum():,}",
        f"- **Lectores:** {int(dfValid['n_human_observations'].max()) if len(dfValid) else 'NA'}",
        "",
        "## 2. Verificaciones de calidad",
        "",
        f"- Tokens ET vs benchmark: {checks['tokens_et']} vs {checks['tokens_benchmark']} → {'OK' if checks['tokens_match'] else 'MISMATCH'}",
        f"- IAs sin categoría / sin medidas humanas: {checks['ias_sin_categoria']} / {checks['ias_sin_medidas_humanas']}",
        f"- Rango Zipf: {checks['zipf_rango'][0]:.2f} – {checks['zipf_rango'][1]:.2f}",
        "",
    ]
    if len(concord):
        lines += [
            "### Concordancia de límites '*' (xlsx simplificado) con jieba",
            "",
            "| Texto | Tokens '*' | Jieba no sub-divide | Concordancia (%) |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for _, r in concord.iterrows():
            lines.append(f"| {int(r['trialid'])} | {int(r['star_tokens'])} | {int(r['jieba_single_token'])} | {r['pct_agreement']} |")
        lines.append("")

    pos_counts = df["categoria_gramatical"].value_counts()
    lex_counts = df["tipo_lexico"].value_counts()
    len_counts = df["categoria_largo"].value_counts()

    lines += [
        "## 3. Categorías gramaticales",
        "",
        "| Categoría | Tokens | % | Ejemplos |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for cat, c in pos_counts.items():
        pct = round(c / len(df) * 100, 1)
        ex = ", ".join(df[df["categoria_gramatical"] == cat]["word_clean"].drop_duplicates().head(5).tolist())
        lines.append(f"| {cat} | {c} | {pct}% | {ex} |")

    lines += [
        "",
        "### Funcional vs. contenido",
        "",
        "| Tipo léxico | Tokens | % |",
        "| :--- | :--- | :--- |",
    ]
    for lex, c in lex_counts.items():
        lines.append(f"| {lex} | {c} | {round(c / len(df) * 100, 1)}% |")

    lines += [
        "",
        "## 4. Longitud (en caracteres = sílabas)",
        "",
        "| Categoría | Tokens | % |",
        "| :--- | :--- | :--- |",
    ]
    for lc, c in len_counts.items():
        lines.append(f"| {lc} | {c} | {round(c / len(df) * 100, 1)}% |")

    # humano vs esperado
    lines += [
        "",
        "## 5. Medidas humanas observadas (eye-tracking wave 2)",
        "",
        "| Medida | Media | Mediana |",
        "| :--- | :--- | :--- |",
        f"| Skip rate | {dfValid['human_skip_rate'].mean():.3f} | {dfValid['human_skip_rate'].median():.3f} |",
        f"| Gaze duration primera pasada (ms) | {dfValid['human_firstpass_dur_ms'].mean():.1f} | {dfValid['human_firstpass_dur_ms'].median():.1f} |",
        f"| Tiempo total de lectura (ms) | {dfValid['human_total_dur_ms'].mean():.1f} | {dfValid['human_total_dur_ms'].median():.1f} |",
        "",
        "Correlación (Pearson) entre predictibilidad/surprisal y medidas humanas:",
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

    lines += [
        "",
        "## 6. Diccionario de datos del CSV",
        "",
        "`trialid` (1–12), `text_name`, `sentnum`, `ianum` = `wordnum` (IA real), `word`, `word_clean`,",
        "`largo_caracteres` (= sílabas), `categoria_largo`, `freq_corpus`, `zipf_freq`, `categoria_frecuencia`,",
        "`categoria_gramatical`, `tipo_lexico`, `subtipo_gramatical`, `pos_tag_universal`, `pos_tag_chinese`,",
        "`predictibilidad_prob`, `surprisal_bits`, `categoria_predictibilidad`,",
        "`human_skip_rate`, `human_firstpass_dur_ms`, `human_total_dur_ms`, `n_human_observations`.",
        "",
        "Fin del reporte.",
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    logger.info("Reporte guardado en %s", out_path)


# ---------------------------------------------------------------------------

def main():
    variants = ["simplified", "traditional"]
    report_names = {
        "simplified": "CLASIFICACION_PALABRAS_CHINO_SIMPLIFICADO_WAVE2.md",
        "traditional": "CLASIFICACION_PALABRAS_CHINO_TRADICIONAL_WAVE2.md",
    }
    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    all_checks = []
    for var in variants:
        df = classify_wave2_corpus(var)
        csv_path = BENCH_DIR / f"words_classified_chinese_{var}_wave2.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info("Dataset guardado en %s (%d registros)", csv_path, len(df))

        checks = run_validation(df, var)
        all_checks.append(checks)
        concord = star_concordance_stats() if var == "simplified" else pd.DataFrame()
        report_path = REPO_ROOT / "data" / report_names[var]
        generate_report(df, checks, concord, var, report_path)

    print("\n" + "=" * 60)
    print("CLASIFICACIÓN WAVE 2 CHINO COMPLETADA")
    for c in all_checks:
        print(f"  {c['variant']}: ET={c['tokens_et']} bench={c['tokens_benchmark']} match={c['tokens_match']} humanNA={c['ias_sin_medidas_humanas']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
