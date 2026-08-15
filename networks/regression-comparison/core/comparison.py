"""
comparison.py

Comparación entre familias lingüísticas para la red de regresiones: recolecta
métricas y accuracy de cada build y genera un reporte HTML con tabla resumen,
plots y una pestaña por familia con su red interactiva.

Mismo formato que `language-comparison/core/comparison.py`; cambian las
variables comparadas, porque cambian las que la red produce.
"""

import base64
import csv
import os
import pickle
from collections import OrderedDict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from ._langcomp import get_langcomp_core
from .interactive_viz import EDGE_COLORS, visualize_regression_network_interactive
from .orchestrator import build_families

# Métricas comparables entre familias sin corrección por tamaño muestral.
_SAFE_METRICS = ("regression_share", "refix_share", "reciprocity")


def collect_family_summaries(build_dirs):
    """Arma la lista de dicts con el resumen por familia."""
    lc = get_langcomp_core()
    rows = []
    for family, (build_dir, meta) in build_dirs.items():
        if meta is None:
            continue
        acc = meta.get("accuracy") or {}
        rows.append(
            {
                "family": family,
                "label": lc.FAMILY_LABELS.get(family, family),
                "languages": ", ".join(meta.get("languages", [])),
                "accuracy_mean": acc.get("mean"),
                "accuracy_median": acc.get("median"),
                "accuracy_n": acc.get("n"),
                "n_participants": meta.get("n_participants"),
                "n_nodes": meta.get("n_nodes"),
                "n_edges": meta.get("n_edges"),
                "n_edges_forward": meta.get("n_edges_forward"),
                "n_edges_regression": meta.get("n_edges_regression"),
                "n_edges_regression_local": meta.get("n_edges_regression_local"),
                "n_edges_regression_global": meta.get("n_edges_regression_global"),
                "regression_share": meta.get("regression_share"),
                "refix_share": meta.get("refix_share"),
                "reciprocity": meta.get("reciprocity"),
                "reg_source_agreement": meta.get("reg_source_agreement"),
                "n_sessions_discarded": meta.get("n_sessions_discarded"),
                "build_dir": build_dir,
            }
        )
    return rows


def load_regression_profiles(build_dirs):
    """
    Lee nodes.csv de cada build y devuelve {familia: DataFrame(wordnum,
    reg_in_rate, refix_rate)} ordenado por wordnum.
    """
    series = OrderedDict()
    for family, (build_dir, _meta) in build_dirs.items():
        nodes_path = os.path.join(build_dir, "nodes.csv")
        if not os.path.exists(nodes_path):
            continue
        df = pd.read_csv(nodes_path)
        cols = [c for c in ("wordnum", "reg_in_rate", "refix_rate", "word") if c in df]
        df = df[cols].copy()
        for c in ("reg_in_rate", "refix_rate"):
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        series[family] = df.sort_values("wordnum")
    return series


def visualize_comparison_plots(summaries, profiles, out_dir):
    """
    Genera los plots comparativos y devuelve sus rutas.

      comparison_accuracy.png        — accuracy media por familia.
      comparison_saccade_types.png   — % de regresión y % de refijación.
      comparison_regression_profile.png — reg_in_rate por wordnum.
    """
    plots_dir = os.path.join(out_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    generated = []

    valid = [s for s in summaries if s.get("accuracy_mean") is not None]
    if valid:
        fig, ax = plt.subplots(figsize=(10, 5))
        names = [s["family"] for s in valid]
        means = [s["accuracy_mean"] for s in valid]
        bars = ax.bar(names, means, color="#2980b9", alpha=0.85)
        for b, s in zip(bars, valid):
            ax.text(
                b.get_x() + b.get_width() / 2,
                b.get_height() + 0.01,
                f"n={s['accuracy_n']}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        ax.axhline(0.5, color="#7f8c8d", linestyle="--", linewidth=0.8, alpha=0.6)
        ax.set_title("Comprensión lectora media por familia lingüística", fontsize=12)
        ax.set_ylabel("accuracy (mean)")
        ax.set_ylim(0, 1.05)
        ax.grid(True, axis="y", linestyle=":", alpha=0.4)
        fig.tight_layout()
        path = os.path.join(plots_dir, "comparison_accuracy.png")
        fig.savefig(path, dpi=200)
        plt.close(fig)
        generated.append(path)
        print(f"[OK] Plot de accuracy guardado en: {path}")

    have = [s for s in summaries if s.get("regression_share") is not None]
    if have:
        fig, ax = plt.subplots(figsize=(11, 5))
        names = [s["family"] for s in have]
        x = range(len(names))
        reg = [100 * s["regression_share"] for s in have]
        refix = [100 * (s.get("refix_share") or 0.0) for s in have]
        w = 0.38
        ax.bar([i - w / 2 for i in x], reg, width=w,
               label="Regresiones (% de sacadas)", color=EDGE_COLORS["regression-local"])
        ax.bar([i + w / 2 for i in x], refix, width=w,
               label="Refijaciones (% de movimientos)", color="#7f8c8d")
        ax.set_xticks(list(x))
        ax.set_xticklabels(names)
        ax.set_ylabel("%")
        ax.set_title(
            "Composición del scanpath por familia — proporciones comparables "
            "entre grupos",
            fontsize=12,
        )
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, axis="y", linestyle=":", alpha=0.4)
        fig.tight_layout()
        path = os.path.join(plots_dir, "comparison_saccade_types.png")
        fig.savefig(path, dpi=200)
        plt.close(fig)
        generated.append(path)
        print(f"[OK] Plot de tipos de sacada guardado en: {path}")

    if profiles:
        fig, ax = plt.subplots(figsize=(14, 6))
        for family, df in profiles.items():
            if df.empty or "reg_in_rate" not in df:
                continue
            smoothed = df["reg_in_rate"].rolling(5, min_periods=1, center=True).mean()
            ax.plot(df["wordnum"], smoothed, label=family, linewidth=1.4, alpha=0.9)
        ax.set_title(
            "Regresiones recibidas por palabra (reg_in_rate) — dónde vuelve la "
            "mirada a lo largo del texto",
            fontsize=12,
        )
        ax.set_xlabel("Posición de palabra (wordnum)")
        ax.set_ylabel("regresiones entrantes por lector (media móvil 5)")
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.3)
        fig.tight_layout()
        path = os.path.join(plots_dir, "comparison_regression_profile.png")
        fig.savefig(path, dpi=200)
        plt.close(fig)
        generated.append(path)
        print(f"[OK] Plot de perfil de regresión guardado en: {path}")

    return generated


def _png_to_base64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def _ensure_interactive_html(build_dir, family, trialid):
    """Regenera network_interactive.html desde graph.pkl si no existe."""
    html_path = os.path.join(build_dir, "network_interactive.html")
    if os.path.exists(html_path):
        return html_path
    pkl_path = os.path.join(build_dir, "graph.pkl")
    if not os.path.exists(pkl_path):
        return None
    print(f"--> Regenerando network_interactive.html para '{family}' desde graph.pkl")
    with open(pkl_path, "rb") as f:
        G = pickle.load(f)
    visualize_regression_network_interactive(
        G, build_dir, os.path.basename(build_dir)
    )
    return html_path


def _fmt(value, decimals=3, pct=False):
    if value is None:
        return "n/a"
    if pct:
        return f"{100 * value:.1f}%"
    return f"{value:.{decimals}f}"


def build_comparison_html(summaries, plot_pngs, out_dir, trialid, wave):
    """Ensambla comparison_report.html."""
    lc = get_langcomp_core()
    html_path = os.path.join(out_dir, "comparison_report.html")

    table_rows = ""
    for s in summaries:
        table_rows += (
            "<tr>"
            f"<td><b>{s['family']}</b></td>"
            f"<td>{s['label']}</td>"
            f"<td class='mono'>{s['languages']}</td>"
            f"<td>{_fmt(s.get('accuracy_mean'))}</td>"
            f"<td>{s.get('accuracy_n', '')}</td>"
            f"<td>{s.get('n_participants', '')}</td>"
            f"<td>{s.get('n_nodes', '')}</td>"
            f"<td class='dim'>{s.get('n_edges', '')}</td>"
            f"<td class='dim'>{s.get('n_edges_forward', '')}</td>"
            f"<td class='dim'>{s.get('n_edges_regression', '')}</td>"
            f"<td><b>{_fmt(s.get('regression_share'), pct=True)}</b></td>"
            f"<td><b>{_fmt(s.get('refix_share'), pct=True)}</b></td>"
            f"<td><b>{_fmt(s.get('reciprocity'))}</b></td>"
            f"<td>{_fmt(s.get('reg_source_agreement'))}</td>"
            "</tr>"
        )

    plots_html = ""
    for png in plot_pngs:
        plots_html += (
            f'<div style="text-align:center; margin:20px 0;">'
            f'<img src="{_png_to_base64(png)}" style="max-width:100%;'
            f'border:1px solid #ddd; border-radius:6px;"></div>'
        )

    tabs_html = ""
    for i, s in enumerate(summaries):
        family = s["family"]
        build_dir = s.get("build_dir")
        html_net = _ensure_interactive_html(build_dir, family, trialid) if build_dir else None
        rel = os.path.relpath(html_net, out_dir).replace("\\", "/") if html_net else None

        metrics_html = (
            f'<div style="background:#f8f9fa;border:1px solid #e0e0e0;'
            f'border-radius:8px;padding:12px 16px;margin:12px 0;font-family:sans-serif;">'
            f'<b>{s["label"]}</b> ({s["languages"]}) '
            f'— accuracy: <b>{_fmt(s.get("accuracy_mean"))}</b> '
            f'(mediana {_fmt(s.get("accuracy_median"))}, n={s.get("accuracy_n", "")}) · '
            f'participantes: {s.get("n_participants", "")} · '
            f'nodos: {s.get("n_nodes", "")} · '
            f'aristas: {s.get("n_edges", "")} '
            f'({s.get("n_edges_forward", "")} avance / '
            f'{s.get("n_edges_regression_local", "")} regresión intra-oración / '
            f'{s.get("n_edges_regression_global", "")} inter-oración) · '
            f'regresiones: <b>{_fmt(s.get("regression_share"), pct=True)}</b> de las sacadas · '
            f'refijaciones: <b>{_fmt(s.get("refix_share"), pct=True)}</b> · '
            f'reciprocidad: <b>{_fmt(s.get("reciprocity"))}</b>'
            f'</div>'
        )

        if rel:
            body = (
                f'{metrics_html}'
                f'<iframe src="{rel}" style="width:100%;height:760px;border:1px solid '
                f'#ccc;border-radius:6px;"></iframe>'
            )
        else:
            body = (
                f'{metrics_html}'
                f'<p style="font-family:sans-serif;color:#888;">'
                f'Red interactiva no disponible para esta familia (graph.pkl ausente).</p>'
            )

        selected = "checked" if i == 0 else ""
        tabs_html += (
            f'<input type="radio" name="tabs" id="tab-{i}" class="tab-radio" {selected}>'
            f'<label class="tab-label" for="tab-{i}">{family}</label>'
            f'<div class="tab-content" id="content-{i}">{body}</div>'
        )

    legend_html = (
        '<div class="legend-strip">'
        f'<span><i style="background:{EDGE_COLORS["forward"]}"></i>Avance</span>'
        f'<span><i style="background:{EDGE_COLORS["regression-local"]}"></i>'
        'Regresión intra-oración</span>'
        f'<span><i style="background:{EDGE_COLORS["regression-global"]}"></i>'
        'Regresión inter-oración</span>'
        '<span>Nodo: color = regresiones recibidas por lector · tamaño = fijaciones</span>'
        '</div>'
    )

    css = """
    <style>
    body { font-family: -apple-system, 'Segoe UI', sans-serif; margin: 24px; }
    h1 { text-align: center; }
    table.summary { border-collapse: collapse; margin: 16px auto; width: 96%; font-size: 13px; }
    table.summary th, table.summary td { border: 1px solid #ddd; padding: 6px 9px; text-align: center; }
    table.summary th { background: #2c3e50; color: #fff; font-weight: 600; }
    table.summary tr:nth-child(even) { background: #f5f6fa; }
    table.summary td.mono { font-family: ui-monospace, Consolas, monospace; font-size: 11.5px; }
    table.summary td.dim { color: #888; }
    .legend-strip { display: flex; flex-wrap: wrap; gap: 18px; justify-content: center;
                    margin: 14px auto; font-size: 12.5px; color: #444; }
    .legend-strip i { display: inline-block; width: 16px; height: 3px; border-radius: 2px;
                      margin-right: 6px; vertical-align: middle; }
    .tabs { display: flex; flex-wrap: wrap; margin-top: 20px; }
    .tab-radio { display: none; }
    .tab-label { display: inline-block; padding: 8px 16px; background: #eee;
                 border-radius: 6px 6px 0 0; cursor: pointer; margin-right: 4px;
                 font-weight: 600; }
    .tab-content { width: 100%; order: 999; display: none; }
    .tab-radio:checked + .tab-label { background: #2c3e50; color: #fff; }
    .tab-radio:checked + .tab-label + .tab-content { display: block; border: 1px solid #ddd; padding: 12px; }
    </style>
    """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Redes de Regresión por Familia Lingüística — Trial {trialid}, Wave {wave}</title>
{css}
</head>
<body>
<h1>Redes de Regresión por Familia Lingüística — Trial {trialid}, Wave {wave}</h1>
<p style="text-align:center;color:#555;">
{len(summaries)} familias · scanpath en orden temporal · abrir desde esta carpeta
para que las pestañas carguen.
</p>
{legend_html}
<table class="summary">
<thead>
<tr>
<th>Familia</th><th>Grupo</th><th>Lenguas</th>
<th>accuracy</th><th>n acc.</th><th>lectores</th>
<th>nodos</th><th>aristas</th><th>avance</th><th>regresión</th>
<th>% regresión</th><th>% refijación</th><th>reciprocidad</th><th>concord. MECO</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>
{plots_html}
<div class="tabs">
{tabs_html}
</div>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Reporte comparativo guardado en: {html_path}")
    return html_path


def export_comparison_summary(summaries, out_dir, trialid, wave):
    """Exporta comparison_summary.csv."""
    csv_path = os.path.join(out_dir, "comparison_summary.csv")
    fields = [
        "family", "label", "languages", "accuracy_mean", "accuracy_median",
        "accuracy_n", "n_participants", "n_nodes", "n_edges", "n_edges_forward",
        "n_edges_regression", "n_edges_regression_local",
        "n_edges_regression_global", "regression_share", "refix_share",
        "reciprocity", "reg_source_agreement", "n_sessions_discarded",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trialid", "wave"] + fields)
        for s in summaries:
            w.writerow([trialid, wave] + [s.get(k) for k in fields])
    print(f"[OK] Resumen comparativo guardado en: {csv_path}")
    return csv_path


def run_comparison(
    trialid,
    wave,
    families=None,
    edge_weight="rate",
    min_rate=0.02,
    filter_discordant=True,
    outdir=None,
    reuse_cache=True,
    do_interactive=True,
):
    """
    Orquesta la comparación de un wave: construye o reutiliza una red por
    familia, recolecta resúmenes, genera plots y el HTML comparativo.

    Retorna el directorio de salida de la comparación.
    """
    outdir = outdir or os.path.join("networks", "regression-comparison", "output")
    wave = int(wave)

    build_dirs = build_families(
        lang_group=families or "all",
        trialid=trialid,
        wave=wave,
        edge_weight=edge_weight,
        min_rate=min_rate,
        filter_discordant=filter_discordant,
        outdir=outdir,
        do_interactive=do_interactive,
        reuse_cache=reuse_cache,
    )
    if not build_dirs:
        print("[!] Ninguna familia produjo red; no hay comparación.")
        return None

    summaries = collect_family_summaries(build_dirs)

    comp_dir = os.path.join(outdir, f"comparison_trial{trialid}_w{wave}")
    os.makedirs(comp_dir, exist_ok=True)

    profiles = load_regression_profiles(build_dirs)
    pngs = visualize_comparison_plots(summaries, profiles, comp_dir)

    build_comparison_html(summaries, pngs, comp_dir, trialid, wave)
    export_comparison_summary(summaries, comp_dir, trialid, wave)

    print("\n" + "=" * 66)
    print(f"RESUMEN COMPARATIVO — trial {trialid}, wave {wave}")
    print("=" * 66)
    for s in summaries:
        print(
            f"  {s['family']:14s} acc={_fmt(s.get('accuracy_mean'))}  "
            f"n={str(s.get('n_participants', '')):>4s}  "
            f"reg={_fmt(s.get('regression_share'), pct=True):>6s}  "
            f"refix={_fmt(s.get('refix_share'), pct=True):>6s}  "
            f"recip={_fmt(s.get('reciprocity'))}"
        )
    print("=" * 66 + "\n")

    return comp_dir
