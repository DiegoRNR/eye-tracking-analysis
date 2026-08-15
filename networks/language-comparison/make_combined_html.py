"""
make_combined_html.py

Script experimental: genera UN ÚNICO HTML autocontenido con las redes de
todas las familias de un trial/wave, renderizadas con un solo vis.Network
que hace swap de datos entre pestañas.

No modifica comparison.py ni los builds existentes. Solo lee los outputs ya
generados (graph.pkl + metadata.json + plots comparativos) y escribe un HTML
nuevo en networks/language-comparison/output/combined_trial<X>_w<Y>.html.

Uso:
  python networks/language-comparison/make_combined_html.py
  python networks/language-comparison/make_combined_html.py --trialid 4 --wave 2
"""

import argparse
import base64
import json
import os
import pickle
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from core.language_groups import ALL_FAMILIES  # noqa: E402

_OUTDIR = os.path.join(_HERE, "output")

VIS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"


def _list_family_builds(trialid, wave):
    """Lista los directorios de build de la familia para trial/wave."""
    prefix = f"langcomp_trial{trialid}_w{wave}_"
    builds = []
    if not os.path.isdir(_OUTDIR):
        return builds
    for name in sorted(os.listdir(_OUTDIR)):
        if not name.startswith(prefix):
            continue
        build_dir = os.path.join(_OUTDIR, name)
        if not os.path.isdir(build_dir):
            continue
        if not os.path.exists(os.path.join(build_dir, "graph.pkl")):
            continue
        if not os.path.exists(os.path.join(build_dir, "metadata.json")):
            continue
        builds.append(build_dir)
    return builds


def _load_family(build_dir):
    """Carga graph.pkl + metadata.json de una familia."""
    with open(os.path.join(build_dir, "graph.pkl"), "rb") as f:
        G = pickle.load(f)
    with open(os.path.join(build_dir, "metadata.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    return G, meta


def _viridis_hex(values):
    """Mapea valores a hex viridis normalizado al rango [min, max]."""
    vals = np.array([v for v in values], dtype=float)
    if vals.size == 0:
        return {}
    vmin, vmax = float(vals.min()), float(vals.max())
    if vmax <= vmin:
        vmax = vmin + 1.0
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps["viridis"]
    return {i: mcolors.to_hex(cmap(norm(v))) for i, v in enumerate(vals)}


def _coolwarm_hex(values):
    """Mapea valores a hex coolwarm normalizado al rango [min, max]."""
    vals = np.array([v for v in values], dtype=float)
    if vals.size == 0:
        return {}
    vmin, vmax = float(vals.min()), float(vals.max())
    drange = vmax - vmin if vmax > vmin else 1.0
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps["coolwarm"]
    return {i: mcolors.to_hex(cmap(norm(v))) for i, v in enumerate(vals)}


def _build_family_data(G, meta):
    """
    Serializa nodos/aristas de la familia en el formato vis.js, con colores
    ya calculados en Python (viridis para mean_ps, coolwarm para mean_dps).
    """
    node_items = list(G.nodes(data=True))

    ps_vals = [d.get("mean_ps", 0.0) for _, d in node_items]
    node_colors = _viridis_hex(ps_vals)

    nodes = []
    for i, (n, d) in enumerate(node_items):
        word = d.get("word", str(n))
        nodes.append(
            {
                "id": n,
                "label": word,
                "title": (
                    f"{word} · wordnum {d.get('wordnum', 0)} · "
                    f"fix_count {d.get('fix_count', 0)} · "
                    f"mean_ps {d.get('mean_ps', 0.0):.2f} · "
                    f"mean_ps_z {d.get('mean_ps_z', 0.0):.3f}"
                ),
                "color": node_colors.get(i, "#888"),
                "value": max(1.0, float(d.get("fix_count", 1))),
            }
        )

    edge_items = list(G.edges(data=True))
    dps_vals = [d.get("mean_dps", 0.0) for _, _, d in edge_items]
    edge_colors = _coolwarm_hex(dps_vals)

    edges = []
    for i, (u, v, d) in enumerate(edge_items):
        word_u = G.nodes[u].get("word", u)
        word_v = G.nodes[v].get("word", v)
        edges.append(
            {
                "from": u,
                "to": v,
                "title": (
                    f"{word_u} → {word_v} · {d.get('type', 'forward')} · "
                    f"count {d.get('count', 0)} (sessions={d.get('n_sessions', 0)}) · "
                    f"mean_dps {d.get('mean_dps', 0.0):.2f}"
                ),
                "color": edge_colors.get(i, "#999"),
                "value": float(d.get("count", 1)),
            }
        )

    acc = meta.get("accuracy") or {}
    ps_vals_f = [d.get("mean_ps", 0.0) for _, d in node_items]
    fix_vals = [d.get("fix_count", 0) for _, d in node_items]
    dps_vals_f = [d.get("mean_dps", 0.0) for _, _, d in edge_items]
    count_vals = [d.get("count", 0) for _, _, d in edge_items]

    ranges = {
        "ps": [round(float(np.min(ps_vals_f)), 2), round(float(np.max(ps_vals_f)), 2)]
        if ps_vals_f
        else [0.0, 1.0],
        "fix": [int(np.min(fix_vals)), int(np.max(fix_vals))] if fix_vals else [0, 1],
        "dps": [round(float(np.min(dps_vals_f)), 2), round(float(np.max(dps_vals_f)), 2)]
        if dps_vals_f
        else [0.0, 1.0],
        "count": [int(np.min(count_vals)), int(np.max(count_vals))] if count_vals else [0, 1],
    }

    return {
        "id": meta.get("lang_group", "?"),
        "label": meta.get("lang_group", "?"),
        "languages": meta.get("languages", []),
        "accuracy_mean": acc.get("mean"),
        "accuracy_median": acc.get("median"),
        "accuracy_n": acc.get("n"),
        "n_participants": meta.get("n_participants"),
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "ranges": ranges,
        "nodes": nodes,
        "edges": edges,
    }


def _load_plots(trialid, wave):
    """Carga los plots comparativos como base64 si existen."""
    comp_dir = os.path.join(_OUTDIR, f"comparison_trial{trialid}_w{wave}", "plots")
    plots = {}
    for name in ("comparison_accuracy.png", "comparison_attention.png"):
        p = os.path.join(comp_dir, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                plots[name] = "data:image/png;base64," + base64.b64encode(
                    f.read()
                ).decode("ascii")
    return plots


def build_combined_html(trialid, wave, out_path):
    """Arma el HTML autocontenido con las redes de todas las familias."""
    builds = _list_family_builds(trialid, wave)
    if not builds:
        print(f"[!] No se encontraron builds para trial {trialid}, wave {wave} en {_OUTDIR}")
        return None

    families = []
    for b in builds:
        G, meta = _load_family(b)
        families.append(_build_family_data(G, meta))

    # Mantener el orden canónico de familias (igual que comparison_report.html),
    # no por accuracy.
    order = {fam: i for i, fam in enumerate(ALL_FAMILIES)}
    families.sort(key=lambda f: order.get(f["id"], 999))

    plots = _load_plots(trialid, wave)

    # --- tabla resumen ---
    table_rows = ""
    for f in families:
        acc = f["accuracy_mean"]
        acc_str = f"{acc:.3f}" if acc is not None else "n/a"
        med = f["accuracy_median"]
        med_str = f"{med:.3f}" if med is not None else "n/a"
        table_rows += (
            "<tr>"
            f"<td><b>{f['id']}</b></td>"
            f"<td>{', '.join(f['languages'])}</td>"
            f"<td>{acc_str}</td>"
            f"<td>{med_str}</td>"
            f"<td>{f['accuracy_n']}</td>"
            f"<td>{f['n_participants']}</td>"
            f"<td>{f['n_nodes']}</td>"
            f"<td>{f['n_edges']}</td>"
            "</tr>"
        )

    # --- pestañas ---
    tabs_html = ""
    for i, f in enumerate(families):
        selected = 'checked' if i == 0 else ''
        acc = f["accuracy_mean"]
        acc_str = f"{acc:.3f}" if acc is not None else "n/a"
        med = f["accuracy_median"]
        med_str = f"{med:.3f}" if med is not None else "n/a"
        tabs_html += (
            f'<input type="radio" name="tabs" id="tab-{i}" class="tab-radio" {selected}>'
            f'<label class="tab-label" for="tab-{i}">{f["id"]}</label>'
            f'<div class="tab-content" id="content-{i}">'
            f'<div class="fam-metrics">'
            f'<b>{f["id"]}</b> · accuracy <b>{acc_str}</b> (mediana {med_str}, '
            f'n={f["accuracy_n"]}) · participantes {f["n_participants"]} · '
            f'nodos {f["n_nodes"]} · aristas {f["n_edges"]}'
            f'</div>'
            f'</div>'
        )

    # --- datos de las familias embebidos como JSON ---
    family_json = json.dumps(families, ensure_ascii=True)

    # --- plots ---
    plots_html = ""
    if "comparison_accuracy.png" in plots:
        plots_html += (
            f'<div style="text-align:center; margin:20px 0;">'
            f'<img src="{plots["comparison_accuracy.png"]}" '
            f'style="max-width:100%;border:1px solid #ddd;border-radius:6px;"></div>'
        )
    if "comparison_attention.png" in plots:
        plots_html += (
            f'<div style="text-align:center; margin:20px 0;">'
            f'<img src="{plots["comparison_attention.png"]}" '
            f'style="max-width:100%;border:1px solid #ddd;border-radius:6px;"></div>'
        )

    css = """
    <style>
    body { font-family: -apple-system, 'Segoe UI', sans-serif; margin: 24px; }
    h1 { text-align: center; }
    table.summary { border-collapse: collapse; margin: 16px auto; width: 92%; }
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
    .fam-metrics { background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;
                   padding:12px 16px;margin:12px 0;font-family:sans-serif; }
    #net-wrap { width: 100%; position: relative; }
    #mynetwork { width: 100%; height: 760px; border: 1px solid #ccc; border-radius: 6px; }
    </style>
    """

    js = f"""
    <script>
    var FAMILIES = {family_json};

    var container = document.getElementById('mynetwork');
    var current = null;

    function updateLegend(fam) {{
        var r = fam.ranges || {{ps: [0, 1], fix: [0, 1], dps: [0, 1], count: [0, 1]}};
        var map = {{
            'lg-ps-min': r.ps[0],
            'lg-ps-max': r.ps[1],
            'lg-fix-min': r.fix[0],
            'lg-fix-max': r.fix[1],
            'lg-dps-min': r.dps[0],
            'lg-dps-max': r.dps[1],
            'lg-count-min': r.count[0],
            'lg-count-max': r.count[1]
        }};
        for (var k in map) {{
            var el = document.getElementById(k);
            if (el) el.textContent = map[k];
        }}
    }}

    function showFamily(idx) {{
        var fam = FAMILIES[idx];

        var data = {{
            nodes: new vis.DataSet(fam.nodes),
            edges: new vis.DataSet(fam.edges)
        }};
        var n_stab = Math.min(300, Math.max(100, fam.nodes.length * 2));
        var options = {{
            "nodes": {{"font": {{"size": 14}}}},
            "edges": {{
                "smooth": {{"enabled": true, "type": "dynamic"}},
                "arrows": {{"to": {{"enabled": true}}}}
            }},
            "physics": {{
                "enabled": true,
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {{"gravitationalConstant": -50, "springLength": 100}},
                "stabilization": {{"iterations": n_stab}}
            }},
            "interaction": {{
                "hover": true,
                "tooltipDelay": 50,
                "navigationButtons": true,
                "multiselect": true
            }}
        }};
        if (current !== null) {{
            current.setData(data);
            current.setOptions(options);
        }} else {{
            current = new vis.Network(container, data, options);
        }}
        current.stabilize(n_stab);
        updateLegend(fam);
    }}

    document.querySelectorAll('.tab-radio').forEach(function(radio, idx) {{
        radio.addEventListener('change', function() {{
            if (radio.checked) showFamily(idx);
        }});
    }});

    showFamily(0);
    </script>
    """

    legend_html = """
    <div id="legend" style="position: absolute;bottom: 10px;right: 10px;
        z-index: 9999;background: white;padding: 15px;border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);font-family: sans-serif;font-size: 13px;
        width: 240px;user-select: none;-webkit-user-select: none;-moz-user-select: none;">
        <h3 style="margin-top: 0; text-align: center; font-size: 15px;">Legend</h3>

        <div style="margin-bottom: 12px;">
            <strong>Node Color (Mean PS)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span id="lg-ps-min">0</span><span id="lg-ps-max">1</span>
            </div>
            <div style="height: 12px; background: linear-gradient(to right,
                #440154, #31688e, #35b779, #fde725); border-radius: 3px;
                border: 1px solid #ccc;"></div>
        </div>

        <div style="margin-bottom: 12px;">
            <strong>Node Size (fix_count)</strong>
            <div style="display: flex; align-items: center; justify-content: space-between;
                        height: 36px;">
                <span style="font-size: 11px;" id="lg-fix-min">0</span>
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%;
                                background: #555;"></div>
                    <div style="width: 16px; height: 16px; border-radius: 50%;
                                background: #555;"></div>
                    <div style="width: 28px; height: 28px; border-radius: 50%;
                                background: #555;"></div>
                </div>
                <span style="font-size: 11px;" id="lg-fix-max">1</span>
            </div>
        </div>

        <div style="margin-bottom: 12px;">
            <strong>Edge Color (Mean DPS)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span id="lg-dps-min">0</span><span id="lg-dps-max">1</span>
            </div>
            <div style="height: 12px; background: linear-gradient(to right,
                #3b4cc0, #dddddd, #b40426); border-radius: 3px;
                border: 1px solid #ccc;"></div>
        </div>

        <div>
            <strong>Edge Thickness (count)</strong>
            <div style="display: flex; flex-direction: column; align-items: center;
                        gap: 4px; padding: 6px 0;">
                <div style="height: 1px; width: 60px; background: #555;"></div>
                <div style="height: 3px; width: 60px; background: #555;"></div>
                <div style="height: 6px; width: 60px; background: #555;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span id="lg-count-min">0</span><span id="lg-count-max">1</span>
            </div>
        </div>
    </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Redes por Familia — Trial {trialid}, Wave {wave} (autocontenido)</title>
{css}
<script src="{VIS_CDN}"></script>
</head>
<body>
<h1>Redes de Atención por Familia Lingüística — Trial {trialid}, Wave {wave}</h1>
<table class="summary">
<thead>
<tr>
<th>Familia</th><th>Lenguas</th><th>accuracy (mean)</th><th>accuracy (mediana)</th>
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
<div id="net-wrap">
<div id="mynetwork"></div>
{legend_html}
</div>
</div>
{js}
</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML combinado guardado en: {out_path}")
    print(f"    Familias: {', '.join(f['id'] for f in families)}")
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="make_combined_html",
        description="Genera un único HTML autocontenido con las redes de todas las familias.",
    )
    parser.add_argument("--trialid", type=str, default="4", help="ID de texto [1-12].")
    parser.add_argument("--wave", type=str, default="1", choices=["1", "2"], help="Ola a cargar.")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Ruta de salida (default: output/combined_trial<X>_w<Y>.html).",
    )
    args = parser.parse_args(argv)

    out_path = args.out or os.path.join(
        _OUTDIR, f"combined_trial{args.trialid}_w{args.wave}.html"
    )
    return build_combined_html(args.trialid, args.wave, out_path)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
