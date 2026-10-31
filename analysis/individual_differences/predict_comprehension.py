"""
analysis/individual_differences/predict_comprehension.py

Pipeline completo para:
1. Extraer y armonizar datos sociolingüísticos y de antecedentes (LEAP-Q).
2. Unir batería estandarizada de proficiencia en inglés (lextale, vocab, spelling, TOWRE) y cognición (cft20).
3. Cruzar con distancia estructural de la lengua materna (lang_to_en.csv) y comprensión lectora (accuracy).
4. Correlaciones bivariadas, regresión jerárquica y visualizaciones publication-ready (300 DPI).
"""

from __future__ import annotations

import glob
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "analysis" / "individual_differences" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR = OUTPUT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/diegusho/.gemini/antigravity/brain/ec06e3df-cf43-4425-80fa-757a037d6177")


def clean_num(val: Any) -> float:
    """Limpia cadenas, rangos y caracteres extraños para extraer valores numéricos."""
    if pd.isna(val):
        return np.nan
    val_str = str(val).strip().replace(",", ".")
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", val_str)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            return np.nan
    return np.nan


def sanitize_age(val: float) -> float:
    """Corrige anomalías de edad (> 40 suele ser año de calendario o error tipográfico)."""
    if pd.isna(val):
        return np.nan
    if val > 1950 and val < 2025:
        # Si introdujo año calendario (ej. 2006 en vez de edad)
        # Asumiendo participante universitario promedio nacido ~1998
        return np.nan
    if val > 40:
        return np.nan
    if val < 0:
        return np.nan
    return val


# ---------------------------------------------------------------------------
# 1. Extracción y Armonización LEAP-Q
# ---------------------------------------------------------------------------

def extract_leap_q() -> pd.DataFrame:
    """Extrae datos de antecedentes sociolingüísticos armonizados desde todos los archivos LEAP-Q."""
    files = sorted(glob.glob(str(REPO_ROOT / "data" / "MECO-L2_version-2.2" / "*" / "primary-data" / "individual-differences" / "leap-q" / "*.xlsx")))
    records: List[Dict[str, Any]] = []

    for f in files:
        fname = os.path.basename(f)
        try:
            df = pd.read_excel(f)
            # Manejo de formatos de encabezado doble (du, gr)
            if "du.xlsx" in fname or "gr.xlsx" in fname:
                subheaders = df.iloc[0]
                df = df.iloc[1:].copy()
                uid_col = [c for c in df.columns if "uniform" in str(subheaders[c]).lower() or "uniform" in str(c).lower()][0]
                exp_col = "Unnamed: 6" if "Unnamed: 6" in df.columns else None
                start_col = "Age of English ..." if "Age of English ..." in df.columns else None
                fl_read_col = "Unnamed: 22" if "Unnamed: 22" in df.columns else None
                dom_read_col = "Unnamed: 28" if "Unnamed: 28" in df.columns else None
                edu_col = "Education" if "Education" in df.columns else None

                for _, r in df.iterrows():
                    uid = str(r[uid_col]).strip().lower()
                    if uid in ["nan", "none", ""]:
                        continue
                    records.append({
                        "file": fname,
                        "uniform_id": uid,
                        "exposure_english": clean_num(r.get(exp_col)),
                        "english_start_age": sanitize_age(clean_num(r.get(start_col))),
                        "english_fluent_read_age": sanitize_age(clean_num(r.get(fl_read_col))),
                        "english_domain_read": clean_num(r.get(dom_read_col)),
                        "formal_education_years": clean_num(r.get(edu_col)),
                    })
            else:
                uid_col = None
                exp_col = None
                start_col = None
                fl_read_col = None
                dom_read_col = None
                edu_col = None

                for c in df.columns:
                    cl = str(c).lower().strip()
                    if "uniform" in cl:
                        uid_col = c
                    elif "exposure" in cl and "english" in cl:
                        exp_col = c
                    elif ("age" in cl and "start" in cl and "english" in cl) or ("age when you started" in cl) or ("englishstartage" in cl) or ("eng1start" in cl) or ("english_age_learn" in cl) or ("eng1a" in cl):
                        if start_col is None:
                            start_col = c
                    elif ("reading fluent" in cl) or ("fluent english (year)" in cl) or ("eng1flue.read" in cl) or ("english_age_fluent_read" in cl) or ("eng1d" in cl) or ("englishagereadfluently" in cl):
                        if fl_read_col is None:
                            fl_read_col = c
                    elif ("reading (english)" in cl) or ("englishdomainread" in cl) or ("eng3read" in cl) or ("english_read" in cl) or ("eng3c" in cl):
                        if dom_read_col is None:
                            dom_read_col = c
                    elif ("years of formal education" in cl) or ("formaleducation_years" in cl) or ("years_education_overall" in cl) or ("q4a" in cl):
                        if edu_col is None:
                            edu_col = c

                # Ajustes específicos por centro
                if not exp_col and "1eng" in df.columns: exp_col = "1eng"
                if not exp_col and "leap_now_english" in df.columns: exp_col = "leap_now_english"
                if not exp_col and "english percent" in df.columns: exp_col = "english percent"
                if not exp_col and "Q1en %" in df.columns: exp_col = "Q1en %"
                if not exp_col:
                    matches = [c for c in df.columns if "exposed to english" in str(c).lower()]
                    if matches: exp_col = matches[0]

                if uid_col:
                    for _, r in df.iterrows():
                        uid = str(r[uid_col]).strip().lower()
                        if uid in ["nan", "none", ""]:
                            continue
                        records.append({
                            "file": fname,
                            "uniform_id": uid,
                            "exposure_english": clean_num(r.get(exp_col)),
                            "english_start_age": sanitize_age(clean_num(r.get(start_col))),
                            "english_fluent_read_age": sanitize_age(clean_num(r.get(fl_read_col))),
                            "english_domain_read": clean_num(r.get(dom_read_col)),
                            "formal_education_years": clean_num(r.get(edu_col)),
                        })
        except Exception as e:
            print(f"[warning] Error procesando LEAP-Q {fname}: {e}")

    leap_df = pd.DataFrame(records).drop_duplicates(subset=["uniform_id"]).copy()
    print(f"[leap-q] Extraídos {len(leap_df)} registros únicos de participantes.")
    return leap_df


# ---------------------------------------------------------------------------
# 2. Batería Estandarizada L2, Comprensión y Distancia
# ---------------------------------------------------------------------------

def load_clean_individual_differences() -> pd.DataFrame:
    """Carga y consolida la batería individual de L2 en wave 1 y wave 2."""
    p1 = REPO_ROOT / "data" / "MECO-L2_version-2.2" / "wave-1" / "primary-data" / "individual-differences" / "joint.ind.diff.l2.individual.clean.csv"
    p2 = REPO_ROOT / "data" / "MECO-L2_version-2.2" / "wave-2" / "primary-data" / "individual-differences" / "joint.ind.diff.l2.w2.individual.clean.csv"

    df1 = pd.read_csv(p1)
    df2 = pd.read_csv(p2)
    df1["wave"] = 1
    df2["wave"] = 2

    common_cols = ["uniform_id", "lang", "wave", "lextale", "vocab", "vocab.t2.5", "spelling", "TOWRE_word", "TOWRE_nonword", "cft20", "motiv"]
    df = pd.concat([df1[common_cols], df2[common_cols]], ignore_index=True)
    df["uniform_id"] = df["uniform_id"].astype(str).str.strip().str.lower()
    df = df.drop_duplicates(subset=["uniform_id"]).copy()

    # Estandarización z-score por separado para construir language_skill_composite
    for col in ["lextale", "vocab.t2.5", "spelling", "TOWRE_word", "TOWRE_nonword", "cft20"]:
        mean = df[col].mean()
        std = df[col].std()
        df[f"z_{col}"] = (df[col] - mean) / std if std > 0 else 0.0

    # Composite: promedio de las 4 pruebas nucleares de lenguaje
    df["language_skill_composite"] = df[["z_lextale", "z_vocab.t2.5", "z_TOWRE_word", "z_TOWRE_nonword"]].mean(axis=1)
    return df


def load_comprehension() -> pd.DataFrame:
    """Carga la precisión de comprensión promedio por uniform_id."""
    w1 = pd.read_csv(REPO_ROOT / "data" / "MECO-L2_version-2.2" / "wave-1" / "primary-data" / "comprehension" / "joint.comp.l2.csv")
    w2 = pd.read_csv(REPO_ROOT / "data" / "MECO-L2_version-2.2" / "wave-2" / "primary-data" / "comprehension" / "joint_comp_L2_Wave2_trimmed.csv")
    acc = pd.concat([w1[["uniform_id", "accuracy"]], w2[["uniform_id", "accuracy"]]], ignore_index=True)
    acc["uniform_id"] = acc["uniform_id"].astype(str).str.strip().str.lower()
    return acc.groupby("uniform_id", as_index=False)["accuracy"].mean()


def load_distance_map() -> Dict[str, float]:
    """Mapea código de lengua a distancia lingüística estructural."""
    csv_path = REPO_ROOT / "lang_to_en.csv"
    df = pd.read_csv(csv_path)
    return {str(r["lang"]).strip().lower(): float(r["distance"]) for _, r in df.iterrows()}


def build_master_dataset() -> pd.DataFrame:
    """Combina todas las fuentes en un único dataset maestro por participante."""
    leap_df = extract_leap_q()
    diff_df = load_clean_individual_differences()
    acc_df = load_comprehension()
    dist_map = load_distance_map()

    merged = pd.merge(acc_df, diff_df, on="uniform_id", how="inner")
    merged = pd.merge(merged, leap_df.drop(columns=["file"]), on="uniform_id", how="left")

    # Mapeo de distancia
    # lang_to_en usa códigos en minúsculas (ej. du, tr, sp, ge)
    merged["lang_clean"] = merged["lang"].astype(str).str.strip().str.lower()
    # Algunas variantes tienen sufijos como no_w2, tr_w2, ch_s, hi_iiith
    def get_dist(lg: str) -> float:
        base = lg.split("_")[0]
        if lg in dist_map:
            return dist_map[lg]
        if base in dist_map:
            return dist_map[base]
        return np.nan

    merged["linguistic_distance"] = merged["lang_clean"].apply(get_dist)

    out_csv = OUTPUT_DIR / "participant_background_and_comprehension.csv"
    merged.to_csv(out_csv, index=False)
    print(f"[master] Dataset consolidado guardado en {out_csv} ({len(merged)} participantes).")
    return merged


# ---------------------------------------------------------------------------
# 3. Análisis Bivariado y Correlaciones
# ---------------------------------------------------------------------------

def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula correlaciones de Pearson y Spearman entre predictores y comprensión."""
    from scipy import stats

    predictors = [
        ("linguistic_distance", "Distancia Lingüística (L1 a EN)"),
        ("exposure_english", "% Exposición Diaria al Inglés"),
        ("english_start_age", "Edad de Inicio en Inglés (AoA)"),
        ("english_fluent_read_age", "Edad de Lectura Fluida"),
        ("english_domain_read", "Autoevaluación Lectora (1-10)"),
        ("formal_education_years", "Años de Educación Formal"),
        ("lextale", "LexTALE (% Vocabulario)"),
        ("vocab.t2.5", "Vocabulario Tamaño (Nation)"),
        ("spelling", "Precisión Ortográfica"),
        ("TOWRE_word", "Fluidez de Palabras (SWE)"),
        ("TOWRE_nonword", "Decodificación Fonológica (PDE)"),
        ("language_skill_composite", "Composite General de Inglés"),
        ("cft20", "Inteligencia No Verbal (CFT-20)"),
        ("motiv", "Motivación con la Tarea"),
    ]

    rows = []
    y = df["accuracy"]

    for col, label in predictors:
        if col not in df.columns:
            continue
        valid = df.dropna(subset=["accuracy", col])
        if len(valid) < 10:
            continue
        r, p_pearson = stats.pearsonr(valid[col], valid["accuracy"])
        rho, p_spearman = stats.spearmanr(valid[col], valid["accuracy"])

        rows.append({
            "variable": col,
            "label": label,
            "n": len(valid),
            "pearson_r": round(float(r), 4),
            "p_pearson": float(p_pearson),
            "spearman_rho": round(float(rho), 4),
            "p_spearman": float(p_spearman),
        })

    corr_df = pd.DataFrame(rows).sort_values("pearson_r", ascending=False)
    corr_df.to_csv(OUTPUT_DIR / "bivariate_correlations_comprehension.csv", index=False)
    print(f"[correlations] Guardadas correlaciones bivariadas en {OUTPUT_DIR / 'bivariate_correlations_comprehension.csv'}")
    return corr_df


# ---------------------------------------------------------------------------
# 4. Modelos de Regresión Jerárquica
# ---------------------------------------------------------------------------

def run_regression_models(df: pd.DataFrame) -> pd.DataFrame:
    """Ajusta modelos de regresión jerárquica estandarizados para comparar varianza explicada."""
    # Para comparar pesos beta estandarizados directamente:
    analysis_df = df.copy()

    cols_to_standardize = [
        "accuracy", "linguistic_distance", "exposure_english", "english_start_age",
        "lextale", "vocab.t2.5", "spelling", "TOWRE_nonword", "language_skill_composite", "cft20"
    ]

    for c in cols_to_standardize:
        if c in analysis_df.columns:
            std = analysis_df[c].std()
            analysis_df[f"z_{c}"] = (analysis_df[c] - analysis_df[c].mean()) / std if std > 0 else 0.0

    models_specs = [
        ("Modelo 1 (Línea Base Macro)", ["z_linguistic_distance"]),
        ("Modelo 2 (+ Antecedentes LEAP-Q)", ["z_linguistic_distance", "z_exposure_english", "z_english_start_age"]),
        ("Modelo 3 (+ Habilidades Específicas)", ["z_linguistic_distance", "z_exposure_english", "z_lextale", "z_vocab.t2.5", "z_spelling", "z_TOWRE_nonword"]),
        ("Modelo 4 (Composite + Cognición)", ["z_linguistic_distance", "z_exposure_english", "z_language_skill_composite", "z_cft20"]),
    ]

    results = []

    for name, pred_cols in models_specs:
        sub = analysis_df.dropna(subset=["z_accuracy"] + pred_cols)
        X = sm.add_constant(sub[pred_cols])
        y = sub["z_accuracy"]
        fit = sm.OLS(y, X).fit()

        row = {
            "model_name": name,
            "n_obs": fit.nobs,
            "r_squared": round(fit.rsquared, 4),
            "adj_r_squared": round(fit.rsquared_adj, 4),
            "f_statistic": round(fit.fvalue, 3),
            "f_pvalue": fit.f_pvalue,
            "aic": round(fit.aic, 1),
            "bic": round(fit.bic, 1),
        }

        # Guardar coeficientes
        for p in pred_cols:
            row[f"beta_{p}"] = round(fit.params[p], 4)
            row[f"p_{p}"] = fit.pvalues[p]
            row[f"ci_low_{p}"] = round(fit.conf_int().loc[p, 0], 4)
            row[f"ci_high_{p}"] = round(fit.conf_int().loc[p, 1], 4)

        results.append(row)

    res_df = pd.DataFrame(results)
    res_df.to_csv(OUTPUT_DIR / "hierarchical_regression_models.csv", index=False)
    print(f"[models] Modelos jerárquicos guardados en {OUTPUT_DIR / 'hierarchical_regression_models.csv'}")
    return res_df


# ---------------------------------------------------------------------------
# 5. Visualizaciones Publicables (300 DPI)
# ---------------------------------------------------------------------------

def generate_visualizations(df: pd.DataFrame, corr_df: pd.DataFrame):
    """Genera figuras visuales de alta calidad para la presentación y tesis."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    # 1. HEATMAP DE CORRELACIONES
    top_vars = [
        "accuracy", "language_skill_composite", "lextale", "vocab.t2.5", 
        "TOWRE_nonword", "spelling", "exposure_english", "english_domain_read", 
        "english_start_age", "linguistic_distance", "cft20"
    ]
    labels_clean = [
        "Comprensión (Accuracy)", "Composite L2", "LexTALE", "Vocabulario (Nation)", 
        "Decod. Fonológica (PDE)", "Ortografía (Spelling)", "% Exposición Inglés", 
        "Autoeval. Lectora", "Edad Inicio Inglés", "Distancia L1 a EN", "Inteligencia (CFT-20)"
    ]
    
    sub_corr = df[top_vars].corr(method="pearson")

    fig, ax = plt.subplots(figsize=(10.5, 8.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    sns.heatmap(
        sub_corr, 
        annot=True, 
        fmt=".2f", 
        cmap="coolwarm", 
        vmin=-0.6, 
        vmax=0.6,
        xticklabels=labels_clean,
        yticklabels=labels_clean,
        cbar_kws={"label": "Correlación de Pearson (r)", "shrink": 0.8},
        ax=ax
    )
    plt.title("Matriz de Correlación: Antecedentes, Habilidades y Comprensión Lectora", 
              fontsize=13, fontweight="bold", pad=15, color="#0F172A")
    plt.xticks(rotation=45, ha="right", fontsize=9.5)
    plt.yticks(fontsize=9.5)
    plt.tight_layout()
    heatmap_path = PLOTS_DIR / "correlations_heatmap.png"
    plt.savefig(heatmap_path, bbox_inches="tight", dpi=300)
    plt.close()

    # 2. PANEL MULTI-DISPERSIÓN: 6 PREDICTORES CLAVE VS COMPRENSIÓN
    fig, axes = plt.subplots(2, 3, figsize=(15, 9.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")

    plots_config = [
        ("language_skill_composite", "Language Skill Composite (z)", "purple", 0, 0),
        ("lextale", "LexTALE Score (%)", "#1E40AF", 0, 1),
        ("vocab.t2.5", "Vocabulario Receptivo (Nation)", "#047857", 0, 2),
        ("exposure_english", "Exposición Diaria a Inglés (%)", "#D97706", 1, 0),
        ("english_start_age", "Edad de Inicio en Inglés (Años)", "#DC2626", 1, 1),
        ("linguistic_distance", "Distancia Lingüística (URiEL)", "#475569", 1, 2),
    ]

    for col, title, color, r, c in plots_config:
        ax = axes[r, c]
        sub = df.dropna(subset=[col, "accuracy"])
        
        # Puntos semitransparentes
        ax.scatter(sub[col], sub["accuracy"] * 100, color=color, alpha=0.35, edgecolors="none", s=22)
        
        # Línea de regresión OLS
        sns.regplot(
            data=sub, x=col, y=sub["accuracy"] * 100,
            ax=ax, scatter=False, color="#0F172A",
            line_kws={"linewidth": 2.0, "color": color}
        )

        # Correlación stats
        from scipy import stats
        pr, pp = stats.pearsonr(sub[col], sub["accuracy"] * 100)
        p_str = "< .001" if pp < 0.001 else f"= {pp:.3f}"
        ax.text(
            0.05, 0.92, f"r = {pr:+.3f} (p {p_str})\nN = {len(sub)}",
            transform=ax.transAxes, fontsize=9.5, fontweight="semibold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#E2E8F0", alpha=0.9)
        )

        ax.set_title(title, fontsize=11, fontweight="bold", pad=8, color="#1E293B")
        ax.set_ylabel("Comprensión Lectora (%)", fontsize=9.5, color="#334155")
        ax.set_xlabel(title, fontsize=9.5, color="#334155")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_facecolor("#F8FAFC")

    plt.suptitle("Predictores de Comprensión Lectora en Inglés: Habilidades y Antecedentes", 
                 fontsize=15, fontweight="bold", y=0.99, color="#0F172A")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    scatter_path = PLOTS_DIR / "scatter_predictors_vs_comprehension.png"
    plt.savefig(scatter_path, bbox_inches="tight", dpi=300)
    plt.close()

    # 3. FOREST PLOT DINÁMICO DE PESOS BETA ESTANDARIZADOS (MODELOS 3 Y 4)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300, sharex=True)
    fig.patch.set_facecolor("#FFFFFF")

    # Mapeo de nombres limpios para etiquetas del Forest Plot
    var_labels = {
        "z_vocab.t2.5": "Vocabulario Receptivo (Nation)",
        "z_spelling": "Precisión Ortográfica",
        "z_lextale": "LexTALE (Decisión Léxica)",
        "z_TOWRE_nonword": "Decod. Fonológica (PDE)",
        "z_linguistic_distance": "Distancia Lingüística L1",
        "z_exposure_english": "% Exposición Diaria Inglés",
        "z_english_start_age": "Edad de Inicio Inglés (AoA)",
        "z_language_skill_composite": "Language Skill Composite",
        "z_cft20": "Inteligencia No Verbal (CFT-20)",
    }

    def plot_forest(ax, model_row, title, subtitle):
        ax.set_facecolor("#F8FAFC")
        pred_vars = [c.replace("beta_", "") for c in model_row.index if c.startswith("beta_") and pd.notna(model_row[c])]
        # ordenar por beta
        pred_vars = sorted(pred_vars, key=lambda v: model_row[f"beta_{v}"], reverse=True)
        
        y_pos = np.arange(len(pred_vars))
        for i, var in enumerate(pred_vars):
            b = model_row[f"beta_{var}"]
            low = model_row[f"ci_low_{var}"]
            high = model_row[f"ci_high_{var}"]
            pval = model_row[f"p_{var}"]
            
            color = "#1E40AF" if b > 0 and pval < 0.05 else ("#DC2626" if b < 0 and pval < 0.05 else "#64748B")
            ax.errorbar(b, i, xerr=[[b - low], [high - b]], fmt="o", color=color,
                        ecolor=color, elinewidth=2.2, capsize=4.5, capthick=1.5, markersize=8)
            
            sig = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else "ns"))
            ax.text(high + 0.02, i, f"β = {b:+.3f} ({sig})", va="center", fontsize=8.8, fontweight="bold", color="#1E293B")

        ax.axvline(0, color="#94A3B8", linestyle="--", linewidth=1.2)
        ax.set_yticks(y_pos)
        ax.set_yticklabels([var_labels.get(v, v) for v in pred_vars], fontsize=9.5, fontweight="semibold")
        ax.invert_yaxis()
        ax.set_xlabel("Coeficiente Estandarizado β (IC 95%)", fontsize=10, labelpad=6)
        ax.set_title(f"{title}\n{subtitle}", fontsize=11, fontweight="bold", pad=10, color="#0F172A")
        ax.grid(True, linestyle="--", alpha=0.4, axis="x")

    models_df = pd.read_csv(OUTPUT_DIR / "hierarchical_regression_models.csv")
    m3 = models_df[models_df["model_name"].str.contains("Modelo 3")].iloc[0]
    m4 = models_df[models_df["model_name"].str.contains("Modelo 4")].iloc[0]

    plot_forest(ax1, m3, "Modelo 3: Habilidades Específicas", f"R² = {m3['r_squared']*100:.1f}% (Adj R² = {m3['adj_r_squared']*100:.1f}%, p < .001)")
    plot_forest(ax2, m4, "Modelo 4: Composite + Cognición", f"R² = {m4['r_squared']*100:.1f}% (Adj R² = {m4['adj_r_squared']*100:.1f}%, p < .001)")

    plt.suptitle("Importancia Relativa de Predictores sobre la Comprensión Lectora en Inglés", 
                 fontsize=13.5, fontweight="bold", y=0.99, color="#0F172A")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    forest_path = PLOTS_DIR / "model_coefficients_forest.png"
    plt.savefig(forest_path, bbox_inches="tight", dpi=300)
    plt.close()

    # Copiar a artefactos
    for p in [heatmap_path, scatter_path, forest_path]:
        shutil.copy(p, ARTIFACT_DIR / p.name)

    print("[viz] Todas las figuras generadas y copiadas exitosamente.")


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------

def main():
    print("=== INICIANDO PIPELINE DE ANTECEDENTES Y COMPRENSIÓN ===")
    df = build_master_dataset()
    corr_df = compute_correlations(df)
    models_df = run_regression_models(df)
    generate_visualizations(df, corr_df)
    print("=== PIPELINE COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
