"""
interactive_viz.py

Visualización interactiva de la red de regresiones vía pyvis (HTML standalone
con vis.js). Genera <build_dir>/network_interactive.html.

Mismo estilo que `language-comparison/core/interactive_viz.py`: título arriba,
panel de leyenda fijo a la derecha, menú de filtros de pyvis, atenuación de la
red al seleccionar un nodo y barra de carga oculta.

Añade además un panel fijo a la izquierda con el ranking de **destinos de
regresión** (in-degree del subgrafo de regresión), ordenable y enlazado con la
red: al hacer clic en una fila se centra y resalta ese nodo.

Canales visuales (cambian respecto de la red ΔPS porque cambian las variables):
  - Color de nodo:   viridis sobre `reg_in_rate` (regresiones que atrae).
  - Tamaño de nodo:  `fix_count`.
  - Color de arista: categórico por `type` (forward / regression-local /
                     regression-global).
  - Grosor de arista: `rate` (fracción de lectores que hacen la transición).
"""

import html as _html
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import numpy as np

from pyvis.network import Network

# Paleta categórica validada para daltonismo (ver skill dataviz).
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


def compute_return_ranking(G, top_n=20):
    """
    Ranking de destinos de regresión: las palabras que más re-lectura atraen.

    Para cada nodo calcula:
      reg_in_deg  — nº de palabras distintas desde las que llega una regresión
                    (in-degree restringido al subgrafo de regresión).
      reg_in_rate — regresiones recibidas por lector (atributo de nodo).
      in_deg      — in-degree total, incluyendo llegadas de avance.

    Se ordena por `reg_in_deg` porque el in-degree total está dominado por la
    lectura hacia adelante: toda palabra recibe llegadas de avance por el mero
    hecho de leerse en orden, así que no discrimina.
    """
    reg_in_deg = {n: 0 for n in G.nodes}
    reg_in_strength = {n: 0.0 for n in G.nodes}

    for _u, v, d in G.edges(data=True):
        if str(d.get("type", "")).startswith("regression"):
            reg_in_deg[v] += 1
            reg_in_strength[v] += float(d.get("rate", 0.0))

    in_deg = dict(G.in_degree())

    rows = []
    for n, d in G.nodes(data=True):
        rows.append(
            {
                "id": n,
                "word": d.get("word", str(n)),
                "wordnum": int(d.get("wordnum", 0)),
                "sentnum": int(d.get("sentnum", 1)),
                "reg_in_deg": reg_in_deg[n],
                "reg_in_strength": round(reg_in_strength[n], 3),
                "reg_in_rate": float(d.get("reg_in_rate", 0.0)),
                "reg_in": int(d.get("reg_in", 0)),
                "in_deg": in_deg.get(n, 0),
            }
        )

    rows.sort(key=lambda r: (-r["reg_in_deg"], -r["reg_in_rate"], r["wordnum"]))
    return rows[:top_n]


def _ranking_panel_html(ranking, total_nodes):
    """Panel lateral con el ranking de destinos de regresión."""
    if not ranking:
        return ""

    body = ""
    for i, r in enumerate(ranking, 1):
        word = _html.escape(str(r["word"]))
        body += (
            f'<tr class="rk-row" data-node="{_html.escape(json.dumps(r["id"]))}"'
            f' data-regdeg="{r["reg_in_deg"]}" data-rate="{r["reg_in_rate"]}"'
            f' data-indeg="{r["in_deg"]}" data-pos="{r["wordnum"]}" data-rank="{i}"'
            f' title="oración {r["sentnum"]} · {r["reg_in"]} regresiones recibidas">'
            f'<td class="rk-n">{i}</td>'
            f'<td class="rk-w">{word}<span class="rk-pos">{r["wordnum"]}</span></td>'
            f'<td class="rk-v">{r["reg_in_deg"]}</td>'
            f'<td class="rk-v rk-dim">{r["reg_in_rate"]:.2f}</td>'
            f'<td class="rk-v rk-dim">{r["in_deg"]}</td>'
            "</tr>"
        )

    return f"""
    <div id="rk-panel">
      <div class="rk-head">
        <h3>Destinos de regresión</h3>
        <button id="rk-toggle" type="button" aria-expanded="true"
                title="Contraer / expandir">−</button>
      </div>
      <p class="rk-sub">Top {len(ranking)} de {total_nodes} · clic en una fila
         para centrarla en la red</p>
      <div class="rk-scroll">
        <table id="rk-table">
          <thead>
            <tr>
              <th class="rk-n"></th>
              <th class="rk-w rk-sort" data-key="pos"
                  title="Ordenar por posición en el texto">palabra</th>
              <th class="rk-v rk-sort rk-active" data-key="regdeg"
                  title="Palabras distintas desde las que llega una regresión">reg&nbsp;in</th>
              <th class="rk-v rk-sort" data-key="rate"
                  title="Regresiones recibidas por lector">/lector</th>
              <th class="rk-v rk-sort" data-key="indeg"
                  title="In-degree total, incluye llegadas de avance">total</th>
            </tr>
          </thead>
          <tbody>{body}</tbody>
        </table>
      </div>
    </div>
    """


_RANKING_STYLE = """
<style>
#rk-panel {
  position: fixed; top: 50%; left: 20px; transform: translateY(-50%);
  z-index: 9999; background: #fff; border-radius: 8px; padding: 12px 14px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3); font-family: sans-serif;
  width: 268px; user-select: none; -webkit-user-select: none;
}
#rk-panel .rk-head { display: flex; align-items: center; gap: 8px; }
#rk-panel h3 { margin: 0; font-size: 14px; flex: 1; }
#rk-toggle {
  border: 1px solid #ccc; background: #f5f5f5; border-radius: 4px;
  width: 22px; height: 22px; line-height: 1; cursor: pointer;
  font-size: 14px; color: #333; flex: none;
}
#rk-toggle:hover { background: #e8e8e8; }
#rk-panel .rk-sub { margin: 6px 0 8px; font-size: 10.5px; color: #777; line-height: 1.35; }
#rk-panel.rk-collapsed .rk-sub,
#rk-panel.rk-collapsed .rk-scroll { display: none; }
.rk-scroll { max-height: 330px; overflow-y: auto; }
#rk-table { border-collapse: collapse; width: 100%; font-size: 11.5px; }
#rk-table th {
  position: sticky; top: 0; background: #fff; text-align: right;
  font-weight: 600; color: #555; padding: 3px 4px; font-size: 10px;
  border-bottom: 1px solid #ddd; text-transform: uppercase; letter-spacing: .03em;
}
#rk-table th.rk-sort { cursor: pointer; }
#rk-table th.rk-sort:hover { color: #000; text-decoration: underline; }
#rk-table th.rk-active { color: #2c3e50; text-decoration: underline; }
#rk-table td { padding: 2px 4px; border-bottom: 1px solid #f2f2f2; }
#rk-table td.rk-n { color: #aaa; text-align: right; width: 18px; font-variant-numeric: tabular-nums; }
#rk-table td.rk-w { text-align: left; font-weight: 600; color: #222; }
#rk-table td.rk-v { text-align: right; font-variant-numeric: tabular-nums; }
#rk-table td.rk-dim { color: #888; font-weight: 400; }
#rk-table .rk-pos { color: #bbb; font-weight: 400; margin-left: 5px; font-size: 10px; }
#rk-table tbody tr { cursor: pointer; }
#rk-table tbody tr:hover td { background: #eef4fb; }
#rk-table tbody tr.rk-selected td { background: #2c3e50; color: #fff; }
#rk-table tbody tr.rk-selected td.rk-dim,
#rk-table tbody tr.rk-selected td.rk-n,
#rk-table tbody tr.rk-selected .rk-pos { color: #cfd8e3; }
</style>
"""

_RANKING_SCRIPT = """
<script>
(function() {
  var panel = document.getElementById('rk-panel');
  if (!panel || typeof network === 'undefined') { return; }

  var tbody = panel.querySelector('#rk-table tbody');
  var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));

  function clearSelection() {
    rows.forEach(function(r) { r.classList.remove('rk-selected'); });
  }

  rows.forEach(function(row) {
    row.addEventListener('click', function() {
      var id = JSON.parse(row.getAttribute('data-node'));
      clearSelection();
      row.classList.add('rk-selected');
      network.selectNodes([id]);
      network.focus(id, { scale: 1.15, animation: { duration: 400 } });
      if (typeof window.rkHighlight === 'function') { window.rkHighlight([id]); }
    });
  });

  network.on('deselectNode', clearSelection);

  var sortKey = 'regdeg';
  panel.querySelectorAll('th.rk-sort').forEach(function(th) {
    th.addEventListener('click', function() {
      var key = th.getAttribute('data-key');
      sortKey = key;
      panel.querySelectorAll('th.rk-sort').forEach(function(o) {
        o.classList.toggle('rk-active', o === th);
      });
      var asc = (key === 'pos');
      rows.sort(function(a, b) {
        var av = parseFloat(a.getAttribute('data-' + key));
        var bv = parseFloat(b.getAttribute('data-' + key));
        if (av === bv) {
          return parseInt(a.getAttribute('data-rank')) -
                 parseInt(b.getAttribute('data-rank'));
        }
        return asc ? av - bv : bv - av;
      });
      rows.forEach(function(r, i) {
        r.querySelector('td.rk-n').textContent = i + 1;
        tbody.appendChild(r);
      });
    });
  });

  document.getElementById('rk-toggle').addEventListener('click', function() {
    var collapsed = panel.classList.toggle('rk-collapsed');
    this.textContent = collapsed ? '+' : '\\u2212';
    this.setAttribute('aria-expanded', String(!collapsed));
  });
})();
</script>
"""


def visualize_regression_network_interactive(G, build_dir, prefix, subtitle=""):
    """Renderiza la red en build_dir/network_interactive.html con pyvis."""
    os.makedirs(build_dir, exist_ok=True)
    out_path = os.path.join(build_dir, "network_interactive.html")

    reg_arr = np.array(
        [d.get("reg_in_rate", 0.0) for _, d in G.nodes(data=True)], dtype=float
    )
    if reg_arr.size:
        reg_min, reg_max = float(reg_arr.min()), float(reg_arr.max())
    else:
        reg_min, reg_max = 0.0, 1.0
    norm = mcolors.Normalize(
        vmin=reg_min, vmax=reg_max if reg_max > reg_min else reg_min + 1.0
    )
    cmap_v = matplotlib.colormaps["viridis"]
    reg_to_hex = {
        n: mcolors.to_hex(cmap_v(norm(d.get("reg_in_rate", 0.0))))
        for n, d in G.nodes(data=True)
    }

    fix_arr = np.array(
        [d.get("fix_count", 0) for _, d in G.nodes(data=True)], dtype=int
    )
    fix_min, fix_max = (int(fix_arr.min()), int(fix_arr.max())) if fix_arr.size else (0, 1)

    rate_arr = np.array(
        [d.get("rate", 0.0) for _, _, d in G.edges(data=True)], dtype=float
    )
    rate_min, rate_max = (
        (float(rate_arr.min()), float(rate_arr.max())) if rate_arr.size else (0.0, 1.0)
    )

    type_counts = {}
    for _, _, d in G.edges(data=True):
        t = d.get("type", "forward")
        type_counts[t] = type_counts.get(t, 0) + 1

    n_stab = min(300, max(100, G.number_of_nodes() * 2))

    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False,
        heading="",
        cdn_resources="remote",
        filter_menu=True,
    )
    net.prep_notebook()

    for n, d in G.nodes(data=True):
        word = d.get("word", str(n))
        title = (
            f"{word} · wordnum {d.get('wordnum', 0)} · "
            f"sent {d.get('sentnum', 1)} · "
            f"fix_count {d.get('fix_count', 0)} · "
            f"reg_in {d.get('reg_in', 0)} ({d.get('reg_in_rate', 0.0):.2f}/lector) · "
            f"reg_out {d.get('reg_out', 0)} · "
            f"refix {d.get('n_refix', 0)} ({d.get('refix_rate', 0.0):.2f}/lector)"
        )
        net.add_node(
            n,
            label=word,
            title=title,
            color=reg_to_hex[n],
            value=max(1.0, float(d.get("fix_count", 1))),
        )

    for u, v, d in G.edges(data=True):
        word_u = G.nodes[u].get("word", u)
        word_v = G.nodes[v].get("word", v)
        etype = d.get("type", "forward")
        title = (
            f"{word_u} → {word_v} · {etype} · "
            f"rate {d.get('rate', 0.0):.3f} "
            f"({d.get('n_sessions', 0)} lectores) · "
            f"count {d.get('count', 0)} · "
            f"amplitud {d.get('amplitude', 0.0)} palabras"
        )
        net.add_edge(
            u,
            v,
            title=title,
            value=float(d.get("rate", 0.01)),
            color=EDGE_COLORS.get(etype, "#888888"),
        )

    net.set_options(
        f"""
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
            "stabilization": {{"iterations": {n_stab}}}
          }},
          "interaction": {{
            "hover": true,
            "tooltipDelay": 50,
            "navigationButtons": true,
            "multiselect": true
          }}
        }}
        """
    )

    net.show(out_path)

    sub = f'<div style="text-align:center;color:#555;font-size:13px;margin-bottom:10px;">{subtitle}</div>' if subtitle else ""
    title_html = (
        f'<h1 style="font-family: sans-serif; text-align: center; '
        f'margin: 16px 0 8px;">Red de Regresiones — {prefix}</h1>\n{sub}'
    )

    legend_style = (
        "position: fixed;"
        "top: 50%;"
        "right: 20px;"
        "transform: translateY(-50%);"
        "z-index: 9999;"
        "background: white;"
        "padding: 15px;"
        "border-radius: 8px;"
        "box-shadow: 0 4px 6px rgba(0,0,0,0.3);"
        "font-family: sans-serif;"
        "font-size: 13px;"
        "width: 240px;"
        "user-select: none;"
        "-webkit-user-select: none;"
        "-moz-user-select: none;"
    )

    type_rows = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;margin:5px 0;">'
        f'<div style="width:22px;height:3px;background:{EDGE_COLORS[t]};'
        f'border-radius:2px;flex:none;"></div>'
        f'<span style="font-size:11.5px;">{EDGE_LABELS[t]}</span>'
        f'<span style="margin-left:auto;font-size:11px;color:#666;">'
        f'{type_counts.get(t, 0)}</span></div>'
        for t in ("forward", "regression-local", "regression-global")
    )

    legend_html = f"""
    <div style="{legend_style}">
        <h3 style="margin-top: 0; text-align: center; font-size: 15px;">Legend</h3>

        <div style="margin-bottom: 12px;">
            <strong>Edge Color (type)</strong>
            {type_rows}
        </div>

        <div style="margin-bottom: 12px;">
            <strong>Node Color (reg_in_rate)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span>{reg_min:.2f}</span><span>{reg_max:.2f}</span>
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
                <span style="font-size: 11px;">{fix_min}</span>
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%;
                                background: #555;"></div>
                    <div style="width: 16px; height: 16px; border-radius: 50%;
                                background: #555;"></div>
                    <div style="width: 28px; height: 28px; border-radius: 50%;
                                background: #555;"></div>
                </div>
                <span style="font-size: 11px;">{fix_max}</span>
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
                <span>{rate_min:.2f}</span><span>{rate_max:.2f}</span>
            </div>
            <div style="font-size:10.5px;color:#666;margin-top:3px;">
                Fracción de lectores que hacen la transición
            </div>
        </div>
    </div>
    """

    highlight_script = """
    <script>
    (function() {
        function setHighlight(selectedIds) {
            if (!selectedIds || selectedIds.length === 0) {
                var resetNodes = nodes.get().map(function(n) { n.opacity = 1.0; return n; });
                var resetEdges = edges.get().map(function(e) { e.opacity = 1.0; return e; });
                nodes.update(resetNodes);
                edges.update(resetEdges);
                return;
            }
            var connectedNodeIds = new Set();
            var connectedEdgeIds = new Set();
            selectedIds.forEach(function(id) {
                connectedNodeIds.add(id);
                network.getConnectedNodes(id).forEach(function(c) {
                    connectedNodeIds.add(c);
                });
                network.getConnectedEdges(id).forEach(function(e) {
                    connectedEdgeIds.add(e);
                });
            });
            var updatedNodes = nodes.get().map(function(n) {
                n.opacity = connectedNodeIds.has(n.id) ? 1.0 : 0.2;
                return n;
            });
            var updatedEdges = edges.get().map(function(e) {
                e.opacity = connectedEdgeIds.has(e.id) ? 1.0 : 0.1;
                return e;
            });
            nodes.update(updatedNodes);
            edges.update(updatedEdges);
        }
        network.on("selectNode", function(params) { setHighlight(params.nodes); });
        network.on("deselectNode", function(params) { setHighlight([]); });
        window.rkHighlight = setHighlight;
    })();
    </script>
    """

    ranking = compute_return_ranking(G)
    ranking_html = _ranking_panel_html(ranking, G.number_of_nodes())

    with open(out_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    css_override = (
        "<style>#loadingBar { display: none !important; }</style>" + _RANKING_STYLE
    )
    html_content = html_content.replace("<body>", f"<body>\n{css_override}", 1)
    html_content = html_content.replace("<body>", f"<body>\n{title_html}", 1)
    html_content = html_content.replace(
        "</body>",
        f"{legend_html}\n{ranking_html}\n{highlight_script}\n{_RANKING_SCRIPT}\n</body>",
        1,
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] Visualización interactiva (pyvis) guardada en: {out_path}")
    return out_path
