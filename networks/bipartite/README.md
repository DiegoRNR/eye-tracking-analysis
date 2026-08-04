# Redes Bipartitas de Fijación (Participante ↔ Palabra/Texto)

## Descripción

Modela las interacciones entre los lectores y las características léxicas del texto como una red bipartita ponderada.

**Estructura de la red**

- **Nodos de Tipo A:** participantes (`uniform_id`).
- **Nodos de Tipo B:** palabras clave o pasajes (`trialid` / `word`).
- **Aristas (ponderadas):** duración total de fijación (`dur`), número de fijaciones (`nfix`) o probabilidad de salteo (`skip`).

**Librerías previstas:** `networkx.bipartite`, `scipy.sparse`.

**Métricas y análisis relevantes**

- **Proyección bipartita:** proyectar la red al conjunto de palabras para descubrir qué palabras "activan" perfiles de dificultad similares entre todos los participantes.
- **Anidamiento (nestedness):** determinar si el patrón de fijación es anidado (los lectores avanzados fijan un subconjunto estricto de las palabras que fijan los lectores novatos).

---

## Estado actual

**Pendiente de implementación.** Esta carpeta aún no contiene código. Este README define la estructura objetivo que deberá seguirse cuando se implemente.

---

## Estructura objetivo

Debe replicar exactamente el esquema de `networks/cognitive-load/` (ver `networks/cognitive-load/README.md` como referencia canónica):

```
networks/bipartite/
├── README.md                 # Este archivo
├── bipartite.py              # Entry point CLI: subcomandos `build` y `stats`
├── core/                     # Librería interna
│   ├── __init__.py           # Re-exporta SOLO la API pública
│   ├── data_io.py            # Carga de fijaciones, agregación participante↔palabra
│   ├── network_builder.py    # Construcción de la red bipartita + proyecciones
│   ├── persistence.py        # Serialización + metadata.json para caché
│   ├── paths.py              # Hash de archivos
│   ├── visualization.py      # Plots bipartitos y de proyección
│   └── stats/                # Métricas: nestedness, grados, proyección
└── output/                   # Builds generados (gitignored)
```

### Subcomandos CLI previstos

- `bipartite.py build --subid ... --lang ... --trialid ... --wave ... --groupby ... --edge-weight {dur,nfix,skip} --outdir ...`
- `bipartite.py stats --load <build_dir>`

Los flags compartidos deben extraerse a un helper `_add_shared_args`, igual que en `cogload.py`.

### API pública esperada en `core/__init__.py`

```python
from .network_builder import build_bipartite_network, build_prefix
from .stats import bipartite_metrics_from_cache
from .persistence import save_built_network, load_built_network, check_cache_fresh
from .data_io import load_all_fixations
```

---

## Cómo se ejecutará (una vez implementado)

```bash
# Desde la raíz del repositorio
python networks/bipartite/bipartite.py build --trialid 4 --wave 1 --edge-weight dur
python networks/bipartite/bipartite.py stats \
  --load networks/bipartite/output/bipartite_trial4_w1_dur
```

---

## Formato de `output/<build>/`

Mismo esquema que `cognitive-load/`:

| Archivo | Descripción |
|---------|-------------|
| `nodes_participants.csv` | Nodos de Tipo A con métricas agregadas. |
| `nodes_words.csv` | Nodos de Tipo B con métricas agregadas. |
| `edges.csv` | Aristas participante ↔ palabra con pesos (`dur` / `nfix` / `skip`). |
| `graph.pkl` | Objeto `networkx.Graph` bipartito serializado. |
| `network.graphml` | Formato GraphML (abrible en Gephi/Cytoscape). |
| `projection_words.graphml` | Proyección al conjunto de palabras. |
| `metadata.json` | Parámetros + hashes de fuentes. |
| `plots/` | Visualizaciones. |

---

## Convenciones y restricciones

Esta red heredará las convenciones obligatorias del esquema común (entry point delgado, `core/` con API pública, persistencia con `metadata.json`, argumentos compartidos) y la lista consolidada de cosas que **no** se deben hacer. Ver [`networks/README.md`](../README.md).

Adicional específico de esta red:

- **No** olvidar la marca de bipartito al construir el grafo (`networkx.is_bipartite` debe pasar); usar `networkx.bipartite` explícitamente.

---

## Referencias

- Estructura de referencia: `networks/cognitive-load/README.md`.
- Esquema común y guidelines para nuevas redes: [`networks/README.md`](../README.md).
- Fuente de datos: `data/MECO-L2_version-2.2/.../joint_l2_fixation_trimmed_report_2.2.csv`.
- Convención de contribución: `CONTRIBUTING.md`.
