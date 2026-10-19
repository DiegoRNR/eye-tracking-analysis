"""
networks/scanpath/core/temporal_viz.py

Red de scanpath por texto — ANIMADA (pyvis + JS inyectado).

Cada arista aparece en su PRIMERA travesía conforme avanza la lectura
(t = progreso 0-1 de la fijación destino dentro de la lectura de ese
sujeto, pooled; ver network_builder). Al aparecer destella (opacity 1,
width +1.5) y luego se asienta al estilo estático. Mecánica reveal-once
idéntica a la de word-type-transitions/core/temporal_viz.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from .visualization import build_pyvis_text

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
    #anim-progress { min-width: 210px; text-align: center; font-variant-numeric: tabular-nums; }
    #anim-speed {
        font-family: inherit; font-size: 11px; padding: 5px 6px;
        border-radius: 4px; border: 1px solid #ccc; background: #fff; cursor: pointer;
    }
    @media (max-width: 900px) {
        #anim-slider { width: 120px; }
        #anim-progress { min-width: 130px; font-size: 10px; }
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


def write_text_network_anim(G, out_path: Path, title: str) -> Path:
    """Red pyvis animada de UN texto + scrubber inyectado."""
    net, groups, times = build_pyvis_text(G, title, animated=True)
    groups = groups or []
    times = times or []

    net.write_html(str(out_path), open_browser=False, notebook=False)

    groups_js = json.dumps(groups, separators=(",", ":"))
    times_js = json.dumps(times, separators=(",", ":"))

    ui_scripts = f"""
    <script>
    (function() {{
        var GROUPS = {groups_js};
        var TIMES = {times_js};

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

            function applyProgress(val) {{
                var edgeUpd = [];
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
                    if (show && g.ids.length) {{
                        edgeUpd.push({{
                            id: g.ids[0],
                            color: {{ color: g.c, opacity: 1, highlight: g.c }},
                            width: g.w + 1.5
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
            if (network.fit) network.fit({{ animation: false }});
        }});
    }})();
    </script>
    """

    html = out_path.read_text(encoding="utf-8")
    html = html.replace("<body>", f"<body>\n{CSS_OVERRIDES}", 1)
    html = html.replace("</body>", f"{BAR_HTML}\n{ui_scripts}\n</body>", 1)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def write_grid_wrapper(lang: str, quartile: str, cells, out: Path) -> Path:
    """Delegado al wrapper compartido de visualization."""
    from .visualization import write_grid_wrapper as _wrap

    return _wrap(lang, quartile, "network_anim", cells, out)
