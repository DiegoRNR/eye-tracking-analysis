# Red de Transición de Fijaciones Oculares (Scanpath Networks)

## Descripción

La **Red de Transición de Fijaciones Oculares (Scanpath Network)** modela el mapa de navegación visual de los lectores a medida que procesan un texto. En lugar de tratar las fijaciones como mediciones aisladas de duración, este enfoque representa el proceso de lectura como una **red dirigida y ponderada**:

- **Nodos:** palabras del texto (identificadas por su posición `wordnum` y su cadena de texto `word`).
- **Aristas dirigidas ($u \to v$):** transiciones consecutivas del ojo entre palabras (sacadas).
- **Pesos de aristas ($w_{uv}$):** frecuencia acumulada de saltos directos desde la palabra $u$ hacia la palabra $v$.

Este modelo permite aplicar algoritmos de **ciencia de redes** para caracterizar la fluidez de lectura, detectar cuellos de botella cognitivos y comparar las estrategias de lectura entre hablantes nativos (L1) y lectores de segunda lengua (L2).

---

## Redes por texto (L2, cuartiles Q1/Q4) — `scanpath_texts.py`

Genera, por grupo lingüístico y cuartil de comprensión lectora (misma división
p25/p75 que `word-type-transitions`), una red de scanpath **por texto** con la
palabra como nodo — estática y ANIMADA (aristas aparecen en su primera
travesía conforme avanza la lectura, scrubber ▶/slider/velocidad).

```bash
python networks/scanpath/scanpath_texts.py --lang du        # 2 cuartiles × 12 textos
python networks/scanpath/scanpath_texts.py --lang du,ee --trialid 1,5
python networks/scanpath/scanpath_texts.py --lang all --quartile q4
```

Salidas en `networks/scanpath/output/<lang>/<Q1|Q4>/`:

```
network.html            # wrapper: iframes de los 12 textos
network/<t1..t12>.html  # red estática por texto
network_anim.html       # wrapper animado
network_anim/<tN>.html  # red animada por texto
```

- Layout fijo de mapa de lectura (x = posición dentro de la oración, y = oración), física apagada.
- Color de nodo = ps media (viridis; gris = sin ps); tamaño = fix_count.
- Aristas: azul = avance, roja = regresión; grosor/opacidad = n pooled del cuartil. Refijaciones consecutivas (misma palabra) no generan arista (el conteo queda visible en el tooltip).
- En la animación: destello = primera travesía; luego settle al estilo estático.
- `scanpath_network.py` (script monolítico de un solo texto) NO se ve afectado.

### Estructura del código

```
networks/scanpath/
├── README.md                 # Este archivo
├── scanpath_network.py       # Script monolítico legacy (un texto; pendiente de refactor)
├── scanpath_texts.py         # CLI batch por texto (entry point + core/)
├── core/                     # paths, data_io (L2 limpio + cuartiles), network_builder,
│                             # visualization (estática + wrapper), temporal_viz (animada)
└── output/                   # Reportes y gráficos generados (gitignored)
```

---

## Dashboard interactivo — `scanpath_dashboard.py`

Dashboard HTML **autocontenido** (mismo estilo que
`reading-pattern-mds/output/reading_patterns_dashboard.html`: sidebar +
Plotly) con TODAS las celdas de scanpath embebidas como JSON: se eligen
lengua → texto (t1-t12) → cuartil (Q1/Q4) y se ve la red al instante.

```bash
python networks/scanpath/scanpath_dashboard.py                  # todas las lenguas (~12 MB)
python networks/scanpath/scanpath_dashboard.py --langs du,ee    # subset más liviano
```

Salida: `networks/scanpath/output/scanpath_dashboard.html` (se abre directo
en el navegador, sin servidor).

**Dos granos de nodo** (selector "Grano"):

- **Palabra (mapa de lectura):** la red de `scanpath_texts.py` renderizada en
  Plotly — layout fijo (x = posición en la oración, y = oración), color = ps
  media (viridis, gris = sin ps), tamaño = fijaciones, arista azul = avance /
  roja = regresión con puntas de flecha, grosor = n pooled. Hover muestra
  duración media, ps y n de transiciones.
- **Tipo de palabra (muelle):** las MISMAS transiciones agregadas entre
  categorías gramaticales (`categoria_gramatical` de
  `data/benchmark/words_classified.csv`; join exacto por `(trialid, wordnum)`,
  ianum == wordnum). Layout de muelle determinista (networkx spring, seed 42)
  con leyenda de categorías; el color de la arista sigue la dirección
  dominante (avance vs regresión). Nodos muestran fijaciones, ps media y n° de
  palabras distintas del tipo.

**Modo animado** (pestaña "animada"): re-implementación del reveal de
`temporal_viz` en Plotly — ▶ play + scrubber + velocidad; cada arista aparece
en su **primera travesía** (t = progreso 0-100% de la lectura de cada sujeto,
pooled) con destello y luego settle al estilo estático. Disponible en ambos
granos (tipo→tipo anima las transiciones entre categorías).

**Elementos de core:**

- `core/dashboard.py` — colector (reusa `build_text_network` de las redes por
  texto; serializa nodos/aristas compactos + momento de primera travesía por
  arista) y `generate_dashboard()` (template + JSON embebido).
- `core/dashboard_template.html` — sidebar, renderer Plotly (estático +
  animación) y leyenda de tipos.

---

## Estado

**En transición al esquema estándar.** El script actual es un único archivo (`scanpath_network.py`) en la raíz de la carpeta, sin submódulo `core/`, sin `metadata.json` ni invalidación de caché por hash. La estructura canónica del proyecto (entry point delgado + `core/` con API pública + persistencia determinística) está definida en [`networks/README.md`](../README.md) usando `cognitive-load/` como referencia; esta red será migrada a ese esquema en una iteración posterior.

---

## Estructura del código

```
networks/scanpath/
├── README.md                 # Este archivo
├── scanpath_network.py       # Script ejecutable (CLI monolítico; pendiente de refactor)
└── output/                   # Reportes y gráficos generados (gitignored)
```

---

## Cómo ejecutar

Desde la raíz del repositorio:

### Ejecución básica (texto 1 por defecto)

```bash
python networks/scanpath/scanpath_network.py
```

### Filtrar por idioma materno (L1)

Analizar la red del grupo de participantes con lengua materna `es` leyendo el texto 3:

```bash
python networks/scanpath/scanpath_network.py --lang es --trialid 3
```

### Filtrar por participante individual

Red de un participante específico (`du_4`) en el texto 9:

```bash
python networks/scanpath/scanpath_network.py --subid du_4 --trialid 9
```

### Especificar archivo de fijaciones y carpeta de salida

```bash
python networks/scanpath/scanpath_network.py \
  --file data/MECO-L2_version-2.2/wave-1/primary-data/joint_l2_fixation_trimmed_report_2.2.csv \
  --trialid 1 \
  --outdir networks/scanpath/output/trial_1 \
  --name mi_red_texto1
```

### Flags disponibles

| Flag | Descripción | Default |
|------|-------------|---------|
| `--file <ruta>` | Ruta al CSV de fijaciones (`joint_l2_fixation_trimmed_report_2.2.csv`). | (autodetectado bajo `data/`) |
| `--subid <id>` | Filtrar por participante (`uniform_id`, ej. `du_4`, `es_10`). | (sin filtro) |
| `--lang <l1>` | Filtrar por L1 (ej. `du`, `es`, `de`, `it`). | (sin filtro) |
| `--trialid <1-12>` | ID del texto a analizar. | `1` |
| `--outdir <ruta>` | Carpeta de salida. | `networks/scanpath/output` |
| `--name <sufijo>` | Sufijo para los archivos generados. | (sin sufijo) |

> El script expone los flags con `--help`:
> ```bash
> python networks/scanpath/scanpath_network.py --help
> ```

---

## Métricas calculadas

### A nivel de nodo

- **In-Degree y Out-Degree ponderados:** cantidad de transiciones que llegan o salen de una palabra. Identifican palabras "ancla" o de alta re-fijación.
- **Centralidad de intermediación (Betweenness):** mide el grado en que una palabra actúa como puente o "cuello de botella cognitivo" en los caminos de navegación visual.
- **PageRank:** identifica palabras que concentran la atención del lector, considerando no solo el número de fijaciones sino la relevancia de las palabras desde las que el lector realiza regresiones.
- **Pupil size promedio (`mean_ps`):** diámetro pupilar durante las fijaciones a la palabra (indicador de carga mental).

### A nivel de red

- **Reciprocidad ($R$):** proporción de aristas bidireccionales ($A \to B$ y $B \to A$), cuantificando la tasa de regresiones inmediatas.
- **Proporción de regresiones (Regression Ratio):** porcentaje de sacadas dirigidas hacia palabras anteriores ($v < u$) respecto al total de transiciones.
- **Entropía del scanpath (Shannon Entropy):** cuantifica la previsibilidad vs. caoticidad del patrón de navegación sobre el texto.
- **Densidad de la red:** grado de interconexión entre las palabras del texto.

---

## Archivos generados en `output/`

Tras ejecutar el script, se generan (en `--outdir`):

1. **`scanpath_*_global_metrics.csv`** — métricas globales de la red (nodos, aristas, densidad, entropía, reciprocidad, ratio de regresión).
2. **`scanpath_*_node_metrics.csv`** — métricas por palabra: conteo de fijaciones, tiempo total/promedio, tamaño de pupila, grados y centralidades.
3. **`scanpath_*_edge_list.csv`** — lista de aristas dirigidas, pesos, tipo de transición (`forward`, `regression`, `refixation`) y tiempo promedio de salto.
4. **`scanpath_*_network.graphml`** — red en formato GraphML, abrible en Gephi o Cytoscape.
5. **`scanpath_*_visualization.png`** — gráfico estático (Matplotlib) con el mapa de palabras y las transiciones.
6. **`scanpath_*_interactive.html`** — red interactiva HTML (Pyvis) con drag, zoom y tooltips al pasar el cursor.

> `output/` está en `.gitignore` (`networks/*/output/`).

---

## Referencias

- Esquema estándar y convenciones para nuevas redes: [`networks/README.md`](../README.md).
- Red de referencia (estructura canónica): [`networks/cognitive-load/README.md`](../cognitive-load/README.md).
- Fuente de datos: `data/MECO-L2_version-2.2/.../joint_l2_fixation_trimmed_report_2.2.csv`.
- Convención de contribución: [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
