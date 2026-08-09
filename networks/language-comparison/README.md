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

### Qué hace esta implementación

La implementación expone **tres subcomandos** que cubren el pipeline completo:

| Subcomando | Qué hace | Salida |
|------------|----------|--------|
| `build` | Construye y persiste la red de **una familia** para un `trialid`+`wave`. | `output/langcomp_trial<...>_<familia>/` |
| `stats` | Calcula métricas, cascadas y modularidad sobre un build ya generado (cache). | `stats/` dentro del build |
| `compare` | Construye (o reutiliza) una red **por familia** y genera un reporte HTML comparativo. | `output/comparison_trial<...>_w<...>/` |

**Nota técnica sobre el reuso de código:** la construcción de la red reutiliza
`build_cogload_network` de `networks/cognitive-load` vía `importlib`, cargando su
paquete `core` bajo el alias `cogload_core`. Esto es necesario porque **ambos
paquetes se llaman `core`** y un import directo colisionaría. Ver
`core/network_builder.py`.

---

## Estado

**Implementada.** Sigue el esquema canónico definido en
[`networks/README.md`](../README.md) usando `cognitive-load/` como referencia.

---

## Requisitos y setup

- **Python ≥ 3.11** (pinned en `.python-version`). Gestor de paquetes: `uv`.
- **R** en el PATH, **únicamente** para la conversión RDA → CSV (una sola vez).
- Dependencias Python en `pyproject.toml` (`networkx`, `pandas`, `numpy`,
  `scipy`, `matplotlib`, `seaborn`, `pyvis`).

```bash
# 1. Crear el entorno e instalar dependencias
uv sync
.venv\Scripts\activate        # Windows  (Linux/Mac: source .venv/bin/activate)

# 2. PRERREQUISITO CRÍTICO: materializar los CSVs desde los RDA
#    (los archivos *.csv y *.rds están gitignored; sin ellos no corre nada)
Rscript scripts/convert_rda_to_csv.R
```

R solo se necesita para el paso 2. Una vez que los CSVs existen bajo `data/`,
todo el trabajo es Python.

---

## Cómo ejecutar

Flujo recomendado (desde la raíz del repositorio):

```bash
# 1. Construir la red de una familia
python networks/language-comparison/langcomp.py build --lang-group germanic --trialid 4 --wave 1

# 2. Calcular estadísticas sobre ese build (cache; no reconstruye)
python networks/language-comparison/langcomp.py stats \
  --load networks/language-comparison/output/langcomp_trial4_w1_zscore_germanic_langs-du-en-ge-no

# 3. Comparar todas las familias presentes en el wave (reporte HTML)
python networks/language-comparison/langcomp.py compare --trialid 4 --wave 1

# 4. Abrir el reporte comparativo en el navegador
start networks/language-comparison/output/comparison_trial4_w1/comparison_report.html
```

> **Importante:** abrir `comparison_report.html` **desde su carpeta**
> (`output/comparison_trial4_w1/`) para que los iframes relativos a cada
> `network_interactive.html` de las familias carguen correctamente.

### Flags de `build` y `stats`

| Flag | Descripción | Default |
|------|-------------|---------|
| `--lang-group <grupo>` | Familia lingüística o `all`. | `germanic` |
| `--trialid <1-12>` | ID del texto a analizar. | `1` |
| `--wave {1,2,both}` | Ola(s) a cargar. | `1` |
| `--normalize {zscore,none}` | Normalización de `ps` por sesión. | `zscore` |
| `--outdir <ruta>` | Carpeta raíz de salida. | `networks/language-comparison/output` |
| `--no-interactive` | Omite la generación de `network_interactive.html` (build). | — |

> `stats` admite además `--load <build_dir>` (modo cache) y los umbrales
> `--cascade-window`, `--z-thresh`, `--p-thresh`, `--name`.

### Familias lingüísticas disponibles

| Familia | Códigos L1 | Waves |
|---------|------------|-------|
| `germanic` | du, en, ge, no, da, en_uk, ge_po, ge_zu, ic, se | 1, 2 |
| `romance` | it, sp, bp, sp_ch | 1, 2 |
| `slavic` | ru, ru_mo | 1, 2 |
| `uralic` | ee, fi | 1 |
| `turkic` | tr | 1, 2 |
| `hellenic` | gr | 1 |
| `semitic` | he | 1 |
| `sino-tibetan` | ch_s, ch_t | 2 |
| `indo-aryan` | hi_iiith, hi_iitk | 2 |
| `isolate` | ba (euskera) | 2 |

Las familias sin lenguas en una wave se **omiten automáticamente** en `compare`
(p.ej. `uralic`, `hellenic`, `semitic` no existen en wave 2).

### Formato del prefijo de build

`langcomp_trial<T>_w<W>_<normalize>[_nops-<langs sin ps>]_<grupo>[_langs-<códigos>]`

Ejemplos:

- `langcomp_trial4_w1_zscore_germanic_langs-du-en-ge-no`
- `langcomp_trial4_w2_zscore_nops-ch_s_sino-tibetan_langs-ch_t`

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

## Formato de `output/<build>/`

Tras `build`, la carpeta del build contiene:

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

## Cómo interpretar los resultados

### 1. La red interactiva (`network_interactive.html`)

Es la representación visual de **cómo se mueve la carga cognitiva por las
palabras** del texto, para la familia seleccionada:

| Elemento | Qué codifica | Cómo leerlo |
|----------|--------------|-------------|
| **Nodo = palabra** | Color = `mean_ps` (pupila promedio; viridis: oscuro = poco, amarillo = mucho) | Palabras amarillas = más esfuerzo cognitivo |
| **Tamaño de nodo** | `fix_count` (cuántas veces se fijaron los ojos en esa palabra) | Más grande = más fijaciones = más atención |
| **Arista = transición** | Color = `mean_dps` (Δpupila entre palabras consecutivas; coolwarm: azul = suave, rojo = pico) | Aristas rojas = saltos bruscos de pupila entre 2 palabras = puntos de alta carga |
| **Grosor de arista** | `count` (cuántas sesiones apoyan esa transición) | Más grueso = transición consistente entre muchos lectores |

**Patrones a buscar:**

- **Nodos amarillos + aristas rojas cerca**: palabra de alta dificultad que
  dispara carga en las siguientes.
- **Atención concentrada al inicio** del texto (ej. nombres propios) suele
  indicar aclimatación al pasaje.
- Pasa el cursor sobre un nodo para ver su tooltip (texto plano): `word ·
  wordnum · fix_count · mean_ps · mean_ps_z`. Sobre una arista: `word_u → word_v
  · type · count · mean_dps`.

> ⚠️ Solo comparar `mean_ps_z` entre familias/waves. El `mean_ps` crudo **no es
> comparable entre waves** (rango distinto).

### 2. `metadata.json` — el accuracy de la familia

Responde **"¿qué familia comprende mejor?"**:

```json
"accuracy": { "mean": 0.7672, "median": 0.7917, "std": 0.xx, "n": 109 }
```

- `accuracy.mean` = comprensión promedio de la familia (0–1). **Métrica principal.**
- `accuracy.median` = robusto a extremos; si difiere mucho del mean, hay asimetría.
- `accuracy.n` = **cuidado**: puede ser menor que `n_participants` (daneses W2 sin accuracy).

**Ejemplo real (trial 4, wave 1):**

| Familia | accuracy | n |
|---------|----------|---|
| uralic | **0.767** | 109 |
| slavic | 0.747 | 47 |
| semitic | 0.744 | 45 |
| romance | 0.734 | 92 |
| germanic | 0.720 | 176 |
| turkic | 0.637 | 25 |
| hellenic | **0.582** | 48 |

**Patrón a investigar**: ¿por qué `uralic` (finés/estonio) comprende mejor que
`hellenic` (griego)? El finés ni siquiera es indoeuropeo → apunta a factores de
**exposición al inglés / sistema educativo**, no parentesco lingüístico. Eso es
una hipótesis interesante.

### 3. `stats/global_metrics.csv` — salud de la red

| Métrica | Qué significa | Cómo leerla |
|---------|---------------|-------------|
| `n_nodes` / `n_edges` | Tamaño de la red | Igual número de nodos (142) = todos leyeron el mismo texto; la **densidad** varía |
| `density` | Conexión relativa entre palabras | Más baja (w2 romance 0.0057) = transiciones repartidas entre más palabras |
| `mean_dps` | Δpupila promedio entre palabras | Mismo texto, `mean_dps` alto = saltos pupilares más bruscos = más esfuerzo/inestabilidad |
| `max_dps` | Mayor Δpupila en una arista | Un valor muy alto = al menos una palabra dispara un pico enorme |
| `modularity` | Qué tan modular es la red | Alto (0.78–0.87 en w2) = el texto se agrupa en "zonas" de esfuerzo delimitadas |
| `n_ps_peaks` | Palabras que son picos de carga | Más picos (30 vs 15) = más zonas de alta demanda |

### 4. `stats/node_metrics.csv` — atención palabra por palabra

Es **la fuente de oro** para "¿en qué palabras clave se fija más cada familia?".

Columnas clave: `word`, `wordnum`, `fix_count`, `mean_ps`, `mean_ps_z`,
`strength_in/out`, `community_label`.

- **Palabras más atendidas**: ordenar por `mean_ps_z` desc. Los nombres propios
  y términos del texto dominan (contenido semántico denso).
- **`strength_out` alto** = palabra desde la que se dispara mucha carga hacia
  adelante (palabra "gatillo").
- **`strength_in` alto** = palabra hacia la que se acumula carga (palabra
  "sumidero", donde el lector vuelve).

**Patrón diferencial a buscar**: la **misma palabra** puede tener `mean_ps_z`
alto en una familia y bajo en otra → indica **qué palabra es difícil para quién**.
Cruzando los `node_metrics.csv` de varias familias por `word`, se ven las palabras
con mayor divergencia de atención.

### 5. `stats/cascades.csv` — propagación de carga

Cada fila es un **pico de pupila** detectado en una sesión individual:

| Campo | Significado |
|-------|-------------|
| `peak_wordnum` | Palabra donde está el pico |
| `is_cascade` | `True` = el pico se **propaga** a las 4 palabras siguientes (test t significativo) |
| `window_mean_signal` | Nivel medio de carga tras el pico |
| `baseline_mean_signal` | Línea base previa |
| `p_value` | Significancia de la cascada |

**Cómo leerlo**: filtra `is_cascade=True` y agrupa por `peak_wordnum` → **¿en qué
palabras del texto se disparan cascadas en cada familia?** Si una palabra dispara
cascadas en `turkic`/`hellenic` pero no en `germanic`, es candidata a "palabra
difícil para ese grupo".

### 6. `stats/community_summary.csv` — zonas de esfuerzo

Las comunidades agrupan palabras en zonas de carga: `high_stress` (alta pupila),
`low_stress` (baja), `neutral`. El plot `community_along_text.png` lo visualiza
a lo largo de `wordnum`.

**Patrón a buscar**: comunidades `high_stress` **contiguas** en el texto (misma
región de wordnums) = zonas particularmente exigentes para ese grupo. Si la
franja `high_stress` cubre las mismas oraciones en una familia pero no en otra,
es un hallazgo.

### 7. Plots comparativos (`comparison_trial4_wX/`)

- **`comparison_accuracy.png`**: barras de comprensión por familia → **la
  respuesta visual a "quién comprende mejor"**.
- **`comparison_attention.png`**: líneas `mean_ps_z` por palabra, una por
  familia → **dónde divergen las familias en atención**.

**Patrón clave del de atención**: busca zonas del texto donde las líneas se
separan mucho (una familia en +1σ mientras otra está en −0.5σ). Esas son las
palabras que **discriminan** entre grupos.

### Flujo de análisis recomendado

1. **Global primero**: `comparison_accuracy.png` → ordena familias por comprensión.
2. **Red por familia**: `network_interactive.html` → mira dónde están los nodos amarillos/picos.
3. **Por nodo**: `node_metrics.csv` → identifica las palabras que concentran atención en cada familia.
4. **Diferencial**: cruza `node_metrics.csv` entre familias → palabras con mayor divergencia de `mean_ps_z`.
5. **Cascadas**: `cascades.csv` filtrando `is_cascade=True` → qué palabras disparan propagación en cada grupo.
6. **Modularidad**: `community_summary.csv` + `community_along_text.png` → qué regiones del texto son zonas de esfuerzo por familia.

---

## Convenciones y restricciones

Esta red hereda las convenciones obligatorias del esquema común (entry point
delgado, `core/` con API pública, persistencia con `metadata.json`, argumentos
compartidos, rutas relativas). Ver [`networks/README.md`](../README.md).

Restricciones adicionales específicas:

- **No** comparar `mean_ps` crudo entre waves (rango distinto); usar z-score.
- **No** asumir que `ps` nunca viene como `NA` — filtrar strings no numéricos.
- **No** atribuir `accuracy` a participantes con `uniform_id = 'NA'`.

**Nota metodológica — waves separadas (Opción A):** Wave 1 y Wave 2 son
**cohortes independientes de participantes**. Solo `no` y `tr` aparecen en ambas,
pero son personas distintas. Además el rango de `ps` difiere entre waves
(139–7743 vs 166–3924), por lo que el `mean_ps` crudo no es comparable. Por eso
la implementación genera **reportes separados por wave** (`comparison_trial4_w1/`
y `comparison_trial4_w2/`), y **no** mezcla waves en una sola red. La comparación
entre familias es válida **dentro de cada wave** usando z-scores.

---

## Referencias

- Esquema estándar y convenciones: [`networks/README.md`](../README.md).
- Red de referencia (estructura canónica): [`networks/cognitive-load/README.md`](../cognitive-load/README.md).
- Fuente de datos: `data/MECO-L2_version-2.2/.../joint_l2_fixation_trimmed_report_2.2.csv` (W1), `data/MECO-L2_version-2.2/.../joint_fix_trimmed_L2_wave2_version2.2.csv` (W2).
- Comprensión: `data/MECO-L2_version-2.2/wave-{1,2}/primary-data/comprehension/joint.comp.l2.csv`.
- Especificación de columnas: `data/POPEYE_DATA_SPEC.md`.
- Convención de contribución: `CONTRIBUTING.md`.
