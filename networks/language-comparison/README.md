# Red de Comparación por Familias Lingüísticas (Language-Comparison Networks)

## Descripción

Construye redes de carga cognitiva (atención por palabra vía dilatación pupilar)
**agrupando participantes por familia lingüística** de su L1, y asocia a cada red
la **comprensión lectora promedio** (`accuracy`) de esa familia al leer textos en
inglés como L2.

La red base (nodos = palabras, aristas = ΔPS entre palabras consecutivas) es la
misma que `networks/cognitive-load/`; la innovación es la capa de **agrupación por
familia** + el **accuracy global por participante** adjunto a cada build.

**Estructura de la red**

- **Nodos:** palabras (identificadas por `wordnum:word`), con métricas de fijación
  y tamaño pupilar (`ps`).
- **Aristas:** transiciones entre palabras, ponderadas por `ΔPS = |PS_w2 − PS_w1|`.
- **Metadatos de familia:** `lang_group`, `languages` (códigos L1 del grupo),
  `n_participants`, y bloque `accuracy` (mean, median, std, min, max, n).

---

## Estado

**Implementada.** Sigue el esquema canónico definido en
[`networks/README.md`](../README.md) usando `cognitive-load/` como referencia.

---

## Estructura del código

```
networks/language-comparison/
├── README.md                 # Este archivo
├── langcomp.py               # Entry point CLI: subcomandos `build`, `stats`, `compare`
├── core/
│   ├── __init__.py           # Re-exporta SOLO la API pública
│   ├── language_groups.py    # Mapeo de códigos L1 → familia lingüística
│   ├── data_io.py            # Carga de fijaciones por grupo + accuracy global
│   ├── network_builder.py    # Construcción de la red (reusa cognitive-load)
│   ├── comparison.py         # Comparación multi-familia + reporte HTML
│   ├── paths.py              # Rutas a CSVs de fijación y comprensión
│   ├── persistence.py        # Serialización + metadata.json con accuracy
│   ├── visualization.py      # Plots base (matplotlib/seaborn)
│   ├── interactive_viz.py    # HTML interactivo (pyvis)
│   └── stats/                # Submódulo de métricas
└── output/                   # Builds generados (gitignored)
```

---

## Hallazgos de datos a considerar en las interpretaciones

> Verificados sobre los CSVs generados con `scripts/convert_rda_to_csv.R`
> (conversión de los `.rda` originales de MECO L2 v2.2).

### 1. `ps` (pupila) — no es uniforme entre waves

| Wave | Filas | Rango `ps` | `ps ≤ 0` | `ps = NA` |
|------|-------|------------|----------|-----------|
| 1 | 1,221,387 | 139 – 7743 | 0 | 0 |
| 2 | 1,448,635 | 166 – 3924 | 0 | 72,364 |

- **`ps` nunca es ≤ 0** en ninguna wave, pero **W2 tiene 72,364 filas con `ps = NA`**.
- **Todas las `ps = NA` de W2 pertenecen a `ch_s` (Chino, Singapur).** El grupo
  `ch_s` **no tiene ningún dato de pupila válido**.
- Implicación: en la red por familias, **`ch_s` no aporta aristas** (ΔPS requiere
  `ps` válido). El pipeline debe tratar `NA` (string de R) como inválido, no solo
  `ps ≤ 0`. Además `ps ≤ 0` sí se filtra por seguridad, aunque hoy no ocurre.
- Nota: las unidades y el rango de `ps` difieren entre waves (139–7743 vs
  166–3924). La normalización z-score por sesión absorbe la línea base, pero la
  comparación **cruda de `mean_ps` entre waves no es válida**.

### 2. IDs de sujeto en W2 — daneses incompletos

- **17 sujetos daneses** aparecen en fijación con `uniform_id = 'NA'` (subids
  tipo `DK_AA_T1`, `DKAAP5L2`, …). Esos participantes **no tienen accuracy** en
  `joint_comp_L2_Wave2_trimmed.csv`.
- **4 daneses más** con `uniform_id` normalizado (`da_1`, `da_2`, `da_6`, `da_9`)
  están en fijación pero **ausentes del archivo de comprensión** → sin accuracy.
- Implicación: al calcular el `accuracy` promedio de la familia **Germanic** en
  W2, el `n` será menor que el de participantes con fijaciones. El `metadata.json`
  distingue `n_participants` (con fijación) de `n_with_accuracy`.
- En W1 el único caso inverso es `du_30` (tiene comprensión pero no fijación);
  se descarta naturalmente al hacer join por `uniform_id`.

### 3. `uniform_id` como clave de join (recomendado)

- `uniform_id` (ej. `du_4`) es la clave estable entre fijación y comprensión.
- `subid` (ej. `DU_4`) en fijación equivale a `subject` en comprensión pero con
  formatos inconsistentes (especialmente en daneses de W2, p.ej. `DK_AA_T1`).
- Regla: usar `uniform_id`; **si es `'NA'`, caer a `subid`** para etiquetar la
  sesión, pero **no intentar el join con comprensión** para esos participantes.

### 4. Lenguas y olas

- **W1 (12):** `du, ee, en, fi, ge, gr, he, it, no, ru, sp, tr`.
- **W2 (16):** `ba, bp, ch_s, ch_t, da, en_uk, ge_po, ge_zu, hi_iiith, hi_iitk,
  ic, no, ru_mo, se, sp_ch, tr`.
- `no` y `tr` aparecen en **ambas** waves (no confundir: son cohortes distintas).
- `ch_s` y `ch_t` son chino simplificado (Singapur) y tradicional (Taiwán);
  solo `ch_t` tiene `ps` válido.

### 5. Comprensión lectora

- `accuracy` global por participante (0–1) en `joint.comp.l2.csv` (W1) y
  `joint_comp_L2_Wave2_trimmed.csv` (W2). Columnas: `subject`, `uniform_id`,
  `lang`, `total_answer`, `correct_answer`, `accuracy`.
- `total_answer` = 24 (12 textos × 2 preguntas); `accuracy = correct_answer / 24`.
- **No usar las columnas `ACCURACY` de los breakdowns** (`joint_l2_acc_*`) para
  el promedio global: están a nivel de texto (0–2) o pregunta (0–1).

---

## Cómo ejecutar

Desde la raíz del repositorio:

```bash
# Construir la red de una familia para un trial y wave específicos
python networks/language-comparison/langcomp.py build --lang-group germanic --trialid 4 --wave 1

# Calcular estadísticas sobre un build (caché; no reconstruye)
python networks/language-comparison/langcomp.py stats \
  --load networks/language-comparison/output/langcomp_trial4_w1_zscore_germanic_langs-du-en-ge-no

# Omitir el HTML interactivo (builds más rápidos)
python networks/language-comparison/langcomp.py build --lang-group romance --trialid 2 --wave 1 --no-interactive
```

### Flags disponibles

| Flag | Descripción | Default |
|------|-------------|---------|
| `--lang-group <grupo>` | Familia lingüística (`germanic`, `romance`, `slavic`, `uralic`, `turkic`, `hellenic`, `semitic`, `sino-tibetan`, `indo-aryan`, `isolate`, `all`). | `germanic` |
| `--trialid <1-12>` | ID del texto a analizar. | `1` |
| `--wave {1,2,both}` | Ola(s) a cargar. | `1` |
| `--normalize {zscore,none}` | Normalización de `ps` por sesión. | `zscore` |
| `--outdir <ruta>` | Carpeta de salida. | `networks/language-comparison/output` |
| `--no-interactive` | Omite la generación de `network_interactive.html` (build). | — |

Los flags compartidos siguen el esquema de `_add_shared_args()` de `cognitive-load`.

### Formato del prefijo de build

`langcomp_trial<T>_w<W>_<normalize>[_nops-<langs sin ps>]_<grupo>[_langs-<códigos>]`

Ejemplos:

- `langcomp_trial4_w1_zscore_germanic_langs-du-en-ge-no`
- `langcomp_trial4_w2_zscore_nops-ch_s_sino-tibetan_langs-ch_t`

---

## Formato de `output/<build>/`

| Archivo | Descripción |
|---------|-------------|
| `nodes.csv` | Palabras con métricas de fijación y pupila. |
| `edges.csv` | Aristas con ΔPS promedio, conteo y tipo. |
| `graph.pkl` | Objeto `networkx.DiGraph` serializado. |
| `network.graphml` | Red en GraphML (Gephi/Cytoscape). |
| `metadata.json` | Parámetros del build + `lang_group`, `languages`, `accuracy`, `n_participants` + hashes de fuentes. |
| `plots/` | Gráficos estáticos (serie temporal PS, heatmap, grafo). |
| `network_interactive.html` | Red interactiva (pyvis). |
| `stats/` | Métricas globales, de nodo, de aristas, cascadas y comunidades (tras `stats`). |

### Ejemplo de `metadata.json`

```json
{
  "prefix": "langcomp_trial4_w1_zscore_germanic_langs-du-en-ge-no",
  "lang_group": "germanic",
  "languages": ["du", "en", "ge", "no"],
  "n_participants": 176,
  "n_with_accuracy": 176,
  "accuracy": {
    "mean": 0.7204,
    "median": 0.75,
    "std": 0.126,
    "min": 0.2917,
    "max": 0.9583,
    "n": 176
  },
  "n_nodes": 142,
  "n_edges": 474,
  "source_files": [{ "path": "...", "sha256": "..." }]
}
```

`output/` está en `.gitignore` (`networks/*/output/`).

---

## Cómo comparar familias

Cada build guarda su `accuracy` y métricas en `metadata.json`. Para comparar
familias sobre el mismo trial/wave, se construyen los builds de las familias
de interés y se leen sus `metadata.json`:

```bash
python networks/language-comparison/langcomp.py build --lang-group germanic --trialid 4 --wave 1
python networks/language-comparison/langcomp.py build --lang-group romance --trialid 4 --wave 1
python networks/language-comparison/langcomp.py build --lang-group slavic  --trialid 4 --wave 1
```

Luego, para ver el accuracy de cada familia:

```bash
python -c "import json,glob; [print(f'{m[\"lang_group\"]}: {m[\"accuracy\"][\"mean\"]} (n={m[\"accuracy\"][\"n\"]})') for m in (json.load(open(p)) for p in glob.glob('networks/language-comparison/output/langcomp_trial4_w1_*/*/metadata.json'))]"
```

Para comparar qué palabras reciben más atención por familia, se cargan los
`nodes.csv` de cada build y se cruzan por `wordnum`/`word`.

---

## Comparación automática: subcomando `compare`

Construye (o reutiliza) una red por familia y genera un **reporte HTML
comparativo** con tabla resumen, plots y una pestaña por familia.

```bash
# Todas las familias presentes en el wave
python networks/language-comparison/langcomp.py compare --trialid 4 --wave 1

# Solo familias específicas
python networks/language-comparison/langcomp.py compare --trialid 4 --wave 2 --families germanic romance slavic

# Forzar reconstrucción de todo (ignora builds existentes)
python networks/language-comparison/langcomp.py compare --trialid 4 --wave 1 --no-reuse
```

### Flags de `compare`

| Flag | Descripción | Default |
|------|-------------|---------|
| `--trialid <1-12>` | ID del texto a analizar. | `1` |
| `--wave {1,2,both}` | Ola(s) a cargar. | `1` |
| `--families <f1> <f2> ...` | Familias a comparar (espacios). | todas las presentes en el wave |
| `--normalize {zscore,none}` | Normalización de `ps`. | `zscore` |
| `--outdir <ruta>` | Carpeta raíz de salida. | `networks/language-comparison/output` |
| `--no-reuse` | Reconstruye todas las familias (ignora builds existentes). | — |
| `--no-interactive` | Omite el HTML interactivo de cada familia. | — |

> **Nota:** las familias sin lenguas en el wave se omiten automáticamente
> (p.ej. `sino-tibetan`, `indo-aryan`, `isolate` no existen en wave 1).

### Salida

```
output/comparison_trial4_w1/
├── comparison_report.html      # Tabla + plots + pestañas por familia (red interactiva + métricas)
├── comparison_summary.csv      # accuracy + métricas por familia
└── plots/
    ├── comparison_accuracy.png     # Barras de accuracy.mean por familia
    └── comparison_attention.png    # Líneas mean_ps_z por wordnum (una por familia)
```

> Abrir `comparison_report.html` desde su carpeta (`output/comparison_trial4_w1/`)
> para que los iframes relativos a cada `network_interactive.html` carguen.

### Comportamiento

1. Reutiliza el build de cada familia si ya existe y el caché está fresco
   (`check_cache_fresh`); si no, lo construye (misma lógica que `build`).
2. Si un build reutilizado no tiene `network_interactive.html` (se construyó
   con `--no-interactive`), se regenera desde su `graph.pkl`.
3. Recolecta accuracy + métricas por familia en `comparison_summary.csv` y el
   HTML.

---

## Convenciones y restricciones

Esta red hereda las convenciones obligatorias del esquema común (entry point
delgado, `core/` con API pública, persistencia con `metadata.json`, argumentos
compartidos, rutas relativas). Ver [`networks/README.md`](../README.md).

Restricciones adicionales específicas:

- **No** comparar `mean_ps` crudo entre waves (rango distinto); usar z-score.
- **No** asumir que `ps` nunca viene como `NA` — filtrar strings no numéricos.
- **No** atribuir `accuracy` a participantes con `uniform_id = 'NA'`.

---

## Referencias

- Esquema estándar y convenciones: [`networks/README.md`](../README.md).
- Red de referencia (estructura canónica): [`networks/cognitive-load/README.md`](../cognitive-load/README.md).
- Fuente de datos: `data/MECO-L2_version-2.2/.../joint_l2_fixation_trimmed_report_2.2.csv` (W1), `data/MECO-L2_version-2.2/.../joint_fix_trimmed_L2_wave2_version2.2.csv` (W2).
- Comprensión: `data/MECO-L2_version-2.2/wave-{1,2}/primary-data/comprehension/joint.comp.l2.csv`.
- Especificación de columnas: `data/POPEYE_DATA_SPEC.md`.
- Convención de contribución: `CONTRIBUTING.md`.
