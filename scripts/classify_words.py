#!/usr/bin/env python3
"""
scripts/classify_words.py

Clasificación de palabras del corpus MECO L2 según:
1. Frecuencia: frecuencia absoluta fastText, escala Zipf y categoría de frecuencia.
2. Largo: longitud en caracteres, conteo de sílabas y categoría de longitud.
3. Predictibilidad: modelo de lenguaje n-gram interpolado (probabilidad condicional
   y surprisal de Shannon en bits), categorización, y métricas empíricas de salteo
   humano (skip rate) de los lectores de MECO.
4. Tipo de palabra (Part-of-Speech): Artículos, determinantes, adjetivos, sustantivos,
   verbos, adverbios, pronombres, preposiciones, conjunciones, numerales y partículas;
   además de la distinción funcional vs. léxica (palabras de contenido vs. funcionales).

IMPORTANTE: Este script genera archivos nuevos y NO sobreescribe ningún archivo original.
"""

from __future__ import annotations

import argparse
from collections import Counter
import logging
import math
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple

import pandas as pd
import nltk
from nltk import pos_tag
from nltk.corpus import brown, cmudict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("classify_words")

# Conjuntos lingüísticos auxiliares para inglés
ARTICLES = {"the", "a", "an"}
SUBORDINATING_CONJUNCTIONS = {
    "that", "while", "because", "although", "since", "if", "unless",
    "though", "whereas", "as", "after", "before", "once", "until"
}
AUXILIARY_AND_MODAL_VERBS = {
    "be", "am", "is", "are", "was", "were", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did",
    "can", "could", "may", "might", "must", "shall", "should", "will", "would"
}


def ensure_nltk_resources():
    """Descarga los recursos de NLTK necesarios si no están instalados."""
    resources = [
        ("punkt", "tokenizers/punkt"),
        ("punkt_tab", "tokenizers/punkt_tab"),
        ("averaged_perceptron_tagger_eng", "taggers/averaged_perceptron_tagger_eng"),
        ("universal_tagset", "taggers/universal_tagset"),
        ("brown", "corpora/brown"),
        ("cmudict", "corpora/cmudict")
    ]
    for res_name, res_path in resources:
        try:
            nltk.data.find(res_path)
        except LookupError:
            logger.info(f"Descargando recurso NLTK: {res_name}...")
            nltk.download(res_name, quiet=True)


def get_syllable_counter():
    """Inicializa y retorna una función para contar sílabas usando CMUDict con fallback heurístico."""
    try:
        cmu = cmudict.dict()
    except Exception as e:
        logger.warning(f"No se pudo cargar CMUDict ({e}), usando fallback heurístico.")
        cmu = {}

    def count_syllables(word: str) -> int:
        clean = re.sub(r"[^a-zA-Z]", "", str(word)).lower()
        if not clean:
            return 1
        if clean in cmu:
            # Seleccionar la primera transcripción fonética y contar dígitos de acento primario/secundario
            return [len(list(y for y in x if y[-1].isdigit())) for x in cmu[clean]][0]
        # Fallback heurístico fonético para palabras fuera de vocabulario
        clean = re.sub(r"(?:[^laeiouy]|ed|es|e)$", "", clean)
        clean = re.sub(r"^y", "", clean)
        syls = len(re.findall(r"[aeiouy]{1,2}", clean))
        return max(1, syls)

    return count_syllables


def classify_part_of_speech(
    word_raw: str,
    word_clean: str,
    penn_tag: str,
    univ_tag: str
) -> Tuple[str, str, str]:
    """
    Clasifica una palabra en categorías gramaticales en español y distingue contenido vs función.

    Retorna:
        categoria_gramatical: 'Artículo', 'Determinante', 'Sustantivo', 'Verbo', etc.
        tipo_lexico: 'Palabra de Contenido' o 'Palabra Funcional'
        subtipo_especifico: Descripción refinada (ej. 'Nombre propio', 'Verbo auxiliar', etc.)
    """
    wc = str(word_clean).lower().strip()

    # 1. Artículos
    if wc in ARTICLES:
        return "Artículo", "Palabra Funcional", "Artículo definido/indefinido"

    # 2. Pronombres existenciales y especiales
    if penn_tag == "EX":
        return "Pronombre", "Palabra Funcional", "Pronombre existencial ('there')"

    # 3. Determinantes
    if penn_tag == "DT" or (univ_tag == "DET" and wc not in ARTICLES):
        return "Determinante", "Palabra Funcional", "Determinante demostrativo/cuantificador"

    # 4. Conjunciones (coordinantes y subordinantes)
    if penn_tag == "CC":
        return "Conjunción", "Palabra Funcional", "Conjunción coordinante"
    if penn_tag == "IN" and wc in SUBORDINATING_CONJUNCTIONS:
        return "Conjunción", "Palabra Funcional", "Conjunción subordinante"

    # 5. Pronombres
    if penn_tag in ("PRP", "PRP$", "WP", "WP$", "WDT") or univ_tag == "PRON":
        return "Pronombre", "Palabra Funcional", "Pronombre personal/posesivo/relativo"

    # 6. Sustantivos
    if penn_tag.startswith("NN") or univ_tag == "NOUN":
        sub = "Sustantivo propio" if penn_tag in ("NNP", "NNPS") else "Sustantivo común"
        return "Sustantivo", "Palabra de Contenido", sub

    # 7. Verbos
    if penn_tag.startswith("VB") or penn_tag == "MD" or univ_tag == "VERB":
        if wc in AUXILIARY_AND_MODAL_VERBS or penn_tag == "MD":
            return "Verbo", "Palabra Funcional", "Verbo auxiliar/modal"
        return "Verbo", "Palabra de Contenido", "Verbo léxico/principal"

    # 8. Adjetivos
    if penn_tag.startswith("JJ") or univ_tag == "ADJ":
        return "Adjetivo", "Palabra de Contenido", "Adjetivo calificativo"

    # 9. Adverbios
    if penn_tag.startswith("RB") or penn_tag in ("WRB", "LS") or univ_tag == "ADV":
        return "Adverbio", "Palabra de Contenido", "Adverbio"

    # 10. Preposiciones
    if penn_tag == "IN" or univ_tag == "ADP" or wc == "de":
        return "Preposición", "Palabra Funcional", "Preposición"

    # 11. Numerales
    if penn_tag == "CD" or univ_tag == "NUM":
        return "Numeral", "Palabra Funcional", "Numeral cardinal"

    # 12. Partículas
    if penn_tag in ("TO", "RP", "POS") or univ_tag == "PRT":
        return "Partícula", "Palabra Funcional", "Partícula gramatical / Marcador"

    # 13. Casos especiales / Otro
    if wc in ("multi-", "anti-", "co-"):
        return "Adjetivo", "Palabra de Contenido", "Prefijo adjetival"

    return "Otro", "Palabra Funcional", "Otro elemento léxico"


def classify_length_category(length_chars: int) -> str:
    """Clasificación categórica de la longitud de la palabra."""
    if length_chars <= 4:
        return "Corta (1-4 letras)"
    elif length_chars <= 8:
        return "Media (5-8 letras)"
    else:
        return "Larga (9+ letras)"


def classify_frequency_category(zipf_subtlex: float | None, zipf_fasttext: float) -> str:
    """
    Clasificación categórica de la frecuencia en escala logarítmica de Zipf.
    Se prioriza la norma SUBTLEX-US (Lg10CD, Van Heuven et al. 2014) con la que fue
    calibrada esta escala; se usa la frecuencia fastText como fallback:
    - Zipf >= 6.0: Muy Alta Frecuencia (> 1.000 por millón)
    - 5.0 <= Zipf < 6.0: Alta Frecuencia (100 - 1.000 por millón)
    - 4.0 <= Zipf < 5.0: Media Frecuencia (10 - 100 por millón)
    - Zipf < 4.0: Baja Frecuencia (< 10 por millón, palabras de baja familiaridad)
    """
    z = zipf_subtlex if zipf_subtlex is not None and not pd.isna(zipf_subtlex) else zipf_fasttext
    if z >= 6.0:
        return "Muy Alta Frecuencia"
    elif z >= 5.0:
        return "Alta Frecuencia"
    elif z >= 4.0:
        return "Media Frecuencia"
    else:
        return "Baja Frecuencia"


def classify_predictability_category(prob: float, surprisal_bits: float) -> str:
    """
    Clasificación de predictibilidad basada en probabilidad de transición y surprisal:
    - Alta: prob >= 0.08 o surprisal < 3.65 bits (muy predecible en contexto)
    - Media: 0.005 <= prob < 0.08 o 3.65 <= surprisal < 7.64 bits
    - Baja: prob < 0.005 o surprisal >= 7.64 bits (inesperada / alta sorpresa)
    """
    if prob >= 0.08 or surprisal_bits < 3.65:
        return "Alta Predictibilidad"
    elif prob >= 0.005 or surprisal_bits < 7.64:
        return "Media Predictibilidad"
    else:
        return "Baja Predictibilidad"


def build_interpolated_language_model(
    meco_sents: List[List[str]],
    lambda_uni: float = 0.1,
    lambda_bi: float = 0.3,
    lambda_tri: float = 0.6
):
    """
    Entrena un modelo de lenguaje de trigramas interpolado (Jelinek-Mercer)
    combinando el corpus Brown (1.1M palabras de inglés estándar) y los textos MECO.
    """
    logger.info("Entrenando modelo de lenguaje probabilístico n-gram...")
    uni_counts = Counter()
    bi_counts = Counter()
    tri_counts = Counter()
    context_bi = Counter()
    context_tri = Counter()

    # Combinar oraciones de Brown + MECO
    all_sents = [list(map(str.lower, s)) for s in brown.sents()] + meco_sents * 2

    for s in all_sents:
        padded = ["<s>", "<s>"] + s + ["</s>"]
        for i in range(2, len(padded)):
            w = padded[i]
            w_prev1 = padded[i - 1]
            w_prev2 = padded[i - 2]

            uni_counts[w] += 1
            bi_counts[(w_prev1, w)] += 1
            context_bi[w_prev1] += 1
            tri_counts[(w_prev2, w_prev1, w)] += 1
            context_tri[(w_prev2, w_prev1)] += 1

    total_words = sum(uni_counts.values())

    def get_predictability(w: str, prev1: str, prev2: str) -> Tuple[float, float]:
        """Calcula probabilidad condicionada P(w | prev1, prev2) y surprisal en bits."""
        p_uni = uni_counts[w] / total_words if total_words > 0 else 1e-6
        p_bi = bi_counts[(prev1, w)] / context_bi[prev1] if context_bi[prev1] > 0 else p_uni
        p_tri = tri_counts[(prev2, prev1, w)] / context_tri[(prev2, prev1)] if context_tri[(prev2, prev1)] > 0 else p_bi

        p_interp = lambda_tri * p_tri + lambda_bi * p_bi + lambda_uni * p_uni
        p_interp = max(1e-9, min(1.0, p_interp))
        surprisal = -math.log2(p_interp)
        return p_interp, surprisal

    return get_predictability


def load_subtlex(repo_root: Path) -> pd.DataFrame:
    """
    Carga el léxico SUBTLEX-US (Van Heuven et al. 2014) y retorna una tabla
    indexada por palabra en minúsculas con sus normas psicométricas de frecuencia:
    - subtlex_zipf: escala Zipf oficial = log10(frecuencia por billón + 1), calculada
      sobre SUBTLWF (frecuencia por millón). NOTA: la columna `Lg10CD` de este archivo
      es log10(CDcount) y NO corresponde a la escala Zipf, por lo que no se usa.
    - subtlex_freq / subtlex_wf_pm / subtlex_cd_pct: normas auxiliares
      (frecuencia absoluta, frecuencia por millón y % de contextos distintos).
    """
    subtlex_path = repo_root / "data" / "benchmark" / "subtlex_us.csv"
    if not subtlex_path.exists():
        logger.warning("SUBTLEX-US no encontrado, se usará solo la frecuencia fastText.")
        return pd.DataFrame()

    subtlex = pd.read_csv(subtlex_path, usecols=["Word", "FREQcount", "SUBTLWF", "SUBTLCD"])
    subtlex["word_clean"] = subtlex["Word"].astype(str).str.lower().str.strip()
    subtlex["subtlex_zipf"] = (subtlex["SUBTLWF"] * 1000 + 1).apply(math.log10).round(4)
    subtlex = subtlex.drop_duplicates(subset="word_clean").drop(columns=["Word"])
    subtlex.rename(columns={
        "FREQcount": "subtlex_freq",
        "SUBTLWF": "subtlex_wf_pm",
        "SUBTLCD": "subtlex_cd_pct",
    }, inplace=True)
    logger.info(f"Normas SUBTLEX-US cargadas: {len(subtlex):,} entradas léxicas únicas.")
    return subtlex


def load_human_eye_tracking_data(repo_root: Path) -> pd.DataFrame:
    """
    Carga y agrega las métricas empíricas de lectura humana de MECO L2 Wave 1 y Wave 2:
    - human_skip_rate: tasa promedio de salteo visual de la palabra (0.0 a 1.0)
    - human_firstpass_dur_ms: duración promedio de la primera fijación / gaze duration (ms)
    - human_total_dur_ms: tiempo total de fijación sobre la palabra (ms)
    """
    eye_paths = [
        repo_root / "data" / "MECO-L2_version-2.2" / "wave-1" / "primary-data" / "eye-tracking" / "joint_data_l2_trimmed_version2.2.csv",
        repo_root / "data" / "MECO-L2_version-2.2" / "wave-2" / "primary-data" / "eye-tracking" / "joint_data_trimmed_L2_wave2_version2.2.csv",
    ]

    dfs = []
    cols_to_use = ["trialid", "wordnum", "skip", "dur", "firstrun.dur"]

    for p in eye_paths:
        if p.exists():
            logger.info(f"Cargando datos de eye-tracking desde: {p.name}...")
            try:
                sub_df = pd.read_csv(p, usecols=cols_to_use)
                dfs.append(sub_df)
            except Exception as e:
                logger.warning(f"No se pudo cargar {p}: {e}")

    if not dfs:
        logger.warning("No se encontraron archivos de eye-tracking para enriquecimiento humano.")
        return pd.DataFrame()

    full_eye = pd.concat(dfs, ignore_index=True)
    logger.info(f"Agregando {len(full_eye):,} observaciones de fijaciones humanas...")

    agg = full_eye.groupby(["trialid", "wordnum"]).agg(
        human_skip_rate=("skip", "mean"),
        human_firstpass_dur_ms=("firstrun.dur", "mean"),
        human_total_dur_ms=("dur", "mean"),
        n_human_observations=("skip", "count")
    ).reset_index()

    return agg


def classify_words_pipeline(
    benchmark_csv_path: Path,
    repo_root: Path,
    include_eye_tracking: bool = True
) -> pd.DataFrame:
    """Pipeline completo de clasificación de palabras."""
    ensure_nltk_resources()
    count_syllables = get_syllable_counter()

    logger.info(f"Cargando dataset base de palabras: {benchmark_csv_path}...")
    df_words = pd.read_csv(benchmark_csv_path)
    df_words["ia_clean"] = df_words["ia_clean"].astype(str).str.lower().str.strip()
    logger.info(f"Total palabras a clasificar: {len(df_words)}")

    # 0. Integrar normas SUBTLEX-US (frecuencia psicométrica por palabra)
    subtlex = load_subtlex(repo_root)
    if not subtlex.empty:
        df_words = pd.merge(df_words, subtlex, left_on="ia_clean", right_on="word_clean", how="left").drop(columns=["word_clean"])

    # 1. Preparar oraciones de MECO para POS tagging y Modelo de Lenguaje
    meco_sents = []
    sentence_map = {}
    for (trialid, sentnum), group in df_words.groupby(["trialid", "sentnum"], sort=False):
        s_words = [str(w).lower() for w in group["ia_clean"]]
        meco_sents.append(s_words)
        sentence_map[(trialid, sentnum)] = s_words

    # 2. Entrenar Modelo de Lenguaje para Predictibilidad
    predict_fn = build_interpolated_language_model(meco_sents)

    # 3. Iterar por oración y clasificar POS, Largo, Frecuencia y Predictibilidad
    logger.info("Ejecutando clasificación gramatical (POS), longitud, frecuencia y predictibilidad...")
    classified_records = []

    for (trialid, sentnum), group in df_words.groupby(["trialid", "sentnum"], sort=False):
        # Limpiar tokens para etiquetador manteniendo mayúsculas contextuales
        cleaned_tokens = [re.sub(r"^[^\w]+|[^\w]+$", "", str(w)) for w in group["ia"]]
        cleaned_tokens = [t if t else str(w) for t, w in zip(cleaned_tokens, group["ia_clean"])]

        tags_univ = pos_tag(cleaned_tokens, tagset="universal")
        tags_penn = pos_tag(cleaned_tokens)

        sent_words_clean = [str(w).lower() for w in group["ia_clean"]]

        for idx, ((_, row), (_, u_tag), (_, p_tag)) in enumerate(zip(group.iterrows(), tags_univ, tags_penn)):
            ia = str(row["ia"])
            ia_clean = str(row["ia_clean"])
            length_chars = int(row["length"])
            freq = int(row["freq"])
            zipf_freq = float(row["zipf_freq"])
            zipf_subtlex = row.get("subtlex_zipf")
            if subtlex.empty:
                zipf_subtlex = None

            # A. Largo
            num_syls = count_syllables(ia_clean)
            length_cat = classify_length_category(length_chars)

            # B. Frecuencia (prioriza SUBTLEX-US; fallback fastText)
            freq_cat = classify_frequency_category(zipf_subtlex, zipf_freq)

            # C. Tipo de Palabra (POS)
            pos_cat_es, tipo_lexico, subtipo = classify_part_of_speech(ia, ia_clean, p_tag, u_tag)

            # D. Predictibilidad y Surprisal
            curr_w = sent_words_clean[idx]
            prev1 = sent_words_clean[idx - 1] if idx >= 1 else "<s>"
            prev2 = sent_words_clean[idx - 2] if idx >= 2 else "<s>"
            p_cond, surprisal = predict_fn(curr_w, prev1, prev2)
            pred_cat = classify_predictability_category(p_cond, surprisal)

            classified_records.append({
                # Identificadores
                "trialid": int(row["trialid"]),
                "sentnum": int(row["sentnum"]),
                "ianum": int(row["ianum"]),
                "word": ia,
                "word_clean": ia_clean,

                # 1. Largo
                "largo_caracteres": length_chars,
                "num_silabas": num_syls,
                "categoria_largo": length_cat,

                # 2. Frecuencia
                "freq_fasttext": freq,
                "zipf_freq_fasttext": round(zipf_freq, 4),
                "subtlex_zipf": round(float(zipf_subtlex), 4) if zipf_subtlex is not None and not pd.isna(zipf_subtlex) else None,
                "subtlex_freq": int(row.get("subtlex_freq")) if not subtlex.empty and "subtlex_freq" in row and not pd.isna(row.get("subtlex_freq")) else None,
                "subtlex_wf_pm": round(float(row.get("subtlex_wf_pm")), 4) if not subtlex.empty and "subtlex_wf_pm" in row and not pd.isna(row.get("subtlex_wf_pm")) else None,
                "subtlex_cd_pct": round(float(row.get("subtlex_cd_pct")), 2) if not subtlex.empty and "subtlex_cd_pct" in row and not pd.isna(row.get("subtlex_cd_pct")) else None,
                "categoria_frecuencia": freq_cat,

                # 3. Tipo de Palabra (POS)
                "categoria_gramatical": pos_cat_es,
                "tipo_lexico": tipo_lexico,
                "subtipo_gramatical": subtipo,
                "pos_tag_universal": u_tag,
                "pos_tag_penn": p_tag,

                # 4. Predictibilidad
                "predictibilidad_prob": round(p_cond, 6),
                "surprisal_bits": round(surprisal, 3),
                "categoria_predictibilidad": pred_cat,
            })

    result_df = pd.DataFrame(classified_records)

    # 5. Enriquecimiento opcional con datos reales de eye-tracking (human skip rate & duration)
    if include_eye_tracking:
        eye_df = load_human_eye_tracking_data(repo_root)
        if not eye_df.empty:
            logger.info("Integrando métricas empíricas de fijación y salteo humano...")
            result_df = pd.merge(
                result_df,
                eye_df,
                left_on=["trialid", "ianum"],
                right_on=["trialid", "wordnum"],
                how="left"
            )
            # Limpiar columnas redundantes de join
            if "wordnum" in result_df.columns:
                result_df.drop(columns=["wordnum"], inplace=True)
            result_df["human_skip_rate"] = result_df["human_skip_rate"].round(4)
            result_df["human_firstpass_dur_ms"] = result_df["human_firstpass_dur_ms"].round(2)
            result_df["human_total_dur_ms"] = result_df["human_total_dur_ms"].round(2)

    logger.info("Clasificación de palabras completada exitosamente.")
    return result_df


def generate_markdown_report(df: pd.DataFrame, output_path: Path):
    """Genera un reporte analítico detallado en Markdown."""
    total_words = len(df)
    unique_words = df["word_clean"].nunique()

    # Frecuencias por categoría gramatical
    pos_counts = df["categoria_gramatical"].value_counts()
    pos_pcts = (pos_counts / total_words * 100).round(2)

    # Tipos léxicos
    lex_counts = df["tipo_lexico"].value_counts()
    lex_pcts = (lex_counts / total_words * 100).round(2)

    # Frecuencia
    freq_counts = df["categoria_frecuencia"].value_counts()
    freq_pcts = (freq_counts / total_words * 100).round(2)

    # Largo
    len_counts = df["categoria_largo"].value_counts()
    len_pcts = (len_counts / total_words * 100).round(2)

    # Predictibilidad
    pred_counts = df["categoria_predictibilidad"].value_counts()
    pred_pcts = (pred_counts / total_words * 100).round(2)

    lines = [
        "# Clasificación Integral de Palabras (Corpus MECO L2)",
        "",
        "> **Nota:** Este documento fue generado automáticamente por `scripts/classify_words.py`. "
        "No sobreescribe ningún archivo original del repositorio.",
        "",
        "## 1. Resumen General del Corpus",
        "",
        f"- **Total de ocurrencias (tokens):** {total_words:,}",
        f"- **Palabras únicas (vocabulario lemático):** {unique_words:,}",
        f"- **Cantidad de textos (trials):** {df['trialid'].nunique()}",
        f"- **Cantidad de oraciones:** {df.groupby(['trialid', 'sentnum']).ngroups}",
        "",
        "---",
        "",
        "## 2. Agrupación por Tipo de Palabra (Categorías Gramaticales)",
        "",
        "| Categoría Gramatical | Frecuencia Absoluta | Porcentaje (%) | Ejemplos Representativos |",
        "| :--- | :--- | :--- | :--- |"
    ]

    for cat in pos_counts.index:
        count = pos_counts[cat]
        pct = pos_pcts[cat]
        examples = df[df["categoria_gramatical"] == cat]["word_clean"].drop_duplicates().head(5).tolist()
        ex_str = ", ".join(examples)
        lines.append(f"| **{cat}** | {count} | {pct}% | *{ex_str}* |")

    lines.extend([
        "",
        "### Distribución Funcional vs. Léxica",
        "",
        "| Tipo Léxico | Frecuencia | Porcentaje (%) | Definición en Lectura Ocular |",
        "| :--- | :--- | :--- | :--- |"
    ])

    for lex in lex_counts.index:
        c = lex_counts[lex]
        p = lex_pcts[lex]
        if "Contenido" in lex:
            desc = "Portan la carga semántica principal (sustantivos, adjetivos, verbos léxicos). Mayor duración de fijación."
        else:
            desc = "Estructura sintáctica (artículos, preposiciones, pronombres). Alta tasa de salteo visual (*skipping*)."
        lines.append(f"| **{lex}** | {c} | {p}% | {desc} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Clasificación por Frecuencia de la Palabra",
        "",
        "Calculada sobre el corpus fastText y la escala psicométrica de Zipf (Van Heuven et al., 2014):",
        "",
        "| Categoría de Frecuencia | Rango Zipf | Cantidad de Palabras | Porcentaje (%) |",
        "| :--- | :--- | :--- | :--- |"
    ])

    for fc in ["Muy Alta Frecuencia", "Alta Frecuencia", "Media Frecuencia", "Baja Frecuencia"]:
        if fc in freq_counts:
            c = freq_counts[fc]
            p = freq_pcts[fc]
            rango = ">= 6.0" if "Muy" in fc else ("5.0 - 5.99" if "Alta" in fc else ("4.0 - 4.99" if "Media" in fc else "< 4.0"))
            lines.append(f"| **{fc}** | {rango} | {c} | {p}% |")

    lines.extend([
        "",
        "### Cobertura y validación de normas SUBTLEX-US",
        "",
    ])
    if "subtlex_zipf" in df.columns:
        covered = df["subtlex_zipf"].notna().sum()
        lines.extend([
            f"- **Palabras cubiertas por SUBTLEX:** {covered:,} de {total_words:,} ({covered / total_words * 100:.1f}%)",
            f"- **Categoría de frecuencia basada en:** SUBTLEX-US (`subtlex_zipf` = log10 frec./billón + 1) con fallback a fastText.",
            f"- **Zipf SUBTLEX promedio:** {df['subtlex_zipf'].mean():.2f} | **Zipf fastText promedio:** {df['zipf_freq_fasttext'].mean():.2f}",
            f"- **Delta medio (fastText − SUBTLEX):** {(df['zipf_freq_fasttext'] - df['subtlex_zipf']).mean():.2f}",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## 4. Clasificación por Largo de la Palabra",
        "",
        "| Categoría de Longitud | Caracteres | Cantidad de Palabras | Porcentaje (%) | Promedio Sílabas |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ])

    for lc in ["Corta (1-4 letras)", "Media (5-8 letras)", "Larga (9+ letras)"]:
        if lc in len_counts:
            c = len_counts[lc]
            p = len_pcts[lc]
            avg_syl = df[df["categoria_largo"] == lc]["num_silabas"].mean()
            chars = "1 a 4" if "Corta" in lc else ("5 a 8" if "Media" in lc else ">= 9")
            lines.append(f"| **{lc}** | {chars} | {c} | {p}% | {avg_syl:.2f} |")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Predictibilidad de la Palabra y Surprisal",
        "",
        "La predictibilidad fue modelada mediante probabilidad condicional interpolada de n-gramas ($P(w_i \\mid w_{i-1}, w_{i-2})$) "
        "y Surprisal de Shannon ($S(w_i) = -\\log_2 P$).",
        "",
        "| Nivel de Predictibilidad | Cantidad de Palabras | Porcentaje (%) | Surprisal Promedio (bits) |",
        "| :--- | :--- | :--- | :--- |"
    ])

    for pr in ["Alta Predictibilidad", "Media Predictibilidad", "Baja Predictibilidad"]:
        if pr in pred_counts:
            c = pred_counts[pr]
            p = pred_pcts[pr]
            avg_surp = df[df["categoria_predictibilidad"] == pr]["surprisal_bits"].mean()
            lines.append(f"| **{pr}** | {c} | {p}% | {avg_surp:.2f} bits |")

    if "human_skip_rate" in df.columns:
        lines.extend([
            "",
            "### Validación Empírica con Eye-Tracking Humano (MECO L2)",
            "",
            "En eye-tracking, las palabras altamente predecibles y de alta frecuencia presentan mayores tasas de salteo (*skipping rate*):",
            "",
            "| Categoría Predictibilidad | Skip Rate Humano Medio | Gaze Duration Media (ms) | Tiempo Total Medio (ms) |",
            "| :--- | :--- | :--- | :--- |"
        ])
        for pr in ["Alta Predictibilidad", "Media Predictibilidad", "Baja Predictibilidad"]:
            if pr in df["categoria_predictibilidad"].values:
                sub = df[df["categoria_predictibilidad"] == pr]
                sk = sub["human_skip_rate"].mean() * 100
                gz = sub["human_firstpass_dur_ms"].mean()
                tt = sub["human_total_dur_ms"].mean()
                lines.append(f"| **{pr}** | {sk:.1f}% | {gz:.1f} ms | {tt:.1f} ms |")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Diccionario de Datos del Archivo Generado (`words_classified.csv`)",
        "",
        "| Campo | Tipo | Descripción |",
        "| :--- | :--- | :--- |",
        "| `trialid` | Entero | Identificador del texto presentado [1, 12] |",
        "| `sentnum` | Entero | Número de la oración dentro del texto |",
        "| `ianum` | Entero | Número secuencial de la palabra dentro del texto |",
        "| `word` | Texto | Palabra tal como fue presentada (con puntuación) |",
        "| `word_clean` | Texto | Palabra limpia en minúsculas sin signos de puntuación |",
        "| `largo_caracteres` | Entero | Longitud de la palabra en caracteres/letras |",
        "| `num_silabas` | Entero | Cantidad de sílabas fonéticas (CMUDict + reglas) |",
        "| `categoria_largo` | Texto | Categoría de longitud: Corta, Media o Larga |",
        "| `freq_fasttext` | Entero | Frecuencia absoluta en el corpus fastText |",
        "| `zipf_freq_fasttext` | Decimal | Frecuencia Zipf según fastText (fallback) |",
        "| `subtlex_zipf` | Decimal | Frecuencia Zipf psicométrica SUBTLEX-US (log10 frec. por billón + 1, Van Heuven et al. 2014) |",
        "| `subtlex_freq` | Entero | Frecuencia absoluta SUBTLEX-US corpus (FREQcount) |",
        "| `subtlex_wf_pm` | Decimal | Frecuencia por millón SUBTLEX-US (SUBTLWF) |",
        "| `subtlex_cd_pct` | Decimal | Porcentaje de contextos distintos SUBTLEX-US (SUBTLCD) |",
        "| `categoria_frecuencia` | Texto | Muy Alta, Alta, Media o Baja Frecuencia (basada en SUBTLEX) |",
        "| `categoria_gramatical` | Texto | Artículo, Sustantivo, Verbo, Adjetivo, Adverbio, etc. |",
        "| `tipo_lexico` | Texto | Palabra de Contenido vs. Palabra Funcional |",
        "| `subtipo_gramatical` | Texto | Detalle gramatical (ej. Propio, Auxiliar, etc.) |",
        "| `pos_tag_universal` | Texto | Tag Universal (NOUN, VERB, ADJ, ADV, DET, etc.) |",
        "| `pos_tag_penn` | Texto | Tag Penn Treebank (NN, NNP, VBD, VBZ, JJ, RB, etc.) |",
        "| `predictibilidad_prob` | Decimal | Probabilidad condicional n-gram $P(w_i \\mid \\text{contexto})$ |",
        "| `surprisal_bits` | Decimal | Información de Shannon en bits ($-\\log_2 P$) |",
        "| `categoria_predictibilidad` | Texto | Alta, Media o Baja Predictibilidad |",
        "| `human_skip_rate` | Decimal | Tasa real de salteo de los participantes MECO |",
        "| `human_firstpass_dur_ms` | Decimal | Duración de primera pasada humana en milisegundos |",
        "| `human_total_dur_ms` | Decimal | Tiempo de lectura total humano en milisegundos |",
        "",
        "Fin del reporte."
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    logger.info(f"Reporte guardado en: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Clasificación de palabras del corpus MECO L2 (Frecuencia, Largo, Predictibilidad y POS)."
    )
    parser.add_argument(
        "--benchmark-csv",
        type=str,
        default="data/benchmark/L2 word length and frequency.csv",
        help="Ruta al archivo base de palabras (L2 word length and frequency.csv)."
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="data/benchmark/words_classified.csv",
        help="Ruta de salida para el nuevo archivo CSV de palabras clasificadas."
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="data/CLASIFICACION_PALABRAS.md",
        help="Ruta de salida para el reporte analítico en Markdown."
    )
    parser.add_argument(
        "--no-eye-data",
        action="store_true",
        help="Omitir el enriquecimiento con datos empíricos de eye-tracking."
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    bench_path = repo_root / args.benchmark_csv
    out_csv_path = repo_root / args.output_csv
    out_report_path = repo_root / args.output_report

    if not bench_path.exists():
        logger.error(f"Archivo de palabras no encontrado: {bench_path}")
        sys.exit(1)

    df_classified = classify_words_pipeline(
        benchmark_csv_path=bench_path,
        repo_root=repo_root,
        include_eye_tracking=not args.no_eye_data
    )

    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_classified.to_csv(out_csv_path, index=False, encoding="utf-8")
    logger.info(f"Dataset clasificado guardado en: {out_csv_path} ({len(df_classified)} filas)")

    out_report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(df_classified, out_report_path)

    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print(f"Archivo clasificado: {out_csv_path}")
    print(f"Reporte analítico:   {out_report_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
