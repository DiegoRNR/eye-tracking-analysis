# Red de Regresiones por Familia Lingüística (Regression-Comparison Networks)

## Descripción

Red **dirigida de sacadas** construida reconstruyendo el scanpath en **orden
temporal** (`start`), con las aristas **tipadas** según la dirección del
movimiento ocular. A diferencia de `cognitive-load/` y `language-comparison/`
—que ordenan las fijaciones por `wordnum` y por tanto solo pueden producir
aristas hacia adelante— esta red conserva las **regresiones** y las
**refijaciones**, que son los predictores clásicos de dificultad en lectura L2.

**Estructura de la red**

- **Nodos:** palabras (`wordnum:word`), con métricas de fijación, refijación y
  regresión entrante/saliente.
- **Aristas dirigidas, tipadas:**
  - `forward` — `v.wordnum > u.wordnum`.
  - `regression-local` — `v.wordnum < u.wordnum`, misma oración.
  - `regression-global` — `v.wordnum < u.wordnum`, cruza frontera de oración.
  - Las **refijaciones** (`v.wordnum == u.wordnum`) no generan self-loop: se
    acumulan en el nodo (`n_refix`) para no distorsionar los grados.
- **Pesos:** `rate` (fracción de lectores que hacen la transición — el único
  comparable entre familias), `count`, `n_sessions`, `amplitude`
  (`|Δwordnum|`), `mean_dur_target`.
- **Metadatos de familia:** heredados de `language-comparison`: `lang_group`,
  `languages`, `n_participants`, `n_with_accuracy`, `accuracy`.

**Librerías:** `networkx`, `pandas`, `numpy`, `matplotlib`, `pyvis`. Sin
dependencias nuevas respecto de `pyproject.toml`.

> Especificación completa y evidencia preliminar:
> [`propuesta-red-regresiones.html`](../language-comparison/propuesta-red-regresiones.html).

---

## Estado

**Implementados `build` y `compare`.** Pendiente `stats` (ver "Qué falta").

| Subcomando | Qué hace | Salida |
|------------|----------|--------|
| `build` | Construye y persiste la red de una familia (o de todas). | `output/regcomp_trial<...>_<familia>/` |
| `compare` | Reutiliza o construye una red por familia y genera un reporte HTML comparativo. | `output/comparison_trial<...>_w<...>/` |

---

## Cómo ejecutar

Desde la raíz del repositorio:

```bash
# 1. Construir todas las familias presentes en el wave
python networks/regression-comparison/regcomp.py build \
  --lang-group all --trialid 4 --wave 1

# 2. Reporte comparativo del wave (reutiliza los builds existentes)
python networks/regression-comparison/regcomp.py compare --trialid 4 --wave 1

# 3. Abrir el reporte
start networks/regression-comparison/output/comparison_trial4_w1/comparison_report.html
```

`compare` construye por su cuenta las familias que falten, así que el paso 1 es
opcional. El CSV de fijaciones se lee **una sola vez** para todas las familias
del wave.

> **Importante:** abrir `comparison_report.html` **desde su carpeta** para que
> los iframes relativos a cada `network_interactive.html` carguen.

### Flags

| Flag | Descripción | Default |
|------|-------------|---------|
| `--lang-group <grupo>` | Familia lingüística o `all`. | `germanic` |
| `--trialid <1-12>` | ID del texto. | `1` |
| `--wave {1,2}` | Ola. **No** se admite `both`: son cohortes independientes. | `1` |
| `--edge-weight {rate,count,dur}` | Peso principal de arista. | `rate` |
| `--min-rate <float>` | Poda aristas soportadas por menos de esa fracción de lectores. | `0.02` |
| `--no-filter-discordant` | Conserva sesiones cuyo texto no coincide con el del trial. | — |
| `--outdir <ruta>` | Carpeta raíz de salida. | `networks/regression-comparison/output` |
| `--no-interactive` | Omite `network_interactive.html`. | — |

`build` toma además `--lang-group`; `compare` toma `--families <f1> <f2> ...`
(por defecto todas las del wave) y `--no-reuse` para reconstruir todo en vez de
reutilizar los builds existentes.

### Salida de `compare`

```
output/comparison_trial4_w1/
├── comparison_report.html    # Tabla + plots + una pestaña por familia con su red
├── comparison_summary.csv    # accuracy + métricas por familia
└── plots/
    ├── comparison_accuracy.png            # Comprensión media por familia
    ├── comparison_saccade_types.png       # % regresión y % refijación
    └── comparison_regression_profile.png  # reg_in_rate por wordnum
```

### Cómo leer la tabla del reporte

El HTML es deliberadamente **simple**: tabla, plots y una pestaña por familia,
sin texto explicativo. Las salvedades para interpretarlo viven aquí.

| Columna | ¿Comparable entre familias? | Por qué |
|---------|------------------------------|---------|
| `accuracy` | Sí | Comprensión global del participante (24 preguntas). No varía con `trialid`. |
| `% regresión`, `% refijación` | **Sí** | Proporciones por sacada: independientes del tamaño del grupo. |
| `reciprocidad` | **Sí** | Fracción de aristas con su inversa; es una proporción. |
| `nodos` | Sí | 142 en todos los builds sanos de `trial 4`; un valor distinto delata texto discordante. |
| `aristas`, `avance`, `regresión` | **No** | Recuentos afectados por la poda `--min-rate`; ver [Aviso sobre `--min-rate`](#aviso-sobre---min-rate-y-comparabilidad). |
| `lectores` | — | Contexto, no métrica. |
| `concord. MECO` | — | Diagnóstico de reconstrucción; ver [Validación cruzada](#validación-cruzada-contra-meco). `1.000` = exacta. |

Cuando una familia pierde sesiones por el filtro de texto discordante, el
recuento queda en `comparison_summary.csv` (`n_sessions_discarded`) y el detalle
en el `metadata.json` de cada build (`discarded_sessions`). En `trial 4` wave 2
son `se_38` en germánica y `bp_23` en románica; ver
[Filtro de sesiones con texto discordante](#2-filtro-de-sesiones-con-texto-discordante).

---

## Diferencias de implementación respecto de `language-comparison`

Tres decisiones que no son cosméticas:

### 1. No se filtra por `ps`

`language-comparison/core/data_io.py` descarta las fijaciones sin pupila
válida. Aquí **no**: eliminar una fijación rompe la cadena temporal e inventa
una transición directa entre las dos que la rodean. `ps` se conserva como
atributo opcional del nodo.

Consecuencia práctica: **`ch_s` (chino, Singapur) entra en la red**. No tiene
ningún dato de pupila, por lo que `language-comparison` lo excluye por completo
(sus builds llevan el marcador `nops-ch_s`). Aquí la familia sino-tibetana pasa
de 43 a **69 participantes**.

### 2. Filtro de sesiones con texto discordante

Se descartan las sesiones cuyo `max(ianum)` **supera** la moda del trial. Es el
defecto documentado en la auditoría: `bp_23` y `se_38` tienen `trialid = 4`
apuntando a un pasaje de 187 palabras, lo que mezclaba dos textos en una sola
red (292 y 299 nodos en `language-comparison`). Aquí ambos builds quedan en 142
nodos.

Solo se descarta **por exceso**, nunca por defecto: un `max(ianum)` menor que la
moda significa que ese lector no fijó las últimas palabras del pasaje (140 o 141
de 142 es habitual), no que haya leído otro texto.

### 3. Clave de sesión robusta a `uniform_id` ausente

Los 17 participantes daneses de wave 2 sin `uniform_id` caen a `subid`. Cuidado
al tocar esto: pandas puede leer esas columnas con dtype `str` **nullable**,
donde el valor ausente es `pd.NA` y no la cadena `'nan'`; comparar con `.ne()`
devuelve `NA` en vez de `False` y `.where()` conserva el `NA`. El efecto es que
los 17 daneses colapsan en **una sola sesión**, sus scanpaths se concatenan y
cada costura inventa una regresión enorme. Ver el comentario en
`core/data_io.py`.

---

## Validación cruzada contra MECO

MECO ya trae las regresiones etiquetadas en `word.reg.out` / `word.reg.out.to`.
El builder compara su reconstrucción temporal contra esas columnas y guarda el
índice de Jaccard en `metadata.json` como `reg_source_agreement`.

**Resultado: 1.000 en los 14 builds de `trial 4`**, salvo sino-tibetana (0.787),
y esa excepción está explicada: `ch_s` tiene el 100 % de `word.reg.*` en `NA`
—el mismo bloque de columnas vacío que `ps`—, así que MECO no aporta etiquetas
para ese laboratorio. Aislando `ch_t`, la concordancia vuelve a 1.000.

La reconstrucción del scanpath es, por tanto, exacta allí donde puede
verificarse.

---

## Formato de `output/<build>/`

Prefijo: `regcomp_trial<T>_w<W>_<edge-weight>_<grupo>[_langs-<códigos>]`.

| Archivo | Contenido |
|---------|-----------|
| `nodes.csv` | Palabras con `fix_count`, `dwell_total`, `mean_dur`, `first_pass_dur`, `n_refix`, `refix_rate`, `reg_in`, `reg_out`, `reg_in_rate`, `reg_out_rate`, `seen_rate`, `mean_ps`. |
| `edges.csv` | Aristas con `type`, `count`, `n_sessions`, `rate`, `amplitude`, `mean_dur_target`. |
| `graph.pkl` | `networkx.DiGraph` serializado. |
| `network.graphml` | GraphML para Gephi/Cytoscape. |
| `metadata.json` | Parámetros, `accuracy`, conteos por tipo de arista, `reciprocity`, `reg_source_agreement`, sesiones descartadas y hashes SHA-256 de las fuentes. |
| `network_interactive.html` | Red interactiva (pyvis). |

### La red interactiva

Mismo estilo que `language-comparison` (título, panel de leyenda fijo, menú de
filtros, atenuación al seleccionar un nodo). Cambian los canales, porque cambian
las variables:

| Elemento | Codifica |
|----------|----------|
| **Color de nodo** | `reg_in_rate` (viridis): regresiones recibidas por lector. Amarillo = palabra a la que se vuelve. |
| **Tamaño de nodo** | `fix_count`. |
| **Color de arista** | `type`: azul = avance, naranja = regresión intra-oración, verde = regresión inter-oración. |
| **Grosor de arista** | `rate`: fracción de lectores que hacen la transición. |

---

## Restricciones

Además de las convenciones de [`networks/README.md`](../README.md):

- **No** ordenar fijaciones por `wordnum` en ningún punto del builder. El orden
  es `start`; ordenar por posición es el defecto que esta red corrige.
- **No** comparar recuentos de aristas entre familias sin rarefactar (ver abajo).
- **No** emitir self-loops por refijación.
- **No** mezclar refijaciones y regresiones en una sola clase de arista: frente
  a la comprensión tienen signo opuesto y se cancelan.
- **No** usar `ps` crudo para ningún peso.

### Aviso sobre `--min-rate` y comparabilidad

`--min-rate` **no** vuelve comparables los recuentos de aristas entre familias:
con `0.02`, una familia de 25 lectores no puede resolver por debajo del 4 % y no
poda nada, mientras que una de 176 exige 4 lectores por arista. El efecto es que
los recuentos quedan hoy **anti**correlacionados con `n` (germánica W1, n=176 →
707 aristas; semítica, n=45 → 1 087).

Son comparables entre familias las **proporciones por sacada**
(`regression_share`, `refix_share`) y `reciprocity`. Para comparar tamaño o
densidad hace falta rarefacción a `n` común, todavía no implementada.

---

## Qué falta

1. `stats` — métricas rarefactadas, sumideros de regresión (PageRank sobre el
   subgrafo de regresión), bucles de re-lectura, amplitud, modularidad.
2. `participant_metrics.csv` — una fila por lector con tasas de regresión y
   refijación + `accuracy`, para correlacionar con n ≈ 540 en vez de con 7
   medias de familia.
3. Plots estáticos por build (`visualization.py`).

---

## Referencias

- Propuesta y evidencia: [`propuesta-red-regresiones.html`](../language-comparison/propuesta-red-regresiones.html).
- Esquema estándar: [`networks/README.md`](../README.md).
- Red de referencia canónica: [`networks/cognitive-load/README.md`](../cognitive-load/README.md).
- Capa de agrupación reutilizada: [`networks/language-comparison/README.md`](../language-comparison/README.md).
- Especificación de columnas: `data/POPEYE_DATA_SPEC.md` (bloque `word.reg.*`).
