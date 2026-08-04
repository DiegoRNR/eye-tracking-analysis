# Eye-Tracking Analysis

Proyecto orientado al análisis de datos de eye-tracking del corpus **MECO L2** mediante técnicas de **ciencia de redes**. El objetivo es modelar distintos aspectos del proceso de lectura como grafos y extraer métricas que permitan comparar estrategias lectoras para obtener patrones que expliquen niveles de comprensión, tendencias según lengua natural, etc.

---

## Estructura del proyecto

```
eye-tracking-analysis/
├── data/                           # Datos crudos presentados en OSF
│   ├── MECO-L2_version-2.2/        # Dataset MECO L2 v2.2 (wave-1, wave-2)
│   ├── benchmark/                  # Textos MECO y métricas léxicas de referencia
│   ├── by.sub.l1.csv               # Agregado por sujeto y L1
│   ├── POPEYE_DATA_SPEC.md         # Especificación del esquema de datos
│   └── README.md                   # Documentación detallada del dataset
│
├── networks/                       # Cada red vive en su propia carpeta
│   ├── README.md                   # Listado de redes existentes e indicaciones para agregar nuevas redes
│   ├── cognitive-load/             # Red de carga cognitiva pupilodilatada
│   ├── scanpath/                   # Red de transición de sacadas (en transición)
│   ├── alignment/                  # Alineamiento scanpath ↔ sintaxis/semántica (pendiente)
│   └── bipartite/                  # Red bipartita participante ↔ palabra (pendiente)
│
├── scripts/                        # Utilidades auxiliares
│   └── convert_rda_to_csv.R        # Conversión .rda → .csv para R
│
├── pyproject.toml                  # Dependencias del proyecto Python
├── uv.lock                         # Lockfile reproducible (gestionado con `uv`)
├── .python-version                 # Versión de Python fijada (≥3.11)
├── CONTRIBUTING.md                 # Convención de ramas, estilo y flujo de PRs
└── README.md                       # Este archivo
```

### ¿Qué hace cada red?

| Carpeta | Qué modela | Estado | README |
|---------|------------|--------|--------|
| `networks/cognitive-load/` | Carga cognitiva via ΔPS entre palabras consecutivas; cascadas pupilares y modularidad del esfuerzo. | Implementada | [README](networks/cognitive-load/README.md) |
| `networks/scanpath/` | Transiciones de sacadas entre palabras; reciprocidad, regresiones, PageRank. | En transición al esquema estándar | [README](networks/scanpath/README.md) |
| `networks/alignment/` | Compara la red de sacadas con la estructura semántica/sintáctica del texto. | Pendiente | [README](networks/alignment/README.md) |
| `networks/bipartite/` | Red participante ↔ palabra con métricas de fijación como pesos. | Pendiente | [README](networks/bipartite/README.md) |

> **Para correr una red, ve a su carpeta y lee su `README.md`.** Ahí encontrarás la estructura interna, los flags del CLI, el formato de salida y las convenciones que se deben respetar.
>
> Para agregar una red nueva, las convenciones obligatorias (estructura de carpetas, entry point delgado, `core/` con API pública, persistencia, etc.) están centralizadas en [`networks/README.md`](networks/README.md).

### Datos

Los archivos pesados (`*.csv`, `*.rds`) y las salidas generadas (`networks/*/output/`) están listados en `.gitignore` y **no se versionan**.

- [`data/README.md`](data/README.md) — descripción general del dataset.
- [`data/POPEYE_DATA_SPEC.md`](data/POPEYE_DATA_SPEC.md) — especificación del esquema de columnas de los reportes de fijación de MECO L2 (basada en el paquete R `popEye`).

---

## Setup del entorno

### Requisitos

- **Python ≥ 3.11** (ver `.python-version`).
- **R** (cualquier versión razonablemente reciente) en el `PATH`, necesario **únicamente** para correr `scripts/convert_rda_to_csv.R` y materializar los CSV a partir de los RDA. Si los CSV ya están generados, R no es necesario.
- **`uv`** (recomendado) para gestionar el entorno Python; opcional, se puede usar `venv` + `pip`.

### Opción A — con `uv` (recomendado)

```bash
# Instalar uv (si no está): https://docs.astral.sh/uv/
uv sync
source .venv/bin/activate
```

`uv sync` crea `.venv/`, instala las dependencias desde `pyproject.toml` + `uv.lock` y deja el proyecto editable.

### Opción B — con `venv` + `pip`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Convertir datos `.rda` → `.csv`

Los pipelines de Python (`networks/*`) leen los reportes de MECO L2 en formato **CSV**, no RDA. Si los CSV no están ya materializados bajo `data/`, ejecuta el script de conversión (requiere R en `PATH`):

```bash
Rscript scripts/convert_rda_to_csv.R
```

Sin argumentos, procesa recursivamente todos los `.rda`/`.RData` bajo `data/` y deja los `.csv` junto a cada fuente. Para un archivo específico:

```bash
Rscript scripts/convert_rda_to_csv.R data/MECO-L2_version-2.2/.../archivo.rda
```

---

## Quickstart

La red **cognitive-load** es la única completamente alineada al esquema estándar. Ejemplo mínimo:

```bash
# 1. Construir la red para un participante en un trial específico
python networks/cognitive-load/cogload.py build --subid du_7 --trialid 4 --wave 1

# 2. Calcular estadísticas sobre el build (caché; no reconstruye)
python networks/cognitive-load/cogload.py stats \
  --load networks/cognitive-load/output/cogload_trial4_w1_zscore_sequential_subdu_7
```

Salida esperada:

```
networks/cognitive-load/output/cogload_trial4_w1_zscore_sequential_subdu_7/
├── nodes.csv
├── edges.csv
├── graph.pkl
├── network.graphml
├── metadata.json
├── plots/
└── network_interactive.html
```

Para flags completos y ejemplos adicionales ver [`networks/cognitive-load/README.md`](networks/cognitive-load/README.md).

---

## Scripts auxiliares

- `scripts/convert_rda_to_csv.R` — convierte archivos `.rda`/`.RData` de R a `.csv`. Útil cuando se necesitan datos en formato tabular para los pipelines Python.
  ```bash
  Rscript scripts/convert_rda_to_csv.R data/MECO-L2_version-2.2/.../archivo.rda
  # sin argumentos: procesa todos los .rda bajo data/
  ```

---

## Contribución

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md) para la convención de ramas (`feature/`, `fix/`, `data/`, `refactor/`, `chore/`, `docs/`), estilo de código y flujo de Pull Requests.
