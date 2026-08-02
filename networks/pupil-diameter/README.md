Redes de Carga Cognitiva y Dilatación Pupilar (Pupil-Dilated Cognitive Load Networks)

El diámetro pupilar (ps en el dataset de fijaciones joint_l2_fixation_trimmed_report_2.2.csv) es un indicador directo del esfuerzo mental, activación del Locus Coeruleus y carga de memoria de trabajo.

Estructura de la Red:
Nodos: Palabras u oraciones.
Pesos de los Nodos: Magnitud de la dilatación pupilar ($PS$) durante la fijación en dicha palabra.
Aristas: Transición entre palabras ponderada por el $\Delta PS = |PS_{word_2} - PS_{word_1}|$.
Métricas Clave:
Cascadas de Carga Cognitiva (Cognitive Load Cascades): Detectar si un pico de pupila en una palabra de alta dificultad (ej. palabra rara) propaga alta carga pupilar a las 3 o 4 palabras siguientes en la red.
Modularidad del Esfuerzo: Agrupar el texto en zonas de "alto estrés cognitivo" vs "zonas de procesamiento fluido".
Librerías Python: scipy.signal, networkx, seaborn.