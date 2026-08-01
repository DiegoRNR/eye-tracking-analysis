# Dataset MECO L2

## Descripción

## Datos

### Variables Base

- `trialid`: Número de texto (y número de prueba en el experimento).
- `sentnum`: Número del pasaje en el texto.
- `ianum`: Número de la palabra en el texto.
- `ia`: Palabra en el formato presentado al lector.
- `ia_clean`: Palabra convertida a minúsculas y sin signos de puntuación.
- `freq`: Frecuencia de la palabra en el *fasttext corpus*.
- `zipf_freq`: Frecuencia de la palabra en el *fasttext corpus*, normalizado en escala logarítimica con valores de 1 a 6 (o 7 si se consideran palabras funcionales)
- `length`: Total de caracteres de AOI. 

### Textos

A continuación se listan los textos utilizados en la captura de datos, ordenados según su `trialid` en el dataset.

1. Samuel Morse
2. Leonardo Da Vinci
3. Amazon Rainforest
4. Multiple Intelligences
5. Internet Risks
6. Good Night's Sleep
7. Bird's Feathers
8. Animal Hibernation
9. Leeches as Medical Cure
10. Music File Sharing
11. Pencil
12. Technology

Cada texto tiene asociadas dos preguntas de comprensión lectora sobre el contenido del mismo.

### Comprensión Lectora

Corresponden a datos acerca de la precisión de las respuestas a las preguntas presentadas a los participantes tras la lectura de cada texto.

#### Número de Respuestas Correctas por Participante

Wave 1 - Archivo asociado: `joint.comp.l2.rda`
Wave 2 - Archivo asociado: `joint_comp_L2_Wave2_trimmed.rda`

- `subject`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `total_answer`: Total de preguntas por responder.
- `correct_answer`: Total de respuestas correctas.
- `accuracy`: Porcentaje de acierto de respuestas [0.00, 1.00].

#### Número de Respuestas Correctas por Participante en cada Texto

Wave 1 - Archivo asociado: `joint_l2_acc_breakdown.rda`
Wave 2 - Archivo asociado: `joint_l2_Wave2_acc_breakdown_trimmed.rda`

- `subject`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `number`: Número de texto [1, 12].
- `ACCURACY`: Número de respuestas correctas para el texto [0, 2].

#### Número de Respuestas Correctas por Participante en cada Pregunta

Wave 1 - Archivo asociado: `joint_l2_acc_full_breakdown.rda`
Wave 2 - Archivo asociado: `joint_l2_wave2_acc_full_breakdown_trimmed.rda`

- `subject`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `number`: Número de texto [1, 12].
- `QUESTIONNUM`: Número de pregunta para el texto [1, 2].
- `ACCURACY`: Acierto de respuesta [0, 1].

### Seguimiento Ocular

#### Medidas por Palabra

Wave 1 - Archivo asociado: `joint_data_l2_trimmed_version2.2.rda`
Wave 2 - Archivo asociado: `joint_data_l2_trimmed_version2.2.rda`

- `subid`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `trial`: A. ***Wave 1***
- `trialid`: Número de texto [1, 12].
- `trialnum`: A.
- `itemid`: A.
- `cond`: A.
- `supplementary_id`: A. ***Wave 2***
- `sentnum`: A.
- `wordnum`: A.
- `word`: A.
- `blink`: A.
- `skip`: A.
- `nrun`: A.
- `reread`: A.
- `nfix`: A.
- `refix`: A.
- `reg.in`: A.
- `reg.out`: A.
- `dur`: A.
- `firstrun.skip`: A.
- `firstrun.nfix`: A.
- `firstrun.refix`: A.
- `firstrun.reg.in`: A.
- `firstrun.reg.out`: A.
- `firstrun.dur`: A.
- `firstrun.gopast`: A.
- `firstrun.gopast.sel`: A.
- `firstfix.sac.in`: A.
- `firstfix.sac.out`: A.
- `firstfix.launch`: A.
- `firstfix.land`: A.
- `firstfix.cland`: A.
- `firstfix.dur`: A.
- `singlefix`: A.
- `singlefix.sac.in`: A.
- `singlefix.sac.out`: A.
- `singlefix.launch`: A.
- `singlefix.land`: A.
- `singlefix.cland`: A.
- `singlefix.dur`: A.

#### Palabras por Minuto para cada Pasaje por Participante

Wave 1 - Archivo asociado: `joint.l2.readrate_version2.2.rda`
Wave 2 - Archivo asociado: `joint_readrate_L2_wave2_version2.2.rda`

- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `trialid`: Número de texto [1, 12].
- `rate`: Número de palabras leídas por minuto.

#### Medidas por Oración (10 caracteres)

Wave 1 - Archivo asociado: `joint.l2.readrate_sent_version2.2.rda`
Wave 2 - Archivo asociado: `joint.l2.readrate_sent_version2.2.rda`

- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `trialid`: Número de texto [1, 12].
- `trialnum`: A. ***Wave 2***
- `itemid`: A. ***Wave 2***
- `cond`: A. ***Wave 2***
- `supplementary_id`: A. ***Wave 2***
- `sentnum`: A.
- `sent`: A.
- `sent.nwords`: A.
- `skip`: A.
- `nrun`: A.
- `reread`: A.
- `reg.in`: A.
- `reg.out`: A.
- `total.nfix`: A.
- `total.dur`: A.
- `rate`: Número de palabras leídas por minuto.
- `gopast`: A.
- `gopast.sel`: A.
- `firstrun.skip`: A.
- `firstrun.reg.in`: A.
- `firstrun.reg.out`: A.
- `firstpass.nfix`: A.
- `firstpass.dur`: A.
- `firstpass.forward.nfix`: A.
- `firstpass.forward.dur`: A.
- `firstpass.reread.nfix`: A.
- `firstpass.reread.dur`: A.
- `lookback.nfix`: A.
- `lookback.dur`: A.
- `lookfrom.nfix`: A.
- `lookfrom.dur`: A.

#### Medidas por Sacada

Wave 1 - Archivo asociado: `joint_L2_sac_trimmed_wave1_2.2.rda`
Wave 2 - Archivo asociado: `joint_sac_trimmed_L2_wave2_version2.2.rda`

- `subid`: Identificador de participante (ej. DU_4).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `trialid`: Número de texto [1, 12].
- `trialnum`: A.
- `msg`: Tipo de evento {SAC; BLINK}
- `itemid`: A.
- `cond`: A.
- `trial`: A. ***Wave 2***
- `supplementary_id`: A. ***Wave 2***
- `sacid`: Identificador de evento de sacada para cada texto por participante.
- ***Campos de posición, distancia, tiempo, etc.***

#### Medidas por Fijación

Wave 1 - Archivo asociado: `joint_l2_fixation_trimmed_report_2.2.rda`
Wave 2 - Archivo asociado: `joint_fix_trimmed_L2_wave2_version2.2.rda`

- `subid`: Identificador de participante (ej. DU_4).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `trialid`: Número de texto [1, 12].
- `trialnum`: A.
- `itemid`: A.
- `cond`: A.
- `fixid`: Identificador de evento de sacada para cada texto por participante.
- `word`: A.
- ``: A.
- ***Campos de posición, distancia, tiempo, etc.***

#### Medidas por Pasaje

Wave 1 - Archivo asociado: ***NA**
Wave 2 - Archivo asociado: `joint_passage_trimmed_L2_wave2_version2.2.rda`

- `subid`: Identificador de participante (ej. DU_04).
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `trialid`: Número de texto [1, 12].
- `trialnum`: A.
- `itemid`: A.
- `cond`: A.
- `trial`: A.
- `trial.nwords`: A.
- `supplementary_id`: A.
- `nblink`: A.
- `nrun`: A.
- `nfix`: A.
- `nout`: A.
- `nsac`: A.
- `skip`: A.
- `refix`: A.
- `reg`: A.
- `mfix`: A.
- `firstpass`: A.
- `rereading`: A.
- `total`: A.
- `rate`: A.

### Diferencias Individuales

#### Puntaje Obtenido por Tarea

Wave 1 - Archivo asociado: `joint.ind.diff.l2.rda`
Wave 2 - Archivo asociado: `joint.ind.diff.l2.w2.rda`

- `subid`: Identificador de participante (ej. DU_04). ***Wave 1***
- `uniform_id`: Identificador de participante normalizado (ej. du_4).
- `lang`: Código de lengua primaria del participante (ej. du).
- `spelling`: a.
- `motiv`: a.
- `lextale`: a.
- `TOWRE_word`: a.
- `TOWRE_nonword`: a.
- `vocab`: a.
- `vocab.t2.5`: a.
- `cft20`: a.

#### LEAP-Q

Directorio con archivos `*.xlsx` con información demográfica y proficiencia en lengua primaria e inglés como lengua secundaria de los participantes.

## Estadísticas Descriptivas

### Aspectos Evaluados

- Precisión de la Comprensión
- Medidas de Seguimiento Ocular
- Tasa de Lectura
- Diferencias Individuales

### Campos Medidos

- var: Código identificador de aspecto evaluado.
- lang: Código de lengua primaria de los participantes.
- trialid: Índice identificador de texto evaluado.  
- n: Total de participantes en la evaluación.
- mean: Valor del promedio de valores obtenidos en la evaluación.
- sd: Valor de la desviación estándar obtenida en la evaluación.
- se: Valor del error estándar obtenido en la evaluación.
- median: Valor de la mediana obtenida en la evaluación.
- min: Valor mínimo obtenido en la evaluación.
- max: Valor máximo obtenido en la evaluación.
- q1: Valor del primer cuartil obtenido en la evaluación.
- q3: Valor del tercer cuartil obtenido en la evaluación.
