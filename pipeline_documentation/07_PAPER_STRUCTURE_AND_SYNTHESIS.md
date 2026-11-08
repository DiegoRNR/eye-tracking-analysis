# Estructura Propuesta para el Paper Científico / Tesis
## Guía de Redacción Académica y Síntesis de Resultados

Este documento organiza los hallazgos del proyecto en un formato listo para la redacción de un artículo de investigación para revistas científicas de primer cuartil (*Journal of Memory and Language*, *Cognition*, *Studies in Second Language Acquisition* o *Language Learning*).

---

## 1. Título y Resumen Sugeridos

### Título Propuesto:
> **"From Eye-Movement Transition Networks to Reader Archetypes: How Linguistic Distance, Lexical Competence, and Gaze Dynamics Explain Second Language Reading Comprehension"**  
> *(De las Redes de Transición Ocular a los Arquetipos Lectores: Cómo la Distancia Lingüística, la Competencia Léxica y la Dinámica de la Mirada Explican la Comprensión en Segunda Lengua)*

### Abstract (Borrador Estructurado):
> Reading in a second language (L2) imposes severe demands on visual decoding, memory integration, and strategic monitoring. While scalar eye-tracking metrics (e.g., mean fixation duration) provide isolated indicators of cognitive load, they obscure how readers navigate the syntactic and lexical structure of texts in real time. In this study, we bridge network science and psychometric modeling using the Multilingual Eye-tracking Corpus (MECO Waves 1 and 2; $N = 1,032$ participants across 28 diverse language cohorts). 
> First, by projecting sequential eye fixations onto a unified 11-node fused Part-of-Speech network, we demonstrate that cross-linguistic reading proximity (measured via Jensen-Shannon Distance to native English readers) is a specific marker of L2 proficiency ($r = +0.43, p = 0.029$; and $r = +0.59$ in struggling readers), while structural linguistic distance (URiEL) leaves a significant footprint in native reading ($r \approx 0.63 - 0.71$) that partially converges in L2 ($r \approx 0.30 - 0.44$).
> Second, hierarchical regression establishes the incremental predictive validity of online eye-tracking beyond extensive offline batteries ($\Delta R^2 = 1.0\%, p = 0.003$).
> Third, we identify two complementary cognitive mechanisms: a psycholinguistic mediation pathway where vocabulary indirectly drives comprehension by accelerating real-time fixation speed (Sobel $Z = 3.702, p = 0.00021$, explaining $21.6\%$ of the total effect), and a compensatory moderation mechanism ($\beta_{\text{int}} = -0.108, p < 0.0001$) whereby regressive saccades drastically improve comprehension for low-vocabulary readers ($\beta = +0.844$) but remain neutral for proficient readers.
> Finally, unsupervised $k$-means clustering in a 2D PCA space (capturing $65.9\%$ of behavioral variance) discovers four stable reader archetypes: *Native-like/Efficient* ($27.7\%$), *Strategic/Compensator* ($23.7\%$), *Intermediate/Moderate* ($32.2\%$), and *Blocked/Impaired* ($16.4\%$). Together, these findings support a dynamic, multilevel model of bilingual reading where cognitive compensation and lexical automaticity dynamically shape comprehension success.

---

## 2. Estructura de Secciones del Artículo

### Sección 1: Introducción (*Introduction*)
1. **1.1 El Reto de la Lectura en L2:**
   - Cita de la *Simple View of Reading* (Hoover & Gough) y la hipótesis de la *Lexical Quality* (Perfetti).
   - El conflicto entre la decodificación ascendente (*bottom-up*) y la integración descendente (*top-down*).
2. **1.2 Más Allá de las Métricas Escalares:**
   - La limitación de promediar duraciones de fijación: se pierde la sintaxis y el orden temporal.
   - Justificación de la ciencia de redes para modelar transiciones entre clases gramaticales.
3. **1.3 Dimensión Translingüística y Distancia Tipológica:**
   - El rol de la distancia lingüística (URiEL) y la transferencia de hábitos oculomotores de la L1 a la L2.
4. **1.4 Preguntas de Investigación e Hipótesis:**
   - $H_1$: ¿Leer como un nativo predice la comprensión en L2?
   - $H_2$: ¿Aporta el eye-tracking información predictiva incremental sobre los tests de papel y lápiz?
   - $H_3$: ¿Media la duración de fijación el efecto del vocabulario?
   - $H_4$: ¿Son las regresiones un error de lectura o una compensación estratégica?
   - $H_5$: ¿Emergen arquetipos naturales de lectores bilingües?

---

### Sección 2: Metodología (*Methods*)
1. **2.1 Participantes y Corpus MECO:**
   - Descripción de las Waves 1 y 2 ($28$ cohortes, $N = 1,032$).
   - Cohortes nativos de control (`en_ca`, `en_uk`).
2. **2.2 Materiales y Procedimiento:**
   - Los 12 textos expositivos estandarizados.
   - Evaluación de comprensión mediante preguntas de opción múltiple.
3. **2.3 Clasificación NLP y Espacio de 11 Nodos Fused:**
   - Herramientas (spaCy, Stanza, Jieba, CKIP).
   - Definición de los 11 nodos (Content vs. Function words).
4. **2.4 Construcción de Grafos y Distancia Jensen-Shannon:**
   - Modos `temporal` y `regression`.
   - Formulación del MDS 2D clásico de Torgerson.
5. **2.5 Batería de Diferencias Individuales:**
   - LEAP-Q, Nation Vocab (40 ítems), LexTALE, TOWRE SWE & PDE, CFT-20, Spelling.
6. **2.6 Modelado Estadístico:**
   - Regresión jerárquica OLS, prueba de mediación de Sobel, modelos de moderación con términos de interacción, reducción PCA y clustering $k$-means.

---

### Sección 3: Resultados (*Results*)
*Organizados exactamente de acuerdo con los 4 pilares analíticos y sus figuras:*

1. **3.1 Redes de Transición Ocular y Alineamiento Translingüístico:**
   - Matriz de adyacencia de transiciones y distancias JSD.
   - MDS 2D: relación entre cercanía nativa y comprensión ($r = 0.43, p = 0.029$; Q1: $r = 0.59, p = 0.0015$).
   - Efecto de la distancia URiEL en L1 ($r = 0.63 - 0.71$) vs. L2 ($r = 0.30 - 0.44$).
2. **3.2 Validez Incremental del Eye-Tracking (The Grand Cross):**
   - Presentación de los 4 modelos jerárquicos ($R^2$ de $3.7\%$ a $25.3\%$).
   - Demostración de la ganancia incremental ($\Delta R^2 = 1.0\%, p = 0.003, \Delta \text{AIC} = -2.9$).
3. **3.3 Mecanismos Cognitivos Subyacentes:**
   - **Mediación Sobel:** Vocabulario $\to$ Duración de fijación $\to$ Comprensión ($Z = 3.702, p = 0.00021$, figura 2A).
   - **Compensación por Relectura:** Interacción Vocabulario $\times$ Regresiones ($\beta = -0.108, p < 0.0001$, figuras 2B1 y 2B2).
   - **Calibración Metacognitiva:** Sesgo de subestimación predicho por la distancia lingüística ($\beta = +0.116, p = 0.0064$, figuras 4A, 4B y 4C).
4. **3.4 Descubrimiento de Arquetipos Lectores en L2:**
   - Biplot PCA en 2D (PC1 Fluidez 47.3% vs. PC2 Relectura 18.6%, figura 3A).
   - Cuantificación empírica de los 4 clusters: Nativoide ($27.7\%$), Estratégico ($23.7\%$), Intermedio ($32.2\%$) y Bloqueado ($16.4\%$) (figuras 3B, 3C y tablas asociadas).

---

### Sección 4: Discusión (*Discussion*)
1. **4.1 Reconceptualización de las Regresiones Oculares:**
   - Tradicionalmente, una alta tasa de regresiones se interpreta como señal de dificultad o lectura pobre.
   - Nuestros hallazgos demuestran que es un **mecanismo adaptativo y funcional**: los lectores con vocabulario bajo que releen activamente alcanzan niveles de comprensión comparables a lectores promedio, salvando el cuello de botella léxico.
2. **4.2 La Trampa Metacognitiva de las Lenguas Distantes:**
   - Discusión sobre por qué hablantes de lenguas no indoeuropeas sufren del "síndrome del impostor L2" a pesar de tener un rendimiento objetivo adecuado.
3. **4.3 Implicaciones Pedagógicas y de Diagnóstico:**
   - Cómo diseñar sistemas de tutoría inteligente basados en eye-tracking: no obligar a todos los lectores a leer rápido o sin volver atrás; entrenar el monitoreo estratégico en lectores con bajo léxico.
4. **4.4 Limitaciones y Trabajo Futuro:**
   - Muestra predominantemente universitaria; textos expositivos controlados vs. lectura libre en la web.

---

## 3. Asignación de Figuras y Tablas al Manuscrito

| Elemento en el Paper | Archivo Asociado | Mensaje Central para el Lector |
| :--- | :--- | :--- |
| **Tabla 1 (Metodología)** | `campos_clustering_input.png` | Detalle operacional de las variables de entrada del modelo. |
| **Figura 1 (MDS Redes)** | `output/reading_patterns_dashboard.html` | El mapa translingüístico y la convergencia hacia el patrón nativo. |
| **Tabla 2 (Modelos)** | `hierarchical_regression_models.csv` | El Grand Cross: validez incremental del eye-tracking. |
| **Figura 2 (Mediación)** | `figure_2a_mediation_path_diagram.png` | El vocabulario ayuda porque reduce el tiempo de fijación ocular. |
| **Figura 3 (Compensación)** | `figure_2b1_compensation_quartiles_grid.png` | Releer solo beneficia a quienes tienen bajo vocabulario (Q1). |
| **Figura 4 (Arquetipos PCA)** | `figure_3a_reader_archetypes_pca.png` | Biplot 2D con los vectores de carga y los 4 clusters de lectores. |
| **Tabla 3 (Perfiles)** | `tabla_resumen_arquetipos.png` | Parámetros exactos (media $\pm$ DE) de cada arquetipo lector. |
| **Figura 5 (Calibración)** | `figure_4b_calibration_by_language.png` | Sesgo metacognitivo según lengua materna y distancia lingüística. |

