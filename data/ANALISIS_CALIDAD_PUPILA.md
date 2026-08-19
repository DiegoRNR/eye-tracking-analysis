# Análisis de calidad de la dilatación pupilar (`ps`)

## Alcance

Este documento resume la revisión de la variable `ps` en los dos reportes CSV
de fijaciones del dataset MECO-L2 versión 2.2:

- Wave 1: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint_l2_fixation_trimmed_report_2.2.csv`
- Wave 2: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_fix_trimmed_L2_wave2_version2.2.csv`

La revisión incluyó:

- cobertura y valores ausentes;
- valores cero, negativos y no numéricos;
- distribución global y por lengua;
- diferencias entre participantes y trials;
- outliers altos y bajos;
- cambios abruptos entre fijaciones consecutivas;
- relación con `blink`, `type` y `dur`;
- duplicación e irregularidades ya identificadas en los reportes.

Según la especificación de MECO-L2, `ps` representa el tamaño pupilar
promedio durante la fijación, expresado en píxeles de cámara del EyeLink.
Por esta razón, las diferencias de escala entre participantes pueden ser
legítimas y no debe aplicarse automáticamente un único umbral global.

## Resumen general

| Wave | Filas | `ps` ausente | Porcentaje ausente | Mínimo | Mediana | Máximo |
|---|---:|---:|---:|---:|---:|---:|
| Wave 1 | 1.221.387 | 0 | 0,000% | 139 | 864 | 7.743 |
| Wave 2 | 1.448.635 | 72.364 | 4,995% | 166 | 891 | 3.924 |

No se encontraron valores cero, negativos o no numéricos. Todos los valores
observados son enteros. En Wave 2 la columna aparece como `float` porque
contiene valores ausentes, pero sus valores no ausentes tampoco tienen parte
decimal.

## Hallazgos principales

### 1. Ausencia sistemática de `ps` en Wave 2 para `ch_s`

Las 72.364 ausencias de Wave 2 corresponden exactamente a la lengua `ch_s`.
No hay valores ausentes de `ps` en las otras lenguas.

El patrón es sistemático:

```text
lang = ch_s
ps = NA
wordnum = presente
ianum = presente
word = presente
```

Los registros conservan información de fijación y de palabra, pero no tienen
asignación a oración/línea ni tamaño pupilar. También carecen de las siguientes
variables:

```text
sentnum, sent, sent.nwords,
line, line.change, line.let, line.word,
ps
```

Se observaron 355 grupos observados de participante/lengua/trial de `ch_s`
con todos sus valores `ps` ausentes. No es un patrón compatible con valores
perdidos aleatoriamente; parece indicar una etapa de procesamiento o
exportación incompleta para esta lengua.

Estas filas no deberían eliminarse automáticamente, porque todavía pueden
usarse para análisis de fijaciones y palabras. Sí deben excluirse o marcarse
para cualquier análisis que requiera dilatación pupilar.

### 2. Wave 1 tiene cobertura completa, pero presenta outliers extremos

Wave 1 no tiene valores ausentes de `ps`: todos sus 1.221.387 registros
contienen una medida pupilar.

```text
subid    = fi_5_L2
lang     = fi
trialid  = 4
fixid    = 127
ps       = 7743
```

Los valores vecinos en la secuencia temporal son:

```text
ps = 838 -> 7743 -> 843
```

El salto de aproximadamente 6.900 unidades es muy irregular. El valor está
rodeado por valores cercanos a 800 y aparece como un pico aislado, por lo que
es un candidato fuerte a artefacto de registro o pérdida temporal del
seguimiento pupilar.

Otros valores altos de Wave 1 incluyen:

```text
ee_71 / trialid=6 / fixid=169 / ps=3103
ee_71 / trialid=6 / fixid=170 / ps=2947
DU_05 / trialid=3 / fixid=57  / ps=2803
```

Los valores altos sostenidos de algunos participantes no deben clasificarse
automáticamente como errores, ya que la escala puede variar entre sujetos.

El máximo de Wave 2 es `3924`, correspondiente a `bp23`:

```text
subid    = bp23
lang     = bp
trialid  = 8
fixid    = 1
ps       = 3924
```

En Wave 2, los valores mayores de 3.000 se concentran principalmente en:

- `bp`: 565 filas;
- `ba`: 152 filas;
- `ch_t`: 90 filas;
- `ru_mo`: 7 filas.

No se encontraron valores mayores de 5.000 en Wave 2.

Algunos participantes tienen niveles altos de forma relativamente sostenida:

| Participante | Lengua | Mediana de `ps` | Máximo |
|---|---|---:|---:|
| `bp23` | `bp` | 2.715 | 3.924 |
| `bp81` | `bp` | 2.555 | 3.170 |
| `ba_50` | `ba` | 2.540,5 | 3.466 |
| `ba_19` | `ba` | 2.334 | 3.132 |
| `rum_19` | `ru_mo` | 2.278 | 3.169 |

Estos casos requieren revisión de calibración y calidad de registro, pero no
pueden descartarse únicamente por superar un umbral global.

## Variación entre participantes

La variación entre participantes es muy amplia:

| Wave | Mediana individual mínima | Mediana individual máxima |
|---|---:|---:|
| Wave 1 | 267 | 2.200 |
| Wave 2 | 301 | 2.715 |

Ejemplos de Wave 1:

```text
macmo04: mediana = 267
macmo79: mediana = 297
DU_05:   mediana = 2200
DU_10:   mediana = 2038
```

Ejemplos de Wave 2:

```text
ge_zh_25: mediana = 301
cl_40:    mediana = 328
bp23:     mediana = 2715
bp81:     mediana = 2555
```

Esto muestra que un criterio global como `ps > 2000` no es suficiente para
identificar errores. Es preferible comparar cada observación con la
distribución del mismo participante y, cuando sea posible, del mismo trial.

## Valores bajos

### Wave 1

- 44 filas tienen `ps < 200`.
- 834 filas tienen `ps < 250`.
- Las filas con `ps < 200` pertenecen a cuatro participantes.
- El mínimo es `139`, en `NO1078`.

Ejemplos:

```text
NO1078   / trialid=4  / fixid=170 / ps=139
NO1078   / trialid=4  / fixid=160 / ps=171
macmo03  / trialid=9  / fixid=96  / ps=176
spa47    / trialid=12 / fixid=390 / ps=185
```

### Wave 2

- 17 filas tienen `ps < 200`.
- 233 filas tienen `ps < 250`.
- Las filas con `ps < 200` se concentran principalmente en `sp_ch` y `se`.
- El mínimo es `166`, en `srb52`.

Ejemplos:

```text
srb52  / trialid=1  / fixid=161 / ps=166
srb3   / trialid=5  / fixid=4   / ps=170
cl_40  / trialid=11 / fixid=41  / ps=183
cl_58  / trialid=11 / fixid=238 / ps=192
```

Algunos valores bajos coinciden con `blink=1`, pero no todos. Por lo tanto,
`blink` puede explicar parte de los valores extremos, pero no es suficiente
para identificarlos todos.

## Saltos temporales e irregularidades locales

Se ordenaron las fijaciones por `start` dentro de cada participante y trial y
se calcularon las diferencias absolutas entre valores consecutivos de `ps`.

| Wave | Salto mediano | Percentil 99 | Salto máximo |
|---|---:|---:|---:|
| Wave 1 | 16 | 140 | 6.905 |
| Wave 2 | 17 | 159 | 1.312 |

Los principales ejemplos son:

```text
Wave 1, fi_5_L2 / trialid=4:
838 -> 7743 -> 843

Wave 1, ee_71 / trialid=6:
374 -> 2300 -> 2903 -> 3103

Wave 2, iitk051 / trialid=11:
1351 -> 2663 -> 1569

Wave 2, ba_14 / trialid=5:
1846 -> 605 -> 1738
```

Los saltos grandes pueden deberse a artefactos pupilares, pérdida temporal del
seguimiento, parpadeos o cambios reales de iluminación. Los picos aislados
rodeados por valores muy distintos son más sospechosos que una distribución
completa y establemente alta para un participante.

## Relación con `blink`, `type` y `dur`

### `blink`

Los promedios de `ps` son similares entre fijaciones con y sin parpadeo:

| Wave | `blink=0`: media | `blink=1`: media | `blink=0`: mediana | `blink=1`: mediana |
|---|---:|---:|---:|---:|
| Wave 1 | 911 | 903 | 866 | 849 |
| Wave 2 | 978 | 976 | 891 | 888 |

La variable `blink` no parece producir por sí sola una separación clara entre
valores normales y anómalos.

### `type`

En Wave 2, las 1.543 filas `type="out"` tienen `ps` presente. Por lo tanto,
la ausencia de `ps` no se explica por las fijaciones fuera del área de texto;
corresponde al bloque `ch_s`.

### Duración de fijación

La correlación entre `ps` y `dur` es baja:

- Wave 1: `r = 0,032` aproximadamente;
- Wave 2: `r = 0,038` aproximadamente.

No se observa una relación lineal fuerte entre duración de la fijación y
tamaño pupilar en estos datos agregados.

## Umbrales globales y limitaciones

Usando el rango intercuartílico global se obtienen los siguientes umbrales
superiores:

| Wave | Q1 | Q3 | Umbral superior Q3 + 1,5 IQR | Filas sobre el umbral |
|---|---:|---:|---:|---:|
| Wave 1 | 674 | 1.108 | 1.759 | 14.449 |
| Wave 2 | 671 | 1.210 | 2.018,5 | 31.851 |

Estos umbrales producen muchos casos porque mezclan participantes con escalas
pupilares muy diferentes. Por lo tanto, son útiles para describir la
distribución, pero no deberían usarse directamente como regla de exclusión.

Es preferible utilizar criterios relativos, por ejemplo:

- mediana y MAD por participante;
- percentiles por participante y trial;
- cambios absolutos entre fijaciones consecutivas;
- porcentaje de valores extremos por participante;
- relación con `blink` y duración;
- revisión específica de picos aislados.

## Duplicados e impacto sobre `ps`

Los 10.049 duplicados exactos de Wave 1 identificados en el informe general
también duplican los valores de `ps`. Si se calculan medias, medianas o
conteos directamente sobre el CSV, los cinco participantes afectados tendrán
peso excesivo en los resultados.

La deduplicación debe realizarse antes de cualquier análisis pupilar:

```text
Wave 1 original:        1.221.387 filas
Filas duplicadas extra:    10.049
Wave 1 deduplicada:     1.211.338 filas
```

En Wave 2 no hay duplicados de `(subid, trialid, fixid)`. Sin embargo, no se
debe utilizar `uniform_id` como clave hasta resolver los 17 participantes
daneses con ese campo ausente.

## Comparación entre waves

- La mediana de `ps` es 864 en Wave 1 y 891 en Wave 2.
- Wave 1 tiene un rango máximo mayor por el valor aislado `7743`.
- Wave 2 tiene más valores altos moderados, pero ninguno supera `5000`.
- Las distribuciones no deben compararse como si fueran mediciones de los
  mismos participantes: no hay participantes compartidos entre waves.
- Las diferencias entre lenguas y participantes pueden reflejar escalas de
  cámara, calibración, condiciones experimentales o características del
  registro, además de diferencias fisiológicas.

## Conclusiones

1. Wave 1 tiene cobertura completa de `ps`, pero contiene outliers puntuales
   importantes, especialmente el valor `7743` de `fi_5_L2`.
2. Wave 2 tiene una ausencia sistemática de `ps` para `ch_s`, que afecta
   72.364 filas.
3. Las diferencias de escala entre participantes son muy grandes; un umbral
   global no distingue adecuadamente entre variación individual y error.
4. Los saltos abruptos dentro de una secuencia temporal son más informativos
   para detectar posibles artefactos que los valores altos sostenidos de un
   participante.
5. `blink` no explica por sí solo los outliers pupilares.
6. La relación entre `ps` y duración de fijación es débil en ambas waves.
7. Los duplicados de Wave 1 deben corregirse antes de calcular estadísticas
   pupilares.

## Recomendaciones

1. Corregir o marcar los 10.049 duplicados exactos de Wave 1.
2. Excluir `ch_s` de análisis pupilares o conservarlo con una bandera explícita
   de `ps_missing`.
3. Resolver la correspondencia de `uniform_id` para los 17 participantes
   daneses de Wave 2.
4. Revisar manualmente el pico `fi_5_L2 / trialid=4 / fixid=127 / ps=7743`.
5. Revisar los saltos temporales grandes, especialmente los mayores de 1.000
   unidades dentro de un participante/trial.
6. Usar detección de outliers relativa al participante, no solamente umbrales
   globales.
7. Conservar una bandera de calidad que distinga entre:
   - `ps` ausente por `ch_s`;
   - valor extremo bajo;
   - valor extremo alto;
   - salto temporal abrupto;
   - fila duplicada;
   - fijación con `type="out"`.
8. Revisar los casos marcados contra los archivos originales de EyeLink o los
   criterios de exclusión del protocolo antes de eliminar observaciones.
