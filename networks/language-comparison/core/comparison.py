"""
comparison.py

Comparación entre familias lingüísticas: construye (o reutiliza) una red por
familia para un trial/wave, recolecta sus métricas y accuracy, y genera un
reporte HTML comparativo con pestañas por familia.
"""

import base64
import csv
import json
import os
import pickle
from collections import OrderedDict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .language_groups import ALL_FAMILIES, FAMILY_LABELS, resolve_group
from .network_builder import build_group_network, build_prefix
from .persistence import check_cache_fresh, save_built_network
from .data_io import (
    load_accuracy,
    load_fixations_by_group,
    normalize_session_ps,
    summarize_accuracy,
)
from .paths import file_sha256
from .visualization import visualize_group_network


def _resolve_compare_families(wave, families):
    """
    Devuelve la lista de familias a comparar, solo las que tienen lenguas
    presentes en el wave.

    families: lista de nombres de familia ('germanic', ...) o vacía = todas.
    """
    if families:
        result = []
        for f in families:
            if f == "all":
                result.extend(ALL_FAMILIES)
            elif f in ALL_FAMILIES:
                result.append(f)
            else:
                print(f"[!] Familia desconocida, se omite: {f}")
    else:
        result = list(ALL_FAMILIES)

    available = []
    for f in result:
        langs = resolve_group(f, wave)
        if not langs:
            print(f"[!] Familia '{f}' sin lenguas en wave {wave}; se omite.")
            continue
        available.append(f)
    return available


def _existing_build_dir(outdir, trialid, wave, normalize, lang_group):
    """Busca un build existente de la familia bajo outdir."""
    if not os.path.isdir(outdir):
        return None
    pattern = f"langcomp_trial{trialid}_w{wave}_{normalize}"
    for name in os.listdir(outdir):
        if not name.startswith(pattern):
            continue
        if f"_{lang_group}_" not in name and not name.endswith(f"_{lang_group}"):
            continue
        meta_path = os.path.join(outdir, name, "metadata.json")
        if os.path.exists(meta_path):
            return os.path.join(outdir, name)
    return None


def _build_family(
    lang_group,
    trialid,
    wave,
    normalize,
    outdir,
    do_interactive,
    reuse_cache,
):
    """
    Construye la red de una familia (o reutiliza el build existente si
    reuse_cache=True y el cache está fresco). Retorna (build_dir, metadata)
    o (None, None) si no hay fijaciones.
    """
    if reuse_cache:
        existing = _existing_build_dir(outdir, trialid, wave, normalize, lang_group)
        if existing is not None:
            meta_path = os.path.join(existing, "metadata.json")
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            sources = [s["path"] for s in meta.get("source_files", [])]
            check_cache_fresh(meta, sources)
            print(f"--> Reutilizando build existente para '{lang_group}': {existing}")
            return existing, meta

    fixations, source_files, langs = load_fixations_by_group(
        wave=wave, group=lang_group, trialid=trialid
    )
    if not fixations:
        print(f"[!] Familia '{lang_group}': sin fijaciones; se omite.")
        return None, None

    if normalize == "zscore":
        fixations = normalize_session_ps(fixations)
        for f in fixations:
            f["has_z"] = True
    elif normalize == "none":
        for f in fixations:
            f["ps_z"] = 0.0
            f["has_z"] = False
    else:
        raise ValueError(f"normalize debe ser 'zscore' o 'none', got {normalize!r}")

    acc_map, comp_files = load_accuracy(wave, set(langs))
    accuracy_summary, n_participants, n_with_accuracy = summarize_accuracy(
        acc_map, fixations
    )

    text_label = f"Language-Comparison_{lang_group}_Trial_{trialid}"
    G = build_group_network(fixations, groupby="all", text_label=text_label)

    from .language_groups import langs_without_ps

    ps_absent = langs_without_ps(wave)
    prefix = build_prefix(
        lang_group=lang_group,
        trialid=trialid,
        wave=wave,
        normalize=normalize,
        group_langs=langs,
        ps_absent_langs=[l for l in ps_absent if l in resolve_group(lang_group, wave)],
    )

    all_source = list(source_files) + list(comp_files)
    build_dir = save_built_network(
        G,
        output_dir=outdir,
        prefix=prefix,
        source_files=all_source,
        groupby="all",
        wave=wave,
        trialid=trialid,
        lang_group=lang_group,
        languages=langs,
        accuracy_summary=accuracy_summary,
        n_participants=n_participants,
        n_with_accuracy=n_with_accuracy,
        normalize=normalize,
    )

    visualize_group_network(G, build_dir, prefix)

    if do_interactive:
        from .interactive_viz import visualize_group_network_interactive

        visualize_group_network_interactive(G, build_dir, prefix)

    meta_path = os.path.join(build_dir, "metadata.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    return build_dir, meta


def collect_family_summaries(build_dirs):
    """
    A partir de los build_dirs por familia, arma una lista de dicts con el
    resumen: familia, accuracy (mean/median/n), n_participants,
    n_nodes, n_edges.
    """
    rows = []
    for family, (build_dir, meta) in build_dirs.items():
        if meta is None:
            continue
        acc = meta.get("accuracy") or {}
        rows.append(
            {
                "family": family,
                "label": FAMILY_LABELS.get(family, family),
                "accuracy_mean": acc.get("mean"),
                "accuracy_median": acc.get("median"),
                "accuracy_n": acc.get("n"),
                "n_participants": meta.get("n_participants"),
                "n_nodes": meta.get("n_nodes"),
                "n_edges": meta.get("n_edges"),
                "build_dir": build_dir,
            }
        )
    return rows


def load_attention_series(build_dirs):
    """
    Lee el nodes.csv de cada build y devuelve {family: DataFrame(wordnum,
    mean_ps_z, mean_ps, sentnum)} ordenado por wordnum.
    """
    series = OrderedDict()
    for family, (build_dir, _meta) in build_dirs.items():
        nodes_path = os.path.join(build_dir, "nodes.csv")
        if not os.path.exists(nodes_path):
            continue
        df = pd.read_csv(nodes_path)
        cols = [c for c in ["wordnum", "mean_ps_z", "mean_ps", "sentnum"] if c in df.columns]
        df = df[cols].copy()
        if "mean_ps_z" in df.columns:
            df["mean_ps_z"] = pd.to_numeric(df["mean_ps_z"], errors="coerce").fillna(0.0)
        if "mean_ps" in df.columns:
            df["mean_ps"] = pd.to_numeric(df["mean_ps"], errors="coerce").fillna(0.0)
        df = df.sort_values("wordnum")
        series[family] = df
    return series


def visualize_comparison_plots(summaries, attention_series, out_dir):
    """
    Genera:
      plots/comparison_accuracy.png — barras de accuracy.mean por familia.
      plots/comparison_attention.png — líneas mean_ps_z por wordnum (una por
                                       familia), con media móvil ligera.
    Retorna lista de rutas PNG generadas.
    """
    plots_dir = os.path.join(out_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    generated = []

    valid = [s for s in summaries if s.get("accuracy_mean") is not None]
    if valid:
        fig, ax = plt.subplots(figsize=(10, 5))
        names = [s["family"] for s in valid]
        means = [s["accuracy_mean"] for s in valid]
        ns = [s["accuracy_n"] for s in valid]
        bars = ax.bar(names, means, color="#2980b9", alpha=0.85)
        for b, n in zip(bars, ns):
            ax.text(
                b.get_x() + b.get_width() / 2,
                b.get_height() + 0.01,
                f"n={n}",
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
        print(f"[OK] Plot de accuracy comparativo guardado en: {path}")

    if attention_series:
        fig, ax = plt.subplots(figsize=(14, 6))
        for family, df in attention_series.items():
            if df.empty or "mean_ps_z" not in df.columns:
                continue
            if df["mean_ps_z"].abs().sum() == 0:
                continue
            smoothed = df["mean_ps_z"].rolling(5, min_periods=1, center=True).mean()
            ax.plot(df["wordnum"], smoothed, label=f"{family}", linewidth=1.4, alpha=0.9)
        ax.axhline(0, color="#7f8c8d", linewidth=0.8, linestyle="-", alpha=0.7)
        ax.set_title("Atención por palabra (mean_ps_z) comparada entre familias", fontsize=12)
        ax.set_xlabel("Posición de palabra (wordnum)")
        ax.set_ylabel("mean_ps_z (media móvil 5)")
        ax.legend(loc="best", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.3)
        fig.tight_layout()
        path = os.path.join(plots_dir, "comparison_attention.png")
        fig.savefig(path, dpi=200)
        plt.close(fig)
        generated.append(path)
        print(f"[OK] Plot de atención comparativo guardado en: {path}")

    return generated


def _png_to_base64(path):
    """Codifica un PNG a base64 data URI."""
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def _ensure_interactive_html(build_dir, family, trialid):
    """
    Asegura que exista network_interactive.html en el build. Si el build fue
    reutilizado y no tiene el HTML (se construyó con --no-interactive), lo
    regenera desde graph.pkl.
    """
    html_path = os.path.join(build_dir, "network_interactive.html")
    if os.path.exists(html_path):
        return html_path
    pkl_path = os.path.join(build_dir, "graph.pkl")
    if not os.path.exists(pkl_path):
        return None
    print(f"--> Regenerando network_interactive.html para '{family}' desde graph.pkl")
    with open(pkl_path, "rb") as f:
        G = pickle.load(f)
    from .interactive_viz import visualize_group_network_interactive

    visualize_group_network_interactive(G, build_dir, f"trial{trialid}_{family}")
    return html_path


def build_comparison_html(
    summaries,
    plot_pngs,
    out_dir,
    trialid,
    wave,
    reuse=True,
):
    """
    Ensambla comparison_report.html: título, tabla resumen, plots y pestañas
    por familia con iframe a su network_interactive.html + bloque de métricas.
    """
    html_path = os.path.join(out_dir, "comparison_report.html")

    table_rows = ""
    for s in summaries:
        acc = s.get("accuracy_mean")
        acc_str = f"{acc:.3f}" if acc is not None else "n/a"
        med = s.get("accuracy_median")
        med_str = f"{med:.3f}" if med is not None else "n/a"
        table_rows += (
            "<tr>"
            f"<td><b>{s['family']}</b></td>"
            f"<td>{s['label']}</td>"
            f"<td>{acc_str}</td>"
            f"<td>{med_str}</td>"
            f"<td>{s.get('accuracy_n', '')}</td>"
            f"<td>{s.get('n_participants', '')}</td>"
            f"<td>{s.get('n_nodes', '')}</td>"
            f"<td>{s.get('n_edges', '')}</td>"
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

        acc = s.get("accuracy_mean")
        acc_str = f"{acc:.3f}" if acc is not None else "n/a"
        med = s.get("accuracy_median")
        med_str = f"{med:.3f}" if med is not None else "n/a"

        metrics_html = (
            f'<div style="background:#f8f9fa;border:1px solid #e0e0e0;'
            f'border-radius:8px;padding:12px 16px;margin:12px 0;font-family:sans-serif;">'
            f'<b>{FAMILY_LABELS.get(family, family)}</b> '
            f'— accuracy: <b>{acc_str}</b> (mediana {med_str}, n={s.get("accuracy_n", "")}) · '
            f'participantes: {s.get("n_participants", "")} · '
            f'nodos: {s.get("n_nodes", "")} · aristas: {s.get("n_edges", "")}'
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
                f'Red interactiva no disponible para esta familia '
                f'(graph.pkl ausente).</p>'
            )

        selected = 'checked' if i == 0 else ''
        tabs_html += (
            f'<input type="radio" name="tabs" id="tab-{i}" class="tab-radio" {selected}>'
            f'<label class="tab-label" for="tab-{i}">{family}</label>'
            f'<div class="tab-content" id="content-{i}">{body}</div>'
        )

    css = """
    <style>
    body { font-family: -apple-system, 'Segoe UI', sans-serif; margin: 24px; }
    h1 { text-align: center; }
    table.summary { border-collapse: collapse; margin: 16px auto; width: 90%; }
    table.summary th, table.summary td { border: 1px solid #ddd; padding: 6px 10px; text-align: center; }
    table.summary th { background: #2c3e50; color: #fff; }
    table.summary tr:nth-child(even) { background: #f5f6fa; }
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
<title>Comparación entre Familias Lingüísticas — Trial {trialid}, Wave {wave}</title>
{css}
</head>
<body>
<h1>Comparación entre Familias Lingüísticas — Trial {trialid}, Wave {wave}</h1>
<p style="text-align:center;color:#555;">
{len(summaries)} familias · normalized={ 'zscore' if True else '' } · apertura desde esta carpeta para que las pestañas carguen.
</p>
<table class="summary">
<thead>
<tr>
<th>Familia</th><th>Grupo</th><th>accuracy (mean)</th><th>accuracy (mediana)</th>
<th>n accuracy</th><th>participantes</th><th>nodos</th><th>aristas</th>
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
    """Exporta comparison_summary.csv con accuracy + métricas por familia."""
    csv_path = os.path.join(out_dir, "comparison_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "trialid",
                "wave",
                "family",
                "label",
                "accuracy_mean",
                "accuracy_median",
                "accuracy_n",
                "n_participants",
                "n_nodes",
                "n_edges",
            ]
        )
        for s in summaries:
            w.writerow(
                [
                    trialid,
                    wave,
                    s["family"],
                    s["label"],
                    s.get("accuracy_mean"),
                    s.get("accuracy_median"),
                    s.get("accuracy_n"),
                    s.get("n_participants"),
                    s.get("n_nodes"),
                    s.get("n_edges"),
                ]
            )
    print(f"[OK] Resumen comparativo guardado en: {csv_path}")
    return csv_path


def run_comparison(
    trialid,
    wave,
    families=None,
    normalize="zscore",
    outdir=None,
    reuse_cache=True,
    do_interactive=True,
):
    """
    Orquesta la comparación: construye/reutiliza una red por familia, recolecta
    resúmenes, genera plots y el HTML comparativo. Retorna el directorio de
    salida de la comparación.
    """
    if outdir is None:
        outdir = os.path.join("networks", "language-comparison", "output")

    fam_list = _resolve_compare_families(wave, families)
    print(f"--> Familias a comparar ({len(fam_list)}): {', '.join(fam_list)}")

    build_dirs = OrderedDict()
    for family in fam_list:
        print(f"\n=== Familia: {family} ===")
        build_dir, meta = _build_family(
            lang_group=family,
            trialid=trialid,
            wave=wave,
            normalize=normalize,
            outdir=outdir,
            do_interactive=do_interactive,
            reuse_cache=reuse_cache,
        )
        if build_dir is not None:
            build_dirs[family] = (build_dir, meta)

    if not build_dirs:
        print("[!] Ninguna familia produjo fijaciones; no hay comparación.")
        return None

    summaries = collect_family_summaries(build_dirs)

    comp_dir = os.path.join(outdir, f"comparison_trial{trialid}_w{wave}")
    os.makedirs(comp_dir, exist_ok=True)

    attention = load_attention_series(build_dirs)
    pngs = visualize_comparison_plots(summaries, attention, comp_dir)

    build_comparison_html(
        summaries,
        pngs,
        comp_dir,
        trialid,
        wave,
    )

    export_comparison_summary(summaries, comp_dir, trialid, wave)

    print("\n" + "=" * 60)
    print("RESUMEN COMPARATIVO")
    print("=" * 60)
    for s in summaries:
        acc = s.get("accuracy_mean")
        acc_str = f"{acc:.3f}" if acc is not None else "n/a"
        print(f"  {s['family']:14s} accuracy={acc_str}  "
              f"n={s.get('accuracy_n', '')}  "
              f"nodos={s.get('n_nodes', '')}  aristas={s.get('n_edges', '')}")
    print("=" * 60 + "\n")

    return comp_dir
