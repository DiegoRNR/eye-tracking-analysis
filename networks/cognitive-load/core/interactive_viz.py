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
    Renderiza la red en build_dir/network_interactive.html con pyvis.

    Canales visuales (post-processados en la leyenda HTML):
      - Color de nodo:  viridis sobre `mean_ps` (mapa perceptual uniforme).
      - Tamaño de nodo: proporcional a `fix_count`.
      - Color de arista: coolwarm sobre `mean_dps` (rojo = spike cognitivo).
      - Grosor de arista: proporcional a `count`.

    Tooltip por nodo: tarjeta (card) con layout grid 2-col (label : valor).
    Tooltip por arista: misma tarjeta, con header `{word_u} → {word_v}`.
    """
    os.makedirs(build_dir, exist_ok=True)
    out_path = os.path.join(build_dir, "network_interactive.html")

    # --- node color: viridis on mean_ps ---
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

    # --- node size: fix_count (for legend min/max) ---
    fix_arr = np.array(
        [d.get("fix_count", 0) for _, d in G.nodes(data=True)], dtype=int
    )
    if fix_arr.size:
        fix_min, fix_max = int(fix_arr.min()), int(fix_arr.max())
    else:
        fix_min, fix_max = 0, 1

    # --- edge color: coolwarm on mean_dps ---
    dps_arr = np.array(
        [d.get("mean_dps", 0.0) for _, _, d in G.edges(data=True)], dtype=float
    )
    if dps_arr.size:
        dmin, dmax = float(dps_arr.min()), float(dps_arr.max())
        drange = dmax - dmin if dmax > dmin else 1.0
    else:
        dmin, dmax, drange = 0.0, 0.0, 1.0
    coolwarm = matplotlib.colormaps["coolwarm"]

    # --- edge thickness: count (for legend min/max) ---
    count_arr = np.array(
        [d.get("count", 0) for _, _, d in G.edges(data=True)], dtype=int
    )
    if count_arr.size:
        count_min, count_max = int(count_arr.min()), int(count_arr.max())
    else:
        count_min, count_max = 0, 1

    # --- stabilization iterations, adapted to graph size ---
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

    # --- node tooltip template (card layout) ---
    node_card_css = (
        "background:#ffffff;"
        "border:1px solid #d0d0d0;"
        "border-radius:6px;"
        "padding:10px 12px;"
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
        "font-size:13px;"
        "min-width:180px;"
        "box-shadow:0 2px 4px rgba(0,0,0,0.1);"
        "color:#333;"
    )
    node_card_header_css = (
        "font-weight:600;"
        "font-size:14px;"
        "border-bottom:1px solid #eee;"
        "padding-bottom:4px;"
        "margin-bottom:6px;"
        "color:#2c3e50;"
    )
    node_card_grid_css = (
        "display:grid;"
        "grid-template-columns:auto 1fr;"
        "gap:3px 14px;"
        "align-items:baseline;"
    )
    node_card_label_css = "color:#888;"

    for n, d in G.nodes(data=True):
        word = d.get("word", str(n))
        title = (
            f'<div style="{node_card_css}">'
            f'<div style="{node_card_header_css}">{word}</div>'
            f'<div style="{node_card_grid_css}">'
            f'<span style="{node_card_label_css}">wordnum</span>'
            f'<span>{d.get("wordnum", 0)}</span>'
            f'<span style="{node_card_label_css}">sentnum</span>'
            f'<span>{d.get("sentnum", 1)}</span>'
            f'<span style="{node_card_label_css}">fix_count</span>'
            f'<span>{d.get("fix_count", 0)}</span>'
            f'<span style="{node_card_label_css}">mean_ps</span>'
            f'<span>{d.get("mean_ps", 0.0):.2f}</span>'
            f'<span style="{node_card_label_css}">mean_ps_z</span>'
            f'<span>{d.get("mean_ps_z", 0.0):.3f}</span>'
            f'<span style="{node_card_label_css}">community</span>'
            f'<span>{d.get("community_label", "n/a")}</span>'
            f'</div>'
            f'</div>'
        )
        net.add_node(
            n,
            label=word,
            title=title,
            color=ps_to_hex[n],
            value=max(1.0, float(d.get("fix_count", 1))),
        )

    # --- edge tooltip template (card layout) ---
    for u, v, d in G.edges(data=True):
        word_u = G.nodes[u].get("word", u)
        word_v = G.nodes[v].get("word", v)
        title = (
            f'<div style="{node_card_css}">'
            f'<div style="{node_card_header_css}">{word_u} → {word_v}</div>'
            f'<div style="{node_card_grid_css}">'
            f'<span style="{node_card_label_css}">type</span>'
            f'<span>{d.get("type", "forward")}</span>'
            f'<span style="{node_card_label_css}">count</span>'
            f'<span>{d.get("count", 0)} (sessions={d.get("n_sessions", 0)})</span>'
            f'<span style="{node_card_label_css}">mean_dps</span>'
            f'<span>{d.get("mean_dps", 0.0):.2f}</span>'
            f'</div>'
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

    # --- post-process: UI, responsiveness, and tooltips ---
    title_html = (
        f'<h1 style="font-family: sans-serif; text-align: center; '
        f'margin: 16px 0 8px; color: #333;">Red de Carga Cognitiva — {prefix}</h1>'
    )

    css_overrides = """
    <style>
        #loadingBar { display: none !important; }
        .vis-tooltip { display: none !important; }
        
        #custom-legend {
            position: fixed;
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
            z-index: 9999;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            font-family: sans-serif;
            font-size: 13px;
            width: 240px;
            user-select: none;
            -webkit-user-select: none;
            color: #333;
            transition: all 0.3s ease;
        }

        #legend-toggle-btn {
            display: none;
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            background: #2c3e50;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            cursor: pointer;
            font-family: sans-serif;
            font-weight: 600;
            font-size: 13px;
        }
        
        /* --- Filter panel: left sidebar, mirroring legend --- */
        #custom-filter-panel {
            position: fixed;
            top: 50%;
            left: 20px;
            transform: translateY(-50%);
            z-index: 9998;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 14px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            font-family: sans-serif;
            font-size: 12px;
            width: 250px;
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: all 0.3s ease;
        }
        #custom-filter-panel select,
        #custom-filter-panel input {
            width: 100%;
            padding: 6px;
            border-radius: 4px;
            border: 1px solid #ccc;
            box-sizing: border-box;
            font-family: inherit;
            font-size: 11px;
            margin-bottom: 4px;
        }
        #custom-filter-panel .ts-wrapper {
            width: 100% !important;
            margin-bottom: 4px;
        }
        #custom-filter-panel button,
        #custom-filter-panel input[type="button"] {
            width: 100%;
            background: #2c3e50;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 6px;
            font-family: inherit;
            font-size: 13px;
        }
        #custom-filter-panel button:hover,
        #custom-filter-panel input[type="button"]:hover {
            background: #1a252f;
        }
        #custom-filter-panel center {
            display: flex;
            flex-direction: column;
            align-items: stretch;
            text-align: left;
            gap: 4px;
        }

        #filter-toggle-btn {
            display: none;
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 10000;
            background: #2c3e50;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            cursor: pointer;
            font-family: sans-serif;
            font-weight: 600;
            font-size: 13px;
        }

        @media (max-width: 768px) {
            #custom-legend {
                top: auto;
                bottom: 70px;
                right: 20px;
                transform: none;
                width: auto;
                max-width: 260px;
                display: none;
            }
            #legend-toggle-btn {
                display: block;
            }
            #custom-filter-panel {
                display: none;
            }
            #filter-toggle-btn {
                display: block;
            }
        }
    </style>
    """

    legend_html = f"""
    <button id="legend-toggle-btn" onclick="toggleLegend()">Mostrar Leyenda</button>
    <div id="custom-legend">
        <h3 style="margin-top: 0; text-align: center; font-size: 15px;">Leyenda</h3>
        <div style="margin-bottom: 12px;" data-tooltip="PS = tamaño pupilar promedio. Colores fríos (violeta) = bajo esfuerzo, cálidos (amarillo) = alto esfuerzo cognitivo.">
            <strong>Color del Nodo (PS Promedio)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span>{ps_min:.2f}</span><span>{ps_max:.2f}</span>
            </div>
            <div style="height: 12px; background: linear-gradient(to right,
                #440154, #31688e, #35b779, #fde725); border-radius: 3px;
                border: 1px solid #ccc;"></div>
        </div>
        <div style="margin-bottom: 12px;" data-tooltip="Cantidad de fijaciones sobre la palabra. Nodo más grande = más veces mirada.">
            <strong>Tamaño del Nodo (Fijaciones)</strong>
            <div style="display: flex; align-items: center; justify-content: space-between; height: 36px;">
                <span style="font-size: 11px;">{fix_min}</span>
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #555;"></div>
                    <div style="width: 16px; height: 16px; border-radius: 50%; background: #555;"></div>
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: #555;"></div>
                </div>
                <span style="font-size: 11px;">{fix_max}</span>
            </div>
        </div>
        <div style="margin-bottom: 12px;" data-tooltip="ΔPS = cambio absoluto del tamaño pupilar entre pares de palabras. Azul = bajo cambio, rojo = pico cognitivo.">
            <strong>Color de la Arista (ΔPS Promedio)</strong>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span>{dmin:.2f}</span><span>{dmax:.2f}</span>
            </div>
            <div style="height: 12px; background: linear-gradient(to right,
                #3b4cc0, #dddddd, #b40426); border-radius: 3px; border: 1px solid #ccc;"></div>
        </div>
        <div data-tooltip="Cantidad de transiciones observadas entre el par de palabras. Arista más gruesa = más frecuente.">
            <strong>Grosor de la Arista (Transiciones)</strong>
            <div style="display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 6px 0;">
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

    ui_scripts = """
    <script>
    function toggleLegend() {
        var lg = document.getElementById("custom-legend");
        var btn = document.getElementById("legend-toggle-btn");
        var isHidden = window.getComputedStyle(lg).display === "none";
        if (isHidden) {
            lg.style.display = "block";
            btn.innerHTML = "Ocultar Leyenda";
        } else {
            lg.style.display = "none";
            btn.innerHTML = "Mostrar Leyenda";
        }
    }

    (function() {
        document.addEventListener("DOMContentLoaded", function() {
            if (typeof network === 'undefined') return;

            var tooltipDiv = document.createElement("div");
            tooltipDiv.id = "custom-html-tooltip";
            tooltipDiv.style.position = "absolute";
            tooltipDiv.style.display = "none";
            tooltipDiv.style.zIndex = "10000";
            tooltipDiv.style.pointerEvents = "none";
            document.body.appendChild(tooltipDiv);

            var tooltips = {};
            var updateItems = function(dataset) {
                var items = dataset.get().map(function(item) {
                    if (item.title) {
                        tooltips[item.id] = item.title;
                        item.title = null;
                    }
                    return item;
                });
                dataset.update(items);
            };
            updateItems(nodes);
            updateItems(edges);

            var nodeWhitelist = ["wordnum", "sentnum", "word"];
            for (var nodeId in allNodes) {
                if (!allNodes.hasOwnProperty(nodeId)) continue;
                var node = allNodes[nodeId];
                var keep = {};
                for (var k = 0; k < nodeWhitelist.length; k++) {
                    var f = nodeWhitelist[k];
                    if (node[f] !== undefined) keep[f] = node[f];
                }
                for (var key in node) delete node[key];
                for (var key in keep) node[key] = keep[key];
            }
            for (var edgeId in allEdges) {
                if (!allEdges.hasOwnProperty(edgeId)) continue;
                var edge = allEdges[edgeId];
                var ekeep = {};
                if (edge["from"] !== undefined) ekeep["from"] = edge["from"];
                if (edge["to"] !== undefined) ekeep["to"] = edge["to"];
                for (var key in edge) delete edge[key];
                for (var key in ekeep) edge[key] = ekeep[key];
            }

            network.on("hoverNode", function(params) {
                if (tooltips[params.node]) {
                    tooltipDiv.innerHTML = tooltips[params.node];
                    tooltipDiv.style.display = "block";
                }
            });
            network.on("blurNode", function() { tooltipDiv.style.display = "none"; });

            network.on("hoverEdge", function(params) {
                if (tooltips[params.edge]) {
                    tooltipDiv.innerHTML = tooltips[params.edge];
                    tooltipDiv.style.display = "block";
                }
            });
            network.on("blurEdge", function() { tooltipDiv.style.display = "none"; });

            // Legend Tooltips
            document.querySelectorAll("[data-tooltip]").forEach(function(el) {
                el.addEventListener("mouseenter", function() {
                    tooltipDiv.innerHTML = '<div style="max-width:220px;font-size:12px;background:rgba(255,255,255,0.95);border:1px solid #ccc;border-radius:6px;padding:8px 10px;box-shadow:0 2px 4px rgba(0,0,0,0.15);color:#333;line-height:1.4;">' + el.getAttribute("data-tooltip") + '</div>';
                    tooltipDiv.style.display = "block";
                });
                el.addEventListener("mouseleave", function() {
                    tooltipDiv.style.display = "none";
                });
            });

            // Global Mouse Follower
            document.addEventListener("mousemove", function(e) {
                if (tooltipDiv.style.display === "block") {
                    var x = e.pageX + 15;
                    var y = e.pageY + 15;
                    var rect = tooltipDiv.getBoundingClientRect();
                    if (x + rect.width > window.innerWidth - 10) x = window.innerWidth - rect.width - 10;
                    if (y + rect.height > window.innerHeight - 10) y = window.innerHeight - rect.height - 10;
                    tooltipDiv.style.left = x + "px";
                    tooltipDiv.style.top = y + "px";
                }
            });

            // --- Filter Panel (left sidebar, vertical layout) ---
            var filterMenu = document.getElementById("filter-menu");
            if (filterMenu) {
                var panel = document.createElement("div");
                panel.id = "custom-filter-panel";

                var header = document.createElement("div");
                header.innerHTML = "<strong>Filtros y Controles</strong>";
                header.style.cursor = "pointer";
                header.style.display = "flex";
                header.style.justifyContent = "space-between";
                header.style.alignItems = "center";
                header.style.paddingBottom = "6px";
                header.style.width = "100%";

                var toggleIcon = document.createElement("span");
                toggleIcon.innerHTML = "\u25bc";
                toggleIcon.style.fontSize = "10px";
                header.appendChild(toggleIcon);

                var content = document.createElement("div");
                content.style.display = "flex";
                content.style.flexDirection = "column";
                content.style.marginTop = "8px";
                content.style.borderTop = "1px solid #ccc";
                content.style.paddingTop = "8px";
                content.style.width = "100%";

                content.appendChild(filterMenu);

                var row = filterMenu.querySelector(".row");
                if (row) {
                    row.style.display = "flex";
                    row.style.flexDirection = "column";
                    row.style.gap = "4px";
                    row.style.margin = "0";
                }
                var cols = filterMenu.querySelectorAll("[class*='col-']");
                for (var ci = 0; ci < cols.length; ci++) {
                    cols[ci].style.flex = "1 0 auto";
                    cols[ci].style.width = "100%";
                    cols[ci].style.maxWidth = "none";
                    cols[ci].style.padding = "0";
                }

                filterMenu.querySelectorAll(".ts-wrapper").forEach(function(w) {
                    w.style.width = "100%";
                });

                var btns = filterMenu.querySelectorAll("button");
                for (var bi = 0; bi < btns.length; bi++) {
                    var txt = btns[bi].textContent.trim();
                    if (txt === "Filter") btns[bi].textContent = "Filtrar";
                    else if (txt === "Reset Selection") btns[bi].textContent = "Restablecer";
                }

                var selects = filterMenu.querySelectorAll("select");
                for (var si = 0; si < selects.length; si++) {
                    var sid = selects[si].id;
                    if (sid === "select-item") {
                        var opts = selects[si].options;
                        for (var oi = 0; oi < opts.length; oi++) {
                            if (opts[oi].value === "" && opts[oi].text.indexOf("Select") !== -1)
                                opts[oi].text = "Seleccione un elemento de la red";
                            else if (opts[oi].value === "node") opts[oi].text = "Nodo";
                            else if (opts[oi].value === "edge") opts[oi].text = "Enlace";
                        }
                    } else if (sid === "select-property") {
                        var popts = selects[si].options;
                        for (var pi = 0; pi < popts.length; pi++) {
                            if (popts[pi].value === "" && popts[pi].text.indexOf("Select") !== -1)
                                popts[pi].text = "Selecciona una propiedad";
                        }
                    } else if (sid === "select-value") {
                        var vopts = selects[si].options;
                        for (var vi = 0; vi < vopts.length; vi++) {
                            if (vopts[vi].value === "" && vopts[vi].text.indexOf("Select") !== -1)
                                vopts[vi].text = "Seleccione un valor";
                        }
                    }
                }

                if (typeof itemControl !== "undefined") {
                    itemControl.settings.placeholder = "Seleccione un elemento de la red";
                    if (itemControl.options["node"]) {
                        itemControl.options["node"].title = "Nodo";
                        itemControl.options["node"].text = "Nodo";
                    }
                    if (itemControl.options["edge"]) {
                        itemControl.options["edge"].title = "Enlace";
                        itemControl.options["edge"].text = "Enlace";
                    }
                    itemControl.sync();
                }
                if (typeof propControl !== "undefined") {
                    propControl.settings.placeholder = "Selecciona una propiedad";
                    propControl.sync();
                }
                if (typeof valueControl !== "undefined") {
                    valueControl.settings.placeholder = "Seleccione un valor";
                    valueControl.sync();
                }

                var itemSelect = document.getElementById("select-item");
                if (itemSelect) {
                    itemSelect.addEventListener("change", function() {
                        setTimeout(function() {
                            if (typeof propControl === "undefined") return;
                            var edgeLabels = {"from": "Desde", "to": "Hasta"};
                            var keys = Object.keys(edgeLabels);
                            for (var k = 0; k < keys.length; k++) {
                                var f = keys[k];
                                if (propControl.getOption(f)) {
                                    propControl.removeOption(f);
                                    propControl.addOption({id: f, title: edgeLabels[f]});
                                }
                            }
                        }, 60);
                    });
                }

                header.onclick = function() {
                    if (content.style.display === "none") {
                        content.style.display = "flex";
                        toggleIcon.innerHTML = "\u25bc";
                    } else {
                        content.style.display = "none";
                        toggleIcon.innerHTML = "\u25b2";
                    }
                };

                panel.appendChild(header);
                panel.appendChild(content);
                document.body.appendChild(panel);

                var filterToggle = document.createElement("button");
                filterToggle.id = "filter-toggle-btn";
                filterToggle.textContent = "Mostrar Filtros";
                filterToggle.onclick = function() {
                    var vis = panel.style.display !== "none";
                    if (vis) {
                        panel.style.display = "none";
                        filterToggle.textContent = "Mostrar Filtros";
                    } else {
                        panel.style.display = "flex";
                        filterToggle.textContent = "Ocultar Filtros";
                    }
                };
                document.body.appendChild(filterToggle);
            }

            // --- Highlight Logic ---
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
                    network.getConnectedNodes(id).forEach(function(c) { connectedNodeIds.add(c); });
                    network.getConnectedEdges(id).forEach(function(e) { connectedEdgeIds.add(e); });
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
            network.on("deselectNode", function() { setHighlight([]); });
        });
    })();
    </script>
    """

    with open(out_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    html_content = html_content.replace("<body>", f"<body>\n{css_overrides}", 1)
    html_content = html_content.replace("<body>", f"<body>\n{title_html}", 1)
    html_content = html_content.replace(
        "</body>", f"{legend_html}\n{ui_scripts}\n</body>", 1
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] Visualización interactiva (pyvis) guardada en: {out_path}")
    return out_path