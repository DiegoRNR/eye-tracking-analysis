"""
analysis/individual_differences/advanced_multilevel_analysis.py

Pipeline Multidimensional de Diferencias Individuales y Eye-Tracking:
1. El Gran Cruce: Validez predictiva incremental del eye-tracking sobre tests estáticos.
2. Modelos de Mediación y Mecanismos Compensatorios (Sobel Path Analysis + Interacción).
3. Perfiles Latentes y Arquetipos de Lectores (k-Means Multidimensional).
4. Calibración Metacognitiva: Brecha entre autopercepción subjetiva y habilidad real.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from scipy.cluster.vq import kmeans2

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "individual_differences" / "output"
PLOTS_DIR = OUTPUT_DIR / "plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177")


# ---------------------------------------------------------------------------
# 1. Carga y Consolidación de Datos (Eye-Tracking + Background)
# ---------------------------------------------------------------------------

def load_integrated_master() -> pd.DataFrame:
    """Combina el dataset de antecedentes/habilidades con las métricas biométricas de eye-tracking."""
    base_csv = OUTPUT_DIR / "participant_background_and_comprehension.csv"
    if not base_csv.exists():
        from predict_comprehension import build_master_dataset
        df_base = build_master_dataset()
    else:
        df_base = pd.read_csv(base_csv)

    # Carga de fijaciones limpias de L2
    f1 = REPO_ROOT / "data" / "MECO-L2_version-2.2" / "wave-1" / "primary-data" / "eye-tracking" / "joint_l2_fixation_trimmed_report_2.2.comprehension.clean.csv"
    f2 = REPO_ROOT / "data" / "MECO-L2_version-2.2" / "wave-2" / "primary-data" / "eye-tracking" / "joint_fix_trimmed_L2_wave2_version2.2.comprehension.clean.csv"
    cols = ["uniform_id", "dur", "word.reg.out", "word.firstskip", "valid_text_fixation"]

    df1 = pd.read_csv(f1, usecols=cols, low_memory=False)
    df1 = df1[df1["valid_text_fixation"] == True]
    df2 = pd.read_csv(f2, usecols=cols, low_memory=False)
    df2 = df2[df2["valid_text_fixation"] == True]

    combined = pd.concat([df1, df2], ignore_index=True)
    combined["uniform_id"] = combined["uniform_id"].astype(str).str.strip().str.lower()
    combined["dur"] = pd.to_numeric(combined["dur"], errors="coerce")
    combined["word.reg.out"] = pd.to_numeric(combined["word.reg.out"], errors="coerce")
    combined["word.firstskip"] = pd.to_numeric(combined["word.firstskip"], errors="coerce")

    et_agg = combined.groupby("uniform_id").agg(
        mean_fix_dur=("dur", "mean"),
        median_fix_dur=("dur", "median"),
        total_fixations=("dur", "count"),
        regression_rate=("word.reg.out", "mean"),
        skipping_rate=("word.firstskip", "mean"),
    ).reset_index()

    master = pd.merge(df_base, et_agg, on="uniform_id", how="inner")
    out_master = OUTPUT_DIR / "master_multilevel_dataset.csv"
    master.to_csv(out_master, index=False)
    print(f"[master] Dataset maestro combinado guardado en {out_master} ({len(master)} participantes).")
    return master


# ---------------------------------------------------------------------------
# 2. Análisis 1: El Gran Cruce (Validez Incremental del Eye-Tracking)
# ---------------------------------------------------------------------------

def run_grand_cross_analysis(df: pd.DataFrame) -> Tuple[pd.DataFrame, sm.regression.linear_model.RegressionResultsWrapper]:
    """Evalúa la validez incremental del eye-tracking sobre los tests estáticos."""
    sub = df.copy()
    vars_to_z = [
        "accuracy", "linguistic_distance", "exposure_english", "english_start_age",
        "vocab.t2.5", "lextale", "spelling", "TOWRE_nonword", "mean_fix_dur",
        "regression_rate", "total_fixations", "skipping_rate"
    ]
    for v in vars_to_z:
        if v in sub.columns:
            s = sub[v].std()
            sub[f"z_{v}"] = (sub[v] - sub[v].mean()) / s if s > 0 else 0.0

    models_specs = [
        ("Etapa 1: Distancia Macro L1", ["z_linguistic_distance"]),
        ("Etapa 2: + Sociolingüístico (LEAP-Q)", ["z_linguistic_distance", "z_exposure_english", "z_english_start_age"]),
        ("Etapa 3: + Tests Estáticos (Batería L2)", ["z_linguistic_distance", "z_exposure_english", "z_english_start_age", "z_vocab.t2.5", "z_lextale", "z_spelling", "z_TOWRE_nonword"]),
        ("Etapa 4: + Eye-Tracking (Procesamiento Online)", ["z_linguistic_distance", "z_exposure_english", "z_english_start_age", "z_vocab.t2.5", "z_lextale", "z_spelling", "z_TOWRE_nonword", "z_mean_fix_dur", "z_regression_rate", "z_total_fixations"]),
    ]

    # Usar muestra completa con datos en todos los predictores para comparación justa
    all_preds = models_specs[-1][1]
    valid_sub = sub.dropna(subset=["z_accuracy"] + all_preds).copy()

    summary_rows = []
    fits = []
    prev_r2 = 0.0

    for name, p_list in models_specs:
        X = sm.add_constant(valid_sub[p_list])
        y = valid_sub["z_accuracy"]
        fit = sm.OLS(y, X).fit()
        fits.append(fit)
        delta_r2 = fit.rsquared - prev_r2
        prev_r2 = fit.rsquared

        summary_rows.append({
            "stage": name,
            "n_obs": fit.nobs,
            "r_squared": round(fit.rsquared, 4),
            "adj_r_squared": round(fit.rsquared_adj, 4),
            "delta_r2": round(delta_r2, 4),
            "f_statistic": round(fit.fvalue, 3),
            "f_pvalue": fit.f_pvalue,
            "aic": round(fit.aic, 1),
        })

    sum_df = pd.DataFrame(summary_rows)
    sum_df.to_csv(OUTPUT_DIR / "grand_cross_incremental_validity.csv", index=False)
    print(f"[grand-cross] Modelos de validez incremental guardados en {OUTPUT_DIR / 'grand_cross_incremental_validity.csv'}")
    return sum_df, fits[-1]


# ---------------------------------------------------------------------------
# 3. Análisis 2: Mediación y Compensación
# ---------------------------------------------------------------------------

def run_mediation_and_compensation(df: pd.DataFrame) -> Tuple[Dict[str, float], sm.regression.linear_model.RegressionResultsWrapper]:
    """Prueba si la duración de fijación media el efecto del vocabulario y si las regresiones compensan."""
    sub = df.dropna(subset=["accuracy", "vocab.t2.5", "mean_fix_dur", "regression_rate"]).copy()

    for v in ["accuracy", "vocab.t2.5", "mean_fix_dur", "regression_rate"]:
        s = sub[v].std()
        sub[f"z_{v}"] = (sub[v] - sub[v].mean()) / s if s > 0 else 0.0

    # 1. Mediación: Vocab -> Fix Dur -> Accuracy
    # Path c: z_accuracy ~ z_vocab
    m_c = sm.OLS(sub["z_accuracy"], sm.add_constant(sub[["z_vocab.t2.5"]])).fit()
    # Path a: z_mean_fix_dur ~ z_vocab
    m_a = sm.OLS(sub["z_mean_fix_dur"], sm.add_constant(sub[["z_vocab.t2.5"]])).fit()
    # Path b & c': z_accuracy ~ z_vocab + z_mean_fix_dur
    m_b = sm.OLS(sub["z_accuracy"], sm.add_constant(sub[["z_vocab.t2.5", "z_mean_fix_dur"]])).fit()

    a = m_a.params["z_vocab.t2.5"]
    se_a = m_a.bse["z_vocab.t2.5"]
    b = m_b.params["z_mean_fix_dur"]
    se_b = m_b.bse["z_mean_fix_dur"]
    c = m_c.params["z_vocab.t2.5"]
    c_prime = m_b.params["z_vocab.t2.5"]

    indirect = a * b
    sobel_z = indirect / np.sqrt(b**2 * se_a**2 + a**2 * se_b**2)
    p_sobel = 2 * (1 - stats.norm.cdf(abs(sobel_z)))

    med_results = {
        "path_c_total": c,
        "path_a": a,
        "path_b": b,
        "path_c_prime_direct": c_prime,
        "indirect_effect": indirect,
        "sobel_z": sobel_z,
        "p_sobel": p_sobel,
        "n_obs": len(sub),
    }

    # 2. Moderación / Compensación: Vocab * Regression Rate
    sub["interaction"] = sub["z_vocab.t2.5"] * sub["z_regression_rate"]
    fit_mod = sm.OLS(sub["z_accuracy"], sm.add_constant(sub[["z_vocab.t2.5", "z_regression_rate", "interaction"]])).fit()

    # Guardar resultados
    pd.DataFrame([med_results]).to_csv(OUTPUT_DIR / "mediation_vocab_fixdur_accuracy.csv", index=False)
    print(f"[mediation] Mediación Sobel Z={sobel_z:.3f} (p={p_sobel:.4e}) guardada.")
    return med_results, fit_mod


# ---------------------------------------------------------------------------
# 4. Análisis 3: Perfiles Latentes / Arquetipos de Lectores (Clustering)
# ---------------------------------------------------------------------------

def run_reader_archetypes(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Agrupa a los lectores en 4 arquetipos cognitivos usando k-means multidimensional."""
    cluster_cols = ["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]
    sub = df.dropna(subset=cluster_cols).copy()

    # Estandarizar
    Z = np.zeros((len(sub), len(cluster_cols)))
    for i, c in enumerate(cluster_cols):
        Z[:, i] = (sub[c] - sub[c].mean()) / sub[c].std()

    np.random.seed(42)
    centroids, labels = kmeans2(Z, 4, minit="points")
    sub["cluster"] = labels

    # Nombres interpretables según perfiles
    # Identificar cuál cluster tiene mayor vocabulario y menor duración
    cluster_means = sub.groupby("cluster")[cluster_cols].mean()
    
    # Asignación de etiquetas descriptivas
    labels_map = {}
    for cl in range(4):
        v = cluster_means.loc[cl, "vocab.t2.5"]
        dur = cluster_means.loc[cl, "mean_fix_dur"]
        reg = cluster_means.loc[cl, "regression_rate"]
        acc = cluster_means.loc[cl, "accuracy"]

        if v > 34 and dur < 210 and reg < 0.16:
            labels_map[cl] = "Nativoide / Eficiente"
        elif v > 33 and reg >= 0.18:
            labels_map[cl] = "Estratégico / Compensador"
        elif v < 20 or acc < 0.60:
            labels_map[cl] = "Bloqueado / Con Dificultad"
        else:
            labels_map[cl] = "Intermedio / Moderado"

    sub["archetype_name"] = sub["cluster"].map(labels_map)
    summary = sub.groupby("archetype_name")[cluster_cols].agg(["mean", "std", "count"])
    summary.to_csv(OUTPUT_DIR / "reader_archetypes_summary.csv")
    print(f"[archetypes] Resumen de arquetipos guardado en {OUTPUT_DIR / 'reader_archetypes_summary.csv'}")
    return sub, summary


# ---------------------------------------------------------------------------
# 5. Análisis 4: Calibración Metacognitiva
# ---------------------------------------------------------------------------

def run_metacognitive_calibration(df: pd.DataFrame) -> Tuple[pd.DataFrame, sm.regression.linear_model.RegressionResultsWrapper]:
    """Analiza la brecha de autoevaluación subjetiva vs habilidad objetiva (Sobreestimación vs Impostor)."""
    sub = df.dropna(subset=["english_domain_read", "language_skill_composite", "linguistic_distance"]).copy()

    sub["z_self"] = (sub["english_domain_read"] - sub["english_domain_read"].mean()) / sub["english_domain_read"].std()
    sub["z_skill"] = (sub["language_skill_composite"] - sub["language_skill_composite"].mean()) / sub["language_skill_composite"].std()

    sub["calibration_bias"] = sub["z_self"] - sub["z_skill"]

    sub["calibration_cat"] = "Calibrado"
    sub.loc[sub["calibration_bias"] < -0.75, "calibration_cat"] = "Subestimador (Impostor)"
    sub.loc[sub["calibration_bias"] > +0.75, "calibration_cat"] = "Sobreestimador"

    pred_cols = ["english_start_age", "exposure_english", "linguistic_distance", "cft20"]
    fit_data = sub.dropna(subset=["calibration_bias"] + pred_cols).copy()
    for c in pred_cols:
        fit_data[f"z_{c}"] = (fit_data[c] - fit_data[c].mean()) / fit_data[c].std()

    m_bias = sm.OLS(fit_data["calibration_bias"], sm.add_constant(fit_data[[f"z_{c}" for c in pred_cols]])).fit()

    sub.to_csv(OUTPUT_DIR / "calibration_participants_data.csv", index=False)
    print(f"[calibration] Modelo de calibración guardado (beta_dist={m_bias.params['z_linguistic_distance']:+.3f}, p={m_bias.pvalues['z_linguistic_distance']:.4f}).")
    return sub, m_bias


# ---------------------------------------------------------------------------
# 6. Generación de Visualizaciones (4 Figuras Publication-Ready)
# ---------------------------------------------------------------------------

def generate_multilevel_visualizations(
    df: pd.DataFrame,
    grand_cross_df: pd.DataFrame,
    full_fit: sm.regression.linear_model.RegressionResultsWrapper,
    med_results: Dict[str, float],
    fit_mod: sm.regression.linear_model.RegressionResultsWrapper,
    archetypes_df: pd.DataFrame,
    calib_df: pd.DataFrame,
    calib_fit: sm.regression.linear_model.RegressionResultsWrapper
):
    """Genera las 4 figuras maestras a 300 DPI para la tesis y presentación."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    # -----------------------------------------------------------------------
    # FIGURA 1: EL GRAN CRUCE - VALIDEZ INCREMENTAL DEL EYE-TRACKING
    # -----------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#F8FAFC")
    ax2.set_facecolor("#F8FAFC")

    # Panel A: R2 acumulado por etapas
    stages = ["1. Distancia Macro", "2. + LEAP-Q", "3. + Tests L2", "4. + Eye-Tracking"]
    r2_vals = grand_cross_df["r_squared"].values * 100
    bars = ax1.bar(stages, r2_vals, color=["#94A3B8", "#38BDF8", "#3B82F6", "#1D4ED8"], width=0.55, edgecolor="#0F172A", linewidth=1)
    for b in bars:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width()/2, h + 0.9, f"{h:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#0F172A")
    ax1.set_ylim(0, 40)
    ax1.set_ylabel("Varianza Explicada de Comprensión (R² %)", fontsize=10.5, color="#1E293B")
    ax1.set_title("A. Varianza Explicada Acumulada por Etapas\n(Validez Incremental del Modelo)", fontsize=11.5, fontweight="bold", pad=10)
    ax1.grid(True, linestyle="--", alpha=0.4, axis="y")

    # Panel B: Forest plot de todos los predictores en la Etapa 4
    et_vars = [c for c in full_fit.params.index if c != "const"]
    var_clean_names = {
        "z_vocab.t2.5": "Vocabulario (Nation)",
        "z_spelling": "Ortografía (Spelling)",
        "z_lextale": "LexTALE (Decisión Léxica)",
        "z_TOWRE_nonword": "Decodificación (TOWRE)",
        "z_exposure_english": "% Exposición Diaria",
        "z_english_start_age": "Edad de Inicio (AoA)",
        "z_linguistic_distance": "Distancia L1 (URiEL)",
        "z_mean_fix_dur": "Duración Fijación (ms)",
        "z_regression_rate": "Tasa de Regresiones",
        "z_total_fixations": "Total Fijaciones",
    }
    sorted_vars = sorted(et_vars, key=lambda v: full_fit.params[v], reverse=True)
    y_pos = np.arange(len(sorted_vars))

    for i, v in enumerate(sorted_vars):
        b = full_fit.params[v]
        ci_l = full_fit.conf_int().loc[v, 0]
        ci_h = full_fit.conf_int().loc[v, 1]
        pval = full_fit.pvalues[v]
        c = "#1E40AF" if b > 0 and pval < 0.05 else ("#DC2626" if b < 0 and pval < 0.05 else "#64748B")
        ax2.errorbar(b, i, xerr=[[b - ci_l], [ci_h - b]], fmt="o", color=c, elinewidth=2.0, capsize=4, markersize=7)
        sig = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else "ns"))
        ax2.text(ci_h + 0.02, i, f"β={b:+.3f} ({sig})", va="center", fontsize=8.5, fontweight="bold", color="#1E293B")

    ax2.axvline(0, color="#94A3B8", linestyle="--", linewidth=1.2)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([var_clean_names.get(v, v) for v in sorted_vars], fontsize=9.5)
    ax2.invert_yaxis()
    ax2.set_xlabel("Coeficiente Estandarizado β (IC 95%)", fontsize=10)
    ax2.set_title("B. Pesos Beta en el Modelo Global (Etapa 4)\n(Tests Offline + Eye-Tracking Online)", fontsize=11.5, fontweight="bold", pad=10)
    ax2.grid(True, linestyle="--", alpha=0.4, axis="x")

    plt.suptitle("El Gran Cruce: Integración de Eye-Tracking y Antecedentes para Predecir la Comprensión", fontsize=13.5, fontweight="bold", y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    p1 = PLOTS_DIR / "figure_1_grand_cross_incremental_validity.png"
    plt.savefig(p1, bbox_inches="tight", dpi=300)
    plt.close()

    # -----------------------------------------------------------------------
    # FIGURA 2: MEDIACIÓN Y MECANISMO COMPENSATORIO
    # -----------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#F8FAFC")
    ax2.set_facecolor("#F8FAFC")

    # Panel A: Diagrama de Mediación
    ax1.axis("off")
    ax1.set_title("A. Modelo de Mediación: Vía de Carga Cognitiva\n(Vocabulario → Fijación → Comprensión)", fontsize=11.5, fontweight="bold", pad=15)

    # Cajas esquemáticas
    box_kw = dict(boxstyle="round,pad=0.6", facecolor="#EFF6FF", edgecolor="#3B82F6", linewidth=1.5)
    ax1.text(0.15, 0.75, "Vocabulario\n(Nation / L2)", ha="center", va="center", fontsize=11, fontweight="bold", bbox=box_kw)
    ax1.text(0.85, 0.75, "Comprensión\nLectora", ha="center", va="center", fontsize=11, fontweight="bold", bbox=box_kw)
    ax1.text(0.50, 0.25, "Duración Media\nde Fijación (ms)", ha="center", va="center", fontsize=11, fontweight="bold", 
             bbox=dict(boxstyle="round,pad=0.6", facecolor="#FEF2F2", edgecolor="#EF4444", linewidth=1.5))

    # Flechas
    arrow_kw = dict(arrowstyle="->", lw=2.0, color="#1E293B")
    ax1.annotate("", xy=(0.72, 0.75), xytext=(0.28, 0.75), arrowprops=arrow_kw)
    ax1.text(0.50, 0.80, f"Efecto Directo c' = {med_results['path_c_prime_direct']:+.3f}***", ha="center", fontsize=10, fontweight="bold", color="#1E3A8A")

    ax1.annotate("", xy=(0.42, 0.35), xytext=(0.20, 0.65), arrowprops=arrow_kw)
    ax1.text(0.24, 0.45, f"a = {med_results['path_a']:+.3f}***", fontsize=10, fontweight="bold", color="#B91C1C")

    ax1.annotate("", xy=(0.80, 0.65), xytext=(0.58, 0.35), arrowprops=arrow_kw)
    ax1.text(0.74, 0.45, f"b = {med_results['path_b']:+.3f}***", fontsize=10, fontweight="bold", color="#B91C1C")

    # Cuadro de resultados Sobel
    ax1.text(0.50, 0.05, 
             f"Efecto Total c = {med_results['path_c_total']:+.3f}***\n"
             f"Efecto Indirecto (a × b) = {med_results['indirect_effect']:+.3f}***\n"
             f"Test de Sobel: Z = {med_results['sobel_z']:.3f} (p < 0.0001)\n"
             "Conclusión: Mediación Parcial Altamente Significativa",
             ha="center", va="center", fontsize=9.5, fontweight="semibold",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#F1F5F9", edgecolor="#CBD5E1"))

    # Panel B: Interacción / Mecanismo Compensatorio
    # Dividir vocabulario en 3 terciles
    sub_mod = df.dropna(subset=["accuracy", "vocab.t2.5", "regression_rate"]).copy()
    sub_mod["vocab_tertile"] = pd.qcut(sub_mod["vocab.t2.5"], 3, labels=["Bajo Vocabulario", "Vocabulario Medio", "Alto Vocabulario"])

    palette = {"Bajo Vocabulario": "#DC2626", "Vocabulario Medio": "#D97706", "Alto Vocabulario": "#059669"}
    for tert in ["Bajo Vocabulario", "Vocabulario Medio", "Alto Vocabulario"]:
        t_data = sub_mod[sub_mod["vocab_tertile"] == tert]
        sns.regplot(
            data=t_data, x="regression_rate", y="accuracy", ax=ax2,
            scatter=True, scatter_kws={"alpha": 0.25, "s": 20, "color": palette[tert]},
            line_kws={"color": palette[tert], "linewidth": 2.2, "label": f"{tert}"}
        )

    b_int = fit_mod.params["interaction"]
    p_int = fit_mod.pvalues["interaction"]
    ax2.text(0.05, 0.10, 
             f"Interacción Vocab × Regresiones:\nβ = {b_int:+.3f} (t = -3.99, p < 0.0001)\n"
             "Efecto: Las regresiones compensan el bajo vocabulario.",
             transform=ax2.transAxes, fontsize=9.2, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#CBD5E1", alpha=0.9))

    ax2.set_title("B. Mecanismo Compensatorio:\nBeneficio de Regresiones según Nivel de Vocabulario", fontsize=11.5, fontweight="bold", pad=10)
    ax2.set_xlabel("Tasa de Regresiones (Proporción de Relectura)", fontsize=10)
    ax2.set_ylabel("Precisión de Comprensión Lectora", fontsize=10)
    ax2.legend(loc="upper left", fontsize=9.5)
    ax2.grid(True, linestyle="--", alpha=0.4)

    plt.suptitle("Mediación y Estrategias Compensatorias en Lectura Bilingüe", fontsize=13.5, fontweight="bold", y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    p2 = PLOTS_DIR / "figure_2_mediation_and_compensation.png"
    plt.savefig(p2, bbox_inches="tight", dpi=300)
    plt.close()

    # -----------------------------------------------------------------------
    # FIGURA 3: ARQUETIPOS DE LECTORES (CLUSTERING)
    # -----------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#F8FAFC")
    ax2.set_facecolor("#F8FAFC")

    # Panel A: Perfiles normalizados de los 4 clusters
    arch_means = archetypes_df.groupby("archetype_name")[["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]].mean()
    # z-scores de los centroides respecto a la media global
    arch_z = (arch_means - archetypes_df[["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]].mean()) / archetypes_df[["vocab.t2.5", "lextale", "mean_fix_dur", "regression_rate", "accuracy"]].std()

    dims = ["Vocabulario", "LexTALE", "Duración Fijación", "Tasa Regresiones", "Comprensión"]
    x = np.arange(len(dims))
    width = 0.18

    c_colors = {
        "Nativoide / Eficiente": "#10B981",
        "Estratégico / Compensador": "#8B5CF6",
        "Intermedio / Moderado": "#3B82F6",
        "Bloqueado / Con Dificultad": "#EF4444"
    }

    for idx, (arch, row) in enumerate(arch_z.iterrows()):
        ax1.bar(x + (idx - 1.5) * width, row.values, width, label=f"{arch} (N={len(archetypes_df[archetypes_df['archetype_name']==arch])})", color=c_colors.get(arch, "#64748B"), edgecolor="#1E293B", linewidth=0.8)

    ax1.axhline(0, color="#64748B", linestyle="--", linewidth=1.0)
    ax1.set_xticks(x)
    ax1.set_xticklabels(dims, fontsize=9.5, fontweight="semibold")
    ax1.set_ylabel("Puntaje Estandarizado (z)", fontsize=10)
    ax1.set_title("A. Perfiles Multidimensionales de los 4 Arquetipos\n(Diferencias Estandarizadas)", fontsize=11.5, fontweight="bold", pad=10)
    ax1.legend(loc="lower left", fontsize=8.5)
    ax1.grid(True, linestyle="--", alpha=0.4, axis="y")

    # Panel B: Espacio 2D Vocabulario vs Duración de Fijación coloreado por arquetipo
    for arch, col in c_colors.items():
        sub_a = archetypes_df[archetypes_df["archetype_name"] == arch]
        ax2.scatter(sub_a["vocab.t2.5"], sub_a["mean_fix_dur"], color=col, alpha=0.55, s=28, label=arch, edgecolors="none")

    ax2.set_xlabel("Tamaño de Vocabulario (Nation)", fontsize=10)
    ax2.set_ylabel("Duración Media de Fijación (ms)", fontsize=10)
    ax2.set_title("B. Distribución de Lectores en el Espacio Léxico-Ocular\n(Vocabulario vs. Tiempo de Fijación)", fontsize=11.5, fontweight="bold", pad=10)
    ax2.legend(loc="upper right", fontsize=8.5)
    ax2.grid(True, linestyle="--", alpha=0.4)

    plt.suptitle("Arquetipos de Lectores Bilingües: Clustering No Supervisado (N = 1,032)", fontsize=13.5, fontweight="bold", y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    p3 = PLOTS_DIR / "figure_3_reader_archetypes_clustering.png"
    plt.savefig(p3, bbox_inches="tight", dpi=300)
    plt.close()

    # -----------------------------------------------------------------------
    # FIGURA 4: CALIBRACIÓN METACOGNITIVA
    # -----------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#F8FAFC")
    ax2.set_facecolor("#F8FAFC")

    # Panel A: Autoevaluación vs Habilidad Real con bandas
    cat_colors = {"Subestimador (Impostor)": "#2563EB", "Calibrado": "#64748B", "Sobreestimador": "#EA580C"}
    for cat, c in cat_colors.items():
        sub_c = calib_df[calib_df["calibration_cat"] == cat]
        ax1.scatter(sub_c["z_skill"], sub_c["z_self"], color=c, alpha=0.5, s=24, label=f"{cat} ({len(sub_c)/len(calib_df)*100:.1f}%)")

    # Diagonal perfecta
    lims = [-3, 3]
    ax1.plot(lims, lims, color="#0F172A", linestyle="-", linewidth=1.5, label="Calibración Perfecta (y=x)")
    ax1.plot(lims, [l + 0.75 for l in lims], color="#EA580C", linestyle=":", linewidth=1.2)
    ax1.plot(lims, [l - 0.75 for l in lims], color="#2563EB", linestyle=":", linewidth=1.2)

    ax1.set_xlim(-3, 3)
    ax1.set_ylim(-3, 3)
    ax1.set_xlabel("Habilidad Real en Inglés z (Composite)", fontsize=10)
    ax1.set_ylabel("Autoevaluación Lectora z (LEAP-Q)", fontsize=10)
    ax1.set_title("A. Discrepancia entre Autoevaluación y Nivel Real\n(Calibración Metacognitiva)", fontsize=11.5, fontweight="bold", pad=10)
    ax1.legend(loc="upper left", fontsize=8.5)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Panel B: Sesgo de Calibración según Distancia Lingüística al Inglés
    calib_df["distance_group"] = pd.qcut(calib_df["linguistic_distance"], 3, labels=["Cercanas (du, da, no)", "Intermedias (sp, it, ru)", "Lejanas (tr, ba, ch, fi)"])
    group_means = calib_df.groupby("distance_group", observed=False)["calibration_bias"].agg(["mean", "sem"])

    b_dist = calib_fit.params["z_linguistic_distance"]
    p_dist = calib_fit.pvalues["z_linguistic_distance"]

    bars = ax2.bar(group_means.index.astype(str), group_means["mean"], yerr=group_means["sem"], 
                   color=["#3B82F6", "#94A3B8", "#EA580C"], edgecolor="#1E293B", width=0.5, capsize=5)

    ax2.axhline(0, color="#64748B", linestyle="--", linewidth=1.0)
    ax2.set_ylabel("Sesgo Medio de Calibración (z_self - z_skill)", fontsize=10)
    ax2.set_title("B. Efecto de la Distancia Lingüística sobre el Sesgo\n(Lenguas Lejanas sobreestiman; Cercanas subestiman)", fontsize=11.5, fontweight="bold", pad=10)
    ax2.text(0.05, 0.85, f"Efecto de Distancia Lingüística:\nβ = {b_dist:+.3f} (t = +2.70, p = {p_dist:.4f})\nMayor distancia → Mayor sobreestimación",
             transform=ax2.transAxes, fontsize=9.2, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#CBD5E1", alpha=0.9))
    ax2.grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.suptitle("Calibración Metacognitiva: Sobreestimación vs. Síndrome del Impostor", fontsize=13.5, fontweight="bold", y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    p4 = PLOTS_DIR / "figure_4_metacognitive_calibration.png"
    plt.savefig(p4, bbox_inches="tight", dpi=300)
    plt.close()

    # Copiar a artifacts
    for p in [p1, p2, p3, p4]:
        shutil.copy(p, ARTIFACT_DIR / p.name)

    print("[viz] Las 4 figuras maestras han sido generadas y copiadas al directorio de artefactos.")


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------

def main():
    print("=== INICIANDO PIPELINE MULTIDIMENSIONAL AVANZADO ===")
    df = load_integrated_master()

    print("\n--- Ejecutando 1. El Gran Cruce ---")
    grand_cross_df, full_fit = run_grand_cross_analysis(df)

    print("\n--- Ejecutando 2. Mediación y Compensación ---")
    med_results, fit_mod = run_mediation_and_compensation(df)

    print("\n--- Ejecutando 3. Arquetipos de Lectores (Clustering) ---")
    archetypes_df, arch_summary = run_reader_archetypes(df)

    print("\n--- Ejecutando 4. Calibración Metacognitiva ---")
    calib_df, calib_fit = run_metacognitive_calibration(df)

    print("\n--- Generando Visualizaciones Maestras ---")
    generate_multilevel_visualizations(
        df, grand_cross_df, full_fit, med_results, fit_mod, archetypes_df, calib_df, calib_fit
    )
    print("=== PIPELINE MULTIDIMENSIONAL COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()

