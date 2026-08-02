import os
import sys
import math
import csv
import argparse
from collections import defaultdict, Counter

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from pyvis.network import Network as PyvisNetwork


import plotly.graph_objects as go

HAS_PANDAS = True
HAS_NETWORKX = True
HAS_MATPLOTLIB = True
HAS_PYVIS = True
HAS_PLOTLY = True


def find_default_fixation_file():
    """Busca el archivo de reporte de fijaciones por defecto en el workspace."""
    possible_paths = [
        os.path.join("data", "MECO-L2_version-2.2", "wave-1", "primary-data", "eye-tracking", "joint_l2_fixation_trimmed_report_2.2.csv"),
        os.path.join("data", "MECO-L2_version-2.2", "wave-2", "primary-data", "eye-tracking", "joint_fix_trimmed_L2_wave2_version2.2.csv"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None


def load_fixations(filepath, uniform_id=None, lang=None, trialid=None):
    """
    Carga y filtra las fijaciones del dataset CSV.
    Retorna una lista de diccionarios ordenados cronológicamente por participante y texto.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

    fixations_by_session = defaultdict(list)

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filtrar por participante, idioma materno o ID de texto si se especifican
            uid = row.get('uniform_id') or row.get('subid')
            row_lang = row.get('lang')
            tid = row.get('trialid')

            if uniform_id and uid != uniform_id:
                continue
            if lang and row_lang != lang:
                continue
            if trialid and str(tid) != str(trialid):
                continue

            # Validar número de palabra (wordnum)
            try:
                wordnum = int(float(row.get('wordnum', -1)))
                fixid = int(float(row.get('fixid', -1)))
                dur = float(row.get('dur', 0))
                start = float(row.get('start', 0))
            except (ValueError, TypeError):
                continue

            if wordnum < 0:
                continue

            word_text = row.get('word') or row.get('ia') or f"Word_{wordnum}"
            sentnum = row.get('sentnum', '1')
            ps = float(row.get('ps', 0)) if row.get('ps') else 0.0

            session_key = (uid, row_lang, tid)
            fixations_by_session[session_key].append({
                'uniform_id': uid,
                'lang': row_lang,
                'trialid': tid,
                'fixid': fixid,
                'start': start,
                'dur': dur,
                'wordnum': wordnum,
                'word': word_text,
                'sentnum': sentnum,
                'ps': ps
            })

    # Ordenar fijaciones cronológicamente por (fixid / start) dentro de cada sesión
    for key in fixations_by_session:
        fixations_by_session[key].sort(key=lambda x: (x['fixid'], x['start']))

    return fixations_by_session


class PurePythonDiGraph:
    """Clase ligera de Grafo Dirigido en Python Puro cuando NetworkX no está instalado."""
    def __init__(self, name=""):
        self.name = name
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id, **kwargs):
        if node_id not in self.nodes:
            self.nodes[node_id] = kwargs
        else:
            self.nodes[node_id].update(kwargs)

    def add_edge(self, u, v, **kwargs):
        if (u, v) not in self.edges:
            self.edges[(u, v)] = kwargs
        else:
            self.edges[(u, v)].update(kwargs)

    def number_of_nodes(self):
        return len(self.nodes)

    def number_of_edges(self):
        return len(self.edges)

    def in_degree(self, weight=None):
        indeg = defaultdict(float)
        for (u, v), attrs in self.edges.items():
            w = attrs.get('weight', 1) if weight else 1
            indeg[v] += w
            if u not in indeg:
                indeg[u] += 0
        return indeg

    def out_degree(self, weight=None):
        outdeg = defaultdict(float)
        for (u, v), attrs in self.edges.items():
            w = attrs.get('weight', 1) if weight else 1
            outdeg[u] += w
            if v not in outdeg:
                outdeg[v] += 0
        return outdeg


def build_scanpath_network(fixations_list, text_label="Scanpath Network"):
    """
    Construye una red dirigida y ponderada (NetworkX o PurePythonDiGraph) a partir de una lista de fijaciones.
    
    Nodos: Palabras identificadas por 'wordnum:palabra'.
    Aristas: Transiciones consecuentes de fijación ocular (u -> v).
    """
    if HAS_NETWORKX:
        G = nx.DiGraph(name=text_label)
    else:
        G = PurePythonDiGraph(name=text_label)

    # 1. Registrar Nodos (Palabras) y acumular estadísticas
    node_data = defaultdict(lambda: {
        'word': '',
        'wordnum': 0,
        'sentnum': 0,
        'fix_count': 0,
        'total_dur': 0.0,
        'ps_list': []
    })

    for fix in fixations_list:
        node_id = f"{fix['wordnum']}:{fix['word']}"
        nd = node_data[node_id]
        nd['word'] = fix['word']
        nd['wordnum'] = fix['wordnum']
        nd['sentnum'] = fix['sentnum']
        nd['fix_count'] += 1
        nd['total_dur'] += fix['dur']
        if fix['ps'] > 0:
            nd['ps_list'].append(fix['ps'])

    # Agregar nodos a NetworkX
    for node_id, d in node_data.items():
        mean_ps = (sum(d['ps_list']) / len(d['ps_list'])) if d['ps_list'] else 0.0
        G.add_node(
            node_id,
            word=d['word'],
            wordnum=d['wordnum'],
            sentnum=d['sentnum'],
            fix_count=d['fix_count'],
            total_dur=d['total_dur'],
            mean_dur=d['total_dur'] / d['fix_count'] if d['fix_count'] > 0 else 0,
            mean_ps=mean_ps
        )

    # 2. Registrar Aristas (Transiciones de Fijación)
    edge_counts = Counter()
    edge_durations = defaultdict(list)
    edge_types = defaultdict(str)

    for i in range(len(fixations_list) - 1):
        curr_fix = fixations_list[i]
        next_fix = fixations_list[i + 1]

        u = f"{curr_fix['wordnum']}:{curr_fix['word']}"
        v = f"{next_fix['wordnum']}:{next_fix['word']}"

        edge_counts[(u, v)] += 1
        delta_t = next_fix['start'] - (curr_fix['start'] + curr_fix['dur'])
        edge_durations[(u, v)].append(delta_t)

        if next_fix['wordnum'] > curr_fix['wordnum']:
            edge_types[(u, v)] = 'forward'
        elif next_fix['wordnum'] < curr_fix['wordnum']:
            edge_types[(u, v)] = 'regression'
        else:
            edge_types[(u, v)] = 'refixation'

    # Agregar aristas a NetworkX
    for (u, v), weight in edge_counts.items():
        durs = edge_durations[(u, v)]
        avg_transition_time = sum(durs) / len(durs) if durs else 0.0
        G.add_edge(
            u, v,
            weight=weight,
            type=edge_types[(u, v)],
            mean_transition_time=avg_transition_time
        )

    return G


def compute_scanpath_metrics(G):
    """
    Calcula métricas clave a nivel de nodo y a nivel de red para la Scanpath Network.
    Soporta tanto NetworkX como PurePythonDiGraph.
    """
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    if num_nodes == 0:
        return {}

    max_possible_edges = num_nodes * (num_nodes - 1)
    density = (num_edges / max_possible_edges) if max_possible_edges > 0 else 0.0

    in_degrees = dict(G.in_degree(weight='weight'))
    out_degrees = dict(G.out_degree(weight='weight'))

    betweenness = {}
    pagerank = {}
    if HAS_NETWORKX and isinstance(G, nx.DiGraph):
        try:
            betweenness = nx.betweenness_centrality(G, weight='weight')
        except Exception:
            betweenness = {n: 0.0 for n in G.nodes}

        try:
            pagerank = nx.pagerank(G, weight='weight')
        except Exception:
            pagerank = {n: 1.0 / num_nodes for n in G.nodes}

    if HAS_NETWORKX and isinstance(G, nx.DiGraph):
        edge_items = [(u, v, d) for u, v, d in G.edges(data=True)]
        node_items = dict(G.nodes(data=True))
    else:
        edge_items = [(u, v, d) for (u, v), d in G.edges.items()]
        node_items = G.nodes

    forward_count = sum(d.get('weight', 1) for u, v, d in edge_items if d.get('type') == 'forward')
    regression_count = sum(d.get('weight', 1) for u, v, d in edge_items if d.get('type') == 'regression')
    refixation_count = sum(d.get('weight', 1) for u, v, d in edge_items if d.get('type') == 'refixation')
    total_transitions = forward_count + regression_count + refixation_count

    regression_ratio = (regression_count / total_transitions) if total_transitions > 0 else 0.0

    if HAS_NETWORKX and isinstance(G, nx.DiGraph):
        reciprocity = nx.reciprocity(G) if num_edges > 0 else 0.0
    else:
        mutual_count = sum(1 for (u, v) in G.edges if (v, u) in G.edges)
        reciprocity = (mutual_count / num_edges) if num_edges > 0 else 0.0

    out_edges_map = defaultdict(list)
    for u, v, d in edge_items:
        out_edges_map[u].append((v, d.get('weight', 1)))

    node_entropies = []
    for n in node_items:
        out_list = out_edges_map.get(n, [])
        out_weight_sum = sum(w for _, w in out_list)
        if out_weight_sum > 0:
            h = 0.0
            for _, w in out_list:
                p = w / out_weight_sum
                if p > 0:
                    h -= p * math.log2(p)
            node_entropies.append(h)

    mean_scanpath_entropy = (sum(node_entropies) / len(node_entropies)) if node_entropies else 0.0

    network_metrics = {
        'num_nodes': num_nodes,
        'num_edges': num_edges,
        'density': round(density, 4),
        'reciprocity': round(reciprocity, 4),
        'total_transitions': total_transitions,
        'forward_transitions': forward_count,
        'regression_transitions': regression_count,
        'refixation_transitions': refixation_count,
        'regression_ratio': round(regression_ratio, 4),
        'mean_scanpath_entropy': round(mean_scanpath_entropy, 4)
    }

    for n, d in node_items.items():
        d['in_degree_weighted'] = in_degrees.get(n, 0)
        d['out_degree_weighted'] = out_degrees.get(n, 0)
        d['betweenness'] = round(betweenness.get(n, 0.0), 4)
        d['pagerank'] = round(pagerank.get(n, 0.0), 4)

    return network_metrics


def export_scanpath_report(G, network_metrics, output_dir, prefix="scanpath"):
    """Saca reportes en CSV y formatos de red (GraphML / GEXF)."""
    os.makedirs(output_dir, exist_ok=True)

    if HAS_NETWORKX and isinstance(G, nx.DiGraph):
        node_items = dict(G.nodes(data=True))
        edge_items = [(u, v, d) for u, v, d in G.edges(data=True)]
    else:
        node_items = G.nodes
        edge_items = [(u, v, d) for (u, v), d in G.edges.items()]

    metrics_file = os.path.join(output_dir, f"{prefix}_global_metrics.csv")
    with open(metrics_file, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Metric', 'Value'])
        for k, v in network_metrics.items():
            w.writerow([k, v])
    print(f"[OK] Métricas globales guardadas en: {metrics_file}")

    nodes_file = os.path.join(output_dir, f"{prefix}_node_metrics.csv")
    with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['node_id', 'word', 'wordnum', 'sentnum', 'fix_count', 'total_dur_ms', 'mean_dur_ms', 'mean_ps', 'in_degree_weighted', 'out_degree_weighted', 'betweenness', 'pagerank'])
        for n, d in node_items.items():
            w.writerow([
                n, d.get('word'), d.get('wordnum'), d.get('sentnum'),
                d.get('fix_count'), d.get('total_dur'), round(d.get('mean_dur', 0), 2),
                round(d.get('mean_ps', 0), 2), d.get('in_degree_weighted', 0),
                d.get('out_degree_weighted', 0), d.get('betweenness', 0), d.get('pagerank', 0)
            ])
    print(f"[OK] Métricas de nodo guardadas en: {nodes_file}")

    edges_file = os.path.join(output_dir, f"{prefix}_edge_list.csv")
    with open(edges_file, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['source', 'target', 'weight', 'type', 'mean_transition_time_ms'])
        for u, v, d in edge_items:
            w.writerow([u, v, d.get('weight', 1), d.get('type', 'forward'), round(d.get('mean_transition_time', 0), 2)])
    print(f"[OK] Lista de aristas guardada en: {edges_file}")

    if HAS_NETWORKX and isinstance(G, nx.DiGraph):
        graphml_file = os.path.join(output_dir, f"{prefix}_network.graphml")
        pickle_file = os.path.join(output_dir, f"{prefix}_graph.pkl")
        try:
            nx.write_graphml(G, graphml_file)
            print(f"[OK] Archivo GraphML guardado en: {graphml_file}")
        except Exception as e:
            print(f"[!] No se pudo guardar GraphML: {e}")

        try:
            import pickle
            with open(pickle_file, 'wb') as f:
                pickle.dump(G, f)
            print(f"[OK] Objeto NetworkX (nx.DiGraph) guardado en: {pickle_file}")
        except Exception as e:
            print(f"[!] No se pudo guardar Pickle: {e}")
    else:
        print("[INFO] Instala networkx para habilitar la exportación en GraphML y Pickle.")


def visualize_scanpath_network(G, output_dir, prefix="scanpath"):
    """Genera mapas estáticos con Matplotlib y visualización interactiva HTML con Pyvis si está disponible."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Visualización Estática con Matplotlib
    if HAS_MATPLOTLIB and len(G.nodes) > 0:
        plt.figure(figsize=(14, 8))
        
        # Posición horizontal por wordnum, vertical por sentnum invertido
        pos = {}
        for n, d in G.nodes(data=True):
            try:
                x = int(d.get('wordnum', 0))
                y = -int(d.get('sentnum', 1))
            except ValueError:
                x, y = 0, 0
            pos[n] = (x, y)

        node_sizes = [d.get('fix_count', 1) * 80 for n, d in G.nodes(data=True)]
        edge_widths = [d.get('weight', 1) * 1.5 for u, v, d in G.edges(data=True)]
        edge_colors = ['#e74c3c' if d.get('type') == 'regression' else '#3498db' for u, v, d in G.edges(data=True)]

        labels = {n: d.get('word', '') for n, d in G.nodes(data=True)}

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='#2ecc71', alpha=0.8)
        nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors, alpha=0.6, arrows=True, arrowsize=12)
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_family='sans-serif')

        plt.title(f"Red de Transición de Fijaciones Oculares (Scanpath: {G.name})", fontsize=14, fontweight='bold')
        plt.xlabel("Posición de la Palabra en el Texto (wordnum)")
        plt.ylabel("Oración (sentnum)")
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()

        png_path = os.path.join(output_dir, f"{prefix}_visualization.png")
        plt.savefig(png_path, dpi=300)
        plt.close()
        print(f"[OK] Visualización estática guardada en: {png_path}")

    # 2. Visualización Interactiva HTML mejorada con Pyvis (Anti-superposición)
    if HAS_PYVIS and len(G.nodes) > 0:
        net = PyvisNetwork(height="850px", width="100%", directed=True, notebook=False)

        if HAS_NETWORKX and isinstance(G, nx.DiGraph):
            net.from_nx(G)
            node_items = dict(G.nodes(data=True))
        else:
            node_items = G.nodes
            for n, d in node_items.items():
                net.add_node(n, label=d.get('word', n))
            for (u, v), d in G.edges.items():
                net.add_edge(u, v, weight=d.get('weight', 1))

        # Posicionamiento espacial y estilo de cajas para evitar superposición
        for node in net.nodes:
            n_id = node['id']
            if n_id in node_items:
                d = node_items[n_id]
                wordnum = float(d.get('wordnum', 0))
                sentnum = float(d.get('sentnum', 1))
                
                # Asignar coordenadas iniciales amplias basadas en la lectura
                node['x'] = wordnum * 180.0
                node['y'] = sentnum * 150.0
                node['label'] = f"{d.get('word')}"
                node['shape'] = 'box'
                node['margin'] = 12
                node['borderWidth'] = 2
                node['color'] = {
                    'background': '#ebf5fb',
                    'border': '#2980b9',
                    'highlight': {'background': '#d5e8d4', 'border': '#2ecc71'}
                }
                node['font'] = {'size': 14, 'face': 'Arial'}
                node['title'] = (
                    f"<b>Palabra:</b> {d.get('word')}<br>"
                    f"<b>Posición:</b> Palabra #{d.get('wordnum')} (Oración #{d.get('sentnum')})<br>"
                    f"<b>Fijaciones Totales:</b> {d.get('fix_count')}<br>"
                    f"<b>Duración Total:</b> {d.get('total_dur')} ms<br>"
                    f"<b>Tamaño Pupila Promedio:</b> {d.get('mean_ps')}<br>"
                    f"<b>Betweenness Centrality:</b> {d.get('betweenness', 0)}<br>"
                    f"<b>PageRank:</b> {d.get('pagerank', 0)}"
                )

        # Personalizar aristas (evitar flechas y grosores gigantes por acumulación de pesos)
        for edge in net.edges:
            w = float(edge.get('weight', 1))
            edge['width'] = max(0.5, min(3.5, math.log1p(w) * 0.8))
            edge['smooth'] = {'type': 'curvedCW', 'roundness': 0.15}
            edge_type = edge.get('type', 'forward')
            
            if edge_type == 'regression':
                edge['color'] = 'rgba(231, 76, 60, 0.45)'
            elif edge_type == 'refixation':
                edge['color'] = 'rgba(142, 68, 173, 0.35)'
            else:
                edge['color'] = 'rgba(52, 152, 219, 0.35)'

        # Opciones de física para forzar separación y cero colisión
        net.set_options("""
        var options = {
          "nodes": {
            "borderWidthSelected": 3
          },
          "edges": {
            "arrows": { "to": { "enabled": false } },
            "selectionWidth": 2
          },
          "physics": {
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -180,
              "centralGravity": 0.005,
              "springLength": 240,
              "springConstant": 0.05,
              "avoidOverlap": 1.0
            },
            "minVelocity": 0.75,
            "timestep": 0.35,
            "stabilization": { "iterations": 200 }
          }
        }
        """)

        html_path = os.path.join(output_dir, f"{prefix}_interactive.html")
        try:
            net.write_html(html_path)
            print(f"[OK] Visualización interactiva Pyvis (sin superposición) guardada en: {html_path}")
        except Exception as e:
            print(f"[!] No se pudo guardar HTML de Pyvis: {e}")

    # 3. Visualización Interactiva Avanzada con Plotly (Excelente separación y control)
    if HAS_PLOTLY and len(G.nodes) > 0:
        if HAS_NETWORKX and isinstance(G, nx.DiGraph):
            node_items = dict(G.nodes(data=True))
            edge_items = [(u, v, d) for u, v, d in G.edges(data=True)]
        else:
            node_items = G.nodes
            edge_items = [(u, v, d) for (u, v), d in G.edges.items()]

        node_x, node_y, node_text, node_hover, node_size = [], [], [], [], []
        
        for n, d in node_items.items():
            try:
                x = int(d.get('wordnum', 0))
                y = -int(d.get('sentnum', 1))
            except ValueError:
                x, y = 0, 0
            node_x.append(x)
            node_y.append(y)
            node_text.append(d.get('word', ''))
            node_size.append(max(15, min(45, d.get('fix_count', 1) * 2)))
            
            hover_str = (
                f"<b>Palabra:</b> {d.get('word')}<br>"
                f"<b>Posición:</b> Palabra {d.get('wordnum')} (Oración {d.get('sentnum')})<br>"
                f"<b>Fijaciones:</b> {d.get('fix_count')}<br>"
                f"<b>Duración Total:</b> {d.get('total_dur')} ms<br>"
                f"<b>Pupila Promedio:</b> {d.get('mean_ps')}<br>"
                f"<b>PageRank:</b> {d.get('pagerank', 0)}"
            )
            node_hover.append(hover_str)

        # Aristas de Avances vs Regresiones
        fwd_x, fwd_y = [], []
        reg_x, reg_y = [], []

        for u, v, d in edge_items:
            du = node_items.get(u, {})
            dv = node_items.get(v, {})
            try:
                x0, y0 = int(du.get('wordnum', 0)), -int(du.get('sentnum', 1))
                x1, y1 = int(dv.get('wordnum', 0)), -int(dv.get('sentnum', 1))
            except ValueError:
                continue

            if d.get('type') == 'regression':
                reg_x.extend([x0, x1, None])
                reg_y.extend([y0, y1, None])
            else:
                fwd_x.extend([x0, x1, None])
                fwd_y.extend([y0, y1, None])

        fig = go.Figure()

        # Trazas de aristas
        fig.add_trace(go.Scatter(
            x=fwd_x, y=fwd_y,
            line=dict(width=1.2, color='#3498db'),
            hoverinfo='none',
            mode='lines',
            name='Avances (Forward)'
        ))

        fig.add_trace(go.Scatter(
            x=reg_x, y=reg_y,
            line=dict(width=1.8, color='#e74c3c'),
            hoverinfo='none',
            mode='lines',
            name='Regresiones (Lookback)'
        ))

        # Traza de nodos
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            hovertext=node_hover,
            textposition="top center",
            textfont=dict(size=12, color="#2c3e50"),
            marker=dict(
                size=node_size,
                color='#2ecc71',
                line=dict(width=1.5, color='#27ae60'),
                opacity=0.85
            ),
            name='Palabras'
        ))

        fig.update_layout(
            title=f"Scanpath Network (Plotly Interactivo): {G.name}",
            showlegend=True,
            hovermode='closest',
            margin=dict(b=40, l=40, r=40, t=60),
            xaxis=dict(title="Posición de la Palabra en el Texto (wordnum)", showgrid=True, zeroline=False),
            yaxis=dict(title="Oración (sentnum)", showgrid=True, zeroline=False),
            template="plotly_white",
            height=800
        )

        plotly_html = os.path.join(output_dir, f"{prefix}_plotly.html")
        fig.write_html(plotly_html)
        print(f"[OK] Visualización interactiva Plotly guardada en: {plotly_html}")


def main():
    parser = argparse.ArgumentParser(description="Construir y analizar Redes de Transición de Fijaciones Oculares (Scanpath Networks).")
    parser.add_argument("--file", type=str, help="Ruta al archivo CSV de fijaciones (joint_l2_fixation_trimmed_report_2.2.csv)")
    parser.add_argument("--subid", type=str, help="Filtrar por ID uniforme de participante (ej. du_4, es_10)")
    parser.add_argument("--lang", type=str, help="Filtrar por código de idioma materno L1 (ej. du, es, de, it)")
    parser.add_argument("--trialid", type=str, default="1", help="ID de texto a analizar [1 a 12] (por defecto: 1)")
    parser.add_argument("--outdir", type=str, default=os.path.join("networks", "scanpath", "output"), help="Carpeta de salida para reportes y visualizaciones")
    parser.add_argument("--name", type=str, help="Nombre personalizado para los archivos generados (ej. mi_red_texto1)")

    args = parser.parse_args()

    # 1. Determinar ruta de archivo
    filepath = args.file or find_default_fixation_file()
    if not filepath or not os.path.exists(filepath):
        print(f"[ERROR] No se encontró el archivo de fijaciones. Especifica la ruta con --file.")
        sys.exit(1)

    print(f"--> Cargando fijaciones desde: {filepath}")
    print(f"--> Filtros: Participant={args.subid or 'ALL'}, L1 Language={args.lang or 'ALL'}, Text Trial ID={args.trialid}")

    # 2. Cargar fijaciones
    sessions = load_fixations(filepath, uniform_id=args.subid, lang=args.lang, trialid=args.trialid)

    if not sessions:
        print("[!] No se encontraron fijaciones con los criterios especificados.")
        sys.exit(0)

    print(f"--> Encontradas {len(sessions)} sesiones de lectura (Participante - L1 - Texto).")

    # 3. Si hay múltiples sesiones (ej. agrupar por idioma L1 o por texto), combinamos o procesamos
    all_fixations = []
    for key, fix_list in sessions.items():
        all_fixations.extend(fix_list)

    text_label = f"Trial_{args.trialid}"
    if args.lang:
        text_label += f"_Lang_{args.lang}"
    if args.subid:
        text_label += f"_Sub_{args.subid}"

    # 4. Construir Red
    print(f"--> Construyendo Scanpath Network para {text_label} ({len(all_fixations)} fijaciones en total)...")
    G = build_scanpath_network(all_fixations, text_label=text_label)

    # 5. Calcular Métricas
    metrics = compute_scanpath_metrics(G)
    print("\n" + "="*50)
    print(f"RESUMEN DE MÉTRICAS DE LA RED: {text_label}")
    print("="*50)
    for k, v in metrics.items():
        print(f"  {k:25s}: {v}")
    print("="*50 + "\n")

    # 6. Exportar y Visualizar
    if args.name:
        prefix = args.name
    else:
        prefix = f"scanpath_trial{args.trialid}"
        if args.lang:
            prefix += f"_{args.lang}"
        if args.subid:
            prefix += f"_{args.subid}"

    export_scanpath_report(G, metrics, args.outdir, prefix=prefix)
    visualize_scanpath_network(G, args.outdir, prefix=prefix)

    print("\n[ÉXITO] Proceso completado exitosamente.")


if __name__ == "__main__":
    main()
