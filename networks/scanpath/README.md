# Red de Transición de Fijaciones Oculares (Scanpath Networks)

## Descripción

La **Red de Transición de Fijaciones Oculares (Scanpath Network)** modela el mapa de navegación visual de los lectores a medida que procesan un texto. En lugar de tratar las fijaciones como mediciones aisladas de duración, este enfoque representa el proceso de lectura como una **red dirigida y ponderada** donde:

- **Nodos:** Palabras del texto (identificadas por su posición `wordnum` y su cadena de texto `word`).
- **Aristas Dirigidas ($u \to v$):** Transiciones consecutivas del ojo entre palabras (sacadas).
- **Pesos de Aristas ($w_{uv}$):** Frecuencia acumulada de saltos directos desde la palabra $u$ hacia la palabra $v$.

Este modelo permite aplicar algoritmos de **Ciencia de Redes** para caracterizar la fluidez de lectura, detectar cuellos de botella cognitivos y comparar las estrategias de lectura entre hablantes nativos (L1) y lectores de segunda lengua (L2).

---

## Estructura del Código

El script principal se encuentra en [`build_scanpath_network.py`](file:///c:/Code/eye-tracking-analysis/networks/scanpath/build_scanpath_network.py).

```
networks/scanpath/
├── README.md                   # Documentación de la red scanpath
├── build_scanpath_network.py   # Script ejecutable en Python
└── output/                     # Carpeta donde se guardan los reportes y gráficos
```

---

## Métricas Calculadas

### Métricas a Nivel de Nodo
- **In-Degree y Out-Degree Ponderados:** Cantidad de transiciones que llegan o salen de una palabra. Identifican palabras "ancla" o de alta re-fijación.
- **Centralidad de Intermediación (Betweenness Centrality):** Mide el grado en que una palabra actúa como puente o "cuello de botella cognitivo" en los caminos de navegación visual.
- **PageRank:** Identifica palabras que concentran la atención del lector, considerando no solo el número de fijaciones sino la relevancia de las palabras desde las que el lector realiza regresiones.
- **Pupil Size Promedio (`mean_ps`):** Diámetro pupilar durante las fijaciones a la palabra (indicador de carga mental).

### Métricas a Nivel de Red
- **Reciprocidad ($R$):** Proporción de aristas bidireccionales ($A \to B$ y $B \to A$), cuantificando la tasa de regresiones inmediatas.
- **Proporción de Regresiones (Regression Ratio):** Porcentaje de sacadas dirigidas hacia palabras anteriores ($v < u$) respecto al total de transiciones.
- **Entropía del Scanpath (Shannon Entropy):** Cuantifica la previsibilidad vs. caoticidad del patrón de navegación sobre el texto.
- **Densidad de la Red:** Grado de interconexión entre las palabras del texto.

---

## Instrucciones de Uso

### 1. Ejecución Básica (Texto 1 por Defecto)
```bash
python networks/scanpath/build_scanpath_network.py
```
*(Utilizar `py` en Windows si `python` no está aliasado)*:
```powershell
py networks/scanpath/build_scanpath_network.py
```

### 2. Filtrar por Idioma Materno (L1)
Analizar la red del grupo de participantes con lengua materna Española (`es`) leyendo el Texto ID 3:
```powershell
py networks/scanpath/build_scanpath_network.py --lang es --trialid 3
```

### 3. Filtrar por Participante Individual
Generar la red de un participante específico (`du_4`) en el Texto ID 9:
```powershell
py networks/scanpath/build_scanpath_network.py --subid du_4 --trialid 9
```

### 4. Especificar Carpeta de Salida Personalizada
```powershell
py networks/scanpath/build_scanpath_network.py --trialid 1 --outdir networks/scanpath/output/trial_1
```

---

## Archivos Generados en `output/`

Tras ejecutar el script, se generarán los siguientes archivos en la carpeta de salida:

1. **`scanpath_*_global_metrics.csv`**: Tabla con métricas globales de la red (nodos, aristas, densidad, entropía, reciprocidad, ratio de regresión).
2. **`scanpath_*_node_metrics.csv`**: Tabla por palabra con conteo de fijaciones, tiempo total/promedio, tamaño de pupila, grados y centralidades.
3. **`scanpath_*_edge_list.csv`**: Lista de aristas dirigidas, pesos, tipo de transición (`forward`, `regression`, `refixation`) y tiempo promedio de salto.
4. **`scanpath_*_network.graphml`**: Archivo de red en formato GraphML, listo para abrir y visualizar en **Gephi** o **Cytoscape**.
5. **`scanpath_*_visualization.png`**: Gráfico estático generado con Matplotlib que muestra el mapa de palabras y las transiciones.
6. **`scanpath_*_interactive.html`**: Red interactiva HTML generada con Pyvis (permite arrastrar nodos, hacer zoom y explorar detalles al pasar el cursor).


python networks\scanpath\scanpath_network.py --trialid 1 --name Prueba2s