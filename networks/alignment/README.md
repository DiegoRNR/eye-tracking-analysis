# Red de Alineamiento Scanpath ↔ Estructura Sintáctica/Semántica

## Descripción

Compara la red de fijaciones reales con la estructura natural del lenguaje para cuantificar cuánto se "desvía" la navegación visual del lector respecto a la gramática y semántica del texto.

**Estructura de la red**

- **Red A (ocular):** red de transiciones de fijación reales de los participantes sobre las palabras del pasaje (la misma que produce `networks/scanpath/`).
- **Red B (semántica/sintáctica):** los mismos nodos (palabras), pero las aristas representan similitud semántica de embeddings (spaCy / sentence-transformers) o dependencias gramaticales.

**Librerías previstas:** `spacy`, `sentence-transformers`, `networkx`, `scipy.stats`.

**Métricas y análisis relevantes**

- **Distancia entre grafos / spectral distance:** medir la distancia entre la matriz de adyacencia de lectura y la matriz semántica.
- **Jaccard similarity de aristas:** qué porcentaje de las sacadas visuales siguen la estructura gramatical vs. regresiones no lineales causadas por sobrecarga cognitiva.

---

## Estado actual

**Pendiente de implementación.** Esta carpeta aún no contiene código. Este README define la estructura objetivo que deberá seguirse cuando se implemente.

---

## Estructura objetivo

Debe replicar exactamente el esquema de `networks/cognitive-load/` (ver `networks/cognitive-load/README.md` como referencia canónica):

```
networks/alignment/
├── README.md                 # Este archivo
├── alignment.py              # Entry point CLI: subcomandos `build` y `stats`
├── core/                     # Librería interna
│   ├── __init__.py           # Re-exporta SOLO la API pública
│   ├── data_io.py            # Carga de fijaciones + embeddings/dependencias
│   ├── network_builder.py    # Construcción de Red A y Red B; comparación
│   ├── persistence.py        # Serialización + metadata.json para caché
│   ├── paths.py              # Hash de archivos
│   ├── visualization.py      # Plots de comparación
│   └── stats/                # Métricas de alineamiento (spectral, Jaccard, etc.)
└── output/                   # Builds generados (gitignored)
```

### Subcomandos CLI previstos

- `alignment.py build --subid ... --lang ... --trialid ... --wave ... --groupby ... --outdir ...`
- `alignment.py stats --load <build_dir>`

Los flags compartidos (`--subid`, `--lang`, `--trialid`, `--wave`, `--groupby`, `--outdir`) deben extraerse a un helper `_add_shared_args`, igual que en `cogload.py`.

### API pública esperada en `core/__init__.py`

```python
from .network_builder import build_alignment_networks, build_prefix
from .stats import alignment_metrics_from_cache
from .persistence import save_built_networks, load_built_networks, check_cache_fresh
from .data_io import load_all_fixations
```

---

## Cómo se ejecutará (una vez implementado)

```bash
# Desde la raíz del repositorio
python networks/alignment/alignment.py build --subid du_7 --trialid 4 --wave 1
python networks/alignment/alignment.py stats \
  --load networks/alignment/output/alignment_trial4_w1_subdu_7
```

---

## Formato de `output/<build>/`

Mismo esquema que `cognitive-load/`:

| Archivo | Descripción |
|---------|-------------|
| `nodes.csv` | Palabras con embeddings y métricas de fijación. |
| `edges_ocular.csv` | Aristas de la Red A (scanpath). |
| `edges_semantic.csv` | Aristas de la Red B (semántica/sintáctica). |
| `graph_ocular.pkl`, `graph_semantic.pkl` | Objetos `networkx` serializados. |
| `network_ocular.graphml`, `network_semantic.graphml` | Formato GraphML. |
| `metadata.json` | Parámetros + hashes de fuentes. |
| `plots/` | Visualizaciones de comparación. |

---

## Convenciones y restricciones

Esta red heredará las convenciones obligatorias del esquema común (entry point delgado, `core/` con API pública, persistencia con `metadata.json`, argumentos compartidos) y la lista consolidada de cosas que **no** se deben hacer. Ver [`networks/README.md`](../README.md).

Adicional específico de esta red:

- **No** commitear `output/` ni modelos de embeddings pesados.

---

## Referencias

- Estructura de referencia: `networks/cognitive-load/README.md`.
- Esquema común y guidelines para nuevas redes: [`networks/README.md`](../README.md).
- Fuente de datos: `data/MECO-L2_version-2.2/.../joint_l2_fixation_trimmed_report_2.2.csv`.
- Convención de contribución: `CONTRIBUTING.md`.
