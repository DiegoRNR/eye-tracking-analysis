# Análisis de calidad de los datos de sacadas

## Alcance

Este documento resume la revisión de los dos reportes CSV de sacadas del
dataset MECO-L2 versión 2.2:

- Wave 1: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint_sac_trimmed_wave1_2.2.csv`
- Wave 2: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_sac_trimmed_L2_wave2_version2.2.csv`

La revisión incluyó:

- duplicados exactos y duplicados por clave de evento;
- cobertura por participante, lengua y trial;
- distribución de `SAC` y `BLINK`;
- valores ausentes y patrones dependientes del tipo de evento;
- consistencia temporal y geométrica;
- rangos y outliers de amplitud, distancia y velocidad;
- comparación con los reportes de fijaciones.

Las conclusiones distinguen entre valores plausiblemente esperables por la
naturaleza del evento y anomalías que requieren revisión adicional.

## Resumen de tamaños

| Wave | Filas | Columnas | `SAC` | `BLINK` | Participantes | Grupos participante/trial |
|---|---:|---:|---:|---:|---:|---:|
| Wave 1 | 1.215.649 | 33 | 1.142.997 | 72.652 | 542 | 6.501 |
| Wave 2 | 1.049.467 | 35 | 998.942 | 50.525 | 680 | 5.869 |

## Hallazgos principales

### 1. Duplicados exactos en Wave 1

Wave 1 contiene:

- 10.006 filas adicionales duplicadas exactamente;
- 20.012 filas pertenecientes a grupos duplicados;
- 10.006 claves duplicadas `(subid, trialid, sacid)`;
- 60 grupos participante/trial afectados.

Los duplicados se concentran en los mismos cinco participantes ingleses
identificados en el reporte de fijaciones:

```text
macmo03, macmo06, macmo11, macmo38, macmo39
```

Los duplicados incluyen eventos `SAC` y `BLINK`. Después de eliminar
duplicados exactos, Wave 1 tendría 1.205.643 filas.

Wave 2 no contiene duplicados exactos ni duplicados de
`(subid, trialid, sacid)`.

### 2. Diferencia importante de cobertura en Wave 2

Wave 2 tiene 7.959 grupos participante/lengua/trial en el reporte de
fijaciones, pero solamente 5.869 grupos en el reporte de sacadas.

Por lo tanto, existen:

- 2.090 combinaciones participante/trial presentes en fijaciones pero
  ausentes en sacadas;
- aproximadamente 394.060 fijaciones pertenecientes a esas combinaciones sin
  un reporte correspondiente de sacadas.

Los grupos ausentes no contienen únicamente fijaciones `out`: la mayoría tiene
fijaciones normales `type="in"`.

Ejemplo:

```text
BA_08 / trialid=4
```

Este grupo tiene 179 fijaciones en el reporte de fijaciones, pero no tiene
registros correspondientes en el reporte de sacadas.

Los grupos ausentes se distribuyen ampliamente entre lenguas:

```text
bp:        198
ch_t:      193
se:        182
sp_ch:     182
ru_mo:     170
ge_po:     155
ge_zu:     143
ic:        127
no:        125
en_uk:     122
hi_iitk:   119
ba:        115
da:        112
hi_iiith:   77
tr:         70
```

Este es uno de los problemas más importantes detectados, porque el reporte de
sacadas de Wave 2 no cubre todos los grupos presentes en el reporte de
fijaciones.

### 3. Columnas completamente ausentes en Wave 2

Wave 2 contiene dos columnas completamente vacías:

```text
trial
supplementary_id
```

Ambas tienen 1.049.467 valores ausentes.

Además, `uniform_id` está ausente para 17 participantes daneses, afectando
33.293 filas del reporte de sacadas. No debe utilizarse `uniform_id` como
única clave hasta resolver esos identificadores.

## Consistencia temporal

Todas las filas de ambas waves cumplen exactamente:

```text
dur = stop - start + 1
```

No se encontraron duraciones cero, duraciones negativas ni eventos con
`stop < start`.

Después de eliminar duplicados exactos en Wave 1 tampoco se observaron
intervalos temporales solapados dentro de un participante/trial.

### Duraciones por tipo de evento

| Wave | Tipo | Mediana | Máximo |
|---|---|---:|---:|
| Wave 1 | `SAC` | 24 ms | 200 ms |
| Wave 1 | `BLINK` | 157 ms | 24.290 ms |
| Wave 2 | `SAC` | 24 ms | 531 ms |
| Wave 2 | `BLINK` | 171 ms | 44.342 ms |

Las duraciones extremas pertenecen a `BLINK`, no a sacadas normales.

Ejemplos:

```text
Wave 1:
L2_025 / trialid=1 / sacid=58  / dur=24290 ms
spa47  / trialid=12 / sacid=109 / dur=18280 ms

Wave 2:
rum_26 / trialid=8 / sacid=21 / dur=44342 ms
NO5134 / trialid=8 / sacid=12 / dur=4070 ms
```

Estos valores pueden corresponder a parpadeos prolongados o pérdida del
seguimiento, pero deberían revisarse.

## Consistencia geométrica

En las filas donde las variables están presentes se verifican las relaciones:

```text
dx = xe - xs
dy = ye - ys
dist.px = sqrt(dx^2 + dy^2)
```

Los valores negativos de `dx` y `dy` no son necesariamente errores, porque
representan la dirección del movimiento. Del mismo modo, los valores negativos
de `dist.let` pueden corresponder a regresiones y los valores negativos de
`dist.line` a movimientos hacia una línea anterior.

### Coordenadas incompletas en Wave 2

Existe una fila con coordenadas finales ausentes:

```text
subid   = ch31
lang    = ch_s
trialid = 7
sacid   = 162
msg     = BLINK
xs      = 921.8
xe      = NA
ys      = 720.0
ye      = NA
```

Es el único evento con coordenadas de inicio y final incompletas.

## Variables derivadas ausentes

### Wave 1

Los eventos `SAC` tienen completas las variables principales:

```text
xs, xe, ys, ye,
xsn, xen, ysn, yen,
dx, dy,
dist.px, amp.px, amp.deg,
pv.px, pv.deg
```

Solamente hay ausencias menores en variables relacionadas con palabras:

- `lets`;
- `lete`;
- `dist.let`.

Estas ausencias afectan 414 eventos `SAC` en total y no parecen concentrarse
en una única lengua.

### Wave 2: lengua `ch_s`

Los 68.258 eventos `SAC` de `ch_s` carecen de:

```text
lines, linee, dist.line,
lets, lete, dist.let,
dx, dy, dist.px,
amp.px, pv.px
```

Sin embargo, mantienen `amp.deg` y `pv.deg`. Esto es inconsistente porque las
variables angulares están disponibles mientras que las variables pixeladas y
geométricas equivalentes están ausentes.

### Wave 2: lengua `ch_t`

Además, 11.312 eventos `SAC` de `ch_t` carecen de:

```text
dy, dist.px, amp.px, pv.px
```

También conservan `amp.deg` y `pv.deg`.

En conjunto, Wave 2 tiene **80.040 eventos `SAC`** con al menos una ausencia
en variables geométricas o de velocidad derivadas.

El patrón sugiere un problema específico de procesamiento o exportación para
`ch_s` y `ch_t`, no datos ausentes aleatoriamente.

## Identificadores `sacid`

- En Wave 1, los duplicados de `sacid` coinciden con los duplicados exactos
  del archivo.
- En Wave 2 no hay duplicados de `(subid, trialid, sacid)`.
- No se observaron saltos en la secuencia de `sacid` dentro de los grupos
  existentes.
- Wave 1 tiene los mismos grupos participante/trial que el reporte de
  fijaciones.
- Wave 2 no tiene todos los grupos del reporte de fijaciones.

## Outliers geométricos y cinemáticos

### Distancia en píxeles

Sacadas con `dist.px > 2000`:

| Wave | Cantidad |
|---|---:|
| Wave 1 | 6 |
| Wave 2 | 7 |

Ejemplos de Wave 1:

```text
macmo79  / trialid=6 / sacid=100 / dist.px=2417
macmo79  / trialid=7 / sacid=89  / dist.px=2193
fi_11_L2 / trialid=3 / sacid=109 / dist.px=2143
```

Ejemplos de Wave 2:

```text
bp86    / trialid=1 / sacid=294 / dist.px=2293
iitk070 / trialid=3 / sacid=4   / dist.px=2274
bp86    / trialid=1 / sacid=307 / dist.px=2266
```

Son candidatos para revisión, aunque podrían corresponder a sacadas amplias
o movimientos entre líneas.

### Amplitud angular

El máximo de `amp.deg` es:

- Wave 1: `42,36`;
- Wave 2: `40,51`.

Hay aproximadamente 60.000 eventos por wave con `amp.deg > 10`. Esto puede
indicar movimientos muy amplios, diferencias de calibración, una escala
angular que debe verificarse o valores derivados de coordenadas anómalas.

Ejemplos:

```text
Wave 1: HEB61 / trialid=5 / sacid=119 / amp.deg=42.36
Wave 2: cl_33 / trialid=8 / sacid=45  / amp.deg=40.51
```

### Velocidad pico

Los valores máximos de `pv.px` para eventos `SAC` son:

- Wave 1: `628.050`;
- Wave 2: `303.596`.

Ejemplos:

```text
Wave 1: HEB65    / trialid=6  / sacid=169 / pv.px=628050
Wave 2: iiith013 / trialid=11 / sacid=12  / pv.px=303596
```

`pv.deg` alcanza `3270` en eventos `SAC` de ambas waves. En Wave 2 alcanza
`5105,26` considerando todos los tipos de evento, especialmente eventos
`BLINK` de `ch_s`.

Estos valores deberían revisarse para determinar si corresponden a una escala,
truncamiento o artefacto de cálculo.

## Comparación entre waves

- Wave 1 tiene 1.215.649 filas y Wave 2 tiene 1.049.467.
- Wave 1 contiene duplicados exactos; Wave 2 no.
- Wave 1 cubre todos los grupos participante/trial presentes en su reporte de
  fijaciones.
- Wave 2 omite 2.090 grupos que sí aparecen en fijaciones.
- Wave 2 tiene campos completamente vacíos (`trial` y
  `supplementary_id`).
- Wave 2 presenta ausencia sistemática de variables pixeladas para `ch_s` y
  parte de `ch_t`.
- Las relaciones temporales y geométricas básicas son consistentes cuando los
  datos están disponibles.

## Conclusiones

1. Wave 1 contiene 10.006 filas duplicadas exactamente, afectando cinco
   participantes ingleses.
2. Wave 2 tiene una pérdida importante de cobertura: 2.090 grupos
   participante/trial presentes en fijaciones no aparecen en sacadas.
3. Wave 2 tiene problemas estructurales con las columnas `trial` y
   `supplementary_id`, completamente vacías.
4. Wave 2 presenta ausencia sistemática de variables pixeladas para `ch_s` y
   `ch_t`, aunque conserva medidas angulares.
5. Las variables temporales y las relaciones geométricas básicas son
   consistentes cuando los datos están presentes.
6. Las duraciones extremas corresponden principalmente a `BLINK`, no a `SAC`.
7. Hay valores extremos en `dist.px`, `amp.deg`, `pv.px` y `pv.deg` que deben
   marcarse para revisión.
8. Los valores negativos de `dist.let`, `dist.line`, `dx` o `dy` no deben
   eliminarse automáticamente porque pueden representar la dirección del
   movimiento.

## Recomendaciones

1. Eliminar o marcar los duplicados exactos de Wave 1 antes de calcular
   estadísticas.
2. Comparar sistemáticamente los 2.090 grupos ausentes de Wave 2 con sus
   registros de fijaciones.
3. Mantener una bandera para grupos con fijaciones pero sin reporte de
   sacadas.
4. Excluir o marcar `ch_s` y los 11.312 eventos afectados de `ch_t` para
   análisis que requieran variables pixeladas.
5. Resolver los 17 participantes daneses con `uniform_id` ausente.
6. Revisar los eventos `BLINK` con duraciones extremas.
7. Revisar sacadas con `dist.px > 2000`, `amp.deg > 10`, velocidades pico
   extremas o coordenadas incompletas.
8. Mantener separados los análisis de `SAC` y `BLINK`.
9. Revisar los casos marcados contra los archivos originales de EyeLink o los
   criterios de exclusión del protocolo antes de eliminar observaciones.
