# Catálogo Completo de Figuras, Datasets y Salidas
## Repositorio de Material Empírico para el Paper Científico

Este catálogo enumera todas las figuras generadas en **alta resolución (300 DPI)** y los **datasets tabulares** resultantes de cada fase del pipeline, con sus rutas absolutas, enlaces directos y pies de figura sugeridos para el manuscrito.

---

## 1. Figuras en Alta Resolución (300 DPI)

Todas las figuras están disponibles localmente en:
`analysis/individual_differences/output/plots/`

### 1.1 Matriz de Correlaciones y Validez Incremental

#### Figura S1: Matriz de Correlación Bivariada
* **Archivo:** [`correlations_heatmap.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/correlations_heatmap.png)
* **Artefacto:** [`correlations_heatmap.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/correlations_heatmap.png)
* **Dimensiones:** $3014 \times 2524$ px (300 DPI).
* **Descripción:** Matriz simétrica de correlaciones de Pearson entre la precisión de comprensión lectora (`accuracy`) y los 10 predictores observables directos (sin valores sintéticos/compuestos).
* **Leyenda sugerida:** *Figure S1. Heatmap of Pearson bivariate correlations across language background, psychometric cognitive/linguistic battery, and reading comprehension accuracy ($N = 1,203$). Color scale reflects correlation coefficients ranging from $-0.60$ to $+0.60$.*

#### Figura S2: Forest Plot de Coeficientes de Regresión
* **Archivo:** [`model_coefficients_forest.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/model_coefficients_forest.png)
* **Artefacto:** [`model_coefficients_forest.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/model_coefficients_forest.png)
* **Descripción:** Coeficientes estandarizados ($\beta$) e intervalos de confianza del 95% para cada bloque de predictores.

#### Figura 1: Validez Incremental del Eye-Tracking (The Grand Cross)
* **Archivo:** [`figure_1_grand_cross_incremental_validity.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_1_grand_cross_incremental_validity.png)
* **Artefacto:** [`figure_1_grand_cross_incremental_validity.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_1_grand_cross_incremental_validity.png)
* **Descripción:** Comparación jerárquica de $R^2$ y AIC entre Modelos 1, 2, 3 y 4, demostrando el aporte significativo de las variables oculomotoras en tiempo real ($\Delta R^2 = 1.0\%, p = 0.003$).

---

### 1.2 Mecanismos de Mediación y Compensación

#### Figura 2A: Diagrama de Rutas de Mediación Psicolingüística (Sobel)
* **Archivo:** [`figure_2a_mediation_path_diagram.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_2a_mediation_path_diagram.png)
* **Artefacto:** [`figure_2a_mediation_path_diagram.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_2a_mediation_path_diagram.png)
* **Descripción:** Diagrama formal de mediación mostrando la trayectoria del vocabulario de Nation hacia la duración media de fijación ($a = -0.871, p < 0.0001$) y de la fijación hacia la comprensión ($b = -0.00062, p < 0.0001$).
* **Leyenda sugerida:** *Figure 2A. Psycholinguistic mediation path model. Mean fixation duration significantly mediates 21.6% of the total effect of receptive vocabulary size on L2 reading comprehension (Sobel test $Z = 3.702, p = 0.00021$).*

#### Figura 2B1: Panel de Dispersión de Compensación por Cuartiles
* **Archivo:** [`figure_2b1_compensation_quartiles_grid.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_2b1_compensation_quartiles_grid.png)
* **Artefacto:** [`figure_2b1_compensation_quartiles_grid.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_2b1_compensation_quartiles_grid.png)
* **Descripción:** Cuadrícula de 4 paneles (Q1 a Q4 de vocabulario) con la recta de regresión entre tasa de regresiones y comprensión. Muestra claramente la pendiente pronunciada en Q1 ($\beta = +0.844$) vs. pendientes planas en Q2-Q4.
* **Leyenda sugerida:** *Figure 2B1. Scatterplots and linear regression slopes showing the relationship between saccadic regression rate and reading comprehension across four empirical quartiles of receptive vocabulary size. Regressive re-reading only benefits struggling readers (Q1, $p = 0.0001$).*

#### Figura 2B2: Comparación de Pendientes del Efecto Compensatorio
* **Archivo:** [`figure_2b2_compensation_slopes_comparison.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_2b2_compensation_slopes_comparison.png)
* **Artefacto:** [`figure_2b2_compensation_slopes_comparison.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_2b2_compensation_slopes_comparison.png)
* **Descripción:** Gráfico de barras de error con el valor exacto de la pendiente $\beta$ de regresiones sobre comprensión para cada cuartil de vocabulario.

---

### 1.3 Arquetipos de Lectores L2 ($k$-Means y PCA)

#### Figura 3A: Biplot PCA Bidimensional de Arquetipos
* **Archivo:** [`figure_3a_reader_archetypes_pca.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_3a_reader_archetypes_pca.png)
* **Artefacto:** [`figure_3a_reader_archetypes_pca.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_3a_reader_archetypes_pca.png)
* **Dimensiones:** $2850 \times 2250$ px (300 DPI).
* **Descripción:** Proyección 2D de los $1,032$ participantes en el espacio latente de PC1 (Proficiencia/Velocidad, 47.3% varianza) y PC2 (Relectura Activa, 18.6% varianza). Incluye los vectores de carga de las 5 variables y los centroides de los 4 arquetipos con marcadores en cruz.
* **Leyenda sugerida:** *Figure 3A. Two-dimensional Principal Component Analysis (PCA) biplot capturing 65.9% of total behavioral variance across 1,032 bilingual readers. Individual dots are color-coded by k-means cluster assignment. Black vectors depict feature loadings.*

#### Figura 3B: Distribuciones Reales por Arquetipo (Boxplots)
* **Archivo:** [`figure_3b_reader_archetypes_boxplots.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_3b_reader_archetypes_boxplots.png)
* **Artefacto:** [`figure_3b_reader_archetypes_boxplots.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_3b_reader_archetypes_boxplots.png)
* **Descripción:** Distribuciones reales (diagramas de caja y bigotes) de vocabulario, LexTALE, fijación, regresiones y comprensión separadas por cada arquetipo lector.

#### Figura 3C: Tarjetas Visuales de Perfil por Arquetipo
* **Archivo:** [`figure_3c_reader_archetypes_profiles.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_3c_reader_archetypes_profiles.png)
* **Artefacto:** [`figure_3c_reader_archetypes_profiles.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_3c_reader_archetypes_profiles.png)
* **Descripción:** Tarjetas ejecutivas con esquinas redondeadas y colores temáticos que resumen el porcentaje de la población, estadísticas clave y la estrategia cognitiva de cada arquetipo lector.

#### Tabla-Figura 1: Variables de Entrada para el Clustering ($k$-Means)
* **Archivo:** [`campos_clustering_input.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/campos_clustering_input.png)
* **Artefacto:** [`campos_clustering_input.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/campos_clustering_input.png)
* **Dimensiones:** $4710 \times 1668$ px (300 DPI).
* **Descripción:** Tabla metodológica formal que describe las 5 variables de entrada utilizadas en el clustering, su constructo evaluado, instrumento, unidad, media global y justificación teórica.

#### Tabla-Figura 2: Resumen Numérico por Campo y Arquetipo
* **Archivo:** [`tabla_resumen_arquetipos.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/tabla_resumen_arquetipos.png)
* **Artefacto:** [`tabla_resumen_arquetipos.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/tabla_resumen_arquetipos.png)
* **Dimensiones:** $4554 \times 1594$ px (300 DPI).
* **Descripción:** Tabla exhaustiva con medias $\pm$ desviación estándar y puntuaciones $z$-score por arquetipo para cada una de las 5 dimensiones del clustering.

#### Figura S3: Perfiles de Centroides de Arquetipos
* **Archivo:** [`clustering_fields_and_values.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/clustering_fields_and_values.png)
* **Artefacto:** [`clustering_fields_and_values.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/clustering_fields_and_values.png)
* **Dimensiones:** $3390 \times 2587$ px (300 DPI).
* **Descripción:** Panel doble que combina la tabla numérica de arquetipos con un gráfico de barras agrupadas de z-scores de los centroides.

---

### 1.4 Calibración Metacognitiva

#### Figura 4A: Dispersión de Calibración Metacognitiva
* **Archivo:** [`figure_4a_metacognitive_calibration_scatter.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_4a_metacognitive_calibration_scatter.png)
* **Artefacto:** [`figure_4a_metacognitive_calibration_scatter.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_4a_metacognitive_calibration_scatter.png)
* **Descripción:** Gráfico de dispersión entre autoevaluación subjetiva y comprensión real, ilustrando las zonas de subestimación (*impostor*) y sobreestimación.

#### Figura 4B: Calibración Metacognitiva por Lengua Materna
* **Archivo:** [`figure_4b_calibration_by_language.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_4b_calibration_by_language.png)
* **Artefacto:** [`figure_4b_calibration_by_language.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_4b_calibration_by_language.png)
* **Descripción:** Gráfico de barras horizontales ordenado por el gap de calibración promedio de cada una de las 28 lenguas maternas.

#### Figura 4C: Calibración por Cuartiles de Distancia Lingüística URiEL
* **Archivo:** [`figure_4c_calibration_by_distance_quartiles.png`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/analysis/individual_differences/output/plots/figure_4c_calibration_by_distance_quartiles.png)
* **Artefacto:** [`figure_4c_calibration_by_distance_quartiles.png`](file:///Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177/figure_4c_calibration_by_distance_quartiles.png)
* **Descripción:** Boxplots del gap de calibración agrupados en cuatro cuartiles de distancia tipológica al inglés (Q1: lenguas germánicas muy cercanas; Q4: lenguas lejanas no indoeuropeas).

---

## 2. Catálogo de Datasets Tabulares (CSV)

Todos los datos procesados residen en `analysis/individual_differences/output/`:

| Archivo CSV | Registros ($N$) | Columnas | Contenido y Propósito |
| :--- | :---: | :---: | :--- |
| **`master_multilevel_dataset.csv`** | $1,203$ | $26$ | Dataset maestro que integra LEAP-Q, batería psicométrica, métricas de eye-tracking y comprensión lectora MECO L2. |
| **`participant_background_and_comprehension.csv`** | $1,203$ | $19$ | Versión depurada con variables estandarizadas $z$-score y datos demográficos. |
| **`bivariate_correlations_comprehension.csv`** | $10$ | $8$ | Coeficientes de Pearson, $t$-values y $p$-values bivariados contra la comprensión. |
| **`hierarchical_regression_models.csv`** | $4$ | $9$ | Resumen estadístico de los Modelos 1 a 4 ($R^2$, $\Delta R^2$, $F$, $p$, AIC, BIC). |
| **`grand_cross_incremental_validity.csv`** | $2$ | $7$ | Prueba de hipótesis formal sobre la validez incremental del eye-tracking. |
| **`mediation_vocab_fixdur_accuracy.csv`** | $1$ | $8$ | Estadísticos del modelo de mediación de Sobel (trayectorias $a, b, c, c'$, valor $Z$, $p$, % mediado). |
| **`reader_archetypes_summary.csv`** | $4$ | $16$ | Medias, desviaciones estándar y conteos de las 5 variables para cada uno de los 4 clusters de lectores. |
| **`calibration_participants_data.csv`** | $1,105$ | $12$ | Valores individuales de autoevaluación, comprensión real, gap metacognitivo y distancia tipológica. |

---

## 3. Herramientas Interactivas y Dashboards Web

* **Dashboard de Patrones de Lectura MDS:**
  * Archivo local: [`networks/reading-pattern-mds/output/reading_patterns_dashboard.html`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/networks/reading-pattern-mds/output/reading_patterns_dashboard.html)
  * Tecnología: Plotly.js interactivo autocontenido en HTML.
  * Capacidades: Exploración en vivo del espacio MDS 2D, filtrado por cuartil de comprensión (Q1/Q4), visualización por lengua y correlaciones dinámicas en tiempo real con la comprensión y la distancia lingüística.

