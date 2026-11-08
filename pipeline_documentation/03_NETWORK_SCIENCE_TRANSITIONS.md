# Fase 3: Ciencia de Redes y Transiciones entre Tipos de Palabra
## Modelado de la Trayectoria Ocular como un Grafo Dirigido

---

## 1. El Paradigma de Redes en Eye-Tracking

En lugar de tratar las métricas de lectura como promedios estáticos y aislados (ej. tiempo total o número de fijaciones), este proyecto modela la lectura como un **proceso estocástico dinámico**: una caminata sobre un grafo dirigido ponderado en el espacio de tipos de palabras.

$$G = (V, E, W)$$

* **Nodos ($V$):** Las 11 categorías fused (`NOUN`, `VERB`, `ADJ`, `ADV`, `ADP`, `CONJ`, `PRON`, `PTCL`, `NUM`, `PUNCT`, `X`).
* **Aristas Dirigidas ($E$):** Movimientos sacádicos consecutivos donde el ojo se desplaza desde una palabra de tipo $u$ hacia una palabra de tipo $v$ ($u \to v$).
* **Pesos de las Aristas ($W$):** Matriz estocástica de probabilidades de transición:
  $$P_{uv} = \frac{N(u \to v)}{\sum_{k \in V} N(u \to k)}$$
  Donde $\sum_{v} P_{uv} = 1$. Representa la probabilidad condicional de fijar el tipo $v$ dado que la fijación actual está en el tipo $u$.

---

## 2. Los Dos Modos de Red

Para diseccionar la lectura automática de la resolución consciente de problemas, se implementaron dos modos de construcción de red:

```
SECUENCIA DE FIJACIONES: [1: The] -> [2: quick] -> [3: brown] -> [4: fox] -> [2: quick] -> [5: jumps]
                          (PTCL)      (ADJ)        (ADJ)        (NOUN)       (ADJ)        (VERB)
```

1. **Modo `temporal` (Flujo Completo):**
   * Captura **todas las transiciones consecutivas** en el orden en que ocurrieron en el tiempo:
     $\text{PTCL} \to \text{ADJ} \to \text{ADJ} \to \text{NOUN} \to \text{ADJ} \to \text{VERB}$.
   * Incluye la lectura progresiva natural, los saltos hacia adelante y los auto-bucles ($\text{ADJ} \to \text{ADJ}$ cuando se refija la misma palabra o se lee un adjetivo contiguo).
   * Los parpadeos (*blinks*) cortan la secuencia temporal para evitar aristas espurias.
2. **Modo `regression` (Relectura y Reparación):**
   * Filtra estrictamente las sacadas dirigidas **hacia una posición espacial previa** en el texto:
     $\text{pos}(f_{t+1}) < \text{pos}(f_t)$.
   * En el ejemplo: $[\text{NOUN}] \to [\text{ADJ}]$.
   * Aísla el esfuerzo deliberado de re-análisis sintáctico y clarificación cuando el lector detecta una incongruencia en su modelo mental.

---

## 3. Diseño Experimental $2 \times 2$ por Lengua

Para cada uno de los **28 cohortes lingüísticos**, se construyeron 4 redes independientes:

$$\{\text{Sesión L1 Nativa}, \text{Sesión L2 Inglés}\} \times \{\text{Q1 Peores Lectores}, \text{Q4 Mejores Lectores}\}$$

* **División por Cuartiles de Comprensión:** 
  * Dentro de cada lengua, los lectores se dividieron según su precisión de respuestas (*accuracy*).
  * **Q1:** $\le$ percentil 25 (lectores con baja comprensión).
  * **Q4:** $\ge$ percentil 75 (lectores con alta comprensión).
  * El 50% intermedio se descartó en este análisis de contrastes extremos para maximizar la detectabilidad del patrón.

---

## 4. Métricas de Grafo Extraídas

Cada red produce una rica caracterización topológica:

1. **Centralidad de Grado (In-Degree / Out-Degree):**
   * *In-Degree:* Qué tipos de palabras actúan como "atractores" o destinos finales de las sacadas (predominio masivo de `NOUN` y `VERB`).
   * *Out-Degree:* Qué tipos de palabras actúan como plataformas de lanzamiento para saltos rápidos (predominio de `PTCL` y `ADP`).
2. **Reciprocidad de Transición ($u \rightleftharpoons v$):**
   * Mide la frecuencia con que el lector oscila inmediatamente entre dos categorías contiguas ($u \to v \to u$). Marcador de dificultad local de procesamiento.
3. **Carga Cognitiva en Nodos:**
   * La duración media de fijación en cada nodo se embebe como peso nodal, permitiendo detectar qué categorías consumen mayor tiempo de procesamiento en cada idioma.
4. **Entropía de Transición:**
   * Dispersión de las probabilidades de salida de cada nodo. Lectores expertos exhiben patrones más predecibles y enfocados; lectores con dificultades presentan trayectorias dispersas.

---

## 5. Implementación en el Repositorio

El pipeline reside en el módulo [`networks/word-type-transitions/`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/networks/word-type-transitions/):

* `word_type_transitions.py`: CLI principal (`python word_type_transitions.py all --lang all`).
* `core/network_builder.py`: Lógica de construcción de grafos dirigida en NetworkX.
* `core/grouping.py`: Asignación a cuartiles de comprensión Q1 y Q4.
* `core/stats.py`: Cálculo de métricas de red y matrices estocásticas normalizadas.
* `core/visualization.py`: Generación de diagramas de red y heatmaps de adyacencia.
* `output/<lang>/`: Directorios separados por lengua que almacenan las matrices en formato CSV y las figuras visuales.
