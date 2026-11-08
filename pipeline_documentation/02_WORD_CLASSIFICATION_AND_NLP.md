# Fase 2: Clasificación de Palabras y Procesamiento de Lenguaje Natural (NLP)
## Mapeo al Espacio Universal de 11 Nodos Fused

---

## 1. Motivación Teórica: ¿Por qué clasificar palabras?

El corpus MECO contiene textos con miles de palabras únicas en más de 20 idiomas distintos. Para poder **comparar cuantitativamente el movimiento ocular** entre un lector nativo de hebreo, uno de chino y uno de inglés, es imposible comparar palabras individuales concretas. 

Se requiere proyectar el texto en un **espacio abstracto de roles sintáctico-léxicos** que capture cómo el sistema cognitivo y visual procesa diferentes clases gramaticales.

---

## 2. El Espacio Fused de 11 Categorías

Adoptamos el estándar de **Universal Dependencies (UD)** para el etiquetado morfosintáctico (*UPOS tagging*), colapsando categorías redundantes para evitar matrices de transición esparsas. Esto generó el **Espacio Fused de 11 Nodos**:

| Nodo Fused | UPOS Originales | Naturaleza | Función Cognitiva en Lectura |
| :--- | :--- | :--- | :--- |
| **`NOUN`** | `NOUN`, `PROPN` | Contenido | Núcleos referenciales; alta carga informativa y duración de fijación elevada. |
| **`VERB`** | `VERB`, `AUX` | Contenido | Estructura argumental y eventos; punto crítico para la integración sintáctica. |
| **`ADJ`** | `ADJ` | Contenido | Modificadores semánticos y descriptivos de entidades. |
| **`ADV`** | `ADV` | Contenido | Modificadores circunstanciales de modo, tiempo y lugar. |
| **`PRON`** | `PRON` | Función | Elementos deícticos y correferencia anafórica en memoria de trabajo. |
| **`ADP`** | `ADP` | Función | Preposiciones y posposiciones; marcadores de relaciones sintácticas. |
| **`CONJ`** | `CCONJ`, `SCONJ` | Función | Conectores discursivos (coordinantes y subordinantes); jerarquía lógica. |
| **`PTCL`** | `DET`, `PART` | Función | Artículos determinantes y partículas gramaticales; alta tasa de salto (*skipping*). |
| **`NUM`** | `NUM` | Mixta | Numerales y datos cuantitativos específicos. |
| **`PUNCT`** | `PUNCT` | Estructural | Signos de puntuación; descansos de cláusula y límites oracionales. |
| **`X`** | `X`, `INTJ`, `SYM` | Residual | Palabras extranjeras no clasificadas, símbolos o interjecciones. |

### La Dicotomía Clave: Palabras de Contenido vs. Funcionales
* **Palabras de Contenido (`NOUN`, `VERB`, `ADJ`, `ADV`):** Clases abiertas con alta densidad informativa. Exigen decodificación profunda, generando fijaciones más largas ($>230\text{ ms}$) y raras veces son omitidas.
* **Palabras Funcionales (`ADP`, `CONJ`, `PTCL`, `PRON`):** Clases cerradas de alta frecuencia y longitud corta. Son frecuentemente procesadas en la visión parafoveal y saltadas por lectores expertos.

---

## 3. Pipeline de Herramientas NLP por Familia Lingüística

Para garantizar un etiquetado consistente a través de lenguas tipológicamente heterogéneas, se implementaron flujos especializados en los scripts de `scripts/`:

```
TEXTOS ORIGINALES (L1 y L2)
  │
  ├─► INGLÉS (L2) Y LENGUAS EUROPEAS ALFABÉTICAS:
  │   - Herramienta: spaCy (`en_core_web_sm`, `es_core_news_sm`, `de_core_news_sm`, etc.)
  │   - Salida: Lematización, UPOS y longitud de palabra.
  │
  ├─► LENGUAS CON ESCRITURA NO LATINA O MORFOLOGÍA COMPLEJA:
  │   - Ruso, Griego, Hebreo, Turco, Finés, Vasco, Islandés.
  │   - Herramienta: Stanza (modelos entrenados sobre Universal Dependencies Treebanks).
  │
  ├─► CHINO (Wave 2: Simplificado `ch_s` y Tradicional `ch_t`):
  │   - Reto Metodológico: Ausencia de espacios en blanco entre palabras.
  │   - Herramienta: Jieba para chino simplificado; CKIP Tagger / Stanza para tradicional.
  │   - Segmentación en unidades léxicas antes de la asignación de UPOS.
  │
  └─► HINDI (`hi_iiith`, `hi_iitk`):
      - Segmentación basada en devanagari y Stanza Hindi UD model.
```

---

## 4. Archivos y Datasets Resultantes

Los scripts generaron tablas canónicas de palabras clasificadas guardadas en `data/` y en `data/benchmark/`:

1. **`words_classified.csv`**: Clasificación de las palabras de los 12 textos en inglés (L2).
2. **`words_classified_<lang>_l1.csv`**: Clasificación de los 12 textos nativos para cada una de las 12 lenguas de Wave 1.
3. **`words_classified_chinese_{s,t}_wave2.csv`**: Clasificación de los textos chinos de Wave 2.
4. **`words_classified_<code>_w2l1.csv`**: Clasificación para las 14 variantes de Wave 2 (Vasco, Portugués, Danés, Islandés, Serbio, etc.).

Cada fila de estos archivos detalla:
* `text_id`: Identificador del texto ($1..12$).
* `word_id` / `ianum`: Número de orden de la palabra.
* `word`: Forma superficial de la palabra.
* `upos`: Etiqueta UPOS original.
* `fused_tag`: Uno de los 11 nodos del espacio unificado.
* `length`: Longitud en caracteres.
* `is_content`: Indicador binario ($1$ = contenido, $0$ = función).

