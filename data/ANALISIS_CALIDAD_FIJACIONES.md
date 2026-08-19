# Análisis de calidad de los datos de fijaciones

## Alcance

Este documento resume una revisión de los dos reportes CSV de fijaciones del
dataset MECO-L2 versión 2.2:

- Wave 1: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint_l2_fixation_trimmed_report_2.2.csv`
- Wave 2: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_fix_trimmed_L2_wave2_version2.2.csv`

La revisión incluyó:

- duplicados exactos y duplicados según claves de evento;
- identificadores de participante y completitud por participante/trial;
- valores ausentes y patrones de ausencia;
- consistencia temporal (`start`, `stop` y `dur`);
- rangos y valores extremos de variables numéricas;
- diferencias de estructura y distribución entre ambas waves.

Los resultados describen anomalías observadas en los CSV. Una anomalía no
implica necesariamente que el registro deba eliminarse: algunas pueden ser
consecuencia esperable del trimming o de la definición de los reportes de
popEye.

## Resumen de tamaños

| Wave | Filas | Columnas | `subid` distintos | `uniform_id` distintos | Lenguas |
|---|---:|---:|---:|---:|---:|
| Wave 1 | 1.221.387 | 73 | 542 | 542 | 12 |
| Wave 2 | 1.448.635 | 72 | 680 | 663 | 16 |

La diferencia de una columna es esperable: Wave 1 contiene `trial`, mientras
que Wave 2 no. El resto de las columnas de fijaciones coincide.

## Hallazgos principales

### 1. Duplicación exacta en Wave 1

Wave 1 contiene **10.049 filas adicionales que son duplicados exactos** de
otra fila. Los duplicados afectan exclusivamente a cinco participantes de
la lengua inglesa:

| `subid` | `uniform_id` | Filas duplicadas |
|---|---|---:|
| `macmo03` | `en_3` | 4.160 |
| `macmo06` | `en_6` | 3.830 |
| `macmo11` | `en_11` | 3.632 |
| `macmo38` | `en_38` | 3.214 |
| `macmo39` | `en_39` | 5.262 |

En total, los duplicados aparecen en **60 combinaciones de participante y
trial**. En cada combinación afectada, todas las filas del grupo están
duplicadas. Por ejemplo, el grupo `macmo39` / `trialid=1` tiene 616 filas y
las 616 aparecen dos veces.

La duplicación también se observa en las claves de evento:

```text
clave: (subid, trialid, fixid)
grupos duplicados: 10.049
filas adicionales: 10.049
```

El tamaño de Wave 1 después de eliminar duplicados exactos sería **1.211.338
filas**. La deduplicación debe hacerse conservando una sola copia de cada
fila exacta; no se recomienda resolver este problema usando solamente
`uniform_id`, porque las claves deben conservar también el participante y el
trial.

### 2. `uniform_id` ausente para 17 participantes en Wave 2

Wave 2 contiene 680 valores distintos de `subid`, pero solamente 663 valores
distintos de `uniform_id`. Hay **17 participantes daneses** cuyo
`uniform_id` está ausente en todas sus filas. En conjunto representan
**33.497 fijaciones**.

Los participantes afectados son:

```text
DKAAP1L2, DKAAP2L2, DKAAP3L2, DKAAP4L2, DKAAP5L2,
DKAAP6L2, DKAAP7L2, DKAAP8L2,
DKAAT3L2, DKAAT4L2, DKAAT5L2, DKAAT6L2, DKAAT7L2,
DKAAT8L2, DKAAT9L2, DK_AA_T1, DK_AA_T2
```

Cada uno de estos participantes tiene registros en los 12 trials. Por lo
tanto, parece tratarse de un problema de integración o normalización de
identificadores, no de ausencia de datos de eye-tracking.

Esto produce una diferencia importante según la clave utilizada:

| Clave | Resultado en Wave 2 |
|---|---:|
| `(subid, trialid, fixid)` duplicada | 0 filas adicionales |
| `(uniform_id, trialid, fixid)` duplicada | 30.436 filas adicionales |

Las aparentes duplicaciones con `uniform_id` son causadas por el valor
ausente compartido por los 17 participantes. Para análisis de eventos debe
usarse temporalmente `subid` o corregirse primero la tabla de correspondencia
entre `subid` y `uniform_id`.

### 3. Ausencia sistemática de datos para `ch_s` en Wave 2

Hay **72.364 filas** correspondientes a la lengua `ch_s` que tienen ausentes

```text
sentnum, sent, sent.nwords,
line, line.change, line.let, line.word,
ps
```

Los campos de palabra siguen presentes, por ejemplo `wordnum`, `word`, `ianum`
y `ia`. Esto indica que las filas no están completamente vacías: tienen
información de fijación y asignación a palabras, pero no tienen asignación a
oración/línea ni tamaño pupilar.

El patrón afecta a todos los participantes `ch_s` y a los 12 trials. Por
ejemplo, en `ch_s` faltan 7.659 filas en el trial 1 y 6.589 filas en el trial
12. No parece un conjunto de valores ausentes aleatorios.

Este es el ejemplo conceptual de una fila afectada:

```text
lang = ch_s
wordnum = presente
ianum = presente
word = presente
sentnum = NA
line = NA
ps = NA
```

Debe verificarse si `ch_s` fue procesado con una plantilla de texto distinta
o si faltó una etapa de asignación de oraciones/líneas. Estas filas no deberían
eliminarse automáticamente, porque conservan medidas a nivel de fijación y
palabra.

### 4. Fijaciones fuera del área de texto en Wave 2

Wave 2 contiene **1.543 filas con `type="out"`**. Estas filas no tienen

```text
type = out
xs, ys, xn, yn, start, stop, dur = presentes
wordnum, ianum, sentnum, sent = NA
```

Este patrón es coherente con una fijación fuera del área de texto y debe
distinguirse de un error general de importación. Wave 1 no contiene filas con
`type="out"`.

### 5. Combinaciones participante/trial incompletas

En Wave 1 faltan tres combinaciones de participante y trial. Las tres
corresponden al `trialid=12`:

```text
Gr45   / trialid=12
L2_025 / trialid=12
spa36  / trialid=12
```

Los participantes sí aparecen en otros trials, por lo que se trata de
participantes parcialmente observados, no de identificadores completamente
ausentes.

En Wave 2 también hay participantes con menos de 12 trials. Conviene generar
la tabla de completitud antes de hacer análisis que requieran un panel
participante-trial balanceado.

### 6. Saltos en `fixid`

Se observaron saltos en la secuencia de `fixid`:

- Wave 1: 388 grupos participante/trial con al menos un salto;
- Wave 2: 17 grupos participante/trial con al menos un salto.

Ejemplos de Wave 1:

```text
DU_04 / trialid=9:  fixid 1..158, falta 5
DU_31 / trialid=9:  faltan 7, 16 y 87
```

Ejemplos de Wave 2:

```text
ch02 / trialid=11: faltan 126 dentro de 1..130
ch19 / trialid=10: faltan 9, 26 y 28
```

No se observaron duplicados de `(subid, trialid, fixid)` en Wave 2. Los
saltos pueden deberse a eventos eliminados durante el trimming, por lo que
requieren contrastarse con la documentación del procesamiento antes de
considerarse errores.

## Consistencias confirmadas

### Relación temporal

Todas las filas de ambas waves cumplen exactamente:

```text
dur = stop - start + 1
```

No se encontraron duraciones cero o negativas. La suma `+1` es necesaria
porque los límites están representados como intervalos inclusivos en estos
CSV.

### Duplicados por identificador de evento

Después de distinguir `subid` de `uniform_id`:

- Wave 1: los duplicados de `(subid, trialid, fixid)` coinciden con los
  duplicados exactos descritos arriba;
- Wave 2: no hay duplicados de `(subid, trialid, fixid)`;
- no hay participantes compartidos entre las dos waves;
- no hay valores compartidos de `uniform_id` entre las dos waves.

## Valores extremos para revisión

Estos valores no fueron clasificados automáticamente como errores, pero son
buenos candidatos para inspección:

| Variable | Wave 1 | Wave 2 |
|---|---:|---:|
| Duración máxima | 5.939 ms | 10.553 ms |
| Duraciones mayores de 2.000 ms | 54 | 82 |
| Coordenadas `xs` negativas | 23 | 129 |
| Coordenadas `ys` negativas | 55 | 621 |
| Coordenadas `xs` con valor absoluto mayor que 3.000 | 0 | 8 |

Ejemplos de fijaciones largas:

```text
Wave 1: DU_38 / trialid=2 / fixid=31 / dur=5939 ms
Wave 1: ru_56 / trialid=10 / fixid=77 / dur=5532 ms
Wave 2: NO5169 / trialid=7 / fixid=179 / dur=10553 ms
Wave 2: NO5169 / trialid=12 / fixid=164 / dur=6114 ms
```

Las fijaciones muy largas pueden reflejar pausas, problemas de registro,
parpadeos o participantes que abandonaron temporalmente la lectura. Deben
revisarse según los criterios de exclusión del estudio.

## Comparación entre waves

- Wave 2 tiene más participantes, más lenguas y más filas.
- No hay participantes comunes entre waves, por lo que no es posible tratar
  las waves como mediciones repetidas de los mismos sujetos.
- Solamente los códigos `no` y `tr` aparecen en ambas waves; aun así, las
  muestras no son necesariamente comparables.
- La mediana de duración es muy similar: 205 ms en Wave 1 y 207 ms en Wave 2.
- El esquema es esencialmente común, salvo `trial`, presente solamente en
  Wave 1.
- Las diferencias más importantes no son de distribución temporal, sino de
  calidad/integridad: duplicación en Wave 1, identificadores ausentes en Wave
  2 y ausencia sistemática de variables para `ch_s`.

## Recomendaciones para el análisis

1. En Wave 1, eliminar o marcar las 10.049 filas duplicadas exactas antes de
   calcular conteos de fijaciones o medidas agregadas.
2. En Wave 2, no usar `uniform_id` como clave única hasta resolver los 17
   participantes daneses sin identificador normalizado.
3. Mantener una bandera para las filas `type="out"` y excluirlas solamente
   de análisis que requieran asignación a palabra u oración.
4. Mantener una bandera específica para las 72.364 filas `ch_s` con datos de
   oración/línea/pupila ausentes.
5. Documentar el tratamiento de los participantes/trials incompletos y de
   los saltos en `fixid`.
6. Revisar las fijaciones extremadamente largas y las coordenadas extremas
   contra los criterios de calidad del protocolo experimental.
