"""
networks/scanpath/core/visualization.py

Red de scanpath por texto — estática (pyvis) y wrapper con iframes.

Layout FIJO de mapa de lectura (física apagada): x = posición de la palabra
dentro de su oración, y = fila por oración (orden de lectura). Compartido con
temporal_viz para que la animación use exactamente la misma disposición.

Canales visuales:
  - Color de nodo: viridis sobre mean_ps (gris hueco si sin ps válida).
  - Tamaño de nodo: fix_count.
  - Color de arista: por tipo (forward azul #3498db, regression rojo #e74c3c).
  - Grosor/opacity de arista: count (escala log).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import numpy as np

CMAP_V = matplotlib.colormaps["viridis"]

EDGE_COLORS = {"forward": "#3498db", "regression": "#e74c3c"}
X_STEP = 64.0
Y_STEP = 84.0


def _viridis_hex(t: float) -> str:
    r, g, b, _ = CMAP_V(float(np.clip(t, 0.0, 1.0)))
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def _node_positions(G) -> Tuple[Dict[str, Tuple[float, float]], int, int]:
    """
    Posiciones fijas por mapa de lectura: x = wordnum - primer wordnum de la
    oración, y = fila de la oración (rank de sentnum). Retorna (pos, filas,
    max_words_por_fila).
    """
    sent_min: Dict[int, int] = {}
    for _, d in G.nodes(data=True):
        s = int(d.get("sentnum", 1))
        w = int(d.get("wordnum", 0))
        if s not in sent_min or w < sent_min[s]:
            sent_min[s] = w
    rows = {s: i for i, s in enumerate(sorted(sent_min))}
    pos = {}
    max_dx = 0
    for n, d in G.nodes(data=True):
        s = int(d.get("sentnum", 1))
        dx = int(d.get("wordnum", 0)) - sent_min[s]
        max_dx = max(max_dx, dx)
        pos[n] = (40.0 + dx * X_STEP, 50.0 + rows[s] * Y_STEP)
    return pos, len(rows), max_dx


def build_pyvis_text(G, title: str, animated: bool = False):
    """
    Red pyvis de UN texto. animated=True deja todas las aristas hidden=True
    (el JS de temporal_viz las revela) y retorna (net, groups, times);
    si no, retorna (net, None, None).
    """
    from pyvis.network import Network

    pos, rows, _max_dx = _node_positions(G)
    net = Network(
        height=f"{min(1500, 160 + max(1, rows) * Y_STEP):.0f}px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        cdn_resources="remote",
        notebook=False,
    )
    net.heading = title
    net.toggle_physics(False)

    ps_vals = [d["mean_ps"] for _, d in G.nodes(data=True) if d.get("ps_obs", 0) > 0]
    ps_min = min(ps_vals) if ps_vals else 0.0
    ps_max = max(ps_vals) if ps_vals else 1.0
    if ps_max <= ps_min:
        ps_max = ps_min + 1.0
    fix_vals = [d.get("fix_count", 1) for _, d in G.nodes(data=True)]
    fix_max = max(fix_vals) or 1

    for n, d in G.nodes(data=True):
        present = d.get("ps_obs", 0) > 0
        if present:
            fill = _viridis_hex((d["mean_ps"] - ps_min) / (ps_max - ps_min))
            border = "#37474f"
        else:
            fill = "#f4f4f4"
            border = "#9e9e9e"
        size = 8 + 22 * (d.get("fix_count", 1) / fix_max)
        tip = (
            f"<b>{d.get('word', n)}</b><br>"
            f"palabra #{d.get('wordnum', 0)} · oración {d.get('sentnum', 1)}<br>"
            f"fijaciones: {d.get('fix_count', 0)}<br>"
            f"duración media: {d.get('mean_dur', 0.0):.0f} ms"
        )
        if present:
            tip += f"<br>ps media: {d['mean_ps']:.1f}"
        net.add_node(
            n,
            label=d.get("word", n),
            x=pos[n][0],
            y=pos[n][1],
            size=size,
            title=tip,
            physics=False,
            shape="box",
            margin=6,
            font={"size": 11, "face": "Arial", "color": "#212121"},
            color={"background": fill, "border": border,
                   "highlight": {"background": fill, "border": "#000000"}},
            borderWidth=1,
        )

    counts = [d.get("count", 1) for _, _, d in G.edges(data=True)]
    cmax = max(counts) if counts else 1
    events = G.graph.get("events", [])
    groups = [] if animated else None
    times = [round(float(e["t"]), 5) for e in events] if animated else None
    first_t: Dict[Tuple[str, str], dict] = {}
    for e in events:
        key = (e["u"], e["v"])
        if key not in first_t:
            first_t[key] = e

    for u, v, d in G.edges(data=True):
        c = d.get("count", 1)
        frac = math.log1p(c) / math.log1p(cmax) if cmax > 0 else 0.0
        col = EDGE_COLORS.get(d.get("type", "forward"), "#888888")
        width = 0.8 + 5.2 * frac
        opacity = 0.14 + 0.6 * frac
        tip = (
            f"{G.nodes[u].get('word', u)} → {G.nodes[v].get('word', v)}<br>"
            f"n = {c} · {d.get('type', 'forward')}"
        )
        net.add_edge(
            u, v,
            width=width,
            title=tip,
            color={"color": col, "opacity": opacity, "highlight": col},
            arrows={"to": {"enabled": True, "scaleFactor": 0.4}},
            smooth={"enabled": True, "type": "curvedCW", "roundness": 0.12},
            hidden=animated,
        )
        if animated and (u, v) in first_t:
            groups.append({
                "pairs": [[u, v]],
                "t": round(float(first_t[(u, v)]["t"]), 5),
                "c": col,
                "o": round(opacity, 3),
                "w": round(width, 2),
            })
    return net, groups, times


def write_text_network_static(G, out_path: Path, title: str) -> Path:
    """Red pyvis estática de UN texto + fit() inicial inyectado."""
    net, _groups, _times = build_pyvis_text(G, title, animated=False)
    net.write_html(str(out_path), open_browser=False, notebook=False)
    fit_js = """
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        if (typeof network !== 'undefined' && network.fit) {
            network.fit({ animation: false });
        }
    });
    </script>
    """
    html = out_path.read_text(encoding="utf-8")
    html = html.replace("</body>", f"{fit_js}\n</body>", 1)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def write_grid_wrapper(lang: str, quartile: str, kind: str, cells, out: Path) -> Path:
    """
    Wrapper con iframes. kind: 'network' | 'network_anim'.
    cells: [(tn, titulo), ...].
    """
    subdir = "network" if kind == "network" else "network_anim"
    frames = "\n".join(
        f'<div style="background:#fff;border:1px solid #ddd;border-radius:6px;overflow:hidden">'
        f'<iframe src="./{subdir}/{tn}.html" style="width:100%;height:760px;border:0"></iframe></div>'
        for tn, _ in cells
    )
    titles = "\n".join(
        f'<div style="text-align:center;font-weight:600;padding:4px">{t}</div>'
        for _, t in cells
    )
    heading = (
        "Red de scanpath por texto" if kind == "network"
        else "Red de scanpath por texto — ANIMADA"
    )
    note = (
        "Nodos = palabras en posición de lectura (x: dentro de la oración, y: oración). "
        "Color de nodo = ps media (viridis; gris = sin ps). Arista azul = avance, roja = regresión; "
        "grosor = n de transiciones pooled del cuartil."
        if kind == "network"
        else "Pulsa ▶ en cada panel: las aristas aparecen en su primera travesía según avanza la "
        "lectura (t = progreso 0-100% por sujeto, pooled). Destello = travesía; luego la arista "
        "se asienta a su estilo final (azul avance, roja regresión)."
    )
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>{heading} — {lang} · {quartile}</title></head>
<body style="font-family:Arial,Helvetica,sans-serif;margin:18px;background:#fafafa">
<h2 style="margin:0 0 2px">{heading} — {lang} · {quartile}</h2>
<p style="margin:4px 0 10px;color:#444;max-width:1200px">{note}</p>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;max-width:1700px">
  {titles}
  {frames}
</div>
</body></html>"""
    out.write_text(html, encoding="utf-8")
    return out
