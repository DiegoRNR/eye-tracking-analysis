# Red de Carga Cognitiva Pupilo-dilatada (Cognitive-Load Networks)

## Descripción

El diámetro pupilar (`ps` en `data/MECO-L2_version-2.2/.../joint_l2_fixation_trimmed_report_2.2.csv`) es un indicador de activación cognitiva, es sugerido que el aumento del diámetro pupilar indique una mayor carga cognitiva. Esta red modela cómo la dilatación pupilar se propaga entre palabras consecutivas durante la lectura.

**Estructura de la red**

- **Nodos:** palabras (u oraciones) del texto.
- **Peso de nodo:** magnitud de la dilatación pupilar (`PS`) durante la fijación.
- **Aristas:** transición entre palabras, ponderada por `ΔPS = |PS_word2 − PS_word1|`.

**Métricas clave**

- **Cascadas de carga cognitiva:** detectar si un pico pupilar en una palabra de alta dificultad propaga alta carga a las siguientes 3-4 palabras.
- **Modularidad del esfuerzo:** agrupar el texto en zonas de "alto estrés cognitivo" vs. "procesamiento fluido".

**Librerías:** `scipy.signal`, `networkx`, `seaborn`, `pyvis`.

> Las convenciones que aplica esta red (y que cualquier red nueva debe replicar) viven en [`networks/README.md`](../README.md).

---

## Estructura del código

```
networks/cognitive-load/
├── README.md                 # Este archivo (referencia de estructura)
├── cogload.py                # Entry point CLI: subcomandos `build` y `stats`
├── core/                     # Librería interna (toda la lógica vive aquí)
│   ├── __init__.py           # Re-exporta SOLO la API pública
│   ├── data_io.py            # Carga de fijaciones desde data/MECO-L2_version-2.2
│   ├── network_builder.py    # Construcción de la red (nodos, aristas, pesos)
│   ├── persistence.py        # Serialización a CSV/pickle/GraphML/JSON + caché
│   ├── paths.py              # Hash de archivos (sha256) para invalidación de caché
│   ├── visualization.py      # Plots estáticos con matplotlib/seaborn
│   ├── interactive_viz.py    # HTML interactivo con pyvis (opcional)
│   └── stats/                # Submódulo de métricas
│       ├── _common.py
│       ├── metrics.py
│       ├── cascades.py
│       ├── modularity.py
│       ├── orchestrator.py   # Coordina el cálculo de stats sobre un build
│       ├── exports.py
│       └── viz.py
└── output/                   # Builds generados (gitignored)
```

---

## Cómo ejecutar

Desde la raíz del repositorio, **o** desde `networks/cognitive-load/` (los entry points usan `os.path.dirname` para resolver rutas relativas).

### Construir una red

```bash
python networks/cognitive-load/cogload.py build
```

O con algunos parámetros:

```bash
python networks/cognitive-load/cogload.py build --subid du_7 --trialid 4 --wave 1
```

Salida en `networks/cognitive-load/output/cogload_trial4_w1_zscore_sequential_subdu_7/`.

### Calcular estadísticas sobre un build

```bash
python networks/cognitive-load/cogload.py stats
```

O con parámetros:

```bash
python networks/cognitive-load/cogload.py stats --subid du_7 --trialid 4 --wave 1
```

O desde una red ya construida:

```bash
python networks/cognitive-load/cogload.py stats \
  --load networks/cognitive-load/output/cogload_trial4_w1_zscore_sequential_subdu_7
```

### Flags útiles

- `--subid <id>`: filtra por participante (`uniform_id`, ej. `du_4`).
- `--lang <l1>`: filtra por lengua materna (ej. `du`, `es`, `de`, `it`).
- `--trialid <1-12>`: ID del texto (default `1`).
- `--wave {1,2,both}`: ola(s) a cargar (default `both`).
- `--groupby {participant,lang,all}`: agregación de sesiones (default `all`).
- `--normalize {zscore,none}`: normalización de `PS` por sesión (default `zscore`).
- `--edge-mode {sequential,window,regression}`: definición de aristas (default `sequential`).
- `--edge-window N`: tamaño de ventana hacia adelante cuando `--edge-mode=window` (default 4).
- `--per-sentence`: restringe aristas a dentro de la oración.
- `--no-interactive`: omite la generación del HTML con pyvis.
- `--name SUFIJO`: sufijo para los archivos de stats/plots.

---

## Formato de `output/<build>/`

Tras ejecutar `build`, la carpeta del build contiene:

| Archivo | Descripción |
|---------|-------------|
| `nodes.csv` | Nodos (palabras) con métricas de fijación. |
| `edges.csv` | Aristas con pesos, tipo de transición y ΔPS. |
| `graph.pkl` | Objeto `networkx.DiGraph` serializado. |
| `network.graphml` | Red en GraphML, abrible en Gephi/Cytoscape. |
| `metadata.json` | Parámetros del build + hashes de archivos fuente. |
| `plots/` | Gráficos estáticos (matplotlib/seaborn). |
| `network_interactive.html` | Red interactiva (pyvis). |

`output/` está en `.gitignore` (`networks/*/output/`).

---

## Convenciones y restricciones

Esta red hereda las convenciones obligatorias del esquema común (entry point delgado, `core/` con API pública, persistencia con `metadata.json`, argumentos compartidos) y la lista consolidada de cosas que **no** se deben hacer. Ver [`networks/README.md`](../README.md).
