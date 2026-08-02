Redes Bipartitas de Fijación (Participante – Palabra / Texto)
Modelar las interacciones entre los lectores y las características léxicas.

Estructura de la Red:
Nodos de Tipo A: Participantes (uniform_id).
Nodos de Tipo B: Palabras clave o pasajes (trialid / word).
Aristas (Ponderadas): Duración total de fijación (dur), número de fijaciones (nfix) o probabilidad de salteo (skip).
Librerías Python: networkx.bipartite, scipy.sparse.
Métricas y Análisis Relevantes:
Proyección Bipartita: Proyectar la red al conjunto de palabras para descubrir qué palabras "activan" perfiles de dificultad similares entre todos los participantes.
Anidamiento (Nestedness): Determinar si el patrón de fijación es anidado (es decir, si los lectores avanzados fijan un subconjunto estricto de las palabras que fijan los lectores novatos).