# Fase 1: Datos, Preprocesamiento y Control de Calidad
## Corpus MECO (Multilingual Eye-tracking Corpus) Waves 1 y 2

---

## 1. El Corpus MECO: Diseño Experimental

La investigación utiliza los datos del **Multilingual Eye-tracking Corpus (MECO)** (Kuperman et al., 2023; Siegelman et al., 2022), un consorcio global de investigación psicológica y lingüística.

### Diseño de Doble Sesión Intra-Sujeto (L1 y L2)
Cada participante fue evaluado en **dos sesiones de lectura de eye-tracking**:
1. **Sesión L1 (Lengua Nativa):** Lectura de 12 textos expositivos comparables en longitud y dificultad escritos en su propia lengua materna (textos sobre historia, ciencia y naturaleza).
2. **Sesión L2 (Inglés como Segunda Lengua):** Lectura de los mismos 12 textos estandarizados en inglés (pasajes que tratan sobre la invención del código Morse, los teléfonos inteligentes, la biografía de Jane Goodall, etc.), seguidos de preguntas de comprensión.

---

## 2. Cohortes Lingüísticos ($N = 28$ grupos)

El dataset abarca dos olas de recolección (*Wave 1* y *Wave 2*), cubriendo una enorme diversidad tipológica (familias indoeuropeas germánicas, romances, eslavas; urálicas; afroasiáticas semíticas; sino-tibetanas; euskera como lengua aislada):

| Ola | Código | Idioma | País / Centro |
| :--- | :--- | :--- | :--- |
| **Wave 1** | `du` | Holandés | Países Bajos (Nijmegen) |
| Wave 1 | `ee` | Estonio | Estonia (Tartu) |
| Wave 1 | `en` | **Inglés (Nativo - Cohorte 1)** | Canadá (Edmonton) |
| Wave 1 | `fi` | Finés | Finlandia (Turku) |
| Wave 1 | `ge` | Alemán | Alemania (Mannheim) |
| Wave 1 | `gr` | Griego | Grecia / Chipre |
| Wave 1 | `he` | Hebreo | Israel (Haifa) |
| Wave 1 | `it` | Italiano | Italia (Pavía) |
| Wave 1 | `no` | Noruego | Noruega (Oslo) |
| Wave 1 | `ru` | Ruso | Rusia (Moscú) |
| Wave 1 | `sp` | Español | España (Madrid) |
| Wave 1 | `tr` | Turco | Turquía (Estambul) |
| **Wave 2** | `ba` | Vasco | España (San Sebastián) |
| Wave 2 | `bp` | Portugués | Brasil (Río de Janeiro) |
| Wave 2 | `da` | Danés | Dinamarca (Aarhus) |
| Wave 2 | `en_uk`| **Inglés (Nativo - Cohorte 2)** | Reino Unido (Londres) |
| Wave 2 | `ge_po`| Alemán | Alemania (Potsdam) |
| Wave 2 | `ge_zu`| Alemán | Suiza (Zúrich) |
| Wave 2 | `hi_iiith`| Hindi | India (Hyderabad) |
| Wave 2 | `hi_iitk` | Hindi | India (Kanpur) |
| Wave 2 | `ic` | Islandés | Islandia (Reikiavik) |
| Wave 2 | `ru_mo`| Ruso | Rusia (Moscú w2) |
| Wave 2 | `se` | Serbio | Serbia (Novi Sad) |
| Wave 2 | `sp_ch`| Español | Chile (Santiago) |
| Wave 2 | `no_w2`| Noruego | Noruega (w2) |
| Wave 2 | `tr_w2`| Turco | Turquía (w2) |
| Wave 2 | `ch_s` | Chino Simplificado | China Continental |
| Wave 2 | `ch_t` | Chino Tradicional | Taiwán |

*Nota metodológica:* El cohorte coreano (`kr`) presente en MECO fue excluido de los análisis de red y diferencias individuales al no disponer de sesión L2 en inglés completa.

---

## 3. Dispositivos de Eye-Tracking y Esquema `popEye`

* **Hardware:** EyeLink 1000 / EyeLink Portable Duo (SR Research Ltd.), con frecuencia de muestreo de $500\text{ Hz}$ o $1000\text{ Hz}$, registrando de forma monocular el ojo dominante.
* **Formato de datos:** Basado en el estándar del paquete R `popEye`. Cada fila del archivo de fijaciones representa un evento de fijación visual sobre una región de interés (palabra o IA - *Interest Area*):
  * `subid` / `uniform_id`: Identificador anonimizado único del participante.
  * `trialid` / `itemid`: Identificador del texto/pasaje leído ($1$ a $12$).
  * `wordnum` / `ianum`: Posición secuencial de la palabra dentro del pasaje.
  * `dur`: Duración de la fijación en milisegundos.
  * `xs`, `ys`: Coordenadas espaciales del centroide de fijación en la pantalla.
  * `ps`: Tamaño pupilar durante la fijación (diámetro/área pupilar).
  * `sac_len`: Longitud sacádica de llegada o salida (amplitud angular o en caracteres).

---

## 4. Pipeline de Limpieza y Decisiones Metodológicas

La limpieza de datos crudos se ejecutó en `scripts/preprocess_fixation_data.py` y se documenta en las directrices de `data/POPEYE_DATA_SPEC.md`:

```
DATOS CRUDOS (RDA)
  │
  ▼ [Rscript scripts/convert_rda_to_csv.R]
ARCHIVOS CSV TABULARES
  │
  ▼
1. FILTRADO FISIOLÓGICO DE FIJACIONES:
   - Descarte de duraciones < 60 ms (demasiado cortas para activación léxica; artefactos sacádicos).
   - Descarte de duraciones > 1000 ms (pérdidas de trackeo, parpadeos no detectados o distracción).
  │
  ▼
2. TRATAMIENTO DE PARPADEOS (BLINKS):
   - Eliminación de fijaciones inmediatamente anteriores o posteriores a un evento de parpadeo.
  │
  ▼
3. CORRECCIÓN DE ROTACIÓN DE TEXTOS:
   - En cohortes como Estonio (`ee`) y Ruso (`ru`), el orden de presentación de pasajes se rotó
     entre sujetos. Se mapearon los `itemid` al índice canónico 1..12 usando las matrices de
     referencia `data/benchmark/l1_tokens/itemid_to_text_<lang>.csv`.
  │
  ▼
4. UNIFICACIÓN DE IDENTIFICADORES (ID DEDUPLICATION):
   - Homogeneización de la clave `uniform_id` en minúsculas y sin espacios para permitir
     el cruce perfecto entre reportes de fijación, cuestionarios LEAP-Q y baterías psicométricas.
  │
  ▼
DATASET LIMPIO CONSOLIDADO
`joint_l2_fixation_trimmed_report_2.2.comprehension.clean.csv`
```

---

## 5. Salidas Intermedias Generadas

1. **`data/benchmark/`**: Textos canónicos de los 12 pasajes en inglés y en cada una de las lenguas nativas, junto con conteo de palabras y longitudes.
2. **`data/by.sub.l1.csv`**: Tabla consolidada a nivel de sujeto con métricas agregadas por L1 (duraciones medias, tasas de regresión, aciertos de comprensión).
3. **`data/ANALISIS_CALIDAD_*.md`**: Auditorías sistemáticas de completitud, rangos numéricos y consistencia entre waves.

