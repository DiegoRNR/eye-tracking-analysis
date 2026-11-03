# Guía Exhaustiva de Variables de Diferencias Individuales
## Proyecto de Análisis de Lectura en Segunda Lengua (MECO L2 & LEAP-Q)

Este documento detalla cada una de las variables de **diferencias individuales**, **antecedentes sociolingüísticos**, **habilidades psicométricas**, **medidas de eye-tracking** y **comprensión lectora** empleadas en los análisis de este proyecto.

---

## Índice de Contenidos
1. [Variables de Antecedentes y Sociodemográficas (LEAP-Q y Tipología)](#1-variables-de-antecedentes-y-sociodemográficas-leap-q-y-tipología)
   - `exposure_english` (% Exposición al inglés)
   - `english_start_age` (Edad de inicio en inglés)
   - `english_fluent_read_age` (Edad de lectura fluida en inglés)
   - `english_domain_read` (Autoevaluación de competencia lectora)
   - `formal_education_years` (Años de educación formal)
   - `linguistic_distance` (Distancia lingüística L1-L2)
2. [Batería de Habilidades Lingüísticas y Léxicas L2](#2-batería-de-habilidades-lingüísticas-y-léxicas-l2)
   - `vocab.t2.5` / `vocab` (Vocabulario Receptivo de Paul Nation)
   - `lextale` (Test de Proficiencia Léxica en Inglés)
   - `TOWRE_nonword` / PDE (Eficiencia en Decodificación Fonémica)
   - `TOWRE_word` / SWE (Eficiencia en Lectura de Palabras Reales)
   - `spelling` (Conocimiento Ortográfico)
   - `language_skill_composite` (Índice Compuesto de Competencia L2)
3. [Capacidad Cognitiva General y Actitudinal](#3-capacidad-cognitiva-general-y-actitudinal)
   - `cft20` (Inteligencia Fluida no verbal - Cattell)
   - `motiv` (Motivación hacia la L2)
4. [Métricas de Procesamiento Ocular en Línea (Eye-Tracking)](#4-métricas-de-procesamiento-ocular-en-línea-eye-tracking)
   - `mean_fix_dur` (Duración Media de Fijación)
   - `regression_rate` (Tasa de Regresiones Sacádicas)
   - `skipping_rate` (Tasa de Salto de Palabras)
   - `total_fix_count` (Cantidad Total de Fijaciones)
5. [Variable Criterio / Outcome](#5-variable-criterio--outcome)
   - `accuracy` (Comprensión Lectora L2)
6. [Tabla Resumen Consolidada](#6-tabla-resumen-consolidada)

---

## 1. Variables de Antecedentes y Sociodemográficas (LEAP-Q y Tipología)

Estas variables provienen del cuestionario estandarizado **LEAP-Q** (*Language Experience and Proficiency Questionnaire*, Marian et al., 2007) y de bases de datos lingüísticas cuantitativas (URiEL).

### `% Exposición al Inglés`
* **Nombre en dataset:** `exposure_english`
* **Instrumento:** Cuestionario LEAP-Q (Sección de estimación de porcentaje de uso diario del idioma).
* **Rango / Unidad:** Porcentaje continuo de $0\%$ a $100\%$ ($M = 37.8\%, DE = 23.9\%$).
* **Constructo medido:** Intensidad de la práctica comunicativa real y cotidiana en el idioma inglés en el entorno del participante (medios, estudios, trabajo, interacción social).
* **Interpretación práctica:** Un valor de $60\%$ indica que el participante pasa la mayor parte de su día expuesto al inglés. 
* **Relación con comprensión:** Correlación directa muy baja ($r = 0.02$). La exposición no garantiza comprensión si no se ha consolidado una base de vocabulario suficiente; sin embargo, correlaciona positivamente con el vocabulario ($r = 0.23$) y LexTALE ($r = 0.28$).

---

### `Edad de Inicio en Inglés`
* **Nombre en dataset:** `english_start_age`
* **Instrumento:** Cuestionario LEAP-Q (Pregunta: *"Age when you began acquiring English"*).
* **Rango / Unidad:** Años cumplidos (Rango observado: $1.0$ a $25.0$ años, $M = 9.2$ años, $DE = 3.6$ años).
* **Constructo medido:** Ventana de adquisición temprana de la segunda lengua (edad de adquisición o *AoA - Age of Acquisition*).
* **Interpretación práctica:** Quienes iniciaron antes de los 7 años suelen desarrollar patrones fonológicos y gramaticales más automatizados. Quienes comenzaron en la adolescencia o adultez dependen en mayor medida de mecanismos explícitos de aprendizaje.
* **Relación con comprensión:** Correlación negativa ($r = -0.11, p < 0.001$). A mayor edad de inicio, se tiende a un menor vocabulario ($r = -0.18$), menor LexTALE ($r = -0.24$) y notablemente menor autoconfianza lectora ($r = -0.32$).

---

### `Edad de Lectura Fluida en Inglés`
* **Nombre en dataset:** `english_fluent_read_age`
* **Instrumento:** Cuestionario LEAP-Q (Pregunta: *"Age when you became fluent reading English"*).
* **Rango / Unidad:** Años cumplidos (Rango observado: $4.0$ a $25.0$ años, $M = 14.1$ años, $DE = 3.8$ años).
* **Constructo medido:** Consolidación de la competencia lectora autónoma en la segunda lengua.
* **Interpretación práctica:** Marca el momento subjetivo y biográfico en que el lector dejó de descifrar el texto palabra por palabra y comenzó a procesar ideas completas en inglés sin esfuerzo consciente.

---

### `Autoevaluación de Competencia Lectora`
* **Nombre en dataset:** `english_domain_read`
* **Instrumento:** Cuestionario LEAP-Q (Escala Likert de 0 o 1 a 10 puntos).
* **Rango / Unidad:** Escala ordinal/continua de $1.0$ a $10.0$ ($M = 7.7, DE = 1.6$).
* **Constructo medido:** Metacognición y autoconcepto de autoeficacia lectora en inglés.
* **Interpretación práctica:** Refleja la percepción del participante sobre su soltura para leer textos académicos y cotidianos en inglés.
* **Relación con comprensión:** Correlación positiva moderada ($r = 0.20, p < 0.001$). Se utiliza para calcular el **Gap de Calibración Metacognitiva** ($\text{Autoevaluación}_z - \text{Accuracy}_z$).

---

### `Años de Educación Formal`
* **Nombre en dataset:** `formal_education_years`
* **Instrumento:** Cuestionario LEAP-Q (Pregunta sobre años acumulados de educación formal).
* **Rango / Unidad:** Años continuos ($M = 14.8$ años, $DE = 2.4$ años; equivalente a educación universitaria intermedia).
* **Constructo medido:** Nivel de escolarización y entrenamiento académico formal.

---

### `Distancia Lingüística L1-L2`
* **Nombre en dataset:** `linguistic_distance`
* **Instrumento:** Base de datos tipológica **URiEL** (Littell et al., 2017), integrando distancia filogenética, inventario fonológico y similitud sintáctica respecto al inglés.
* **Rango / Unidad:** Escala normalizada de $0.00$ (muy similar al inglés, ej. holandés $= 0.17$) a $1.00$ (muy lejana, ej. japonés $= 0.68$, hebreo, turco).
* **Constructo medido:** Magnitud de la disparidad estructural entre la lengua materna del participante y la lengua inglesa meta.
* **Interpretación práctica:** A mayor distancia lingüística, menor transferencia positiva directa de estructuras sintácticas y cognados.
* **Relación con comprensión:** Correlación bivariada neutra con la comprensión ($r = -0.03$), pero predice significativamente la adquisición de vocabulario ($r = -0.19$) y el sesgo metacognitivo (los lectores de lenguas distantes tienden a subestimarse).

---

## 2. Batería de Habilidades Lingüísticas y Léxicas L2

Pruebas psicométricas estandarizadas de competencia en inglés administradas de manera controlada e individual en el consorcio MECO.

### `Vocabulario Receptivo (Paul Nation)`
* **Nombre en dataset:** `vocab.t2.5` (y en algunas tablas `vocab`)
* **Instrumento:** *Vocabulary Size Test* adaptado por Paul Nation (batería de 40 ítems representativos de bandas de frecuencia léxica).
* **Rango / Unidad:** Escala discreta de $0$ a $40$ puntos ($M = 30.7, DE = 9.8$; Min: $3$, Max: $40$).
* **Constructo medido:** Tamaño y amplitud del lexicón mental pasivo del lector en inglés (número estimado de familias de palabras conocidas).
* **Interpretación práctica:** Puntuaciones $\ge 36$ indican un vocabulario equivalente a un nivel C1-C2 universitario. Puntuaciones $< 20$ representan una limitación léxica severa.
* **Relación con comprensión:** **El predictor individual más potente de toda la batería ($r = 0.46, p < 10^{-60}$)**. Actúa además como modulador del comportamiento ocular (efecto de compensación por relectura).

---

### `Proficiencia Léxica (LexTALE)`
* **Nombre en dataset:** `lextale`
* **Instrumento:** *Lexical Test for Advanced Learners of English* (Lemhöfer & Broersma, 2012). Test de decisión léxica por computadora con 60 ítems (40 palabras reales en inglés y 20 pseudopalabras verosímiles).
* **Rango / Unidad:** Porcentaje corregido de aciertos de $0\%$ a $100\%$ mediante la fórmula:
  $$\text{LexTALE} = \frac{\% \text{ Palabras Correctas} + \% \text{ Pseudopalabras Rechazadas}}{2}$$
  ($M = 76.9\%, DE = 12.5\%$; Min: $45.0\%$, Max: $100.0\%$).
* **Constructo medido:** Rapidez y precisión del acceso léxico y discriminación ortográfico-semántica en L2.
* **Interpretación práctica:** Al penalizar fuertemente las "falsas alarmas" (decir que una palabra inventada existe), evita el sesgo de adivinación. Es un indicador estándar y universal del nivel de competencia global en inglés.
* **Relación con comprensión:** Fuerte correlación positiva ($r = 0.41, p < 10^{-46}$).

---

### `Eficiencia en Decodificación Fonémica (PDE)`
* **Nombre en dataset:** `TOWRE_nonword` (etiquetado como **PDE**)
* **Instrumento:** Subtest *Phonemic Decoding Efficiency* de la batería **TOWRE** (*Test of Word Reading Efficiency*, Torgesen, Wagner, & Rashotte).
* **Rango / Unidad:** Número de pseudopalabras pronunciadas correctamente en voz alta en un límite estricto de **45 segundos** ($M = 48.6, DE = 12.1$).
* **Constructo medido:** Eficiencia de la vía subléxica / ensamblaje fonológico (conversión grafema-a-fonema) sin apoyo de la memoria semántica ni del contexto.
* **Interpretación práctica:** Evalúa si el lector domina las reglas mecánicas de pronunciación de combinaciones de letras inglesas desconocidas.
* **Relación con comprensión:** Correlación moderada ($r = 0.21, p < 10^{-12}$). Los lectores adultos ya han automatizado este proceso, por lo que la decodificación fonológica explica menor varianza en la comprensión que el vocabulario.

---

### `Eficiencia en Lectura de Palabras Reales (SWE)`
* **Nombre en dataset:** `TOWRE_word` (etiquetado como **SWE**)
* **Instrumento:** Subtest *Sight Word Efficiency* de la batería **TOWRE**.
* **Rango / Unidad:** Número de palabras reales en inglés leídas en voz alta correctamente en **45 segundos** ($M = 82.4, DE = 14.5$).
* **Constructo medido:** Velocidad y automaticidad de la vía léxica directa (reconocimiento visual instantáneo de palabras frecuentes e irregulares).
* **Interpretación práctica:** Refleja la fluidez con la que el lector activa palabras impresas sin necesidad de deletrearlas fonológicamente.
* **Relación con comprensión:** Correlación positiva moderada ($r = 0.30$).

---

### `Conocimiento Ortográfico (Spelling)`
* **Nombre en dataset:** `spelling`
* **Instrumento:** Test estandarizado de dictado y reconocimiento de ortografía en inglés.
* **Rango / Unidad:** Puntaje bruto de aciertos ortográficos ($M = 27.3, DE = 6.4$).
* **Constructo medido:** Calidad, especificidad y riqueza de las representaciones ortográficas almacenadas en la memoria léxica a largo plazo (hipótesis de *Lexical Quality* de Perfetti).
* **Relación con comprensión:** Correlación positiva sustancial ($r = 0.37, p < 10^{-35}$). Saber escribir con precisión las palabras correlaciona fuertemente con la claridad con la que se identifican al leer.

---

### `Índice Compuesto de Competencia L2`
* **Nombre en dataset:** `language_skill_composite`
* **Instrumento:** Índice psicométrico construido mediante el promedio de puntuaciones estandarizadas ($z$-scores) de las cuatro pruebas nucleares:
  $$\text{Composite} = \frac{z_{\text{lextale}} + z_{\text{vocab}} + z_{\text{TOWRE\_word}} + z_{\text{TOWRE\_nonword}}}{4}$$
* **Rango / Unidad:** Puntuación estandarizada continua ($M = 0.00, DE = 0.82$).
* **Constructo medido:** Factor latente general de aptitud y dominio del idioma inglés (reducción de error de medida específico de una sola prueba).
* **Relación con comprensión:** Muy alta correlación ($r = 0.51$). Se utiliza en modelos multivariados como control de proficiencia general.

---

## 3. Capacidad Cognitiva General y Actitudinal

### `Inteligencia Fluida no Verbal (CFT-20)`
* **Nombre en dataset:** `cft20`
* **Instrumento:** *Cattell Culture Fair Intelligence Test* (CFT-20-R). Batería de matrices y series de figuras geométricas con reglas abstractas, independiente del lenguaje.
* **Rango / Unidad:** Puntaje de respuestas correctas ($M = 31.2, DE = 5.8$).
* **Constructo medido:** Capacidad de razonamiento lógico inductivo, memoria de trabajo y resolución de problemas abstractos en tiempo real (Factor $g$ fluido).
* **Interpretación práctica:** Permite aislar si las dificultades del lector se deben a limitaciones cognitivas generales o a un déficit puramente lingüístico en inglés.
* **Relación con comprensión:** Correlación positiva baja-moderada ($r = 0.14, p < 0.001$). Demuestra que en la lectura en L2 la cognición general es secundaria frente a las habilidades específicas del idioma.

---

### `Motivación hacia la L2`
* **Nombre en dataset:** `motiv`
* **Instrumento:** Escala tipo Likert sobre motivación académica, intrínseca e instrumental para dominar y leer en inglés.
* **Rango / Unidad:** Escala continua ($M = 4.2, DE = 0.7$).
* **Constructo medido:** Disposición afectiva y persistencia ante el material escrito en la segunda lengua.

---

## 4. Métricas de Procesamiento Ocular en Línea (Eye-Tracking)

Métricas continuas registradas mediante eye-trackers de alta resolución ($1000\text{ Hz}$ / $500\text{ Hz}$) mientras el participante leía los textos expositivos del protocolo MECO L2.

### `Duración Media de Fijación`
* **Nombre en dataset:** `mean_fix_dur`
* **Instrumento:** Eye-Tracking (MECO L2).
* **Rango / Unidad:** Milisegundos (ms) ($M = 222.5\text{ ms}, DE = 31.3\text{ ms}$; Min: $144.9$, Max: $453.8$).
* **Constructo medido:** Esfuerzo de decodificación e integración léxica local en tiempo real.
* **Interpretación práctica:** Fijaciones cortas ($\sim 200\text{ ms}$) reflejan lectura experta, fluida y automatizada. Fijaciones prolongadas ($> 250\text{ ms}$) evidencian sobrecarga cognitiva y lentitud en el acceso semántico.
* **Rol en modelos:** **Media el 21.6% del efecto del vocabulario sobre la comprensión** (Sobel $Z = 3.702, p = 0.0002$).

---

### `Tasa de Regresiones Sacádicas`
* **Nombre en dataset:** `regression_rate`
* **Instrumento:** Eye-Tracking (MECO L2).
* **Rango / Unidad:** Proporción / porcentaje de movimientos sacádicos dirigidos hacia atrás ($M = 15.1\%, DE = 4.5\%$; Min: $4.0\%$, Max: $34.0\%$).
* **Constructo medido:** Monitoreo metacognitivo en línea y estrategia activa de reparación de rupturas de comprensión.
* **Interpretación práctica:** Volver la mirada a palabras o líneas previas cuando una oración no concuerda con el modelo mental.
* **Rol en modelos:** **Modulador compensatorio clave** ($\beta_{\text{interacción}} = -0.108, p < 0.0001$). Releer beneficia significativamente a lectores con bajo vocabulario ($\beta = +0.84, p = 0.0001$), pero es innecesario para lectores con léxico nativoide.

---

### `Tasa de Salto de Palabras`
* **Nombre en dataset:** `skipping_rate`
* **Instrumento:** Eye-Tracking (MECO L2).
* **Rango / Unidad:** Proporción de palabras no fijadas directamente ($M = 28.4\%, DE = 6.2\%$).
* **Constructo medido:** Procesamiento parafoveal y predicción contextual de palabras de alta frecuencia y función (artículos, preposiciones).

---

### `Cantidad Total de Fijaciones`
* **Nombre en dataset:** `total_fix_count`
* **Instrumento:** Eye-Tracking (MECO L2).
* **Rango / Unidad:** Número entero de fijaciones por texto.
* **Constructo medido:** Carga y costo cognitivo global invertido para completar la lectura.

---

## 5. Variable Criterio / Outcome

### `Precisión de Comprensión Lectora L2`
* **Nombre en dataset:** `accuracy`
* **Instrumento:** Cuestionario MECO L2 aplicado inmediatamente después de cada texto (preguntas de opción múltiple de 4 opciones que evalúan hechos literales e inferencias integrativas profundas).
* **Rango / Unidad:** Proporción de aciertos de $0.00$ a $1.00$ ($M = 71.8\%, DE = 13.5\%$; Min: $8.3\%$, Max: $100.0\%$).
* **Constructo medido:** Éxito en la construcción de un **modelo de situación** coherente y fidedigno del texto en memoria episódica.
* **Uso en el proyecto:** Variable dependiente ($Y$) en todos los modelos de regresión jerárquica, análisis de mediación, clustering no supervisado y calibración metacognitiva.

---

## 6. Tabla Resumen Consolidada

| Variable | Código en Dataset | Categoría | Instrumento | Rango Típico | Media $\pm$ DE | Correlación con Comprensión ($r$) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Vocabulario Receptivo** | `vocab.t2.5` | Psicométrica L2 | Test de Nation (40 ítems) | $0 - 40$ | $30.7 \pm 9.8$ | **$+0.46$** ($p < 10^{-60}$) |
| **Proficiencia Léxica** | `lextale` | Psicométrica L2 | LexTALE Test | $0 - 100\%$ | $76.9\% \pm 12.5\%$ | **$+0.41$** ($p < 10^{-46}$) |
| **Ortografía** | `spelling` | Psicométrica L2 | Dictado/Reconocimiento | $0 - 35$ | $27.3 \pm 6.4$ | **$+0.37$** ($p < 10^{-35}$) |
| **Palabras Reales (SWE)** | `TOWRE_word` | Psicométrica L2 | TOWRE - Form A (45 s) | $0 - 104$ | $82.4 \pm 14.5$ | $+0.30$ ($p < 10^{-24}$) |
| **Pseudopalabras (PDE)** | `TOWRE_nonword` | Psicométrica L2 | TOWRE - Form A (45 s) | $0 - 63$ | $48.6 \pm 12.1$ | $+0.21$ ($p < 10^{-12}$) |
| **Autoevaluación Lectora** | `english_domain_read` | LEAP-Q | Escala subjetiva | $1 - 10$ | $7.7 \pm 1.6$ | $+0.20$ ($p < 10^{-11}$) |
| **Inteligencia Fluida** | `cft20` | Cognitiva General | Matrices CFT-20-R | $0 - 46$ | $31.2 \pm 5.8$ | $+0.14$ ($p < 10^{-5}$) |
| **Edad de Inicio** | `english_start_age` | LEAP-Q | Edad biográfica | $1 - 25$ años | $9.2 \pm 3.6$ años | **$-0.11$** ($p < 0.001$) |
| **Distancia Lingüística** | `linguistic_distance` | Tipología L1 | Matriz URiEL | $0.0 - 1.0$ | $0.38 \pm 0.14$ | $-0.03$ ($p = 0.32$, neutra) |
| **% Exposición Diaria** | `exposure_english` | LEAP-Q | Estimación % uso | $0 - 100\%$ | $37.8\% \pm 23.9\%$ | $+0.02$ ($p = 0.52$, neutra) |
| **Duración de Fijación** | `mean_fix_dur` | Eye-Tracking | Eye-Tracker MECO | $140 - 450$ ms | $222.5 \pm 31.3$ ms | **$-0.27$** ($p < 10^{-20}$) |
| **Tasa de Regresiones** | `regression_rate` | Eye-Tracking | Eye-Tracker MECO | $4 - 34\%$ | $15.1\% \pm 4.5\%$ | $+0.04$ ($p = 0.17$, moderador) |
| **Comprensión (Outcome)** | `accuracy` | Criterio Final | Test MECO L2 | $0 - 100\%$ | $71.8\% \pm 13.5\%$ | **$1.00$** (Criterio $Y$) |
