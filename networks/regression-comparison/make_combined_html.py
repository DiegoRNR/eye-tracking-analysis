"""
make_combined_html.py

Script experimental: genera UN ÚNICO HTML autocontenido con las redes de
regresión de todas las familias de un trial/wave, renderizadas con un solo
vis.Network que hace swap de datos entre pestañas.

Adaptado de networks/language-comparison/make_combined_html.py. Cambian las
variables visualizadas, porque cambian las que la red de regresiones produce:

  - Color de nodo:   viridis sobre `reg_in_rate` (regresiones recibidas por
                     lector). Amarillo = palabra a la que se vuelve.
  - Tamaño de nodo:  `fix_count`.
  - Color de arista: categórico por `type` (azul = avance, naranja = regresión
                     intra-oración, verde = regresión inter-oración).
  - Grosor de arista: `rate` (fracción de lectores que hacen la transición).

No modifica comparison.py ni los builds existentes. Solo lee los outputs ya
generados (graph.pkl + metadata.json + plots comparativos) y escribe un HTML
nuevo en networks/regression-comparison/output/combined_trial<X>_w<Y>.html.

Uso:
  python networks/regression-comparison/make_combined_html.py
  python networks/regression-comparison/make_combined_html.py --trialid 4 --wave 2
"""

import argparse
import base64
import html as _html
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

from core._langcomp import get_langcomp_core  # noqa: E402

_OUTDIR = os.path.join(_HERE, "output")

VIS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"

# Paleta categórica validada para daltonismo (misma que core/interactive_viz.py).
EDGE_COLORS = {
    "forward": "#2a78d6",
    "regression-local": "#eb6834",
    "regression-global": "#1baf7a",
}
EDGE_LABELS = {
    "forward": "Avance",
    "regression-local": "Regresión intra-oración",
    "regression-global": "Regresión inter-oración",
}
_EDGE_ORDER = ("forward", "regression-local", "regression-global")


def _list_family_builds(trialid, wave):
    """Lista los directorios de build de la familia para trial/wave."""
    prefix = f"regcomp_trial{trialid}_w{wave}_"
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


def _build_family_data(G, meta):
    """
    Serializa nodos/aristas de la familia en el formato vis.js.

    Color de nodo por reg_in_rate (viridis, ya calculado en Python), aristas
    con color categórico por `type`, grosor por `rate`.
    """
    node_items = list(G.nodes(data=True))

    reg_vals = [d.get("reg_in_rate", 0.0) for _, d in node_items]
    node_colors = _viridis_hex(reg_vals)

    nodes = []
    for i, (n, d) in enumerate(node_items):
        word = d.get("word", str(n))
        nodes.append(
            {
                "id": n,
                "label": word,
                "title": (
                    f"{word} · wordnum {d.get('wordnum', 0)} · "
                    f"sent {d.get('sentnum', 1)} · "
                    f"fix_count {d.get('fix_count', 0)} · "
                    f"reg_in {d.get('reg_in', 0)} ({d.get('reg_in_rate', 0.0):.2f}/lector) · "
                    f"reg_out {d.get('reg_out', 0)} · "
                    f"refix {d.get('n_refix', 0)} ({d.get('refix_rate', 0.0):.2f}/lector)"
                ),
                "color": node_colors.get(i, "#888"),
                "value": max(1.0, float(d.get("fix_count", 1))),
            }
        )

    edges = []
    for u, v, d in G.edges(data=True):
        word_u = G.nodes[u].get("word", u)
        word_v = G.nodes[v].get("word", v)
        etype = d.get("type", "forward")
        edges.append(
            {
                "from": u,
                "to": v,
                "title": (
                    f"{word_u} → {word_v} · {etype} · "
                    f"rate {d.get('rate', 0.0):.3f} "
                    f"({d.get('n_sessions', 0)} lectores) · "
                    f"count {d.get('count', 0)} · "
                    f"amplitud {d.get('amplitude', 0.0)} palabras"
                ),
                "color": EDGE_COLORS.get(etype, "#888888"),
                "value": float(d.get("rate", 0.01)),
            }
        )

    acc = meta.get("accuracy") or {}
    reg_vals_f = [d.get("reg_in_rate", 0.0) for _, d in node_items]
    fix_vals = [d.get("fix_count", 0) for _, d in node_items]
    rate_vals = [d.get("rate", 0.0) for _, _, d in G.edges(data=True)]

    ranges = {
        "reg": [round(float(np.min(reg_vals_f)), 2), round(float(np.max(reg_vals_f)), 2)]
        if reg_vals_f
        else [0.0, 1.0],
        "fix": [int(np.min(fix_vals)), int(np.max(fix_vals))] if fix_vals else [0, 1],
        "rate": [round(float(np.min(rate_vals)), 3), round(float(np.max(rate_vals)), 3)]
        if rate_vals
        else [0.0, 1.0],
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
        "regression_share": meta.get("regression_share"),
        "refix_share": meta.get("refix_share"),
        "reciprocity": meta.get("reciprocity"),
        "ranges": ranges,
        "nodes": nodes,
        "edges": edges,
    }


def _compute_return_ranking(family):
    """
    Ranking de destinos de regresión (palabras que más re-lectura atraen),
    igual que core/interactive_viz.py compute_return_ranking().

    Retorna lista de dicts (top 20) para insertar en el panel.
    """
    reg_in_deg = {}
    reg_in_strength = {}
    for e in family["edges"]:
        if str(e.get("type", "")).startswith("regression"):
            v = e["to"]
            reg_in_deg[v] = reg_in_deg.get(v, 0) + 1
            reg_in_strength[v] = reg_in_strength.get(v, 0.0) + float(e.get("value", 0.0))

    in_deg = {}
    for e in family["edges"]:
        in_deg[e["to"]] = in_deg.get(e["to"], 0) + 1

    node_map = {}
    for nd in family["nodes"]:
        node_map[nd["id"]] = nd

    rows = []
    for nid, nd in node_map.items():
        rows.append(
            {
                "id": nid,
                "word": nd["label"],
                "reg_in_deg": reg_in_deg.get(nid, 0),
                "reg_in_strength": round(reg_in_strength.get(nid, 0.0), 3),
                "in_deg": in_deg.get(nid, 0),
            }
        )
    rows.sort(key=lambda r: (-r["reg_in_deg"], -r["reg_in_strength"]))
    return rows[:20]


def _load_plots(trialid, wave):
    """Carga los plots comparativos como base64 si existen."""
    comp_dir = os.path.join(_OUTDIR, f"comparison_trial{trialid}_w{wave}", "plots")
    plots = {}
    for name in (
        "comparison_accuracy.png",
        "comparison_saccade_types.png",
        "comparison_regression_profile.png",
    ):
        p = os.path.join(comp_dir, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                plots[name] = "data:image/png;base64," + base64.b64encode(
                    f.read()
                ).decode("ascii")
    return plots


def build_combined_html(trialid, wave, out_path):
    """Arma el HTML autocontenido con las redes de regresión de todas las familias."""
    builds = _list_family_builds(trialid, wave)
    if not builds:
        print(f"[!] No se encontraron builds para trial {trialid}, wave {wave} en {_OUTDIR}")
        return None

    families = []
    for b in builds:
        G, meta = _load_family(b)
        families.append(_build_family_data(G, meta))

    # Orden canónico de familias (igual que comparison_report.html), no por accuracy.
    lc = get_langcomp_core()
    order = {fam: i for i, fam in enumerate(lc.ALL_FAMILIES)}
    families.sort(key=lambda f: order.get(f["id"], 999))

    plots = _load_plots(trialid, wave)

    # --- tabla resumen ---
    def _fmt(v, pct=False, d=3):
        if v is None:
            return "n/a"
        if pct:
            return f"{100 * v:.1f}%"
        return f"{v:.{d}f}"

    table_rows = ""
    for f in families:
        table_rows += (
            "<tr>"
            f"<td><b>{f['id']}</b></td>"
            f"<td>{', '.join(f['languages'])}</td>"
            f"<td>{_fmt(f['accuracy_mean'])}</td>"
            f"<td>{f['accuracy_n']}</td>"
            f"<td>{f['n_participants']}</td>"
            f"<td>{f['n_nodes']}</td>"
            f"<td>{f['n_edges']}</td>"
            f"<td><b>{_fmt(f['regression_share'], pct=True)}</b></td>"
            f"<td><b>{_fmt(f['refix_share'], pct=True)}</b></td>"
            f"<td><b>{_fmt(f['reciprocity'])}</b></td>"
            "</tr>"
        )

    # --- pestañas ---
    tabs_html = ""
    for i, f in enumerate(families):
        selected = 'checked' if i == 0 else ''
        tabs_html += (
            f'<input type="radio" name="tabs" id="tab-{i}" class="tab-radio" {selected}>'
            f'<label class="tab-label" for="tab-{i}">{f["id"]}</label>'
            f'<div class="tab-content" id="content-{i}">'
            f'<div class="fam-metrics">'
            f'<b>{f["id"]}</b> · accuracy <b>{_fmt(f["accuracy_mean"])}</b> '
            f'(n={f["accuracy_n"]}) · participantes {f["n_participants"]} · '
            f'nodos {f["n_nodes"]} · aristas {f["n_edges"]} · '
            f'% regresión <b>{_fmt(f["regression_share"], pct=True)}</b> · '
            f'% refijación <b>{_fmt(f["refix_share"], pct=True)}</b> · '
            f'reciprocidad <b>{_fmt(f["reciprocity"])}</b>'
            f'</div>'
            f'</div>'
        )

    # --- ranking de destinos de regresión (por familia) ---
    rankings = [_compute_return_ranking(f) for f in families]

    # --- datos de las familias embebidos como JSON ---
    family_json = json.dumps(families, ensure_ascii=True)
    ranking_json = json.dumps(rankings, ensure_ascii=True)

    # --- plots ---
    plots_html = ""
    for name in (
        "comparison_accuracy.png",
        "comparison_saccade_types.png",
        "comparison_regression_profile.png",
    ):
        if name in plots:
            plots_html += (
                f'<div style="text-align:center; margin:20px 0;">'
                f'<img src="{plots[name]}" '
                f'style="max-width:100%;border:1px solid #ddd;border-radius:6px;"></div>'
            )

    css = """
    <style>
    body { font-family: -apple-system, 'Segoe UI', sans-serif; margin: 24px; }
    h1 { text-align: center; }
    table.summary { border-collapse: collapse; margin: 16px auto; width: 96%; font-size: 13px; }
    table.summary th, table.summary td { border: 1px solid #ddd; padding: 6px 9px; text-align: center; }
    table.summary th { background: #2c3e50; color: #fff; font-weight: 600; }
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
    #rk-panel {
      position: absolute; top: 12px; left: 12px; z-index: 9998; background: #fff;
      border-radius: 8px; padding: 10px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
      font-family: sans-serif; width: 250px; user-select: none; -webkit-user-select: none;
    }
    #rk-panel .rk-head { display: flex; align-items: center; gap: 8px; }
    #rk-panel h3 { margin: 0; font-size: 13px; flex: 1; }
    #rk-toggle {
      border: 1px solid #ccc; background: #f5f5f5; border-radius: 4px;
      width: 20px; height: 20px; line-height: 1; cursor: pointer;
      font-size: 13px; color: #333; flex: none;
    }
    #rk-panel .rk-sub { margin: 4px 0 6px; font-size: 10px; color: #777; line-height: 1.3; }
    #rk-panel.rk-collapsed .rk-sub,
    #rk-panel.rk-collapsed .rk-scroll { display: none; }
    .rk-scroll { max-height: 300px; overflow-y: auto; }
    #rk-table { border-collapse: collapse; width: 100%; font-size: 11px; }
    #rk-table th {
      position: sticky; top: 0; background: #fff; text-align: right;
      font-weight: 600; color: #555; padding: 2px 4px; font-size: 9.5px;
      border-bottom: 1px solid #ddd; text-transform: uppercase; letter-spacing: .03em;
    }
    #rk-table td { padding: 2px 4px; border-bottom: 1px solid #f2f2f2; }
    #rk-table td.rk-n { color: #aaa; text-align: right; width: 16px; font-variant-numeric: tabular-nums; }
    #rk-table td.rk-w { text-align: left; font-weight: 600; color: #222; }
    #rk-table td.rk-v { text-align: right; font-variant-numeric: tabular-nums; }
    #rk-table td.rk-dim { color: #888; font-weight: 400; }
    #rk-table .rk-pos { color: #bbb; font-weight: 400; margin-left: 5px; font-size: 9.5px; }
    #rk-table tbody tr { cursor: pointer; }
    #rk-table tbody tr:hover td { background: #eef4fb; }
    #rk-table tbody tr.rk-selected td { background: #2c3e50; color: #fff; }
    </style>
    """

    # --- panel de ranking (se rellena por JS) ---
    ranking_html = """
    <div id="rk-panel">
      <div class="rk-head">
        <h3>Destinos de regresión</h3>
        <button id="rk-toggle" type="button" aria-expanded="true"
                title="Contraer / expandir">−</button>
      </div>
      <p class="rk-sub">Top 20 · clic en una fila para centrarla en la red</p>
      <div class="rk-scroll">
        <table id="rk-table">
          <thead>
            <tr>
              <th class="rk-n"></th>
              <th class="rk-w">palabra</th>
              <th class="rk-v">reg&nbsp;in</th>
              <th class="rk-v rk-dim">/lector</th>
              <th class="rk-v rk-dim">total</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
    """

    js = f"""
    <script>
    var FAMILIES = {family_json};
    var RANKINGS = {ranking_json};

    var container = document.getElementById('mynetwork');
    var current = null;

    function updateLegend(fam) {{
        var r = fam.ranges || {{reg: [0, 1], fix: [0, 1], rate: [0, 1]}};
        var map = {{
            'lg-reg-min': r.reg[0],
            'lg-reg-max': r.reg[1],
            'lg-fix-min': r.fix[0],
            'lg-fix-max': r.fix[1],
            'lg-rate-min': r.rate[0],
            'lg-rate-max': r.rate[1]
        }};
        for (var k in map) {{
            var el = document.getElementById(k);
            if (el) el.textContent = map[k];
        }}
    }}

    function fillRanking(idx) {{
        var rows = RANKINGS[idx] || [];
        var tbody = document.querySelector('#rk-table tbody');
        tbody.innerHTML = '';
        rows.forEach(function(r, i) {{
            var tr = document.createElement('tr');
            tr.setAttribute('data-node', JSON.stringify(r.id));
            tr.innerHTML =
                '<td class="rk-n">' + (i + 1) + '</td>' +
                '<td class="rk-w">' + r.word + '<span class="rk-pos"></span></td>' +
                '<td class="rk-v">' + r.reg_in_deg + '</td>' +
                '<td class="rk-v rk-dim">' + r.reg_in_strength.toFixed(2) + '</td>' +
                '<td class="rk-v rk-dim">' + r.in_deg + '</td>';
            tr.addEventListener('click', function() {{
                document.querySelectorAll('#rk-table tbody tr').forEach(
                    function(o) {{ o.classList.remove('rk-selected'); }});
                tr.classList.add('rk-selected');
                var id = JSON.parse(tr.getAttribute('data-node'));
                current.selectNodes([id]);
                current.focus(id, {{scale: 1.15, animation: {{duration: 400}}}});
                if (typeof window.rkHighlight === 'function') {{ window.rkHighlight([id]); }}
            }});
            tbody.appendChild(tr);
        }});
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
                "arrows": {{"to": {{"enabled": true, "scaleFactor": 0.6}}}}
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
        fillRanking(idx);
    }}

    document.querySelectorAll('.tab-radio').forEach(function(radio, idx) {{
        radio.addEventListener('change', function() {{
            if (radio.checked) showFamily(idx);
        }});
    }});

    document.getElementById('rk-toggle').addEventListener('click', function() {{
        var panel = document.getElementById('rk-panel');
        var collapsed = panel.classList.toggle('rk-collapsed');
        this.textContent = collapsed ? '+' : '\\u2212';
        this.setAttribute('aria-expanded', String(!collapsed));
    }});

    window.rkHighlight = function(selectedIds) {{
        if (!selectedIds || selectedIds.length === 0) {{
            var rn = nodes.get().map(function(n) {{ n.opacity = 1.0; return n; }});
            var re = edges.get().map(function(e) {{ e.opacity = 1.0; return e; }});
            nodes.update(rn);
            edges.update(re);
            return;
        }}
        var cn = new Set();
        var ce = new Set();
        selectedIds.forEach(function(id) {{
            cn.add(id);
            network.getConnectedNodes(id).forEach(function(c) {{ cn.add(c); }});
            network.getConnectedEdges(id).forEach(function(e) {{ ce.add(e); }});
        }});
        nodes.update(nodes.get().map(function(n) {{
            n.opacity = cn.has(n.id) ? 1.0 : 0.2; return n;
        }}));
        edges.update(edges.get().map(function(e) {{
            e.opacity = ce.has(e.id) ? 1.0 : 0.1; return e;
        }}));
    }};

    network.on = function() {{}};
    showFamily(0);
    </script>
    """

    type_rows = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
        f'<div style="width:22px;height:3px;background:{EDGE_COLORS[t]};'
        f'border-radius:2px;flex:none;"></div>'
        f'<span style="font-size:11.5px;">{EDGE_LABELS[t]}</span></div>'
        for t in _EDGE_ORDER
    )

    legend_html = """
    <div id="legend" style="position: absolute;bottom: 10px;right: 10px;
        z-index: 9999;background: white;padding: 15px;border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);font-family: sans-serif;font-size: 13px;
        width: 240px;user-select: none;-webkit-user-select: none;-moz-user-select: none;">
        <h3 style="margin-top: 0; text-align: center; font-size: 15px;">Legend</h3>

        <div style="margin-bottom: 12px;">
            <strong>Edge Color (type)</strong>
            {type_rows}
        </div>

        <div style="margin-bottom: 12px;">
            <strong>Node Color (reg_in_rate)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span id="lg-reg-min">0</span><span id="lg-reg-max">1</span>
            </div>
            <div style="height: 12px; background: linear-gradient(to right,
                #440154, #31688e, #35b779, #fde725); border-radius: 3px;
                border: 1px solid #ccc;"></div>
            <div style="font-size:10.5px;color:#666;margin-top:3px;">
                Regresiones recibidas por lector
            </div>
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

        <div>
            <strong>Edge Thickness (rate)</strong>
            <div style="display: flex; flex-direction: column; align-items: center;
                        gap: 4px; padding: 6px 0;">
                <div style="height: 1px; width: 60px; background: #555;"></div>
                <div style="height: 3px; width: 60px; background: #555;"></div>
                <div style="height: 6px; width: 60px; background: #555;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span id="lg-rate-min">0</span><span id="lg-rate-max">1</span>
            </div>
            <div style="font-size:10.5px;color:#666;margin-top:3px;">
                Fracción de lectores que hacen la transición
            </div>
        </div>
    </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Redes de Regresión por Familia — Trial {trialid}, Wave {wave} (autocontenido)</title>
{css}
<script src="{VIS_CDN}"></script>
</head>
<body>
<h1>Redes de Regresión por Familia Lingüística — Trial {trialid}, Wave {wave}</h1>
<table class="summary">
<thead>
<tr>
<th>Familia</th><th>Lenguas</th><th>accuracy</th><th>n acc.</th><th>lectores</th>
<th>nodos</th><th>aristas</th><th>% regresión</th><th>% refijación</th><th>reciprocidad</th>
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
{ranking_html}
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
        description="Genera un único HTML autocontenido con las redes de regresión de todas las familias.",
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
