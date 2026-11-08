# Fase 4: Comparación Translingüística, Patrones de Lectura (MDS) y Distancia Estructural
## Distancia Jensen-Shannon a Lectores Nativos y Efecto de la Distancia URiEL

---

## 1. El Problema Metodológico: ¿Cómo comparar dos redes de lectura?

Una vez construidas las redes de transición entre tipos de palabra para cada cohorte lingüístico, el desafío consiste en **cuantificar cuán similar es el comportamiento lector de un grupo respecto al de los lectores nativos de inglés**.

Los grupos nativos de referencia son:
* `en` (Wave 1: hablantes nativos de inglés canadiense en Edmonton, $N = 53$).
* `en_uk` (Wave 2: hablantes nativos de inglés británico en Londres, $N = 48$).

---

## 2. La Métrica Matemática: Distancia Jensen-Shannon ($JSD$)

Las matrices de adyacencia de cada condición se normalizan como distribuciones conjuntas de probabilidad de aristas sobre el espacio de $11 \times 11 = 121$ posibles transiciones.

Para comparar dos distribuciones de probabilidad $P$ y $Q$, la divergencia de Kullback-Leibler ($D_{KL}$) tiene el defecto de ser asimétrica y tender a infinito si una probabilidad es cero. Por ello, se utiliza la **Distancia Jensen-Shannon ($JSD$)**:

$$M = \frac{1}{2}(P + Q)$$

$$JSDiv(P \parallel Q) = \frac{1}{2} D_{KL}(P \parallel M) + \frac{1}{2} D_{KL}(Q \parallel M)$$

$$JSD(P, Q) = \sqrt{JSDiv(P \parallel Q)}$$

### Propiedades clave:
* Es estrictamente simétrica: $JSD(P, Q) = JSD(Q, P)$.
* Está acotada entre $0$ (distribuciones idénticas) y $1$ (distribuciones completamente disjuntas).
* Su raíz cuadrada cumple la desigualdad triangular (es una **métrica matemática formal**).
* **Cercanía Nativa (*Native Closeness*):** Se define operacionalmente como:
  $$\text{Cercanía} = 1 - JSD$$

---

## 3. Reducción Dimensional: MDS 2D Clásico de Torgerson

Para visualizar la topología global de todos los 28 grupos lingüísticos simultáneamente, la matriz completa de distancias $JSD$ pairwise se proyecta mediante **Escalamiento Multidimensional Clásico (Classical MDS)**:

1. Se construye la matriz de distancias al cuadrado $D^{(2)}$.
2. Se aplica la matriz de centrado doble: $B = -\frac{1}{2} H D^{(2)} H$, donde $H = I - \frac{1}{n}\mathbf{1}\mathbf{1}^T$.
3. Se realiza la descomposición espectral de $B$: $B = V \Lambda V^T$.
4. Las coordenadas 2D provienen de los dos primeros vectores propios escalados por sus valores propios positivos: $X = V_2 \Lambda_2^{1/2}$.

---

## 4. Hipótesis Científicas y Resultados Empíricos

### Hipótesis 1: La Cercanía al Patrón Nativo Predice la Comprensión en L2
* **Pregunta:** ¿Los grupos que mejor comprenden el texto en inglés leen con un patrón de transición visual más similar a los nativos angloparlantes?
* **Resultados en L2 (lectura en inglés):**
  * **$r = +0.43, p = 0.029$** (Spearman $\rho = 0.41, p = 0.035$).
  * Grupos con alta comprensión (ej. holandeses, alemanes, noruegos) exhiben transiciones entre categorías léxicas casi idénticas a los nativos canadienses y británicos.
  * En lectores del cuartil bajo (**Q1**), el efecto es aún más agudo: **$r = +0.59, p = 0.0015$**. Quienes no logran adoptar el patrón nativo sufren un colapso en la comprensión.
* **Control de Especificidad en L1 (lectura en lengua materna):**
  * **$r = -0.12, p = 0.557$** (no significativo).
  * La habilidad lectora general en la propia lengua materna **no predice** parecerse a un lector de inglés. Esto demuestra rigurosamente que la cercanía al patrón inglés es un **marcador específico de dominio de la L2**, no de inteligencia o capacidad lectora genérica.

---

### Hipótesis 2: Huella de la Distancia Lingüística Estructural (URiEL)
* **Variable:** Matriz de distancia tipológica, fonológica y sintáctica `lang_to_en.csv` extraída de URiEL (Littell et al., 2017):
  * Lenguas cercanas: Holandés ($21.8$), Danés ($24.6$), Noruego ($28.3$), Alemán ($31.3$).
  * Lenguas medias: Español ($59.3$), Portugués ($56.5$), Ruso ($52.5$), Griego ($72.1$).
  * Lenguas lejanas: Chino ($88.5$), Hebreo ($91.4$), Turco ($96.3$), Vasco ($97.2$).
* **Resultados en L1:**
  * **$r \approx 0.63 - 0.71, p < 0.001$**.
  * Las lenguas estructuralmente distantes del inglés leen sus propios textos con patrones de transición visual radicalmente diferentes a la norma anglosajona.
* **Resultados en L2:**
  * **$r \approx 0.30 - 0.44$**.
  * Al leer en inglés, todos los lectores convergen de forma forzada hacia la estructura del idioma meta, pero persiste una **huella de transferencia negativa**: los lectores avanzados de lenguas lejanas conservan una mayor distancia visual con los nativos que los lectores de lenguas germánicas ($r = 0.44, p < 0.03$).

---

## 5. Implementación en el Repositorio

El pipeline completo se encuentra en [`networks/reading-pattern-mds/`](file:///Users/diegusho/Documents/Proyecto-Titulo/eye-tracking-analysis/networks/reading-pattern-mds/):

* `reading_patterns.py`: CLI para computar matrices JSD, embeddings MDS y figuras estáticas.
* `output/reading_patterns_dashboard.html`: Dashboard interactivo en Plotly.js que permite filtrar por cohorte, lengua y cuartil, explorando la relación entre comprensión y cercanía visual.
* Tablas exportadas en `output/<mode>/distances/`:
  * `distance_to_native.csv`: Valores JSD y cercanía para cada grupo.
  * `corr_comprehension_reading.csv`: Pruebas de correlación Pearson y Spearman con la comprensión.
  * `corr_linguistic_reading.csv`: Pruebas de correlación con la distancia tipológica URiEL.

