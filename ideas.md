1. Red de Transición de Fijaciones Oculares (Scanpath Networks)
Construir el mapa de navegación visual de los lectores sobre el texto.

Estructura de la Red:
Nodos: Palabras (word / wordnum) o frases dentro de un texto (trialid).
Aristas Dirigidas y Ponderadas ($w_{ij}$): Frecuencia de saltos (sacadas) directos donde la vista se mueve de la palabra $i$ a la palabra $j$.
Librerías Python: networkx, igraph, pyvis (para visualización interactiva HTML).
Métricas y Análisis Relevantes:
In-Degree / Out-Degree: Identificar palabras "ancla" que reciben la mayor cantidad de fijaciones o revisiones.
PageRank / Betweenness Centrality: Encontrar palabras que actúan como "cuellos de botella cognitivos" o puntos críticos donde el procesamiento lingüístico se detiene.
Reciprocidad (Reciprocity): Cuantificar la tasa de regresiones locales inmediatas ($A \to B \to A$).
Comparación de Redes (L1 vs. L2 o por Idioma Materno lang): Comparar la matriz de adyacencia y la entropía de la red entre hablantes nativos de distintas lenguas maternas (ej. español vs. alemán leyendo en inglés).

2. Redes Bipartitas de Fijación (Participante – Palabra / Texto)
Modelar las interacciones entre los lectores y las características léxicas.

Estructura de la Red:
Nodos de Tipo A: Participantes (uniform_id).
Nodos de Tipo B: Palabras clave o pasajes (trialid / word).
Aristas (Ponderadas): Duración total de fijación (dur), número de fijaciones (nfix) o probabilidad de salteo (skip).
Librerías Python: networkx.bipartite, scipy.sparse.
Métricas y Análisis Relevantes:
Proyección Bipartita: Proyectar la red al conjunto de palabras para descubrir qué palabras "activan" perfiles de dificultad similares entre todos los participantes.
Anidamiento (Nestedness): Determinar si el patrón de fijación es anidado (es decir, si los lectores avanzados fijan un subconjunto estricto de las palabras que fijan los lectores novatos).

3. Red de Alineamiento entre Escaneo Ocular y Estructura Sintáctica/Semántica
Comparar la red de fijaciones reales con la estructura natural del lenguaje.

Estructura de la Red:
Red A (Ocular): Red de transiciones de fijación reales de los participantes sobre las palabras del pasaje.
Red B (Semántica/Sintáctica): Red donde los nodos son las mismas palabras, pero las aristas representan la similitud semántica de sus embeddings (usando modelo spaCy / Transformers) o dependencias gramaticales.
Librerías Python: spacy / sentence-transformers (para embeddings/sintaxis), networkx, scipy.stats.
Métricas y Análisis Relevantes:
Distancia entre Grafos (Graph Distance / Spectral Distance): Medir la distancia entre la Matriz de Adyacencia de lectura y la Matriz de Adyacencia Semántica.
Jaccard Similarity de Aristas: Cuantificar qué porcentaje de las sacadas visuales siguen la estructura gramatical vs. regresiones no lineales causadas por sobrecarga cognitiva.

4. El diámetro pupilar (ps en el dataset de fijaciones joint_l2_fixation_trimmed_report_2.2.csv) es un indicador directo del esfuerzo mental, activación del Locus Coeruleus y carga de memoria de trabajo.

Estructura de la Red:
Nodos: Palabras u oraciones.
Pesos de los Nodos: Magnitud de la dilatación pupilar ($PS$) durante la fijación en dicha palabra.
Aristas: Transición entre palabras ponderada por el $\Delta PS = |PS_{word_2} - PS_{word_1}|$.
Métricas Clave:
Cascadas de Carga Cognitiva (Cognitive Load Cascades): Detectar si un pico de pupila en una palabra de alta dificultad (ej. palabra rara) propaga alta carga pupilar a las 3 o 4 palabras siguientes en la red.
Modularidad del Esfuerzo: Agrupar el texto en zonas de "alto estrés cognitivo" vs "zonas de procesamiento fluido".
Librerías Python: scipy.signal, networkx, seaborn.