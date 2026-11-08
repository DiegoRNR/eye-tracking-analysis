# Fase 6: Mecanismos Cognitivos Avanzados y Arquetipos de Lectura
## Mediación Sobel, Compensación por Relectura y Clustering de Lectores ($N = 1,032$)

---

## 1. De la Predicción a la Mecánica Cognitiva

Las regresiones lineales demuestran *qué* variables predicen la comprensión, pero no explican *cómo* interactúan los procesos cognitivos. En esta fase se implementaron cuatro modelos analíticos avanzados:

```
                          ┌───────────────────────────────┐
                          │     VOCABULARIO NATION        │
                          └───────┬───────────────┬───────┘
                                  │               │
             [Mecanismo 1:        │               │ [Mecanismo 2:
              Mediación Sobel]    │               │  Moderación Compensatoria]
                                  ▼               ▼
                        ┌──────────────────┐    ┌──────────────────┐
                        │ DURACIÓN FIJACIÓN│    │ TASA REGRESIONES │
                        │  (Velocidad L2)  │    │  (Relectura Q1)  │
                        └─────────┬────────┘    └─────────┬────────┘
                                  │                       │
                                  └───────────┬───────────┘
                                              ▼
                                 ┌────────────────────────┐
                                 │  COMPRENSIÓN LECTORA   │
                                 │      (ACCURACY)        │
                                 └────────────────────────┘
```

---

## 2. Mecanismo 1: Modelo de Mediación Psicolingüística (Sobel Test)

Se evaluó si la duración de fijación ocular actúa como **mediador causal** entre el tamaño del vocabulario ($X$) y la comprensión lectora ($Y$):

$$X (\text{Vocabulario}) \xrightarrow{a} M (\text{Duración de Fijación}) \xrightarrow{b} Y (\text{Comprensión})$$

* **Trayectoria $a$ ($X \to M$):** $\beta = -0.871, SE = 0.098, t = -8.89, p < 0.0001$. Un mayor vocabulario reduce el tiempo que el ojo se detiene sobre cada palabra.
* **Trayectoria $b$ ($M \to Y \mid X$):** $\beta = -0.00062, SE = 0.00013, t = -4.77, p < 0.0001$. Fijaciones más breves predicen mayor comprensión tras controlar por el vocabulario.
* **Efecto Indirecto ($a \times b$):** $+0.00054$.
* **Estadístico de Sobel:** **$Z = 3.702, p = 0.00021$** (altamente significativo).
* **Porcentaje del Efecto Total Mediado:** **$21.6\%$**.

> **Conclusión Psicolingüística:** Más de la quinta parte del beneficio de tener un vocabulario amplio ocurre porque **libera recursos de memoria de trabajo en tiempo real**: al decodificar palabras en $\sim 200\text{ ms}$ en lugar de $\sim 250\text{ ms}$, el lector preserva capacidad cognitiva para integrar proposiciones globales.

---

## 3. Mecanismo 2: Modelo de Moderación Compensatoria (Vocabulario $\times$ Regresiones)

Se probó la hipótesis de que las regresiones sacádicas (volver atrás en el texto) no afectan a todos por igual, sino que constituyen una **estrategia de compensación para lectores con vocabulario deficiente**:

$$\text{Accuracy} = \beta_0 + \beta_1 \text{Vocab} + \beta_2 \text{Regresiones} + \beta_3 (\text{Vocab} \times \text{Regresiones}) + \epsilon$$

* **Término de Interacción:** **$\beta_3 = -0.108, p < 0.0001$** (interacción negativa altamente significativa).

### Desglose por Cuartiles Empíricos de Vocabulario:
Dividiendo la muestra en cuartiles de puntaje en el test de Nation (`vocab.t2.5`):

| Cuartil de Vocabulario | Rango de Puntaje | Pendiente Regresiones $\to$ Comprensión ($\beta$) | $p$-valor | Interpretación |
| :--- | :---: | :---: | :---: | :--- |
| **Q1 (Vocabulario Bajo)** | $\le 24.0$ / $40$ | **$+0.844$** | **$0.0001$** | **Beneficio masivo:** releer compensa la falta de léxico. |
| **Q2 (Vocabulario Medio-Bajo)**| $25.0 - 35.0$ / $40$ | $+0.134$ | $0.47$ | Pendiente plana (efecto neutro). |
| **Q3 (Vocabulario Medio-Alto)**| $36.0 - 38.0$ / $40$ | $-0.061$ | $0.72$ | Pendiente plana (efecto neutro). |
| **Q4 (Vocabulario Nativoide)** | $39.0 - 40.0$ / $40$ | $-0.102$ | $0.58$ | Pendiente plana (efecto neutro). |

> **Conclusión:** La relectura es una muleta cognitiva funcional. Quienes tienen vocabulario nativoide comprenden en el "primer pase" (*first-pass reading*) y no obtienen ganancia alguna de releer; quienes tienen léxico limitado rescatan su comprensión regresando sobre el texto.

---

## 4. Mecanismo 3: Calibración Metacognitiva y Distancia Lingüística

Se definió el **Gap de Calibración Metacognitiva**:
$$\text{Calibration Gap} = Z(\text{Autoevaluación Lectora}) - Z(\text{Comprensión Real})$$

* $\text{Gap} > 0$: Sobrestimación (efecto Dunning-Kruger).
* $\text{Gap} < 0$: Subestimación (síndrome del impostor L2).

### Efecto de la Distancia Tipológica URiEL:
* Modelo lineal: $\text{Calibration Gap} = \beta_0 + \beta_1 (\text{Distancia Lingüística}) + \epsilon$.
* **$\beta = +0.116, p = 0.0064$**.
* **Hallazgo:** Los lectores nativos de lenguas lejanas al inglés (ej. turco, hebreo, japonés) subestiman sistemáticamente su verdadera competencia lectora real en comparación con hablantes de lenguas germánicas o romances, sufriendo una menor confianza metacognitiva no justificada por su rendimiento objetivo.

---

## 5. Mecanismo 4: Descubrimiento de Arquetipos Lectores ($k$-Means y PCA)

Para trascender las etiquetas fijas por idioma, se implementó un **clustering $k$-Means no supervisado multidimensional** sobre los $N = 1,032$ participantes completos.

### Variables de Entrada ($5$ dimensiones estandarizadas):
1. `vocab.t2.5` (Vocabulario Nation)
2. `lextale` (Proficiencia Léxica)
3. `mean_fix_dur` (Duración Media de Fijación)
4. `regression_rate` (Tasa de Regresiones Sacádicas)
5. `accuracy` (Precisión de Comprensión)

### Reducción PCA y Proyección Bidimensional (65.9% Varianza):
* **PC1 (47.3% varianza): "Proficiencia y Eficiencia Global"**
  * Loadings: Vocabulario ($+0.55$), LexTALE ($+0.54$), Comprensión ($+0.46$), Fijación ($-0.38$).
* **PC2 (18.6% varianza): "Estrategia de Relectura y Monitoreo Activo"**
  * Loadings: Regresiones (**$+0.94$**), Duración fijación ($+0.32$).

---

## 6. Los 4 Arquetipos de Lectores Bilingües

| Arquetipo | Proporción | Vocabulario | LexTALE | Fijación Ocular | Regresiones | Comprensión | Estrategia Cognitiva |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Nativoide / Eficiente** | **$27.7\%$** ($N = 286$) | $37.0 \pm 3.0$ ($+0.72 z$) | $86.9\% \pm 7.9\%$ ($+0.85 z$) | $202.3 \pm 22.4$ ms ($-0.62 z$) | $12.9\% \pm 2.9\%$ ($-0.51 z$) | **$78.3\% \pm 8.8\%$** ($+0.48 z$) | Fluidez automática de primer pase; no requiere relectura compensatoria. |
| **Estratégico / Compensador** | **$23.7\%$** ($N = 245$) | $36.1 \pm 3.8$ ($+0.61 z$) | $84.1\% \pm 9.2\%$ ($+0.62 z$) | $212.8 \pm 24.5$ ms ($-0.29 z$) | **$21.1\% \pm 3.3\%$** (**$+1.37 z$**) | **$76.1\% \pm 10.2\%$** ($+0.32 z$) | Relectura activa y monitoreo constante para asegurar comprensión profunda. |
| **Intermedio / Moderado** | **$32.2\%$** ($N = 332$) | $30.0 \pm 6.9$ ($-0.08 z$) | $70.0\% \pm 8.0\%$ ($-0.53 z$) | $236.2 \pm 25.0$ ms ($+0.46 z$) | $13.6\% \pm 3.4\%$ ($-0.34 z$) | $72.2\% \pm 10.1\%$ ($+0.03 z$) | Decodificación más lenta por palabra; comprensión en rango promedio. |
| **Bloqueado / Con Dificultad** | **$16.4\%$** ($N = 169$) | **$13.5 \pm 6.8$** (**$-1.96 z$**) | $63.0\% \pm 7.9\%$ ($-1.10 z$) | $243.9 \pm 37.1$ ms ($+0.71 z$) | $13.7\% \pm 4.3\%$ ($-0.32 z$) | **$53.6\% \pm 13.9\%$** (**$-1.35 z$**) | Cuello de botella léxico severo que interrumpe el flujo y arruina la comprensión. |

---

## 7. Archivos de Código y Figuras Resultantes

* **Código de análisis:** [`advanced_multilevel_analysis.py`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/advanced_multilevel_analysis.py) y [`generate_separated_plots.py`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/generate_separated_plots.py).
* **Figuras independientes generadas (300 DPI):**
  * Mediación: [`figure_2a_mediation_path_diagram.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_2a_mediation_path_diagram.png)
  * Compensación en 4 paneles: [`figure_2b1_compensation_quartiles_grid.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_2b1_compensation_quartiles_grid.png)
  * Comparación de pendientes: [`figure_2b2_compensation_slopes_comparison.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_2b2_compensation_slopes_comparison.png)
  * Biplot PCA 2D: [`figure_3a_reader_archetypes_pca.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_3a_reader_archetypes_pca.png)
  * Distribuciones en Boxplots: [`figure_3b_reader_archetypes_boxplots.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_3b_reader_archetypes_boxplots.png)
  * Tarjetas de resumen de perfiles: [`figure_3c_reader_archetypes_profiles.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_3c_reader_archetypes_profiles.png)
  * Tabla metodológica de campos de clustering: [`campos_clustering_input.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/campos_clustering_input.png)
  * Tabla numérica por arquetipo: [`tabla_resumen_arquetipos.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/tabla_resumen_arquetipos.png)
