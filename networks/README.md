# networks/

Cada tipo de red del proyecto vive en su propia subcarpeta, siguiendo un esquema común. La red **`cognitive-load/`** es la referencia canónica del esquema: cualquier red nueva debe replicar su estructura.

---

## Redes existentes

| Carpeta | Qué modela | Estado |
|---------|------------|--------|
| [`cognitive-load/`](cognitive-load/README.md) | Carga cognitiva via ΔPS entre palabras consecutivas; cascadas pupilares y modularidad del esfuerzo. | Implementada |
| [`scanpath/`](scanpath/README.md) | Transiciones de sacadas entre palabras; reciprocidad, regresiones, PageRank. | En transición al esquema estándar |
| [`alignment/`](alignment/README.md) | Compara la red de sacadas con la estructura semántica/sintáctica del texto. | Pendiente |
| [`bipartite/`](bipartite/README.md) | Red participante ↔ palabra con métricas de fijación como pesos. | Pendiente |

> Para correr una red, abre su `README.md`. Ahí encontrarás flags, ejemplos y el formato de salida.

---

## Cómo agregar una red nueva

1. Crear la carpeta `networks/<nombre>/`.
2. Crear su `README.md` siguiendo el mismo formato que las existentes (Descripción, estado, estructura objetivo, cómo se ejecutará, formato de `output/`, referencias).
3. Implementar la estructura descrita abajo.

### Estructura de carpetas (canónica)

```
networks/<nombre>/
├── README.md             # Específico de la red (qué modela, métricas, ejemplos)
├── <nombre>.py           # Entry point CLI delgado (solo argparse + delegación)
├── core/                 # Librería interna; TODA la lógica vive aquí
│   ├── __init__.py       # Re-exporta SOLO la API pública (con __all__)
│   ├── data_io.py
│   ├── network_builder.py
│   ├── persistence.py    # Serialización + metadata.json con sha256
│   ├── paths.py          # Mapeo de archivos de datos, file_sha256
│   ├── visualization.py      # Plots base
│   ├── interactive_viz.py    # Visualización con pyvis
│   └── stats/            # Si aplica: submódulo de métricas
└── output/               # Builds generados (gitignored)
```

Referencia: [`networks/cognitive-load/`](cognitive-load/) y su `README.md`.

### Convenciones obligatorias

**1. Entry point delgado con subparsers**

`<nombre>.py` solo contiene `argparse` con subparsers (mínimo `build` y `stats`) y delega a funciones de `core/`. La lógica de negocio **nunca** va en el entry point.

**2. `core/` como librería con API pública**

`core/__init__.py` re-exporta únicamente la API pública usando `__all__`. Helpers internos no se exponen. El entry point hace `from core import build_*, stats_from_cache, ...`.

**3. Persistencia determinística con caché**

- Cada build se guarda en `output/<prefix>/` donde `prefix` se construye con un helper `build_prefix()` a partir de los parámetros (trialid, wave, groupby, subid, lang, etc.).
- Contenido de cada build: `nodes.csv`, `edges.csv`, `graph.pkl`, `network.graphml`, `metadata.json`, `plots/`, y opcionalmente `network_interactive.html`.
- `metadata.json` registra los `source_files` con su hash SHA-256. Una función `check_cache_fresh()` compara el hash actual contra el guardado para invalidar builds obsoletos.
- `output/` está en `.gitignore` (regla `networks/*/output/`).

**4. Argumentos compartidos**

Los flags recurrentes (`--subid`, `--lang`, `--trialid`, `--wave`, `--groupby`, `--normalize`, `--outdir`) se extraen a un helper (`_add_shared_args`) para que `build` y `stats` los compartan sin duplicación.

**5. Rutas relativas**

Usar siempre rutas relativas al repositorio. No se admiten rutas absolutas (ver `CONTRIBUTING.md`).

---

## Qué NO hacer

Aplica a **toda** red en `networks/`:

- **No** desviarse del esquema establecido sin actualizar este README y el README de la red afectada.
- **No** poner lógica de red en el entry point; todo va en `core/`.
- **No** exponer helpers internos en `core/__init__.py`; solo la API pública.
- **No** usar rutas absolutas (`C:/Users/...`, `/home/...`, etc.).
- **No** commitear `output/` ni artefactos pesados.
- **No** añadir dependencias nuevas sin actualizar `pyproject.toml` y `uv.lock`.
- **No** saltar la escritura de `metadata.json`; es la base de la invalidación de caché y proporciona trazabilidad de las redes generadas.
