# Red de Transiciones entre Tipos de Palabra — Mejores vs Peores Lectores (Q4 vs Q1), Nativo vs Inglés

## Descripción

Redes dirigidas y ponderadas en el **espacio de tipos de palabra** (etiquetas
fused de POS) construidas a partir de la **secuencia temporal de fijaciones**.
Nodos = tipos de palabra; aristas dirigidas = transiciones consecutivas del ojo
entre IAs de tipo u → tipo v.

Diseño **2×2 por grupo lingüístico**: {L1 nativo, L2 inglés} × {Q1 peor, Q4
mejor} por comprensión lectora (accuracy), con **duración media de fijación
como atributo de carga cognitiva** en los nodos. **28 grupos**: 12 lenguas
wave 1, chino wave 2 (2 variantes) y las 14 variantes L1 wave 2 (cada una es
un GRUPO SEPARADO, sin fusiones). Koreano excluido (sin sesión L2).

## Condiciones

| Grupo | Sesión L1 (nativo) | Sesión L2 (inglés) |
| :--- | :--- | :--- |
| 12 lenguas wave 1 (`du ee en fi ge gr he it no ru sp tr`) | `joint_l1_fixation_report_2.1.rda` (textos Janus…Placas en lengua nativa) | `joint_l2_fixation_trimmed_report_2.2.comprehension.clean.csv` (textos Morse…Smartphones) |
| Chino (`ch_s`, `ch_t`) | `joint_fix_trimmed_l1_wave2_version2.1.rda` | `joint_fix_trimmed_L2_wave2_version2.2.comprehension.clean.csv` |
| 14 variantes wave 2 (`ba bp da en_uk ge_po ge_zu hi_iiith hi_iitk ic ru_mo se sp_ch no_w2 tr_w2`) | idem chino (cache `l1_wave2_fix.csv`; `itemid` mapeado con `l1_tokens_w2/itemid_to_text_<code>.csv`; ic y en_uk rotan) | idem chino (wave 2; los cohortes noruego/turco aparecen como lang `no`/`tr` en los datos → alias a `no_w2`/`tr_w2`) |

Nombres de las variantes wave 2: `ba`=Vasco, `bp`=Portugués (Brasil), `da`=Danés,
`en_uk`=Inglés UK, `ge_po`=Alemán (Potsdam), `ge_zu`=Alemán (Zúrich),
`hi_iiith`/`hi_iitk`=Hindi (IIITH/IITK), `ic`=Islandés, `ru_mo`=Ruso (w2),
`se`=Serbio, `sp_ch`=Español (Chile), `no_w2`/`tr_w2`=Noruego/Turco (cohorte w2).

- **Cuartiles DENTRO de cada grupo**: Q1 = accuracy ≤ p25, Q4 = accuracy ≥ p75;
  el centro se descarta (misma lógica que `comp-groups`). Accuracy desde
  `joint_l1_acc.rda` / `joint_comp_L1_Wave2_trimmed.rda` (L1) y
  `joint.comp.l2.csv` / `joint_comp_L2_Wave2_trimmed.csv` (L2).
- **Identidad de texto L1 wave 1 = `itemid`** mapeado a índice 1..12 con los CSV
  `data/benchmark/l1_tokens/itemid_to_text_<lang>.csv` (Estonio y Ruso rotaban
  el orden de presentación entre sujetos).
- **Tipificación**: `words_classified_<lang>_l1.csv` (L1 alfabético wave 1),
  `words_classified_chinese_{s,t}_wave2.csv` (L1 chino),
  `words_classified_<code>_w2l1.csv` (variantes L1 wave 2) y
  `words_classified.csv` (L2 inglés).
- **Accuracy wave 2**: los sujetos duplicados (`ch_t_43`, `sp_ch_1`) se
  promedian; `sp_ch_1` queda fuera de ambos cuartiles por diseño.

## Espacio de etiquetas (fused)

| Nodo fused | UPOS |
| :--- | :--- |
| `NOUN` | NOUN, PROPN |
| `VERB` | VERB, AUX |
| `CONJ` | CCONJ, SCONJ |
| `PTCL` | DET, PART |
| `ADJ`, `ADV`, `ADP`, `PRON`, `NUM`, `X`, `PUNCT` | idem |

## Modos de transición

- **`temporal`** (primario): todas las transiciones consecutivas (auto-bucles
  incluidos); parpadeos cortan la secuencia.
- **`regression`**: solo transiciones con target estrictamente anterior.

## Ejecución PER LENGUA

Cada lengua escribe en SU PROPIO árbol `output/<lang>/`, separado por modo de
red. Nada se mezcla entre lenguas.

```bash
cd networks/word-type-transitions

# una lengua completa (build + compare + figures + report):
python word_type_transitions.py all --lang du

# solo un modo:
python word_type_transitions.py all --lang ee --mode temporal

# varias lenguas / subcomandos sueltos:
python word_type_transitions.py build   --lang fi,ge
python word_type_transitions.py compare --lang fi,ge
python word_type_transitions.py figures --lang fi,ge
python word_type_transitions.py report  --lang fi,ge

# todas las lenguas (28 grupos):
python word_type_transitions.py all --lang all
```

Lenguas válidas: `du ee en fi ge gr he it no ru sp tr ch_s ch_t` +
`ba bp da en_uk ge_po ge_zu hi_iiith hi_iitk ic ru_mo se sp_ch no_w2 tr_w2`
(la CLI valida y lista las opciones si una es desconocida).

## Formato de `output/`

```
output/
├── metadata.json                      # global: sha256 de entradas compartidas
└── <lang>/                            # ej. du/, ee/, …, ch_t/
    ├── condition_summary.csv          # n sujetos, accuracy media, QA por celda
    ├── accuracy_subjects.csv          # accuracy + quartile por sujeto (L1/L2)
    ├── REPORT.md                      # reporte completo de la lengua
    ├── temporal/
    │   ├── per_participant_<cond>.csv # sujeto × arista (probs fila-normalizadas)
    │   ├── transitions_<cond>.csv     # probs POOLED de grupo por arista
    │   ├── counts_<cond>.csv          # matriz NxN de conteos POOLED
    │   ├── matrix_<cond>.csv          # matriz NxN de probabilidades
    │   ├── node_attributes_<cond>.csv # mean_dur, dwell_share, n_fix por tipo
    │   ├── node_metrics_<cond>.csv    # PageRank, in/out strength, densidad
    │   ├── comparison_<contraste>.csv # 4 contrastes: permutación + BH-FDR
    │   └── figures/                   # suite de figuras del modo
    └── regression/                    # idem temporal/
```

(`<cond>` = `L1-<lang>-Q1` … `L2-<lang>-Q4`; contrastes = `Q4vQ1_L1`,
`Q4vQ1_L2`, `L1vL2_Q4`, `L1vL2_Q1`.)

## Figuras (por lengua, en `output/<lang>/<mode>/figures/`)

| Figura | Contenido |
| :--- | :--- |
| `accuracy_box.png` (en `temporal/figures/`, compartida) | Box plot de accuracy por celda del 2×2 (L1/L2 × peor/mejor) con puntos por sujeto. |
| `transitions_bar.png` | Top-15 transiciones clase→clase por **conteos pooled** (n de transiciones), un panel por condición; color = clase origen. |
| `fixations_bar.png` | **n de fijaciones por clase** de palabra, 4 series (una por condición). |
| `heatmap_bestworst.png` | Matrices DIFERENCIA **Q4−Q1** para L1 y L2 (divergente, escala compartida): mejores vs peores en la misma sesión. |
| `heatmap_l1vl2.png` | Matrices DIFERENCIA **L1−L2** dentro de Q4 y dentro de Q1 (divergente, escala compartida): nativo vs inglés en el mismo cuartil. |
| `network.png` | **Grafo de red 2×2** en layout circular fijo (orden FUSED, comparable entre paneles): ancho/alpha de arista = P(v\|u) pooled, tamaño de nodo = dwell share, color de nodo = duración media (viridis compartido), auto-bucles curvos. Clases **huecas y punteadas** = sin fijaciones clasificadas en esa condición (ej. PUNCT en L2, que no existe en el benchmark inglés). |
| `network.html` + `network/<cond>.html` | **Versión INTERACTIVA (pyvis/vis.js)** del mismo grafo 2×2 en una sola página: layout fijo idéntico entre paneles, hover con estadísticas exactas (P(v\|u), n pooled, dwell %, duración media, PageRank), nodos arrastrables. Los self-bucles u→u se dibujan como **satélites punteados** justo fuera de cada clase (vis.js no soporta aristas al propio nodo). Requiere internet (vis.js por CDN). |

## Estadística (sin cambios)

Test de permutación por arista (2000 permutaciones; **pareada por sujeto**
sign-flip cuando hay ≥5 sujetos comunes entre celdas — 446 sujetos hicieron
ambas sesiones en wave 1; permutación independiente si no). Corrección
**Benjamini–Hochberg** (FDR 5%). Celdas con n < 4 no se contrastan.
Nota: L1 vs L2 usa textos distintos (nativos vs ingleses) por diseño MECO.
