"""
interactive_viz.py

Visualización interactiva de la red vía pyvis (HTML standalone con vis.js).

Genera <build_dir>/network_interactive.html — primera clase al lado de
nodes.csv / network.graphml / metadata.json, no en plots/ (que se reserva
para los PNGs estáticos de matplotlib).
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import numpy as np

from pyvis.network import Network


def visualize_network_interactive(G, build_dir, prefix):
    """
    Renderiza la red en plots/network_interactive.html con pyvis.

    - Color de nodo: viridis sobre `mean_ps`.
    - Tamaño de nodo: proporcional a `fix_count`.
    - Color de arista: coolwarm sobre `mean_dps`.
    - Grosor de arista: proporcional a `count`.
    - Tooltip HTML por nodo: word, wordnum, sentnum, fix_count, mean_ps, mean_ps_z, community.
    - Tooltip HTML por arista: type, count, n_sessions, mean_dps.
    - Layout forceAtlas2Based con botones de navegación y physics toggle.
    """
    os.makedirs(build_dir, exist_ok=True)
    out_path = os.path.join(build_dir, "network_interactive.html")

    ps_arr = np.array(
        [d.get("mean_ps", 0.0) for _, d in G.nodes(data=True)], dtype=float
    )
    ps_min = float(ps_arr.min())
    ps_max = float(ps_arr.max())
    norm = mcolors.Normalize(
        vmin=ps_min, vmax=ps_max if ps_max > ps_min else ps_min + 1.0
    )
    cmap_v = matplotlib.colormaps["viridis"]
    ps_to_hex = {
        n: mcolors.to_hex(cmap_v(norm(d.get("mean_ps", 0.0))))
        for n, d in G.nodes(data=True)
    }

    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False,
        heading=f"Red de Carga Cognitiva — {prefix}",
        cdn_resources="remote",
    )
    # Workaround for pyvis 0.3.2: prep_notebook loads the template; despite the
    # name, it's the right call for HTML output too. The constructor only
    # calls it when notebook=True, leaving self.template=None otherwise.
    net.prep_notebook()

    for n, d in G.nodes(data=True):
        word = d.get("word", str(n))
        title = (
            f"<b>{word}</b><br>"
            f"wordnum={d.get('wordnum', 0)}, sentnum={d.get('sentnum', 1)}<br>"
            f"fix_count={d.get('fix_count', 0)}<br>"
            f"mean_ps={d.get('mean_ps', 0.0):.2f}<br>"
            f"mean_ps_z={d.get('mean_ps_z', 0.0):.3f}<br>"
            f"community={d.get('community_label', 'n/a')}"
        )
        net.add_node(
            n,
            label=word,
            title=title,
            color=ps_to_hex[n],
            value=max(1.0, float(d.get("fix_count", 1))),
        )

    dps_arr = np.array(
        [d.get("mean_dps", 0.0) for _, _, d in G.edges(data=True)], dtype=float
    )
    if dps_arr.size:
        dmin = float(dps_arr.min())
        dmax = float(dps_arr.max())
        drange = dmax - dmin if dmax > dmin else 1.0
    else:
        dmin, dmax, drange = 0.0, 0.0, 1.0
    coolwarm = matplotlib.colormaps["coolwarm"]
    for u, v, d in G.edges(data=True):
        title = (
            f"{u} → {v}<br>"
            f"type={d.get('type', 'forward')}<br>"
            f"count={d.get('count', 0)} (sessions={d.get('n_sessions', 0)})<br>"
            f"mean_dps={d.get('mean_dps', 0.0):.2f}"
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
        """
        var options = {
          "nodes": {"font": {"size": 14}},
          "edges": {
            "smooth": {"enabled": true, "type": "dynamic"},
            "arrows": {"to": {"enabled": true}}
          },
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {"gravitationalConstant": -50, "springLength": 100},
            "stabilization": {"iterations": 200}
          },
          "interaction": {"hover": true, "tooltipDelay": 100, "navigationButtons": true}
        }
        """
    )

    net.show(out_path)
    print(f"[OK] Visualización interactiva (pyvis) guardada en: {out_path}")
    return out_path
