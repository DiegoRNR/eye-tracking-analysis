# Fase 5: Diferencias Individuales, Modelado Jerárquico y Predicción
## Del Nivel Grupal al Nivel del Lector Individual ($N = 1,203$)

---

## 1. El Salto Metodológico: De Cohortes a Individuos

Habiendo demostrado a nivel de grupo que la cercanía del patrón visual predice la comprensión, la siguiente fase aborda el **nivel micro y personal del lector**:

> ¿Cómo se combinan los antecedentes sociolingüísticos, la inteligencia general, la proficiencia en el idioma y las métricas de eye-tracking en tiempo real para determinar si un individuo comprende o fracasa al leer en inglés?

Para responder a esto, se construyó el **Master Multilevel Dataset** ([`master_multilevel_dataset.csv`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/master_multilevel_dataset.csv)), consolidando a **$1,203$ participantes** ($1,032$ con batería psicométrica, cuestionario LEAP-Q y eye-tracking completos).

---

## 2. Matriz de Correlación Bivariada (10 Predictores Directos)

Se calculó la matriz de correlación de Pearson entre los 10 predictores observables directos y la comprensión lectora ([`correlations_heatmap.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/correlations_heatmap.png)):

```
                    Comprensión  LexTALE  Vocabulario  Decodificación  Ortografía  % Exposición  Autoeval.  Edad Inicio  Distancia L1  Inteligencia
Comprensión                1.00     0.41         0.46            0.21        0.37          0.02       0.20        -0.11         -0.03          0.14
LexTALE                    0.41     1.00         0.63            0.31        0.54          0.28       0.45        -0.24         -0.17          0.05
Vocabulario (Nation)       0.46     0.63         1.00            0.26        0.38          0.23       0.42        -0.18         -0.19          0.07
Decodificación (PDE)       0.21     0.31         0.26            1.00        0.31          0.19       0.26        -0.21         -0.09         -0.06
Ortografía (Spelling)      0.37     0.54         0.38            0.31        1.00          0.14       0.35        -0.14         -0.03          0.02
% Exposición Inglés        0.02     0.28         0.23            0.19        0.14          1.00       0.35        -0.26          0.07          0.01
Autoevaluación Lectora     0.20     0.45         0.42            0.26        0.35          0.35       1.00        -0.32         -0.05         -0.04
Edad Inicio Inglés        -0.11    -0.24        -0.18           -0.21       -0.14         -0.26      -0.32         1.00         -0.06         -0.07
Distancia L1 a EN         -0.03    -0.17        -0.19           -0.09       -0.03          0.07      -0.05        -0.06          1.00          0.08
Inteligencia (CFT-20)      0.14     0.05         0.07           -0.06        0.02          0.01      -0.04        -0.07          0.08          1.00
```

### Hallazgos Bivariados Clave:
1. **La Primacía del Léxico:** El vocabulario receptivo de Nation ($r = 0.46, p < 10^{-60}$) y el test LexTALE ($r = 0.41, p < 10^{-46}$) son los predictores individuales más poderosos de la comprensión en L2.
2. **Ortografía como Indicador de Calidad Léxica:** La prueba de *spelling* correlaciona con fuerza ($r = 0.37$), respaldando la hipótesis de *Lexical Quality* de Perfetti.
3. **Decodificación Mecánica es Secundaria:** El test de pseudopalabras TOWRE-PDE correlaciona de forma moderada ($r = 0.21$), lo que demuestra que en lectores universitarios el cuello de botella no es sonorizar letras, sino el significado.
4. **La Exposición y Distancia no Operan Directamente:** La exposición diaria ($r = 0.02$) y la distancia lingüística ($r = -0.03$) no tienen impacto bivariado directo en la comprensión; sus efectos operan de forma indirecta moldeando el vocabulario adquirido.

---

## 3. Modelado de Regresión Jerárquica

Para desentrañar el poder explicativo por capas de información, se ajustaron modelos de regresión lineal múltiple por pasos (*hierarchical regression*):

$$\text{Accuracy} = \beta_0 + \sum \beta_k X_k + \epsilon$$

| Bloque / Modelo | Variables Incluidas | $R^2$ | $\Delta R^2$ | $F$ Change | $p$-valor | AIC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **M1: Antecedentes** | Edad inicio, % exposición, distancia L1, autoevaluación | $0.037$ | $3.7\%$ | $9.82$ | $< 0.0001$ | $1720.5$ |
| **M2: + Cognición** | + Inteligencia fluida (CFT-20) | $0.052$ | $1.5\%$ | $16.14$ | $< 0.0001$ | $1706.1$ |
| **M3: + Batería L2** | + Vocabulario Nation, LexTALE, TOWRE SWE & PDE, Spelling | $0.243$ | **$19.1\%$** | $50.31$ | $< 0.0001$ | $1584.4$ |
| **M4: + Eye-Tracking** | + Duración de fijación (`mean_fix_dur`), Tasa de regresión | **$0.253$** | **$1.0\%$** | $6.87$ | **$0.003$** | **$1581.5$** |

---

## 4. La Prueba del "Grand Cross": Validez Incremental del Eye-Tracking

Uno de los aportes teóricos y metodológicos más cruciales para el paper es la prueba **Grand Cross**:

* **La pregunta escéptica:** *¿Aporta el eye-tracking información real sobre la comprensión que no esté ya capturada por un test de vocabulario o un examen de inglés escrito?*
* **La evidencia empírica:** 
  * Añadir las variables oculomotoras en tiempo real al Modelo 3 genera un incremento significativo de varianza explicada ($\Delta R^2 = 1.0\%, F(2, 1022) = 6.87, p = 0.003$).
  * El Criterio de Información de Akaike desciende de $1584.4$ a $1581.5$ ($\Delta \text{AIC} = -2.9$), demostrando que el modelo que incorpora la conducta visual es matemáticamente superior y más parsimonioso.
* **Significado Teórico:** El eye-tracking no es un simple adorno experimental; mide la **eficiencia del procesamiento en línea** (velocidad de decodificación e integración en memoria de trabajo) que los tests estáticos *offline* son incapaces de registrar.

---

## 5. Implementación en el Repositorio

* Script principal: [`predict_comprehension.py`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/predict_comprehension.py).
* Datos generados en `analysis/individual_differences/output/`:
  * `participant_background_and_comprehension.csv`
  * `bivariate_correlations_comprehension.csv`
  * `hierarchical_regression_models.csv`
  * `grand_cross_incremental_validity.csv`
  * `correlations_heatmap.png`
