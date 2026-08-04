# Dataset MECO L2

> **Nota de especificación:** Las definiciones campo por campo de los
> reportes popEye que MECO L2 reutiliza están en
> [`POPEYE_DATA_SPEC.md`](POPEYE_DATA_SPEC.md). El README lista los
> campos disponibles en cada archivo y enlaza a la spec para su
> semántica detallada (unidades, ojo dominante, fórmulas de agregación).

## Descripción

Datos del *Multilingual Eye-movements Corpus*, componente L2 (Kuperman et al., 2023, DOI: 10.1017S0272263121000954; Kuperman et al., 2025, DOI: 10.1017/S0272263125000105), en su versión 2.2. El corpus contiene registros de eye-tracking durante lectura en 12 textos en inglés como L2, más tareas de comprensión lectora, medidas de diferencias individuales y datos demográficos. Se distribuye en dos waves independientes.

## Datos

Los archivos se organizan bajo `MECO-L2_version-2.2/wave-{1,2}/` y `benchmark/`. Cada subsección debajo documenta un archivo (o set de archivos) con sus campos.

### Textos

Wave 1 - Archivo asociado: `data/benchmark/texts.meco.l2.rda`
Wave 2 - Archivo asociado: `data/benchmark/texts.meco.l2.rda`

- `trialid`: Número de texto (y número de prueba en el experimento) [1, 12].
- `text`: Texto completo presentado al lector.
- `question1`: Primera pregunta de comprensión lectora para el texto.
- `question2`: Segunda pregunta de comprensión lectora para el texto.

### Características de palabras

Wave 1 - Archivo asociado: `data/benchmark/L2 word length and frequency.rda`
Wave 2 - Archivo asociado: `data/benchmark/L2 word length and frequency.rda`

- `trialid`: Número de texto [1, 12].
- `sentnum`: Número de la oración dentro del texto.
- `ianum`: Número de la palabra dentro del texto.
- `ia`: Palabra en el formato presentado al lector.
- `ia_clean`: Palabra convertida a minúsculas y sin signos de puntuación.
- `freq`: Frecuencia de la palabra en el *fasttext corpus*.
- `zipf_freq`: Frecuencia en escala logarítmica de Zipf [1, 6] (o 7 si se
  consideran palabras funcionales), sobre el *fasttext corpus*.
- `length`: Total de caracteres de la palabra.

### Comprensión Lectora

#### Número de Respuestas Correctas por Participante

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/comprehension/joint.comp.l2.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/comprehension/joint_comp_L2_Wave2_trimmed.rda`

- `subject`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `total_answer`: Total de preguntas por responder.
- `correct_answer`: Total de respuestas correctas.
- `accuracy`: Porcentaje de acierto de respuestas [0.00, 1.00].

#### Número de Respuestas Correctas por Participante en cada Texto

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/comprehension/joint_l2_acc_breakdown.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/comprehension/joint_l2_Wave2_acc_breakdown_trimmed.rda`

- `subject`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `number`: Número de texto [1, 12].
- `ACCURACY`: Número de respuestas correctas para el texto [0, 2].

#### Número de Respuestas Correctas por Participante en cada Pregunta

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/comprehension/joint_l2_acc_full_breakdown.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/comprehension/joint_l2_wave2_acc_full_breakdown_trimmed.rda`

- `subject`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `number`: Número de texto [1, 12].
- `QUESTIONNUM`: Número de pregunta para el texto [1, 2].
- `ACCURACY`: Acierto de respuesta [0, 1].

### Seguimiento Ocular

#### Medidas por Palabra

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint_data_l2_trimmed_version2.2.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_data_trimmed_L2_wave2_version2.2.rda`

- `lang`: Código de lengua primaria del participante (ej. du).
- `trial`: Nombre abreviado del trial — presente sólo en wave 1.
- `supplementary_id`: Identificador suplementario — presente sólo en wave 2.
- `uniform_id`: Identificador de participante normalizado (ej. du_4).

***Campos popEye***

- `subid`, `trialid`, `trialnum`, `itemid`, `cond`, `sentnum`, `wordnum`, `word`, `blink`, `skip`, `nrun`, `reread`, `nfix`, `refix`, `reg.in`, `reg.out`, `dur`, `firstrun.skip`, `firstrun.nfix`, `firstrun.refix`, `firstrun.reg.in`, `firstrun.reg.out`, `firstrun.dur`, `firstrun.gopast`, `firstrun.gopast.sel`, `firstfix.sac.in`, `firstfix.sac.out`, `firstfix.launch`, `firstfix.land`, `firstfix.cland`, `firstfix.dur`, `singlefix`, `singlefix.sac.in`, `singlefix.sac.out`, `singlefix.launch`, `singlefix.land`, `singlefix.cland`, `singlefix.dur`

Definición de cada campo: ver [Reporte de Palabra / Área de Interés](POPEYE_DATA_SPEC.md#reporte-de-palabra-area-de-interes-word--interest-area-report).

#### Palabras por Minuto para cada Pasaje por Participante

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint.l2.readrate_version2.2.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_readrate_L2_wave2_version2.2.rda`

- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `trialid`: Número de texto [1, 12].
- `rate`: Número de palabras leídas por minuto.

#### Medidas por Oración

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint.l2.readrate_sent_version2.2.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_sent_trimmed_L2_wave2_version2.2.rda`

> Wave 1 sólo incluye el subset de *readrate por oración*. <br>
> Wave 2 incluye el reporte de oración completo.

- `lang`: Código de lengua primaria del participante (ej. du).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `supplementary_id`: Identificador suplementario — presente sólo en wave 2.

***Campos popEye***

- `subid` (sólo wave 2), `trialid`, `trialnum`, `itemid` (sólo wave 2), `cond` (sólo wave 2), `sentnum`, `sent`, `sent.nwords`, `skip`, `nrun`, `reread`, `reg.in`, `reg.out`, `total.nfix`, `total.dur`, `rate`, `gopast`, `gopast.sel`, `firstrun.skip`, `firstrun.reg.in`, `firstrun.reg.out`, `firstpass.nfix`, `firstpass.dur`, `firstpass.forward.nfix`, `firstpass.forward.dur`, `firstpass.reread.nfix`, `firstpass.reread.dur`, `lookback.nfix`, `lookback.dur`, `lookfrom.nfix`, `lookfrom.dur`

Definición de cada campo: ver [Reporte de Oración](POPEYE_DATA_SPEC.md#reporte-de-oracion-sentence-report).

#### Medidas por Sacada

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint_sac_trimmed_wave1_2.2.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_sac_trimmed_L2_wave2_version2.2.rda`

- `lang`: Código de lengua primaria del participante (ej. du).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `msg`: Tipo de evento `{SAC, BLINK}`.
- `sacid`: Identificador de evento de sacada para cada texto por participante.
- `trial`: Nombre abreviado del trial — presente sólo en wave 2.
- `supplementary_id`: Identificador suplementario — presente sólo en wave 2.

***Campos popEye***

- `subid`, `trialid`, `trialnum`, `itemid`, `cond`, `start`, `stop`, `dur`, `xs`, `ys`, `xe`, `ye`, `xsn`, `ysn`, `xen`, `yen`, `dist.let`

Definición de cada campo: ver [Reporte de Sacada](POPEYE_DATA_SPEC.md#reporte-de-sacada-saccade-report).

> **Extensiones MECO L2 (no en `Measures.md` canónico de popEye):** el
> archivo incluye además `lines`, `linee`, `dist.line`, `lets`, `lete`,
> `dx`, `dy`, `dist.px`, `amp.px`, `amp.deg`, `pv.px`, `pv.deg`. Son
> campos adicionales del reporte de sacada de MECO L2 y no están
> documentados como campos popEye estándar.

#### Medidas por Fijación

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint_l2_fixation_trimmed_report_2.2.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_fix_trimmed_L2_wave2_version2.2.rda`

- `lang`: Código de lengua primaria del participante (ej. du).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `fixid`: Identificador de evento de fijación para cada texto por participante.
- `trial`: Nombre abreviado del trial — presente sólo en wave 1.
- `trial.nwords`: Número de palabras del trial — presente sólo en wave 1.

***Campos popEye***

- `subid`, `trialid`, `trialnum`, `itemid`, `cond`, `start`, `stop`, `xs`, `ys`, `xn`, `yn`, `ym`, `dur`, `ps`, `sac.in`, `sac.out`, `type`, `blink`, `line`, `line.change`, `line.let`, `line.word`, `letternum`, `letter`, `wordnum`, `word`, `ianum`, `ia`, `sentnum`, `sent`, `sent.nwords`, `word.fix`, `word.run`, `word.runid`, `word.run.fix`, `word.firstskip`, `word.refix`, `word.launch`, `word.land`, `word.cland`, `word.reg.out`, `word.reg.in`, `word.reg.out.to`, `word.reg.in.from`, `ia.fix`, `ia.run`, `ia.runid`, `ia.run.fix`, `ia.firstskip`, `ia.refix`, `ia.launch`, `ia.land`, `ia.cland`, `ia.reg.out`, `ia.reg.in`, `ia.reg.out.to`, `ia.reg.in.from`, `sent.word`, `sent.fix`, `sent.run`, `sent.runid`, `sent.run.fix`, `sent.firstskip`, `sent.refix`, `sent.reg.out`, `sent.reg.in`, `sent.reg.out.to`, `sent.reg.in.from`

Definición de cada campo (incluyendo `ps`): ver [Reporte de Fijación](POPEYE_DATA_SPEC.md#reporte-de-fijacion-fixation-report).

#### Medidas por Pasaje

Wave 1 - Archivo asociado: ***NA***
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_passage_trimmed_L2_wave2_version2.2.rda`

> El reporte de Pasaje **no aparece** en la documentación estándar de
> popEye (`materials/Measures.md`); es una agregación a nivel de
> passage (texto completo) introducida por MECO L2. Los campos representan 
> totales/promedios sobre todas las palabras y oraciones del texto.

- `subid`, `trialid`, `trialnum`, `itemid`, `cond`, `trial`, `trial.nwords`, `nblink`, `nrun`, `nfix`, `nout`, `sac`, `skip`, `refix`, `reg`, `mfix`, `firstpass`, `rereading`, `total`, `rate`
- `lang`: Código de lengua primaria del participante (ej. du).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `supplementary_id`: Identificador suplementario — presente sólo en wave 2.

### Diferencias Individuales

#### Puntaje Obtenido por Tarea

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/individual-differences/joint.ind.diff.l2.rda`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/individual-differences/joint.ind.diff.l2.w2.rda`

- `subid`: Identificador de participante (ej. DU_04) — presente sólo en wave 1.
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `spelling`: Puntaje en tarea de deletreo.
- `motiv`: Puntaje en cuestionario de motivación.
- `lextale`: Puntaje en tarea LexTALE de vocabulario.
- `TOWRE_word`: Puntaje TOWRE — palabras reales.
- `TOWRE_nonword`: Puntaje TOWRE — pseudopalabras.
- `vocab`: Puntaje en tarea de vocabulario.
- `vocab.t2.5`: Puntaje de vocabulario con topes en percentiles 2.5 y 97.5.
- `cft20`: Puntaje en *Culture Fair Intelligence Test* (20 ítems).

#### LEAP-Q

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/primary-data/individual-differences/leap-q/*.xlsx`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/primary-data/individual-differences/leap-q/*.xlsx`

Directorio con archivos `*.xlsx` con información demográfica y
proficiencia en lengua primaria e inglés como lengua secundaria de los
participantes (cuestionario LEAP-Q).

### Estadísticas Descriptivas

Archivos auxiliares generados por el código de MECO L2 (publicados como
suplemento del paper). Resumen, por lengua y/o texto, las variables
dependientes de cada sección.

#### Comprensión por Pasaje

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/auxiliary-files/descriptive_acc_passage.csv`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/auxiliary-files/descriptive_acc_passage.csv`

- `var`: Código identificador de la variable de precisión (`acc`).
- `lang`: Código de lengua primaria de los participantes.
- `trialid`: Índice identificador de texto evaluado [1, 12].
- `n`: Total de participantes en la evaluación.
- `mean`: Valor promedio de respuestas correctas.
- `sd`: Desviación estándar.
- `se`: Error estándar.
- `median`: Mediana.
- `min`: Valor mínimo.
- `max`: Valor máximo.
- `q1`: Primer cuartil.
- `q3`: Tercer cuartil.

#### Eye-tracking por Lengua

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/auxiliary-files/descriptive_eyemove_language.csv`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/auxiliary-files/descriptive_eyemove_language.csv`

- `var`: Código identificador de la medida de eye-tracking (ej. `dur`, `nfix`).
- `lang`: Código de lengua primaria de los participantes.
- `n`: Total de participantes en la evaluación.
- `mean`, `sd`, `se`, `median`, `min`, `max`: Estadísticos resumen sobre la variable.

#### Tasa de Lectura por Pasaje

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/auxiliary-files/descriptive_rate_passage.csv`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/auxiliary-files/descriptive_rate_passage.csv`

- `var`: Código identificador de la variable de tasa (`rate`).
- `lang`: Código de lengua primaria de los participantes.
- `trialid`: Índice identificador de texto evaluado [1, 12].
- `n`, `mean`, `sd`, `se`, `median`, `min`, `max`, `q1`, `q3`: Estadísticos resumen sobre la variable.

#### Diferencias Individuales por Lengua

Wave 1 - Archivo asociado: `MECO-L2_version-2.2/wave-1/auxiliary-files/descriptive_ind_language.csv`
Wave 2 - Archivo asociado: `MECO-L2_version-2.2/wave-2/auxiliary-files/descriptive_ind_language.csv`

- `var`: Código identificador de la prueba (ej. `cft`, `lextale`, `TOWRE_*`).
- `lang`: Código de lengua primaria de los participantes.
- `n`, `mean`, `sd`, `se`, `median`, `min`, `max`: Estadísticos resumen sobre la variable.
