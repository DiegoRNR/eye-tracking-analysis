# Especificación de Datos popEye (Reportes de Fijación de MECO L2)

## Alcance

Este documento especifica las columnas de los reportes de fijación de MECO L2
(`joint_l2_fixation_trimmed_report_2.2.csv` y
`joint_fix_trimmed_L2_wave2_version2.2.csv`) que provienen del paquete R
popEye (Schroeder, 2019; <https://github.com/sascha2schroeder/popEye>).

El paper de MECO L2 (Siekmann et al., 2021; DOI:
[10.1017/S0272263121000954](https://doi.org/10.1017/S0272263121000954))
y sus materiales suplementarios (S1–S7) **no proveen un diccionario de
datos** para el reporte de fijación. Esta especificación se reconstruye a
partir del código fuente R de popEye (rama master, commit al momento de
escritura).

## Aparato y adquisición

- **Eye tracker:** EyeLink Portable Duo, 1000, o 1000+ (SR Research).
  ([Fuente: paper de MECO L2, sección "Apparatus"](https://doi.org/10.1017/S0272263121000954))
- **Tasa de muestreo:** 1.000 Hz.
- **Presentación de estímulos:** Experiment Builder (SR Research).
- **Ojo analizado:** ojo dominante autoreportado (el ojo derecho en la
  mayoría de los participantes). Grabación binocular, análisis monocular.
  ([Fuente: paper de MECO L2, sección "Apparatus"](https://doi.org/10.1017/S0272263121000954))
- **Restricción de mentón**, calibración de 9 puntos + validación de 9
  puntos al inicio de cada trial, control de drift antes de cada trial.

## Procedencia

- **Paquete R popEye:** Schroeder, S. (2019). popEye — An R package
  to analyse eye movement data from reading experiments. Repositorio
  GitHub, <https://github.com/sascha2schroeder/popEye>.
- **Paper de MECO L2:** Siekmann, F., et al. (2023). Evidence from the
  Multilingual Eye-movements Corpus. *Studies in Second Language
  Acquisition*. DOI: 10.1017/S0272263121000954.
- **Formato de línea EFIX:** SR Research, documentación de formato
  EyeLink ASC / EDF.

---

## Definición de campos por reporte

Las definiciones de cada campo están tomadas del
[`materials/Measures.md`](https://github.com/sascha2schroeder/popEye/blob/master/materials/Measures.md)
canónico de popEye (rama master). MECO L2 exporta **4 de los 7 reportes
estándar de popEye** — los reportes *Subject* y *Trial* no están
presentes en el corpus.

### Reporte de Fijación (Fixation report)

**Archivo MECO L2:** `joint_l2_fixation_trimmed_report_2.2.rda` (wave 1)
y `joint_fix_trimmed_L2_wave2_version2.2.rda` (wave 2).

**Identificadores y contexto**

- `subid`: ID del participante (e.g. `DU_4`).
- `trialid`: posición del trial en el análisis [1–12].
- `trialnum`: posición del trial en el experimento.
- `itemid`: ID del item.
- `cond`: condición experimental (si aplica).
- `fixid`: número de la fijación dentro del trial.
- `sentnum`: número de oración dentro del texto.
- `sent`: nombre abreviado de la oración.
- `sent.nwords`: número de palabras de la oración.
- `trial`: nombre abreviado del trial (sólo wave 1).
- `trial.nwords`: número de palabras del trial.

**Posición y tiempo**

- `start`: tiempo de inicio (en ms desde el inicio del trial).
- `stop`: tiempo de fin (en ms desde el inicio del trial).
- `dur`: duración de la fijación.
- `xs`, `ys`: posición cruda x/y (en píxeles).
- `xn`, `yn`: posición corregida x/y (en píxeles), después de drift
  correction y asignación de línea.
- `ym`: posición y media (posición de la línea).
- `type`: indicador de si la fijación es un outlier ("out"), i.e. está
  fuera del área de texto.

**Vecinos sacádicos**

- `sac.in`: longitud de la sacada entrante (en letras).
- `sac.out`: longitud de la sacada saliente (en letras).

**Estado del ojo**

- `blink`: si ocurrió un parpadeo justo antes o después de la
  fijación.
- `line`: número de línea a la que se asignó la fijación.
- `line.change`: diferencia entre la línea de la fijación actual y la
  anterior.
- `line.let`, `line.word`: número de letra/palabra dentro de la línea.
- `letternum`: número de letra dentro del trial.
- `letter`: nombre de la letra.
- `wordnum`: número de palabra dentro del trial.
- `word`: nombre de la palabra.
- `ianum`: número de IA (interest area) dentro del trial.
- `ia`: nombre de la IA.

**Medidas a nivel de palabra**

- `word.fix`: número de fijación sobre la palabra.
- `word.run`: número de lectura (run) de la palabra.
- `word.runid`: número del run de la palabra al que pertenece la
  fijación.
- `word.run.fix`: número de la fijación dentro del run.
- `word.firstskip`: si la palabra fue saltada durante la primera
  pasada (first-pass).
- `word.refix`: si la palabra fue refijada con la fijación actual.
- `word.launch`: distancia del sitio de lanzamiento desde el inicio
  de la palabra.
- `word.land`: posición de aterrizaje dentro de la palabra.
- `word.cland`: posición de aterrizaje centrada.
- `word.reg.out`: si una regresión salió desde la palabra.
- `word.reg.in`: si una regresión entró a la palabra.
- `word.reg.out.to`: a qué palabra apunta la regresión saliente.
- `word.reg.in.from`: desde qué palabra viene la regresión entrante.

**Medidas a nivel de IA**

- `ia.fix`, `ia.run`, `ia.runid`, `ia.run.fix`: análogas a las de
  palabra, para la IA.
- `ia.firstskip`, `ia.refix`, `ia.launch`, `ia.land`, `ia.cland`:
  análogas a las de palabra, para la IA.
- `ia.reg.out`, `ia.reg.in`, `ia.reg.out.to`, `ia.reg.in.from`:
  análogas a las de palabra, para la IA.

**Medidas a nivel de oración**

- `sent.word`: número de palabra dentro de la oración.
- `sent.fix`: número de fijación sobre la oración.
- `sent.run`: número de run de la oración.
- `sent.runid`: número del run de la oración al que pertenece la
  fijación.
- `sent.run.fix`: número de la fijación dentro del run.
- `sent.firstskip`, `sent.refix`: análogas a las de palabra, para la
  oración.
- `sent.reg.out`, `sent.reg.in`, `sent.reg.out.to`,
  `sent.reg.in.from`: análogas a las de palabra, para la oración.

**Pupila**

- `ps`: tamaño pupilar promedio (average pupil size) sobre el intervalo
  de la fijación, en píxeles de cámara del EyeLink, ojo dominante.

### Reporte de Sacada (Saccade report)

**Archivo MECO L2:** `joint_L2_sac_trimmed_wave1_2.2.rda` (wave 1) y
`joint_sac_trimmed_L2_wave2_version2.2.rda` (wave 2).

**Identificadores y contexto**

- `subid`, `trialid`, `trialnum`, `itemid`, `cond`: como en el reporte
  de fijación.
- `sacid`: número de la sacada dentro del trial.
- `msg`: tipo de evento: `SAC` (sacada) o `BLINK` (parpadeo).

**Posición y tiempo**

- `start`, `stop`: tiempo de inicio/fin (en ms desde el inicio del
  trial).
- `dur`: duración (en ms).
- `xs`, `ys`: posición cruda de inicio (en píxeles).
- `xe`, `ye`: posición cruda de fin (en píxeles).
- `xsn`, `ysn`: posición corregida de inicio.
- `xen`, `yen`: posición corregida de fin.
- `dist.let`: longitud de la sacada (en letras).

> **Nota:** MECO L2 incluye campos adicionales en su reporte de sacada
> que **no están en el `Measures.md` canónico de popEye**: `lines`,
> `linee`, `dist.line`, `lets`, `lete`, `dx`, `dy`, `dist.px`, `amp.px`,
> `amp.deg`, `pv.px`, `pv.deg`. Estos parecen ser extensiones de MECO
> (o de una versión de popEye posterior a la documentada en
> `Measures.md`) y **no** están documentados como campos de popEye. No
> se incluyen en esta especificación.

### Reporte de Palabra / Área de Interés (Word / Interest area report)

**Archivo MECO L2:** `joint_data_l2_trimmed_version2.2.rda` (wave 1) y `joint_data_trimmed_L2_wave2_version2.2.rda` (wave 2).

Este reporte agrega las fijaciones a nivel de palabra. Un registro por
(palabra, participante, trial). El esquema de popEye para este reporte
se llama *Interest area report*.

**Identificadores y contexto**

- `subid`, `trialid`, `trialnum`, `itemid`, `cond`: como arriba.
- `sentnum`: número de oración dentro del texto.
- `ianum`: número de IA dentro del texto.
- `ia`: texto de la IA (palabra en el formato presentado al lector).

**Estado de la palabra**

- `blink`: si hubo un parpadeo justo antes, durante, o justo después
  de que la IA fuera fijada.
- `skip`: si la IA fue fijada durante el trial.
- `nrun`: número de veces que la IA fue releída dentro del trial
  ("releída" = leída otra vez después de haber sido dejada a la
  izquierda o derecha).
- `reread`: si la IA fue releída al menos una vez durante el trial.
- `nfix`: número de fijaciones sobre la IA durante todo el trial.
- `refix`: si la IA fue refijada al menos una vez durante el trial.
- `reg.in`: si hubo al menos una regresión hacia la IA.
- `reg.out`: si hubo al menos una regresión desde la IA.
- `dur`: tiempo total de lectura de la IA durante el trial en ms
  (total reading time).

**Medidas de primera pasada (first-pass reading)**

- `firstrun.skip`: si la IA fue saltada en la primera pasada.
- `firstrun.nfix`: número de fijaciones sobre la IA en la primera
  pasada.
- `firstrun.refix`: si la IA fue refijada en la primera pasada.
- `firstrun.reg.in`: si hubo una regresión hacia la IA en la primera
  pasada.
- `firstrun.reg.out`: si hubo una regresión desde la IA en la primera
  pasada.
- `firstrun.dur`: tiempo de lectura de la IA en la primera pasada
  (gaze duration).
- `firstrun.gopast`: suma de las duraciones de todas las fijaciones
  desde que se entró a la IA hasta que se la dejó a la derecha
  (regression path duration).
- `firstrun.gopast.sel`: selective go-past time: go-past time menos el
  tiempo del regression path.

**Medidas de la primera fijación**

- `firstfix.sac.in`: longitud de la sacada entrante (en letras) para
  la primera fijación sobre la IA.
- `firstfix.sac.out`: longitud de la sacada saliente (en letras) para
  la primera fijación.
- `firstfix.launch`: distancia del sitio de lanzamiento (longitud de
  la sacada entrante hasta el espacio antes de la IA).
- `firstfix.land`: posición de aterrizaje (letra) de la primera
  fijación.
- `firstfix.cland`: posición de aterrizaje centrada (Vitu et al.,
  2001: landing position − ((wordlength + 1) / 2)).
- `firstfix.dur`: duración de la primera fijación sobre la IA.

**Medidas de single-fixation** (cuando la IA fue fijada sólo una vez
en la primera pasada)

- `singlefix`: si la IA fue fijada sólo una vez en la primera pasada.
- `singlefix.sac.in`, `singlefix.sac.out`, `singlefix.launch`,
- `singlefix.land`, `singlefix.cland`, `singlefix.dur`: análogas a las
  anteriores, restringidas al caso de single-fixation.

### Reporte de Oración (Sentence report)

**Archivo MECO L2:** `joint_sent_trimmed_L2_wave2_version2.2.rda`
(sólo wave 2).

Un registro por (oración, participante, trial). Las medidas forward,
rereading, look-back y look-from se calculan de forma análoga a la
herramienta "Getting Reading Measures" de SR Research, basada en el
software Eyelink Analysojia (Turku Eye Labs).

**Identificadores y contexto**

- `subid`, `trialid`, `trialnum`, `itemid`, `cond`: como arriba.
- `sentnum`: número de la oración dentro del trial.
- `sent`: nombre abreviado de la oración.
- `sent.nwords`: número de palabras de la oración.

**Estado de la oración**

- `blink`: si ocurrió un parpadeo durante la lectura de la oración.
- `skip`: si la oración fue saltada.
- `nrun`: número de veces que la oración fue leída.
- `reread`: si la oración fue leída más de una vez.
- `reg.in`: si hubo una regresión hacia la oración.
- `reg.out`: si hubo una regresión desde la oración.
- `total.nfix`: número de fijaciones hechas sobre la oración.
- `total.dur`: tiempo total de lectura de la oración.
- `rate`: tasa de lectura (palabras por minuto).
- `gopast`: suma de las duraciones de todas las fijaciones desde que
  se entró a la oración hasta que se la dejó a la derecha (regression
  path duration).
- `gopast.sel`: selective go-past time: regression path duration menos
  el tiempo del regression path.

**Medidas de primera pasada**

- `firstrun.skip`: si la oración fue saltada en la primera pasada.
- `firstrun.reg.in`: si hubo regresión hacia la oración en la primera
  pasada.
- `firstrun.reg.out`: si hubo regresión desde la oración en la
  primera pasada.
- `firstpass.nfix`: número de fijaciones hechas durante la primera
  pasada.
- `firstpass.dur`: tiempo de primera pasada (first-pass reading time).
- `firstpass.forward.nfix`: número de fijaciones forward de primera
  pasada (caen en una palabra posterior de la oración).
- `firstpass.forward.dur`: duración de las fijaciones forward durante
  la primera pasada.
- `firstpass.reread.nfix`: número de fijaciones de relectura de
  primera pasada (caen en una palabra ya leída).
- `firstpass.reread.dur`: duración de las fijaciones de relectura
  durante la primera pasada.

**Lookback y look-from**

- `lookback.nfix`: número de fijaciones hechas sobre la oración
  después de regresar a ella desde otra oración.
- `lookback.dur`: duración de las fijaciones de lookback sobre la
  oración.
- `lookfrom.nfix`: número de fijaciones de relectura sobre otra
  oración iniciadas desde esta oración.
- `lookfrom.dur`: duración de las fijaciones de lookfrom sobre la
  oración.

### Reporte de Pasaje (Passage report)

**Archivo MECO L2:** `joint_passage_trimmed_L2_wave2_version2.2.rda`
(sólo wave 2).

> **Este reporte NO aparece en la documentación estándar de popEye**
> (`materials/Measures.md` lista sólo *Subject*, *Trial*, *Sentence*,
> *Interest area*, *Word*, *Fixation* y *Saccade*). MECO L2 lo incluye
> como una agregación a nivel de passage (texto completo). Los nombres
> de los campos son consistentes con el resto de popEye, pero la
> existencia del reporte en sí es una adición de MECO. No se documenta
> aquí la definición campo por campo; los nombres son
> autoexplicativos (`nblink`, `nrun`, `nfix`, `nout`, `nsac`, `mfix`,
> `firstpass`, `rereading`, `total`, `rate`, etc.) y representan
> totales/promedios sobre todas las palabras y oraciones del passage.
