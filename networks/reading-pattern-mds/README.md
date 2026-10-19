# MDS de Patrones de Lectura (distancia a lectores nativos de inglés)

## Descripción

Compara el **patrón de lectura** de cada grupo lingüístico contra los cohortes
**nativos de inglés** — `en_ca` (grupo `en`, wave 1) y `en_uk` (wave 2) — y lo
proyecta en un **MDS 2-D** donde la proximidad entre puntos refleja la
semejanza de los patrones de lectura.

Espacio de características: **distribuciones de transición entre tipos de
palabra** (`NOUN->VERB`, etc.) sobre el espacio FUSED de 11 nodos, calculadas
con la MISMA lógica/filtros que `networks/word-type-transitions` (se reutiliza
su `core` importado como `wttcore`: `data_io`, `label_map`, `grouping`,
`network_builder`). Solo sesiones del MISMO tipo se comparan entre sí (L1 text
sets nativos vs referencias L1 en_*; L2 inglés vs referencias L2 en_*).

- **Distancia:** Jensen–Shannon (sqrt → métrica) entre distribuciones pooled
  sobre aristas alineadas por unión (conteos pooled → prob. de fila → masa
  global re-normalizada a 1).
- **MDS:** clásico determinista (Torgerson, `eigh`); stress-1 en el título.
  Sin dependencias nuevas (numpy/scipy/matplotlib ya están en el proyecto).

## Grupos

Todos los `CONDITION_LANGS` excepto los cohortes ingleses: du, ee, fi, ge, gr,
he, it, no, ru, sp, tr, ch_s, ch_t, ba, bp, da, ge_po, ge_zu, hi_iiith,
hi_iitk, ic, ru_mo, se, sp_ch, no_w2, tr_w2 (26 grupos). Referencias: `en`
(→ en_ca) y `en_uk`.

## Cómo ejecutar

```bash
python networks/reading-pattern-mds/reading_patterns.py all --mode temporal
python networks/reading-pattern-mds/reading_patterns.py build --mode regression
python networks/reading-pattern-mds/reading_patterns.py figures --mode temporal
python networks/reading-pattern-mds/reading_patterns.py dashboard   # ambos modos
```

Koreano excluido (sin sesión L2), igual que word-type-transitions.

## Dashboard interactivo

`output/reading_patterns_dashboard.html` (autocontenido, se abre directo en el
navegador; plotly.js via CDN) con los DOS modos embebidos:

- **MDS map**: coordenadas del embedding GLOBAL (MDS sobre TODAS las
  condiciones; el filtrado solo oculta/muestra puntos, subsets comparables).
  Filtros: lengua (checkboxes + buscador), sesión L1/L2, cuartiles
  (todos | Q1 | Q4 | Q1+Q4), cohortes nativos en_ca/en_uk, líneas de enlace,
  etiquetas, y color **por lengua**, **por distancia lingüística** o **por comprensión lectora**.
  Hover con las distancias J-S a nativos, cercanía nativa (`1 - JSD`), comprensión (%) y distancia lingüística.
- **Comprensión vs Lectura**: x = accuracy de comprensión (%), y = cercanía a nativos (`1 - JSD`) o distancia J-S, con línea OLS + estadísticas Pearson/Spearman en vivo (`corr_comprehension_reading.csv`).
- **Distancia lingüística**: x = lang_to_en.csv, y = J-S de lectura (media de
  cohortes | en_ca | en_uk), línea OLS + Pearson/Spearman del corte visible.
- **Info**: descripción del método.

## Comprensión lectora y cercanía a nativos

Accuracy de comprensión agregada por grupo, sesión y cuartil (`lang_comprehension_accuracy.csv`) contrastada contra la cercanía (`1 - JSD`) y distancia (`JSD`) a lectores nativos de inglés (`corr_comprehension_reading.csv`).

Resultados clave (modo `temporal`, media de cohortes nativos):

- **L2 (lectura en inglés): r = +0.43, p = 0.029 (Spearman ρ = 0.41, p = 0.035)** — grupos con mayor comprensión lectora en inglés adoptan patrones de transición visual significativamente más cercanos a los nativos de inglés.
- **L2 Cuartil bajo (Q1): r = +0.59, p = 0.0015** — el efecto es aún más pronunciado entre los lectores con mayores dificultades en L2.
- **L1 (lectura nativa): r = -0.12, p = 0.557 (no significativo)** — la habilidad lectora general en su propia lengua no predice cercanía al patrón inglés, confirmando que la cercanía es un marcador específico de competencia en L2.

## Distancia lingüística al inglés

`lang_to_en.csv` (raíz del repo) se mapea a los grupos:
`Ge→ge/ge_po/ge_zu`, `no→no/no_w2`, `ru→ru/ru_mo`, `sp→sp/sp_ch`,
`hi→hi_iiith/hi_iitk`, `ch→ch_s/ch_t`, `Tr→tr/tr_w2`, `Se→se`,
`kr→(sin grupo)`. Tabla: `output/<mode>/distances/lang_linguistic_distance.csv`.

Correlación con la distancia de lectura (`corr_linguistic_reading.csv`);
resultados clave (temporal, media de cohortes):

- **L1 (lectura nativa): r ≈ 0.63–0.71, p < 0.001** — la distancia lingüística
  al inglés SE refleja: lenguas más alejadas leen su idioma con patrones más
  distintos a los nativos de inglés. Efecto algo mayor en Q4 (r=0.71) que Q1
  (r=0.68).
- **L2 (lectura en inglés): r ≈ 0.30–0.44, marginal** — al leer en inglés el
  patrón se acerca de todos modos a los nativos; la distancia lingüística
  aparece sobre todo en los MEJORES lectores (Q4: r=0.44, p<0.03), no en Q1.

## Salidas (`output/<mode>/`)

```
profiles/profiles_full.csv              # condición × arista (grupo completo, sin cuartiles)
profiles/profiles_quartile.csv          # ídem con división Q1/Q4 (p25/p75, centro fuera)
distances/dist_full_all.csv             # matriz J-S entre TODAS las condiciones full
distances/dist_quartile_all.csv         # ídem Q1/Q4
distances/distance_to_native.csv        # J-S, cercanía (1-JSD) y accuracy de cada grupo a nativos
distances/lang_comprehension_accuracy.csv # accuracy por grupo, sesión y cuartil
distances/corr_comprehension_reading.csv  # correlación comprensión ↔ cercanía/distancia a nativos
distances/corr_linguistic_reading.csv   # correlación distancia lingüística ↔ lectura
distances/embeddings.csv                # coordenadas MDS por figura
figures/*.png                           # figuras MDS
```

### Variantes de figuras (spec del usuario)

| Variante | Contenido | Archivos |
|----------|-----------|----------|
| 1. L* vs nativos | un plot por sesión: L1 de todas las lenguas + refs `L1-en_ca/en_uk` (y lo mismo con L2) | `l1_vs_native.png`, `l2_vs_native.png` |
| 2. Por lengua | {L1-X, L2-X} vs las 4 refs (L1/L2 × en_ca/en_uk), 6 puntos, distancias J-S anotadas | `lang_<code>.png` |
| 3. Cuartiles | repite 1 y 2 con Q1/Q4: 2 marcas por lengua (Q1 hueco, Q4 relleno) + refs en_*-Q1/Q4 | `q_l1_vs_native.png`, `q_l2_vs_native.png`, `q_lang_<code>.png` |

Estilo: color por lengua, marcador por sesión (L1 ● / L2 ▲; refs en_* ★), Q1
hueco / Q4 relleno, línea fina uniendo L1↔L2 de cada grupo o Q1↔Q4 de cada
(grupo, sesión), stress-1 en el título.

## Interpretación

- Las sesiones **L2** (leyendo en inglés) quedan mucho más cerca de los
  nativos que las **L1** (leyendo su propia lengua): la distancia J-S medida
  refleja la semejanza del patrón de transición sobre el MISMO espacio de
  aristas y el MISMO tipo de sesión/texto.
- `distance_to_native.csv` da el valor numérico exacto por grupo, sesión y
  cuartil (para el reporte).
- Chinese (ch_s/ch_t) no tiene referencia `L2-en_ca` en wave 2 (el cohorte
  `en` es wave 1): sus plots por lengua muestran solo refs en_uk en L2.

## Estructura

```
networks/reading-pattern-mds/
├── README.md
├── reading_patterns.py    # CLI (build | figures | dashboard | all, --mode)
├── core/
│   ├── paths.py           # rutas, registro de condiciones, palette labels
│   ├── _wtt.py            # bootstrap del core de word-type-transitions como wttcore
│   ├── profiles.py        # distribuciones pooled por condición (full + Q1/Q4)
│   ├── distances.py       # J-S pairwise + persistencia
│   ├── mds.py             # MDS clásico (Torgerson) + stress-1
│   ├── viz.py             # figuras matplotlib
│   ├── lingdistance.py    # lang_to_en.csv → grupos + correlación Pearson/Spearman
│   ├── dashboard.py       # dashboard HTML self-contained (filtros client-side)
│   └── app.py             # orquestación de variantes
└── output/                # gitignored
```
