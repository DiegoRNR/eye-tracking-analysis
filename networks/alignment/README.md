Red de Alineamiento entre Escaneo Ocular y Estructura Sintáctica/Semántica
Comparar la red de fijaciones reales con la estructura natural del lenguaje.

Estructura de la Red:
Red A (Ocular): Red de transiciones de fijación reales de los participantes sobre las palabras del pasaje.
Red B (Semántica/Sintáctica): Red donde los nodos son las mismas palabras, pero las aristas representan la similitud semántica de sus embeddings (usando modelo spaCy / Transformers) o dependencias gramaticales.
Librerías Python: spacy / sentence-transformers (para embeddings/sintaxis), networkx, scipy.stats.
Métricas y Análisis Relevantes:
Distancia entre Grafos (Graph Distance / Spectral Distance): Medir la distancia entre la Matriz de Adyacencia de lectura y la Matriz de Adyacencia Semántica.
Jaccard Similarity de Aristas: Cuantificar qué porcentaje de las sacadas visuales siguen la estructura gramatical vs. regresiones no lineales causadas por sobrecarga cognitiva.