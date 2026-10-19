"""
networks/word-type-transitions/core/temporal_viz.py

Red de transiciones entre clases ANIMADA en el tiempo (pyvis + JS inyectado).

Genera, por lengua y modo:
- output/<lang>/<mode>/figures/network_anim/<cond>.html — red pyvis de UNA
  condición con barra de reproducción: las aristas aparecen en orden de
  lectura (t = progreso 0-1 de la fijación destino dentro de su lectura,
  ver network_builder.condition_events).
- output/<lang>/<mode>/figures/network_anim.html — wrapper 2×2 con iframes,
  espejo del network.html estático (que NO se toca).

Mecánica (reveal-once):
- Cada arista (o satélite de self-loop) aparece en su PRIMERA travesía y
  permanece. Al aparecer, destella con el Δdur del evento (coolwarm
  simétrico en 0: rojo = fijación destino más larga) y luego se asienta al
  estilo estático (paleta de la clase origen, opacity por P(v|u)).
- Layout circular FIJO con física apagada (igual que el estático): las
  aristas nacen hidden=True y el JS las revela.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .label_map import FUSED_ORDER
from .network_builder import condition_events
from .paths import CONDITION_LANGS, MODES, figures_dir, mode_dir
from .persistence import load_condition_summary
from .visualization import (
    CELLS,
    LANG_NAMES,
    NODE_PALETTE,
    _load_counts,
    _load_matrix,
    _load_node_attrs,
    _node_xy,
    _viridis_hex,
)

CSS_OVERRIDES = """
<style>
    #loadingBar { display: none !important; }
    .vis-tooltip { display: none !important; }
    #anim-bar {
        position: fixed;
        bottom: 16px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 10000;
        background: rgba(255, 255, 255, 0.95);
        padding: 10px 16px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        font-family: Arial, Helvetica, sans-serif;
        font-size: 12px;
        color: #333;
        display: flex;
        align-items: center;
        gap: 12px;
        user-select: none;
        -webkit-user-select: none;
        max-width: calc(100% - 32px);
    }
    #anim-bar button {
        background: #2c3e50;
        color: white;
        border: none;
        padding: 8px 14px;
        border-radius: 18px;
        cursor: pointer;
        font-weight: 600;
        font-size: 12px;
        font-family: inherit;
        white-space: nowrap;
    }
    #anim-bar button:hover { background: #1a252f; }
    #anim-slider { width: 220px; accent-color: #2c3e50; cursor: pointer; }
    #anim-progress { min-width: 200px; text-align: center; font-variant-numeric: tabular-nums; }
    #anim-speed {
        font-family: inherit; font-size: 11px; padding: 5px 6px;
        border-radius: 4px; border: 1px solid #ccc; background: #fff; cursor: pointer;
    }
    @media (max-width: 900px) {
        #anim-slider { width: 120px; }
        #anim-progress { min-width: 120px; font-size: 10px; }
    }
</style>
"""

BAR_HTML = """
<div id="anim-bar">
    <button id="anim-play">&#9654; Reproducir</button>
    <input type="range" id="anim-slider" min="0" max="100" value="0" step="0.25">
    <span id="anim-progress">0% &middot; 0 transiciones</span>
    <select id="anim-speed">
        <option value="0.5">0.5&times;</option>
        <option value="1" selected>1&times;</option>
        <option value="2">2&times;</option>
        <option value="5">5&times;</option>
    </select>
    <button id="anim-reset">&#9198; Reiniciar</button>
</div>
"""


def _cond(session: str, lang: str, quartile: str) -> str:
    return f"{session}-{lang}-{quartile}"


def _first_traversals(events: List[dict]) -> Dict[Tuple[str, str], dict]:
    """Primera travesía por par de clases (events viene ordenado por t)."""
    first: Dict[Tuple[str, str], dict] = {}
    for e in events:
        key = (e["u"], e["v"])
        if key not in first:
            first[key] = e
    return first


def _cell_title(session: str, q: str, lang: str, mode: str, cs) -> str:
    cid = _cond(session, lang, q)
    n = None
    if len(cs):
        row = cs[(cs["condition"] == cid) & (cs["mode"] == mode)]
        if len(row):
            n = int(row["n_subjects"].iloc[0])
    return (
        f"{'Nativo (L1)' if session == 'L1' else 'Inglés (L2)'} · "
        f"{'peor' if q == 'Q1' else 'mejor'}" + (f" (n={n})" if n else "")
    )


def _build_anim_condition(
    session: str,
    q: str,
    lang: str,
    mode: str,
    title: str,
    matrix,
    attrs,
    nodes: List[str],
    pos: Dict[str, Tuple[float, float]],
    dur_norm,
    dwell_max: float,
    ddur_lim: float,
    events: List[dict],
    out_path: Path,
) -> Path:
    """Red pyvis animada de UNA condición + scrubber inyectado."""
    from pyvis.network import Network

    net = Network(height="700px", width="100%", directed=True, bgcolor="#ffffff",
                  cdn_resources="remote", notebook=False)
    net.heading = title
    net.toggle_physics(False)

    CX = CY = 350.0
    R = 230.0

    def xy(n: str) -> Tuple[float, float]:
        x, y = pos[n]
        return (CX + (x - 0.5) * 2 * R, CY - (y - 0.5) * 2 * R)

    dwell = {n: float(attrs.loc[n, "dwell_share"]) for n in nodes if n in attrs.index}
    mdur = {n: float(attrs.loc[n, "mean_dur_ms"]) for n in nodes if n in attrs.index}
    nfix = {n: float(attrs.loc[n, "n_fixations"]) for n in nodes if n in attrs.index}

    wmax = float(matrix.values.max()) or 1.0

    # --- nodos: idénticos al estático (siempre visibles) ---
    for n in nodes:
        x, y = xy(n)
        present = n in dwell and dwell.get(n, 0.0) > 0
        dur_ok = present and mdur.get(n, np.nan) == mdur.get(n, np.nan)
        size = 12 + 60 * (dwell.get(n, 0.0) / dwell_max)
        if dur_ok:
            fill = _viridis_hex(dur_norm(mdur[n]))
            font_color = "#ffffff" if dur_norm(mdur[n]) < 0.55 else "#1a1a1a"
            border = "#222222"
        else:
            fill = "#ffffff"
            font_color = "#8a8a8a"
            border = "#999999"
        tip = f"<b>{n}</b>"
        if present:
            tip += (
                f"<br>dwell: {dwell[n]*100:.1f}%"
                + (f"<br>duración media: {mdur[n]:.0f} ms" if dur_ok else "")
                + f"<br>n fijaciones: {nfix[n]:,.0f}"
            )
        else:
            tip += "<br><i>sin fijaciones clasificadas en esta condición</i>"
        node_kw = dict(label=n, x=x, y=y, size=size, title=tip, physics=False,
                       shape="dot", font={"size": 15, "color": font_color, "face": "Arial"},
                       color={"background": fill, "border": border,
                              "highlight": {"background": fill, "border": "#000000"}},
                       border_width=2)
        if not present:
            node_kw["shapeProperties"] = {"borderDashes": [4, 3]}
        net.add_node(n, **node_kw)

    # --- aristas normales: ocultas hasta su primera travesía ---
    for u in nodes:
        for v in nodes:
            if u == v:
                continue
            w = float(matrix.loc[u, v]) if (u in matrix.index and v in matrix.columns) else 0.0
            if w <= 0:
                continue
            frac = w / wmax
            col = NODE_PALETTE.get(u, "#888888")
            net.add_edge(
                u, v,
                width=1.0 + 16.0 * frac,
                title=f"{u} → {v}<br>P(v|u) = {w:.3f}",
                color={"color": col, "opacity": 0.10 + 0.72 * frac, "highlight": col},
                arrows={"to": {"enabled": True, "scaleFactor": 0.45}},
                smooth={"enabled": True, "type": "curvedCW", "roundness": 0.16},
                hidden=True,
            )

    # --- satélites de self-loop: nodo + 2 aristas, ocultos ---
    for u in nodes:
        ws = float(matrix.loc[u, u]) if u in matrix.index else 0.0
        if ws <= 0:
            continue
        frac = min(ws / wmax, 1.0)
        x, y = xy(u)
        dx, dy = x - CX, y - CY
        L = (dx**2 + dy**2) ** 0.5 or 1.0
        sx, sy = CX + dx / L * (R + 62), CY + dy / L * (R + 62)
        sat = f"{u}↺"
        col = NODE_PALETTE.get(u, "#888888")
        tip = f"{u} → {u} (self-bucle)<br>P(u|u) = {ws:.3f}"
        net.add_node(sat, label="", x=sx, y=sy, size=6, title=tip, physics=False,
                     shape="dot", color={"background": col, "opacity": 0.55, "border": col},
                     hidden=True)
        for a, b in ((u, sat), (sat, u)):
            net.add_edge(a, b, width=0.8 + 9.0 * frac, title=tip,
                         color={"color": col, "opacity": 0.30 + 0.55 * frac, "highlight": col},
                         arrows={"to": {"enabled": True, "scaleFactor": 0.4}}, dashed=True,
                         smooth={"enabled": False}, hidden=True)

    net.write_html(str(out_path), open_browser=False, notebook=False)

    # --- grupos de revelado (JS) ---
    first = _first_traversals(events)
    groups = []
    for (u, v), ev in sorted(first.items(), key=lambda kv: (kv[1]["t"], kv[0])):
        ddur = float(ev["dur2"]) - float(ev["dur1"])
        if u == v:
            ws = float(matrix.loc[u, u]) if u in matrix.index else 0.0
            if ws <= 0:
                continue
            frac = min(ws / wmax, 1.0)
            sat = f"{u}↺"
            groups.append({
                "pairs": [[u, sat], [sat, u]],
                "node": sat,
                "t": round(float(ev["t"]), 5),
                "d": round(ddur, 3),
                "c": NODE_PALETTE.get(u, "#888888"),
                "o": round(0.30 + 0.55 * frac, 3),
                "w": round(0.8 + 9.0 * frac, 2),
            })
        else:
            w = float(matrix.loc[u, v]) if (u in matrix.index and v in matrix.columns) else 0.0
            if w <= 0:
                continue
            frac = w / wmax
            groups.append({
                "pairs": [[u, v]],
                "node": None,
                "t": round(float(ev["t"]), 5),
                "d": round(ddur, 3),
                "c": NODE_PALETTE.get(u, "#888888"),
                "o": round(0.10 + 0.72 * frac, 3),
                "w": round(1.0 + 16.0 * frac, 2),
            })

    times = [round(float(e["t"]), 5) for e in events]

    # --- inyección ---
    events_js = json.dumps(groups, ensure_ascii=False)
    times_js = json.dumps(times, separators=(",", ":"))
    dlim_js = f"{ddur_lim:.3f}"

    ui_scripts = f"""
    <script>
    (function() {{
        var GROUPS = {events_js};
        var TIMES = {times_js};
        var DLIM = {dlim_js};

        document.addEventListener("DOMContentLoaded", function() {{
            if (typeof network === 'undefined') return;

            var slider = document.getElementById("anim-slider");
            var btnPlay = document.getElementById("anim-play");
            var btnReset = document.getElementById("anim-reset");
            var progress = document.getElementById("anim-progress");
            var speedSel = document.getElementById("anim-speed");

            var byPair = {{}};
            edges.get().forEach(function(e) {{
                byPair[e.from + "|" + e.to] = e.id;
            }});
            GROUPS.forEach(function(g) {{
                g.ids = [];
                for (var i = 0; i < g.pairs.length; i++) {{
                    var id = byPair[g.pairs[i][0] + "|" + g.pairs[i][1]];
                    if (id !== undefined) g.ids.push(id);
                }}
                g.shown = false;
            }});

            function flashColor(d) {{
                var tt = DLIM > 0 ? Math.max(-1, Math.min(1, d / DLIM)) : 0;
                var r, gg, b;
                if (tt < 0) {{
                    var k = (tt + 1) / 2;
                    r = 59 + (221 - 59) * k;
                    gg = 76 + (221 - 76) * k;
                    b = 192 + (221 - 192) * k;
                }} else {{
                    r = 221 + (180 - 221) * tt;
                    gg = 221 + (4 - 221) * tt;
                    b = 221 + (38 - 221) * tt;
                }}
                return "rgb(" + Math.round(r) + "," + Math.round(gg) + "," + Math.round(b) + ")";
            }}

            function applyProgress(val) {{
                var nodeUpd = [], edgeUpd = [];
                var shownCount = 0, transCount = 0;
                for (var i = 0; i < TIMES.length; i++) {{
                    if (TIMES[i] <= val) transCount++;
                }}
                for (var j = 0; j < GROUPS.length; j++) {{
                    var g = GROUPS[j];
                    var show = g.t <= val;
                    if (show) shownCount++;
                    if (show === g.shown) continue;
                    g.shown = show;
                    for (var k = 0; k < g.ids.length; k++) {{
                        edgeUpd.push({{ id: g.ids[k], hidden: !show }});
                    }}
                    if (g.node) nodeUpd.push({{ id: g.node, hidden: !show }});
                    if (show && g.ids.length) {{
                        edgeUpd.push({{
                            id: g.ids[0],
                            color: {{ color: flashColor(g.d), opacity: 1, highlight: g.c }},
                            width: g.w + 2
                        }});
                        (function(gg) {{
                            setTimeout(function() {{
                                edges.update({{
                                    id: gg.ids[0],
                                    color: {{ color: gg.c, opacity: gg.o, highlight: gg.c }},
                                    width: gg.w
                                }});
                            }}, 900);
                        }})(g);
                    }}
                }}
                if (nodeUpd.length) nodes.update(nodeUpd);
                if (edgeUpd.length) edges.update(edgeUpd);
                progress.innerHTML = Math.round(val * 100) + "% &middot; " +
                    transCount + " transiciones &middot; " +
                    shownCount + "/" + GROUPS.length + " pares";
            }}

            var playing = false, rafId = null, lastTs = null, speed = 1.0, p = 0.0;

            function tick(ts) {{
                if (!playing) return;
                if (lastTs === null) lastTs = ts;
                var dt = (ts - lastTs) / 1000;
                lastTs = ts;
                p = Math.min(1.0, p + dt * speed * 0.15);
                applyProgress(p);
                slider.value = p * 100;
                if (p >= 1.0) {{ stopPlay(); return; }}
                rafId = requestAnimationFrame(tick);
            }}

            function startPlay() {{
                if (playing) return;
                if (p >= 1.0) {{ p = 0; applyProgress(0); }}
                playing = true;
                lastTs = null;
                btnPlay.innerHTML = "&#9208; Pausa";
                rafId = requestAnimationFrame(tick);
            }}

            function stopPlay() {{
                playing = false;
                if (rafId !== null) {{ cancelAnimationFrame(rafId); rafId = null; }}
                btnPlay.innerHTML = "&#9654; Reproducir";
            }}

            btnPlay.addEventListener("click", function() {{ playing ? stopPlay() : startPlay(); }});
            btnReset.addEventListener("click", function() {{
                stopPlay();
                p = 0;
                slider.value = 0;
                applyProgress(0);
            }});
            slider.addEventListener("input", function() {{
                stopPlay();
                p = parseFloat(slider.value) / 100.0;
                applyProgress(p);
            }});
            speedSel.addEventListener("change", function() {{ speed = parseFloat(speedSel.value); }});

            applyProgress(0);
            progress.innerHTML = "0% &middot; 0 transiciones &middot; 0/" + GROUPS.length + " pares";
        }});
    }})();
    </script>
    """

    html = out_path.read_text(encoding="utf-8")
    html = html.replace("<body>", f"<body>\n{CSS_OVERRIDES}", 1)
    html = html.replace("</body>", f"{BAR_HTML}\n{ui_scripts}\n</body>", 1)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def _anim_wrapper(lang: str, mode: str, cells, out: Path, dmin: float, dmax: float,
                  ddur_lim: float) -> Path:
    """HTML contenedor: grilla 2×2 de iframes + leyenda (espejo del estático)."""
    legend = " ".join(
        f'<span style="margin-right:10px"><span style="display:inline-block;width:11px;height:11px;'
        f'background:{NODE_PALETTE[n]};border-radius:3px;margin-right:4px;vertical-align:middle"></span>'
        f"<small>{n}</small></span>"
        for n in FUSED_ORDER
    )
    frames = "\n".join(
        f'<div style="background:#fff;border:1px solid #ddd;border-radius:6px;overflow:hidden">'
        f'<iframe src="./network_anim/{cid}.html" style="width:100%;height:640px;border:0"></iframe></div>'
        for _, _, cid in cells
    )
    cell_titles = "\n".join(
        f'<div style="grid-row:{i // 2 + 2};grid-column:{i % 2 + 1};text-align:center;'
        f'font-weight:600;padding:4px">{t}</div>'
        for i, (_, t, _) in enumerate(cells)
    )
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Red animada — {LANG_NAMES.get(lang, lang)} · {mode}</title></head>
<body style="font-family:Arial,Helvetica,sans-serif;margin:18px;background:#fafafa">
<h2 style="margin:0 0 2px">Red de transiciones entre clases — ANIMADA — {LANG_NAMES.get(lang, lang)} · modo {mode}</h2>
<p style="margin:4px 0 10px;color:#444">
  Cada arista aparece en su primera travesía conforme avanza la lectura
  (t = progreso 0-100% por lector, pooled): destello <b>rojo/azul</b> = Δdur del evento
  (rojo = fijación destino más larga), luego se asienta al estilo estático
  (color = clase origen, opacity = P(v|u)). Pulsa ▶ en cada panel.
</p>
<div style="margin:6px 0 12px">{legend}</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;max-width:1500px">
  {cell_titles}
  {frames}
</div>
<div style="margin-top:14px;display:flex;align-items:center;gap:10px">
  <small>duración media (ms):</small>
  <span style="width:220px;height:12px;border:1px solid #ccc;border-radius:3px;display:inline-block;
    background:linear-gradient(to right,#440154,#3b528b,#21918c,#5ec962,#fde725)"></span>
  <small>{dmin:.0f} ms</small><span style="flex:1"></span><small>{dmax:.0f} ms</small>
  <span style="flex:1"></span>
  <small>Δdur destello:</small>
  <span style="width:160px;height:12px;border:1px solid #ccc;border-radius:3px;display:inline-block;
    background:linear-gradient(to right,#3b4cc0,#dddddd,#b40426)"></span>
  <small>−{ddur_lim:.0f} ms ⇄ +{ddur_lim:.0f} ms</small>
</div>
</body></html>"""
    out.write_text(html, encoding="utf-8")
    return out


def plot_network_animations(lang: str, mode: str) -> Optional[Path]:
    """
    Animaciones del 2×2 para una lengua y modo.
    Retorna el path del wrapper network_anim.html (o None si faltan builds).
    """
    mats, attrs = {}, {}
    for session, q in CELLS:
        m = _load_matrix(lang, mode, session, q)
        a = _load_node_attrs(lang, mode, session, q)
        if m is None or a is None:
            print(f"[anim] {lang} ({mode}): faltan matrix/node_attributes para "
                  f"{_cond(session, lang, q)} — ejecuta build primero")
            return None
        mats[(session, q)] = m
        attrs[(session, q)] = a

    nodes = [n for n in FUSED_ORDER if any(n in m.index for m in mats.values())]
    if not nodes:
        print(f"[anim] {lang} ({mode}): red vacía — omitido")
        return None
    mats = {k: m.reindex(index=nodes, columns=nodes).fillna(0.0) for k, m in mats.items()}
    pos = _node_xy(nodes)

    durs = np.concatenate([a["mean_dur_ms"].dropna().values for a in attrs.values()])
    dmin = float(durs.min()) if len(durs) else 0.0
    dmax = float(durs.max()) or 1.0
    if dmax <= dmin:
        dmax = dmin + 1.0
    from matplotlib.colors import Normalize
    dur_norm = Normalize(vmin=dmin, vmax=dmax)
    dwell_max = max(float(a["dwell_share"].max()) for a in attrs.values()) or 1.0

    # eventos por condición + límite Δdur compartido (escala comparable)
    cell_events = {}
    ddur_lim = 0.0
    for session, q in CELLS:
        ev = condition_events(session, lang, q, mode)
        cell_events[(session, q)] = ev
        for e in _first_traversals(ev).values():
            ddur_lim = max(ddur_lim, abs(float(e["dur2"]) - float(e["dur1"])))
    if ddur_lim <= 0:
        ddur_lim = 1.0
    for (session, q), ev in cell_events.items():
        print(f"[anim] {_cond(session, lang, q)}: {len(ev)} eventos, "
              f"{len(_first_traversals(ev))} pares")

    cs = load_condition_summary(lang)
    anim_dir = figures_dir(lang, mode) / "network_anim"
    anim_dir.mkdir(parents=True, exist_ok=True)

    cells = []
    for session, q in CELLS:
        cid = _cond(session, lang, q)
        title = _cell_title(session, q, lang, mode, cs)
        out = _build_anim_condition(
            session, q, lang, mode, title,
            mats[(session, q)], attrs[(session, q)], nodes, pos,
            dur_norm, dwell_max, ddur_lim, cell_events[(session, q)],
            anim_dir / f"{cid}.html",
        )
        cells.append((cid, title, cid))
        print(f"[OK] {out}")

    out = figures_dir(lang, mode) / "network_anim.html"
    _anim_wrapper(lang, mode, cells, out, dmin, dmax, ddur_lim)
    print(f"[OK] {out}")
    return out


def generate_all_animations(langs: Optional[List[str]] = None, modes=MODES) -> None:
    """Animaciones temporales para las lenguas y modos indicados."""
    if langs is None:
        langs = list(CONDITION_LANGS)
    all_langs = set(CONDITION_LANGS)
    for lang in langs:
        if lang not in all_langs:
            continue
        for mode in modes:
            if not mode_dir(lang, mode).exists():
                print(f"[anim] {lang} ({mode}): sin build previo — omitido")
                continue
            plot_network_animations(lang, mode)
