"""
interactive_viz.py

Visualización interactiva de la red vía pyvis (HTML standalone con vis.js).

Genera <build_dir>/network_interactive.html.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import numpy as np

from pyvis.network import Network


def visualize_group_network_interactive(G, build_dir, prefix):
    """
    Renderiza la red en build_dir/network_interactive.html con pyvis.

    Canales visuales:
      - Color de nodo:  viridis sobre `mean_ps`.
      - Tamaño de nodo: proporcional a `fix_count`.
      - Color de arista: coolwarm sobre `mean_dps`.
      - Grosor de arista: proporcional a `count`.
    """
    os.makedirs(build_dir, exist_ok=True)
    out_path = os.path.join(build_dir, "network_interactive.html")

    ps_arr = np.array(
        [d.get("mean_ps", 0.0) for _, d in G.nodes(data=True)], dtype=float
    )
    if ps_arr.size:
        ps_min, ps_max = float(ps_arr.min()), float(ps_arr.max())
    else:
        ps_min, ps_max = 0.0, 1.0
    norm = mcolors.Normalize(
        vmin=ps_min, vmax=ps_max if ps_max > ps_min else ps_min + 1.0
    )
    cmap_v = matplotlib.colormaps["viridis"]
    ps_to_hex = {
        n: mcolors.to_hex(cmap_v(norm(d.get("mean_ps", 0.0))))
        for n, d in G.nodes(data=True)
    }

    fix_arr = np.array(
        [d.get("fix_count", 0) for _, d in G.nodes(data=True)], dtype=int
    )
    if fix_arr.size:
        fix_min, fix_max = int(fix_arr.min()), int(fix_arr.max())
    else:
        fix_min, fix_max = 0, 1

    dps_arr = np.array(
        [d.get("mean_dps", 0.0) for _, _, d in G.edges(data=True)], dtype=float
    )
    if dps_arr.size:
        dmin, dmax = float(dps_arr.min()), float(dps_arr.max())
        drange = dmax - dmin if dmax > dmin else 1.0
    else:
        dmin, dmax, drange = 0.0, 0.0, 1.0
    coolwarm = matplotlib.colormaps["coolwarm"]

    count_arr = np.array(
        [d.get("count", 0) for _, _, d in G.edges(data=True)], dtype=int
    )
    if count_arr.size:
        count_min, count_max = int(count_arr.min()), int(count_arr.max())
    else:
        count_min, count_max = 0, 1

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

    tooltip_css = (
        "background:#ffffff;"
        "border:1px solid #d0d0d0;"
        "border-radius:6px;"
        "padding:8px 12px;"
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
        "font-size:13px;"
        "color:#2c3e50;"
        "white-space:nowrap;"
        "box-shadow:0 2px 4px rgba(0,0,0,0.1);"
    )

    for n, d in G.nodes(data=True):
        word = d.get("word", str(n))
        title = (
            f'<div style="{tooltip_css}">'
            f'<b>{word}</b> · wordnum {d.get("wordnum", 0)} · '
            f'fix_count {d.get("fix_count", 0)} · '
            f'mean_ps {d.get("mean_ps", 0.0):.2f} · '
            f'mean_ps_z {d.get("mean_ps_z", 0.0):.3f}'
            f'</div>'
        )
        net.add_node(
            n,
            label=word,
            title=title,
            color=ps_to_hex[n],
            value=max(1.0, float(d.get("fix_count", 1))),
        )

    for u, v, d in G.edges(data=True):
        word_u = G.nodes[u].get("word", u)
        word_v = G.nodes[v].get("word", v)
        title = (
            f'<div style="{tooltip_css}">'
            f'<b>{word_u} → {word_v}</b> · {d.get("type", "forward")} · '
            f'count {d.get("count", 0)} (sessions={d.get("n_sessions", 0)}) · '
            f'mean_dps {d.get("mean_dps", 0.0):.2f}'
            f'</div>'
        )
        t = (d.get("mean_dps", 0.0) - dmin) / drange
        net.add_edge(
            u,
            v,
            title=title,
            value=d.get("count", 1),
            color=mcolors.to_hex(coolwarm(t)),
        )

    net.set_options(
        f"""
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

    title_html = (
        f'<h1 style="font-family: sans-serif; text-align: center; '
        f'margin: 16px 0 8px;">Red de Carga Cognitiva — {prefix}</h1>'
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
    legend_html = f"""
    <div style="{legend_style}">
        <h3 style="margin-top: 0; text-align: center; font-size: 15px;">Legend</h3>

        <div style="margin-bottom: 12px;">
            <strong>Node Color (Mean PS)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span>{ps_min:.2f}</span><span>{ps_max:.2f}</span>
            </div>
            <div style="height: 12px; background: linear-gradient(to right,
                #440154, #31688e, #35b779, #fde725); border-radius: 3px;
                border: 1px solid #ccc;"></div>
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

        <div style="margin-bottom: 12px;">
            <strong>Edge Color (Mean DPS)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span>{dmin:.2f}</span><span>{dmax:.2f}</span>
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
                <span>{count_min}</span><span>{count_max}</span>
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
    })();
    </script>
    """

    with open(out_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    css_override = "<style>#loadingBar { display: none !important; }</style>"
    html_content = html_content.replace("<body>", f"<body>\n{css_override}", 1)
    html_content = html_content.replace("<body>", f"<body>\n{title_html}", 1)
    html_content = html_content.replace(
        "</body>", f"{legend_html}\n{highlight_script}\n</body>", 1
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] Visualización interactiva (pyvis) guardada en: {out_path}")
    return out_path
