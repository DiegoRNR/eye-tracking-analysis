# Análisis de calidad de los datos de comprensión lectora

## Alcance

Este documento resume la revisión de los seis archivos CSV de comprensión
lectora del dataset MECO-L2 versión 2.2:

### Wave 1

- Total por participante:
  `wave-1/primary-data/comprehension/joint.comp.l2.csv`
- Desglose por texto:
  `wave-1/primary-data/comprehension/joint_l2_acc_breakdown.csv`
- Desglose por pregunta:
  `wave-1/primary-data/comprehension/joint_l2_acc_full_breakdown.csv`

### Wave 2

- Total por participante:
  `wave-2/primary-data/comprehension/joint_comp_L2_Wave2_trimmed.csv`
- Desglose por texto:
  `wave-2/primary-data/comprehension/joint_l2_Wave2_acc_breakdown_trimmed.csv`
- Desglose por pregunta:
  `wave-2/primary-data/comprehension/joint_l2_wave2_acc_full_breakdown_trimmed.csv`

Se revisaron:

- duplicados exactos y duplicados por clave;
- valores ausentes y cobertura por participante;
- rangos de respuestas y precisión;
- correspondencia entre los tres niveles de agregación;
- completitud de textos y preguntas;
- distribución de resultados por texto, pregunta y lengua;
- coincidencia de participantes con los datos de eye-tracking.

## Resumen de tamaños

| Wave | Participantes | Total | Por texto | Por pregunta |
|---|---:|---:|---:|---:|
| Wave 1 | 543 | 543 | 6.516 | 13.032 |
| Wave 2 | 660 | 660 | 7.920 | 15.840 |

La estructura esperada es:

```text
1 fila total por participante
12 filas por participante en el desglose por texto
24 filas por participante en el desglose por pregunta
```

Ambas waves cumplen esta estructura exactamente.

## Integridad estructural

En ambas waves:

- cada participante tiene exactamente 24 preguntas;
- cada participante tiene exactamente 12 textos;
- cada texto tiene exactamente 2 preguntas;
- `number` toma valores entre 1 y 12;
- `QUESTIONNUM` toma valores entre 1 y 2;
- no hay valores ausentes;
- no hay duplicados exactos;
- no hay sujetos repetidos en el archivo total;
- cada `subject` se asocia a un único `uniform_id`;
- cada `subject` se asocia a una única lengua.

## Duplicados y claves

No se encontraron duplicados exactos en ninguno de los seis archivos.

Las claves esperadas también son únicas:

| Archivo | Clave única verificada |
|---|---|
| Total por participante | `(subject)` |
| Desglose por texto | `(subject, number)` |
| Desglose por pregunta | `(subject, number, QUESTIONNUM)` |

No se detectaron filas duplicadas utilizando `uniform_id` en lugar de
`subject`.

## Rangos de valores

### Total por participante

En ambas waves:

```text
total_answer = 24
correct_answer >= 0
correct_answer <= 24
0 <= accuracy <= 1
```

Rangos observados:

| Wave | Mínimo de aciertos | Máximo de aciertos | Accuracy mínima | Accuracy máxima |
|---|---:|---:|---:|---:|
| Wave 1 | 4 | 24 | 0,1667 | 1,0000 |
| Wave 2 | 2 | 24 | 0,0833 | 1,0000 |

### Desglose por texto

`ACCURACY` tiene únicamente los valores esperados:

```text
0 = ninguna pregunta correcta
1 = una pregunta correcta
2 = dos preguntas correctas
```

### Desglose por pregunta

`ACCURACY` tiene únicamente los valores:

```text
0 = respuesta incorrecta
1 = respuesta correcta
```

No se encontraron valores negativos, valores mayores que el máximo permitido
ni valores decimales inesperados.

## Reconciliación entre archivos

En ambas waves se verificaron las siguientes identidades:

```text
correct_answer
  = suma de ACCURACY en el desglose por texto

correct_answer
  = suma de ACCURACY en el desglose por pregunta

total_answer
  = número de filas del desglose por pregunta
```

Todas las identidades se cumplen sin discrepancias.

Por ejemplo, para cada participante:

```text
correct_answer = sum(ACCURACY por texto)
correct_answer = sum(ACCURACY por pregunta)
total_answer   = 24
```

No se encontraron participantes cuyo total contradiga sus desgloses.

## Precisión agregada

| Wave | Media de aciertos | Media de `accuracy` | Mediana de `accuracy` |
|---|---:|---:|---:|
| Wave 1 | 17,291 de 24 | 0,7205 | 0,75 |
| Wave 2 | 17,271 de 24 | 0,7196 | 0,75 |

Los resultados globales son prácticamente iguales. Esto no implica que las
waves sean muestras longitudinales comparables: no contienen los mismos
participantes y tienen composiciones lingüísticas distintas.

## Redondeo de `accuracy` en Wave 1

Wave 1 presenta una pequeña irregularidad numérica en el archivo total:

- 27 participantes tienen una diferencia entre `accuracy` y
  `correct_answer / total_answer`;
- todos pertenecen a la lengua `ge`;
- la diferencia máxima es aproximadamente `0,000333`.

Ejemplos:

```text
correct_answer = 20
accuracy       = 0,833
20 / 24        = 0,833333...
```

```text
correct_answer = 17
accuracy       = 0,708
17 / 24        = 0,708333...
```

Esto parece ser redondeo a tres decimales, no una contradicción en el número
de respuestas. Wave 2 conserva la precisión completa y no presenta este patrón
sistemático.

## Distribución de puntajes individuales

### Wave 1

El menor resultado es:

```text
Gr34 / lang=gr / 4 de 24 / accuracy=0,1667
```

Otros resultados bajos incluyen:

```text
Gr36   / 7 de 24
L2_024 / 7 de 24
NO1170 / 7 de 24
tr_26  / 7 de 24
```

Los resultados máximos incluyen:

```text
HEB60 / 24 de 24
DU_43 / 23 de 24
```

### Wave 2

El menor resultado es:

```text
srb38 / lang=se / 2 de 24 / accuracy=0,0833
```

Otros resultados bajos incluyen:

```text
srb3    / 6 de 24
srb60   / 6 de 24
```

Los resultados máximos incluyen:

```text
rum_5   / 24 de 24
bp87    / 23 de 24
```

Estos resultados extremos son válidos dentro del rango del instrumento y no
constituyen por sí mismos errores de datos.

## Dificultad por texto

### Wave 1

| Texto | Media de aciertos | Ceros | Puntaje completo |
|---:|---:|---:|---:|
| 1 | 1,2836 | 58 | 212 |
| 2 | 1,2541 | 89 | 227 |
| 3 | 1,3904 | 29 | 241 |
| 4 | 1,5488 | 55 | 353 |
| 5 | 1,7219 | 9 | 401 |
| 6 | 1,7348 | 2 | 401 |
| 7 | 1,4107 | 58 | 281 |
| 8 | 1,6409 | 24 | 372 |
| 9 | 1,7385 | 21 | 422 |
| 10 | 1,4641 | 40 | 292 |
| 11 | 1,0866 | 48 | 95 |
| 12 | 1,0166 | 101 | 110 |

Los textos 11 y 12 son los más difíciles de Wave 1. El texto 12 tiene 101
participantes con cero respuestas correctas.

### Wave 2

| Texto | Media de aciertos | Ceros | Puntaje completo |
|---:|---:|---:|---:|
| 1 | 1,2818 | 75 | 261 |
| 2 | 1,2545 | 108 | 276 |
| 3 | 1,3742 | 51 | 298 |
| 4 | 1,5424 | 53 | 411 |
| 5 | 1,7530 | 12 | 509 |
| 6 | 1,7106 | 8 | 477 |
| 7 | 1,4515 | 57 | 355 |
| 8 | 1,6652 | 19 | 458 |
| 9 | 1,7121 | 33 | 503 |
| 10 | 1,4530 | 55 | 354 |
| 11 | 1,0939 | 59 | 121 |
| 12 | 0,9788 | 125 | 111 |

Los textos 11 y 12 también son los más difíciles de Wave 2. El texto 12 tiene
125 participantes con cero respuestas correctas.

El orden general de dificultad es muy parecido entre waves, lo que sugiere que
la codificación de textos se mantuvo estable.

## Diferencias entre preguntas

Hay diferencias importantes entre las dos preguntas de algunos textos.

| Texto | Wave | Pregunta 1 | Pregunta 2 |
|---:|---|---:|---:|
| 3 | Wave 1 | 92,45% | 46,59% |
| 3 | Wave 2 | 88,94% | 48,48% |
| 6 | Wave 1 | 97,97% | 75,51% |
| 11 | Wave 1 | 19,34% | 89,32% |
| 12 | Wave 1 | 24,49% | 77,16% |
| 12 | Wave 2 | 21,67% | 76,21% |

Las preguntas 1 de los textos 11 y 12 son especialmente difíciles, mientras
que las preguntas 2 de esos textos tienen tasas de acierto altas.

Este patrón parece reflejar diferencias de dificultad entre preguntas, no una
inconsistencia de codificación: está presente de forma similar en ambas waves.

## Participantes por lengua

### Wave 1

```text
du 47, ee 58, en 45, fi 51, ge 45, gr 48,
he 45, it 51, no 40, ru 47, sp 41, tr 25
```

### Wave 2

```text
ba 36, bp 54, ch_s 47, ch_t 42, da 25,
en_uk 50, ge_po 43, ge_zu 47, hi_iiith 53,
hi_iitk 45, ic 45, no 22, ru_mo 49,
se 43, sp_ch 45, tr 14
```

Las waves no son muestras equivalentes:

- no hay participantes compartidos;
- solamente `no` y `tr` aparecen con el mismo código en ambas;
- las variantes lingüísticas no son directamente intercambiables, por ejemplo
  `ge` frente a `ge_po`/`ge_zu` o `sp` frente a `sp_ch`.

## Coincidencia con eye-tracking

Se compararon los `uniform_id` de comprensión con los participantes de los
reportes de eye-tracking.

### Wave 1

```text
Comprensión: 543 participantes
Eye-tracking: 542 participantes
Coincidencia: 542 participantes
```

El participante de comprensión sin coincidencia en eye-tracking es:

```text
du_30
```

### Wave 2

```text
Comprensión: 660 participantes
Eye-tracking por uniform_id: 659 participantes
Coincidencia directa: 658 participantes
```

Participantes de comprensión sin coincidencia directa en eye-tracking:

```text
ba_29
ch_s_1
```

Participante presente en eye-tracking pero no en comprensión:

```text
ch_t_1
```

Estas diferencias deben considerarse al combinar precisión de comprensión con
medidas oculares.

## Conclusiones

1. Los seis archivos de comprensión tienen cobertura completa y estructura
   consistente.
2. No se encontraron duplicados, IDs repetidos ni valores fuera de rango.
3. Los totales por participante coinciden con los desgloses por texto y
   pregunta.
4. Wave 1 tiene un redondeo pequeño de `accuracy` en 27 participantes de
   `ge`.
5. Los textos 11 y 12 son claramente más difíciles en ambas waves.
6. Las preguntas 1 de los textos 11 y 12 presentan tasas de acierto muy bajas.
7. Wave 1 contiene un participante de comprensión sin coincidencia de
   eye-tracking.
8. Wave 2 tiene dos participantes de comprensión sin coincidencia directa en
   eye-tracking y uno presente solamente en eye-tracking.
9. Las diferencias globales de precisión entre waves son mínimas, pero no
   deben interpretarse como comparación longitudinal porque las muestras y
   lenguas difieren.

## Recomendaciones

1. Mantener `correct_answer` como fuente principal para los análisis globales.
2. Calcular `accuracy` como `correct_answer / total_answer` o redondear de forma
   uniforme en ambas waves.
3. Conservar los archivos por texto y por pregunta para análisis de dificultad
   específica.
4. Reportar por separado los textos 11 y 12 debido a su dificultad extrema.
5. Verificar la correspondencia de los participantes antes de combinar
   comprensión y eye-tracking.
6. No excluir automáticamente a participantes con puntuaciones bajas: los
   valores están dentro del rango válido y pueden representar diferencias
   reales de comprensión o dominio lingüístico.
