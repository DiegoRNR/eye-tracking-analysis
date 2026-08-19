# Análisis de calidad de los IDs de palabras y oraciones

## Alcance

Este documento resume la revisión de los identificadores de palabra y oración
en los dos reportes CSV de fijaciones:

- Wave 1: `MECO-L2_version-2.2/wave-1/primary-data/eye-tracking/joint_l2_fixation_trimmed_report_2.2.csv`
- Wave 2: `MECO-L2_version-2.2/wave-2/primary-data/eye-tracking/joint_fix_trimmed_L2_wave2_version2.2.csv`

Se revisaron las siguientes variables:

```text
trialid, itemid,
sentnum, sent, sent.nwords,
sent.word,
wordnum, ianum,
word, ia
```

También se compararon los valores con:

```text
data/benchmark/L2 word length and frequency.csv
```

El objetivo fue detectar inconsistencias en la jerarquía:

```text
texto -> oración -> palabra -> fijación
```

## Resumen ejecutivo

1. Los identificadores de palabra son internamente consistentes en ambas
   waves.
2. `wordnum` e `ianum` coinciden en todas las filas con palabra asignada.
3. `word` e `ia` también coinciden en todas las filas con palabra asignada.
4. Wave 2 tiene 73.907 filas sin identificadores de oración; 72.364 de ellas
   pertenecen a `ch_s`.
5. Ambas waves contienen las mismas 16 definiciones de oración cuyo
   `sent.nwords` no coincide con el benchmark.
6. Tres participantes de cada wave presentan un desplazamiento entre
   `trialid` e `itemid`.
7. Para identificar correctamente el texto, `itemid` es más confiable que
   `trialid`.

## 1. Consistencia de los IDs de palabra

### Wave 1

En Wave 1:

- `wordnum == ianum` en las 1.211.338 filas únicas;
- `word == ia` en todas las filas;
- no hay valores ausentes en `wordnum`, `ianum`, `word` o `ia`;
- cada palabra se asocia consistentemente con su texto dentro de cada
  participante/trial.

### Wave 2

En Wave 2:

- `wordnum == ianum` en las 1.447.092 filas con palabra asignada;
- `word == ia` en todas esas filas;
- las 1.543 filas restantes corresponden a `type="out"` y no tienen palabra
  asignada;
- no se detectó corrupción general de los IDs de palabra.

Ejemplo de una fila normal:

```text
wordnum = 24
ianum   = 24
word    = pencil.
ia      = pencil.
```

Los espacios del ejemplo solamente alinean visualmente los valores; los nombres
correctos de las columnas son `wordnum` e `ianum`.

## 2. Ausencia de IDs de oración en Wave 2

Wave 1 no tiene valores ausentes en los identificadores de oración.

Wave 2 tiene 73.907 filas sin:

```text
sentnum
sent
sent.nwords
sent.word
```

Estas filas se dividen en:

| Tipo de fila | Filas |
|---|---:|
| `ch_s` | 72.364 |
| `type="out"` | 1.543 |

Las filas `type="out"` no tienen asignación a palabra u oración, lo cual es
esperable.

Las filas de `ch_s`, en cambio, sí conservan información de palabra:

```text
wordnum = presente
word    = presente
ia      = presente
sentnum = NA
sent    = NA
```

Esto indica una pérdida específica de la asociación palabra-oración para
`ch_s`, no una ausencia completa del registro de fijación.

Las filas `ch_s` pueden utilizarse para análisis a nivel de palabra, pero no
para análisis que requieran agrupar directamente por oración sin reconstruir
la asociación.

## 3. Inconsistencias de `sent.nwords`

Se comparó `sent.nwords` con el número de palabras definido en el benchmark.
En ambas waves aparecen exactamente las mismas 16 combinaciones
`itemid/sentnum` con discrepancias.

| `itemid` | `sentnum` | `sent.nwords` | Benchmark |
|---:|---:|---:|---:|
| 1 | 6 | 22 | 23 |
| 5 | 4 | 16 | 18 |
| 9 | 3 | 25 | 26 |
| 10 | 1 | 10 | 11 |
| 10 | 2 | 10 | 11 |
| 10 | 7 | 17 | 18 |
| 11 | 1 | 11 | 13 |
| 11 | 2 | 10 | 11 |
| 11 | 6 | 18 | 34 |
| 11 | 7 | 15 | sin correspondencia |
| 12 | 1 | 14 | 21 |
| 12 | 2 | 7 | 26 |
| 12 | 3 | 25 | 16 |
| 12 | 4 | 16 | 45 |
| 12 | 5 | 44 | 40 |
| 12 | 6 | 40 | sin correspondencia |

La cantidad de filas pertenecientes a estas definiciones es:

| Wave | Grupos de oración afectados | Filas afectadas |
|---|---:|---:|
| Wave 1 | 16 | 254.068 |
| Wave 2 | 16 | 287.682 |

No todas las filas afectadas muestran una violación explícita de
`sent.word <= sent.nwords`, porque no todas las palabras de una oración tienen
que haber sido fijadas. Sin embargo, la metadata de la oración es inconsistente
con la secuencia completa de palabras.

### Violaciones explícitas

También se encontraron filas donde:

```text
sent.word > sent.nwords
```

Estas filas son especialmente claras porque el índice observado de palabra
dentro de la oración supera el número declarado de palabras:

| Wave | Filas con `sent.word > sent.nwords` |
|---|---:|
| Wave 1 | 15.682 |
| Wave 2 | 16.641 |

Ejemplo:

```text
itemid      = 1
sentnum     = 6
sent.nwords = 22
sent.word   = 23
wordnum     = 161
```

En este caso, `sent.word=23` indica que la oración contiene al menos 23
posiciones de palabra, mientras que `sent.nwords` declara solamente 22.

## 4. `itemid` frente a `trialid`

La comparación con el benchmark muestra que los textos coinciden correctamente
cuando se utiliza:

```text
(itemid, sentnum, ianum)
```

La comparación produce discrepancias cuando se utiliza solamente:

```text
(trialid, sentnum, ianum)
```

Esto indica que `itemid` identifica el texto observado de forma más confiable,
mientras que `trialid` puede representar la posición del trial o contener un
desplazamiento para algunos participantes.

## 5. Desplazamientos específicos en Wave 1

En Wave 1, tres participantes presentan una diferencia sistemática entre
`trialid` e `itemid`:

```text
Gr45    / lang=gr
L2_025  / lang=it
spa36   / lang=sp
```

En los trials afectados se cumple:

```text
itemid = trialid + 1
```

Ejemplos:

```text
Gr45 / trialid=7  / itemid=8
Gr45 / trialid=8  / itemid=9
Gr45 / trialid=9  / itemid=10

L2_025 / trialid=6  / itemid=7
L2_025 / trialid=7  / itemid=8

spa36 / trialid=5 / itemid=6
spa36 / trialid=6 / itemid=7
```

El desplazamiento afecta:

- 18 grupos participante/trial;
- 3.407 filas;
- los textos, palabras y oraciones de esos grupos.

Ejemplo de conflicto:

```text
lang    = gr
trialid = 7
itemid  = 8
word    = Hibernation
```

El texto `Hibernation` corresponde al `itemid=8`, no al `trialid=7`.

## 6. Desplazamientos específicos en Wave 2

En Wave 2, tres participantes presentan el mismo tipo de problema:

```text
BA_54 / lang=ba
bp23  / lang=bp
srb38 / lang=se
```

Ejemplos:

```text
bp23  / trialid=3  / itemid=4
bp23  / trialid=4  / itemid=5
bp23  / trialid=5  / itemid=6

srb38 / trialid=2 / itemid=3
srb38 / trialid=3 / itemid=4

BA_54 / trialid=11 / itemid=12
```

En estos casos también se cumple:

```text
itemid = trialid + 1
```

El desplazamiento afecta:

- 20 grupos participante/trial;
- 4.358 filas.

## 7. Validación con el benchmark

Al utilizar `itemid` como identificador del texto:

- `word` coincide con `ia` en todas las filas con IDs válidos;
- los valores de `ia` coinciden con el benchmark en todas las filas
  comparables;
- los aparentes errores encontrados al usar `trialid` desaparecen.

Esto confirma que muchas discrepancias aparentes no son errores de palabra,
sino consecuencia de usar `trialid` en lugar de `itemid` para identificar el
texto.

## 8. Interpretación de la secuencia de filas

El orden físico de las filas en los CSV no es una secuencia limpia de palabras
ni de eventos temporales. Se observaron descensos frecuentes de `sentnum`,
`sent.word`, `wordnum` e `ianum` en el orden original.

Esto no debe interpretarse automáticamente como una inconsistencia de IDs. Las
filas están organizadas según la estructura del reporte y las fijaciones, no
necesariamente en orden cronológico o creciente de palabra.

Para validar secuencias se recomienda ordenar por:

```text
subid, trialid, start
```

y utilizar `itemid` para comprobar la identidad del texto.

## Comparación entre waves

| Comprobación | Wave 1 | Wave 2 |
|---|---:|---:|
| `wordnum == ianum` en filas válidas | Sí | Sí |
| `word == ia` en filas válidas | Sí | Sí |
| Filas sin IDs de oración | 0 | 73.907 |
| Grupos con desplazamiento `trialid/itemid` | 18 | 20 |
| Participantes con desplazamiento | 3 | 3 |
| Definiciones inconsistentes de `sent.nwords` | 16 | 16 |
| Validación de texto correcta usando `itemid` | Sí | Sí |

## Conclusiones

1. No se detectó corrupción general de los IDs de palabra.
2. `wordnum`, `ianum`, `word` e `ia` son consistentes cuando la fijación tiene
   una palabra asignada.
3. Wave 2 tiene una pérdida sistemática de información de oración para `ch_s`.
4. Ambas waves contienen las mismas 16 inconsistencias en `sent.nwords`.
5. Seis participantes en total presentan desplazamientos entre `trialid` e
   `itemid`, tres en cada wave.
6. La identidad del texto debe determinarse usando `itemid`, no únicamente
   `trialid`.
7. Las filas `type="out"` deben mantenerse separadas porque no tienen IDs de
   palabra ni oración por definición.

## Recomendaciones

1. Usar `(subid, itemid, sentnum, ianum)` como clave jerárquica del contenido.
2. Marcar los seis participantes con desplazamiento entre `trialid` e
   `itemid`.
3. Revisar los 16 valores inconsistentes de `sent.nwords` en ambas waves.
4. Excluir o marcar las 72.364 filas `ch_s` sin información de oración.
5. Mantener separadas las 1.543 filas `type="out"` de Wave 2.
6. Validar las palabras contra el benchmark usando `itemid`.
7. No utilizar el orden físico del CSV como evidencia de secuencia de palabras.
8. Documentar explícitamente si `trialid` representa posición experimental y
   `itemid` representa identidad del texto.
