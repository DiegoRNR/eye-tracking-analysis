# Clasificación Integral de Palabras (Chino Mandarín Simplificado (简体中文))

> **Nota metodológica:** Este documento y su dataset asociado forman parte del benchmark multilingüe de eye-tracking MECO adaptado para **Chino Mandarín Simplificado (简体中文)**. Sigue de forma rigurosa la taxonomía lingüística, la escala logarítmica de Zipf y las métricas de predictibilidad/surprisal.

## 1. Resumen General del Corpus

- **Total de ocurrencias (tokens):** 1,513
- **Palabras léxicas únicas (vocabulario):** 795
- **Cantidad de textos (trials):** 12
- **Cantidad de oraciones:** 91
- **Total de caracteres chinos (字数):** 2,791
- **Promedio de caracteres por palabra:** 1.84

---

## 2. Agrupación por Tipo de Palabra (Categorías Gramaticales)

| Categoría Gramatical | Frecuencia Absoluta | Porcentaje (%) | Ejemplos Representativos |
| :--- | :--- | :--- | :--- |
| **Sustantivo** | 501 | 33.11% | *塞缪尔, 莫尔斯, 今天, 身份, 莫尔斯电码* |
| **Verbo** | 314 | 20.75% | *是, 学习, 包括, 告诉, 花* |
| **Partícula** | 145 | 9.58% | *的, 了, 着, 地, 等* |
| **Adverbio** | 123 | 8.13% | *最, 一直, 赶来, 才, 最快* |
| **Pronombre** | 95 | 6.28% | *之一, 他, 这, 那些, 这个* |
| **Conjunción** | 90 | 5.95% | *和, 但, 虽然, 并, 由于* |
| **Adjetivo** | 74 | 4.89% | *著名, 杰出, 遥远, 好, 重要* |
| **Preposición** | 68 | 4.49% | *对, 在, 向, 以, 被* |
| **Numeral** | 52 | 3.44% | *一位, 许多, 1825, 年, 一名* |
| **Modismo (成语)** | 28 | 1.85% | *悲痛欲绝, 发明家, 有生之年, 追溯到, 生态系统* |
| **Otro** | 21 | 1.39% | *得, 很, 单一, 额外, 年幼* |
| **Clasificador** | 2 | 0.13% | *个, 只* |

### Distribución Funcional vs. Léxica (实词 vs. 虚词)

En la lingüística china tradicional y la psicolingüística de lectura ocular, la distinción entre **Palabras de Contenido (实词 - Shící)** y **Palabras Funcionales (虚词 - Xūcí)** es el determinante primordial de la duración de fijación y el salteo sacádico:

| Tipo Léxico | Frecuencia | Porcentaje (%) | Función en Procesamiento Lector |
| :--- | :--- | :--- | :--- |
| **Palabra de Contenido** | 945 | 62.46% | Portan significado referencial y semántico (sustantivos, verbos, adjetivos, clasificadores). Mayor fijación cognitiva. |
| **Palabra Funcional** | 568 | 37.54% | Relaciones sintácticas y gramaticales (partículas, preposiciones/coverbos, conjunciones, pronombres). Muy alta tasa de salteo visual (*skipping*). |

---

## 3. Clasificación por Frecuencia de la Palabra (Escala Zipf)

Calculada sobre el corpus léxico de referencia compatible con SUBTLEX-CH (Cai & Brysbaert, 2010) y la escala psicométrica estandarizada de Zipf (Van Heuven et al., 2014):

$$\text{Zipf} = \log_{10}(\text{frecuencia por millón}) + 3$$

| Categoría de Frecuencia | Rango Zipf | Cantidad de Palabras | Porcentaje (%) | Frecuencia por Millón Típica |
| :--- | :--- | :--- | :--- | :--- |
| **Muy Alta Frecuencia** | >= 6.0 | 439 | 29.02% | > 1.000 / millón |
| **Alta Frecuencia** | 5.0 - 5.99 | 474 | 31.33% | 100 - 1.000 / millón |
| **Media Frecuencia** | 4.0 - 4.99 | 374 | 24.72% | 10 - 100 / millón |
| **Baja Frecuencia** | < 4.0 | 226 | 14.94% | < 10 / millón (términos especializados) |

---

## 4. Clasificación por Longitud en Caracteres (字数)

A diferencia de las lenguas alfabéticas donde la longitud se mide en letras variables, en chino mandarín **cada carácter es una unidad morfofonológica estricta (1 carácter = 1 sílaba)**:

| Categoría de Longitud | Caracteres (字) | Cantidad de Palabras | Porcentaje (%) | Ejemplos Típicos |
| :--- | :--- | :--- | :--- | :--- |
| **Monosilábica (1 carácter)** | 1字 | 464 | 30.67% | *最, 的, 是, 和* |
| **Disilábica (2 caracteres)** | 2字 | 908 | 60.01% | *今天, 著名, 身份, 电报* |
| **Polisilábica (3+ caracteres)** | 3字+ | 141 | 9.32% | *塞缪尔, 莫尔斯, 莫尔斯电码, 发明者* |

---

## 5. Predictibilidad, Surprisal de Shannon y Lectura Ocular

La predictibilidad en contexto fue calculada mediante un modelo de lenguaje de trigramas interpolado ($P(w_i \mid w_{i-1}, w_{i-2})$) y Surprisal de Shannon ($S(w_i) = -\log_2 P$ en bits):

| Nivel de Predictibilidad | Cantidad de Palabras | Porcentaje (%) | Surprisal Promedio (bits) |
| :--- | :--- | :--- | :--- |
| **Alta Predictibilidad** | 1422 | 93.99% | 0.62 bits |
| **Media Predictibilidad** | 91 | 6.01% | 6.27 bits |

### Proyecciones Psicofísicas de Eye-Tracking en Chino

De acuerdo con los hallazgos en eye-tracking durante lectura en chino (Rayner et al., 2007; Yan et al., 2006; Bai et al., 2008), las métricas del lector responden a la longitud de la palabra y el surprisal:

| Categoría Longitud | Tasa de Salteo Estimada (*Skip Rate*) | Gaze Duration Estimada (ms) | Tiempo Total Estimado (ms) |
| :--- | :--- | :--- | :--- |
| **Monosilábica (1 carácter)** | 56.5% | 184.0 ms | 278.6 ms |
| **Disilábica (2 caracteres)** | 20.3% | 253.6 ms | 376.1 ms |
| **Polisilábica (3+ caracteres)** | 3.2% | 339.5 ms | 486.9 ms |

---

## 6. Diccionario de Datos del Archivo CSV Generado

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `trialid` | Entero | Identificador del texto en el corpus [1, 12] |
| `sentnum` | Entero | Número de oración dentro del texto |
| `ianum` | Entero | Número secuencial de la palabra dentro del texto |
| `word` | Texto | Palabra tal como se presenta (con puntuación contigua) |
| `word_clean` | Texto | Palabra limpia en caracteres chinos sin puntuación |
| `largo_caracteres` | Entero | Longitud en caracteres chinos (字数) |
| `num_silabas` | Entero | Cantidad de sílabas (en chino: 1 carácter = 1 sílaba) |
| `categoria_largo` | Texto | Monosilábica (1字), Disilábica (2字), Polisilábica (3+字) |
| `freq_corpus` | Entero | Frecuencia absoluta en el corpus léxico de referencia |
| `zipf_freq` | Decimal | Frecuencia psicométrica estandarizada de Zipf [1.0, 7.6] |
| `categoria_frecuencia` | Texto | Muy Alta, Alta, Media o Baja Frecuencia |
| `categoria_gramatical` | Texto | Sustantivo, Verbo, Adjetivo, Clasificador (量词), Partícula (助词), etc. |
| `tipo_lexico` | Texto | Palabra de Contenido (实词) vs. Palabra Funcional (虚词) |
| `subtipo_gramatical` | Texto | Clasificación gramatical detallada |
| `pos_tag_universal` | Texto | Etiqueta Universal Dependencies (NOUN, VERB, ADJ, PART, etc.) |
| `pos_tag_chinese` | Texto | Etiqueta original Jieba / Penn Chinese Treebank (n, v, a, q, u, etc.) |
| `predictibilidad_prob` | Decimal | Probabilidad condicional n-gram $P(w_i \mid \text{contexto})$ |
| `surprisal_bits` | Decimal | Cantidad de información de Shannon en bits ($-\log_2 P$) |
| `categoria_predictibilidad` | Texto | Alta, Media o Baja Predictibilidad |
| `expected_skip_rate` | Decimal | Probabilidad esperada de salteo ocular visual |
| `expected_firstpass_dur_ms` | Decimal | Duración estimada de primera pasada / gaze duration (ms) |
| `expected_total_dur_ms` | Decimal | Duración estimada de tiempo de lectura total (ms) |

Fin del reporte.
