"""
scripts/wave2_chinese_texts.py

Cargador de textos Wave 2 del corpus MECO-L1 para las variantes de Chino
Mandarín Simplificado (ch_s) y Tradicional (ch_t).

Fuentes de datos:
1. "supp texts_wave2.xlsx" (data/MECO-L1_version2.1/wave-2/auxiliary files/
   reading task materials/): textos presentados en la tarea de lectura.
   - Hoja Sheet1, filas 3 (simplificado) y 4 (tradicional), columnas B..M = trials 1..12.
   - La fila de chino simplificado contiene marcas '*' delimitando palabras tal
     como fueron presentadas a los participantes.
   - La fila de chino tradicional NO contiene delimitadores de palabra (texto continuo).
   - Contiene artefactos que deben limpiarse: saltos de línea literales "\\n",
     espacios de ancho cero (U+200B), espacios sueltos y un token de cierre "。\\n".

2. "joint_data_trimmed_wave2_version2.1.rda" (primary-data/eye tracking data):
   columna `word` por (lang, trialid, wordnum) — la segmentación REAL que vieron
   los participantes, con puntuación pegada al token (p. ej. "中，", "。").

DECISIÓN DE FUENTE DE TOKENS (documentada):
Se utiliza la columna `word` del archivo .rda como fuente autoritativa de
segmentación para AMBAS variantes, porque:
  (a) Es la única segmentación existente para chino tradicional (el xlsx no
      tiene marcas de palabra en esa fila).
  (b) Garantiza alineación 1:1 (trialid, wordnum) con las medidas de
      eye-tracking, lo que permite fusionar las métricas humanas
      (skip rate, duraciones de fijación) en el benchmark.
  (c) En simplificado, las marcas '*' del xlsx coinciden con el texto plano del
      .rda (verificado para los 12 textos), pero difieren levemente en la
      adherencia de puntuación (p. ej. tid3: "中" + "，使用" en xlsx vs "中，" +
      "使用" en .rda) y en el conteo de tokens (tid1: 179 vs 180). Usar el .rda
      elimina esa ambigüedad y refleja exactamente los interest areas (IA)
      construidos por los laboratorios.
El xlsx se usa como: (i) referencia de verificación del texto plano, y
(ii) fuente de las marcas '*' para un control de concordancia con jieba.
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

logger = logging.getLogger("wave2_chinese_texts")

REPO_ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-2"
    / "auxiliary files"
    / "reading task materials"
    / "supp texts_wave2.xlsx"
)
RDA_PATH = (
    REPO_ROOT
    / "data"
    / "MECO-L1_version2.1"
    / "wave-2"
    / "primary-data"
    / "eye tracking data"
    / "joint_data_trimmed_wave2_version2.1.rda"
)
TOKENS_DIR = REPO_ROOT / "data" / "benchmark" / "wave2_chinese_tokens"

N_TEXTS = 12

# Nombres de los textos (orden = trialid 1..12, según encabezado del xlsx)
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

LANG_BY_VARIANT = {"simplified": "ch_s", "traditional": "ch_t"}
VARIANT_BY_LANG = {"ch_s": "simplified", "ch_t": "traditional"}


def clean_token(raw: str) -> Tuple[str, str]:
    """
    Limpia un token crudo del .rda y retorna (word_raw, word_clean).

    Limpiezas aplicadas (mínimas, documentadas):
    - Elimina espacios iniciales/finales (p. ej. " 氧气").
    - Elimina saltos de línea internos ("\\n" real) heredados del material fuente.
    - word_clean: elimina TODA puntuación (CJK y latina) dejando solo caracteres,
      dígitos y letras; normaliza dígitos de ancho completo a ASCII.
    """
    w = raw.replace("\n", "").replace("\r", "").strip()
    # Dígitos full-width usados en ch_t tid4 (１９３６) -> ASCII
    w = w.translate(str.maketrans("０１２３４５６７８９ＡＢＣ", "0123456789ABC"))
    clean = re.sub(
        r"[·・，。；：！？、“”‘’《》（）()「」『』…—\.,;:!?\"'\[\]\s]+",
        "",
        w,
    )
    return w, clean


@lru_cache(maxsize=None)
def load_et_tokens(variant: str = "simplified") -> Dict[int, List[Dict]]:
    """
    Carga la segmentación autoritativa (columna `word` del .rda) desde los CSVs
    exportados por R (ver export_et_tokens() más abajo).

    Retorna: {trialid: [{"sentnum": int, "wordnum": int, "word": str, "word_clean": str}, ...]}
    """
    lang = LANG_BY_VARIANT[variant]
    if not TOKENS_DIR.exists() or not any(TOKENS_DIR.glob(f"*_{lang}.csv")):
        export_et_tokens()
    result: Dict[int, List[Dict]] = {}
    for tid in range(1, N_TEXTS + 1):
        csv_path = TOKENS_DIR / f"tid{tid:02d}_{lang}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Falta el archivo de tokens: {csv_path}. Ejecutar export_et_tokens().")
        df = pd.read_csv(csv_path, encoding="utf-8")
        entries = []
        for _, row in df.iterrows():
            w, clean = clean_token(str(row["word"]))
            entries.append(
                {
                    "sentnum": int(row["sentnum"]),
                    "wordnum": int(row["wordnum"]),
                    "word": w,
                    "word_clean": clean,
                }
            )
        result[tid] = entries
    return result


def export_et_tokens() -> None:
    """
    Exporta la secuencia única de palabras (wordnum -> word, sentnum) por
    (trialid, lang) desde el .rda wave 2 usando Rscript. Genera un CSV por
    combinación en data/benchmark/wave2_chinese_tokens/.
    """
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    rscript_code = f"""
e <- new.env()
load({str(RDA_PATH)!r}, envir=e)
d <- e$joint.data
outdir <- {str(TOKENS_DIR)!r}
for (tid in 1:{N_TEXTS}) {{
  for (lg in c("ch_s","ch_t")) {{
    sub <- d[d$lang==lg & d$trialid==tid,]
    wmap <- sub[!duplicated(sub$wordnum),]
    wmap <- wmap[order(wmap$wordnum), c("sentnum","wordnum","word")]
    write.csv(wmap, file.path(outdir, sprintf("tid%02d_%s.csv", tid, lg)),
              row.names=FALSE, fileEncoding="UTF-8")
  }}
}}
cat("exported\\n")
"""
    res = subprocess.run(
        ["Rscript", "-e", rscript_code],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if "exported" not in res.stdout:
        raise RuntimeError(f"Falló la exportación R:\n{res.stdout}\n{res.stderr}")
    logger.info("Tokens ET exportados a %s", TOKENS_DIR)


@lru_cache(maxsize=None)
def load_xlsx_texts() -> Dict[str, Dict[int, str]]:
    """
    Lee los textos crudos del xlsx wave 2 (Sheet1).
    Retorna: {"simplified": {trialid: texto}, "traditional": {trialid: texto}}
    con limpieza de artefactos (\\n, U+200B, espacios redundantes).
    """
    import openpyxl

    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = list(ws.iter_rows(min_row=1, max_row=5, max_col=13, values_only=True))
    wb.close()

    texts: Dict[str, Dict[int, str]] = {"simplified": {}, "traditional": {}}
    for row in rows:
        label = row[0]
        if label is None:
            continue
        label = str(label).strip()
        if label.startswith("Chinese(simplified)"):
            key = "simplified"
        elif label.startswith("Chinese(traditional)"):
            key = "traditional"
        else:
            continue
        for idx, cell in enumerate(row[1:12 + 1], start=1):
            if cell is None:
                continue
            t = str(cell)
            t = t.replace("\\n", "\n")  # saltos literales "\\n" del material
            t = t.replace("\u200b", "")  # zero-width spaces
            t = t.replace("\n", " ")
            t = re.sub(r"\s+", " ", t).strip()
            if key == "simplified":
                t = t.replace("*", "")  # marcas de delimitación de palabra
            texts[key][idx] = t
    return texts


@lru_cache(maxsize=None)
def load_xlsx_star_tokens() -> Dict[int, List[str]]:
    """
    Lee las marcas '*' de la fila de chino simplificado (Sheet1) como tokens
    de referencia. Se usan SOLO para el control de concordancia con jieba.
    Retorna: {trialid: [token, ...]} (tokens con puntuación tal cual).
    """
    import openpyxl

    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    row = None
    for r in ws.iter_rows(min_row=1, max_row=5, max_col=13, values_only=True):
        if r[0] and str(r[0]).strip().startswith("Chinese(simplified)"):
            row = r
            break
    wb.close()
    if row is None:
        raise RuntimeError("No se encontró la fila Chinese(simplified) en el xlsx")

    result: Dict[int, List[str]] = {}
    for idx, cell in enumerate(row[1:12 + 1], start=1):
        if cell is None:
            result[idx] = []
            continue
        t = str(cell).replace("\\n", "\n").replace("\n", " ")
        toks = [tok.strip() for tok in t.split("*") if tok.strip()]
        result[idx] = toks
    return result


def sentences_from_tokens(entries: List[Dict]) -> List[List[Dict]]:
    """
    Agrupa la lista plana de tokens (ordenada por wordnum) en oraciones según
    `sentnum`, preservando el orden y la numeración original.
    """
    by_sent: Dict[int, List[Dict]] = {}
    for e in sorted(entries, key=lambda x: x["wordnum"]):
        by_sent.setdefault(e["sentnum"], []).append(e)
    return [by_sent[sn] for sn in sorted(by_sent)]


def flatten_text(entries: List[Dict]) -> str:
    """Texto plano concatenando tokens (sin espacios, como se presenta en chino)."""
    return "".join(e["word"] for e in sorted(entries, key=lambda x: x["wordnum"]))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    tokens = load_et_tokens("simplified")
    total = sum(len(v) for v in tokens.values())
    print(f"ch_s: {total} tokens en {len(tokens)} textos")
    trad = load_et_tokens("traditional")
    total_t = sum(len(v) for v in trad.values())
    print(f"ch_t: {total_t} tokens en {len(trad)} textos")
    x = load_xlsx_texts()
    for var in ("simplified", "traditional"):
        print(var, "textos xlsx:", sorted(x[var].keys()))
