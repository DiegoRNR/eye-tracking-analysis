"""
persistence.py

Serialización de la red construida a CSV/pickle/GraphML/JSON y recarga posterior.
"""

import csv
import json
import os
import pickle
from datetime import datetime, timezone

import networkx as nx
import pandas as pd

from .paths import file_sha256


def save_built_network(
    G,
    output_dir,
    prefix,
    source_files,
    groupby,
    wave,
    subid=None,
    lang=None,
    trialid=None,
    normalize="zscore",
    edge_mode="sequential",
    edge_window=4,
):
    """
    Persiste la red construida y sus metadatos en una carpeta por build.

    Crea <output_dir>/<prefix>/{nodes.csv, edges.csv, graph.pkl, network.graphml, metadata.json}.
    """
    build_dir = os.path.join(output_dir, prefix)
    os.makedirs(build_dir, exist_ok=True)

    nodes_path = os.path.join(build_dir, "nodes.csv")
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "node_id",
                "word",
                "wordnum",
                "sentnum",
                "fix_count",
                "dwell_total",
                "mean_dur",
                "mean_ps",
                "ps_std",
                "ps_max",
                "ps_obs",
                "mean_ps_z",
                "ps_z_std",
                "ps_z_max",
            ]
        )
        for n, d in G.nodes(data=True):
            w.writerow(
                [
                    n,
                    d.get("word", ""),
                    d.get("wordnum", 0),
                    d.get("sentnum", 1),
                    d.get("fix_count", 0),
                    round(d.get("dwell_total", 0.0), 2),
                    round(d.get("mean_dur", 0.0), 2),
                    round(d.get("mean_ps", 0.0), 2),
                    round(d.get("ps_std", 0.0), 2),
                    round(d.get("ps_max", 0.0), 2),
                    d.get("ps_obs", 0),
                    round(d.get("mean_ps_z", 0.0), 4),
                    round(d.get("ps_z_std", 0.0), 4),
                    round(d.get("ps_z_max", 0.0), 4),
                ]
            )
    print(f"[OK] Nodos guardados en: {nodes_path}")

    edges_path = os.path.join(build_dir, "edges.csv")
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "mean_dps", "count", "n_sessions", "type"])
        for u, v, d in G.edges(data=True):
            w.writerow(
                [
                    u,
                    v,
                    round(d.get("mean_dps", 0.0), 2),
                    d.get("count", 0),
                    d.get("n_sessions", 0),
                    d.get("type", "forward"),
                ]
            )
    print(f"[OK] Aristas guardadas en: {edges_path}")

    pkl_path = os.path.join(build_dir, "graph.pkl")
    with open(pkl_path, "wb") as f:
        pickle.dump(G, f)
    print(f"[OK] Objeto NetworkX (DiGraph) guardado en: {pkl_path}")

    graphml_path = os.path.join(build_dir, "network.graphml")
    try:
        nx.write_graphml(G, graphml_path)
        print(f"[OK] Archivo GraphML guardado en: {graphml_path}")
    except Exception as e:
        print(f"[!] No se pudo guardar GraphML: {e}")

    metadata = {
        "prefix": prefix,
        "graph_name": G.name,
        "groupby": groupby,
        "wave": wave,
        "subid": subid,
        "lang": lang,
        "trialid": trialid,
        "normalize": normalize,
        "edge_mode": edge_mode,
        "edge_window": edge_window,
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source_files": [
            {"path": p, "sha256": file_sha256(p)} for p in source_files
        ],
    }
    meta_path = os.path.join(build_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"[OK] Metadatos guardados en: {meta_path}")

    return build_dir


def load_built_network(build_dir):
    """
    Carga una red previamente persistida.

    Intenta primero con graph.pkl (rápido). Si no existe, reconstruye desde
    nodes.csv y edges.csv.
    """
    pkl_path = os.path.join(build_dir, "graph.pkl")
    if os.path.exists(pkl_path):
        with open(pkl_path, "rb") as f:
            G = pickle.load(f)
        print(f"[OK] Red cargada desde pickle: {pkl_path}")
    else:
        nodes_path = os.path.join(build_dir, "nodes.csv")
        edges_path = os.path.join(build_dir, "edges.csv")
        if not (os.path.exists(nodes_path) and os.path.exists(edges_path)):
            raise FileNotFoundError(
                f"No se encontró graph.pkl ni nodes.csv/edges.csv en: {build_dir}"
            )
        nodes_df = pd.read_csv(nodes_path)
        edges_df = pd.read_csv(edges_path)
        G = nx.DiGraph()
        for _, row in nodes_df.iterrows():
            G.add_node(
                row["node_id"],
                word=row.get("word", ""),
                wordnum=int(row.get("wordnum", 0)),
                sentnum=int(row.get("sentnum", 1)),
                fix_count=int(row.get("fix_count", 0)),
                dwell_total=float(row.get("dwell_total", 0.0)),
                mean_dur=float(row.get("mean_dur", 0.0)),
                mean_ps=float(row.get("mean_ps", 0.0)),
                ps_std=float(row.get("ps_std", 0.0)),
                ps_max=float(row.get("ps_max", 0.0)),
                ps_obs=int(row.get("ps_obs", 0)),
                mean_ps_z=float(row.get("mean_ps_z", 0.0)) if "mean_ps_z" in row else 0.0,
                ps_z_std=float(row.get("ps_z_std", 0.0)) if "ps_z_std" in row else 0.0,
                ps_z_max=float(row.get("ps_z_max", 0.0)) if "ps_z_max" in row else 0.0,
            )
        for _, row in edges_df.iterrows():
            G.add_edge(
                row["source"],
                row["target"],
                mean_dps=float(row.get("mean_dps", 0.0)),
                count=int(row.get("count", 0)),
                n_sessions=int(row.get("n_sessions", 0)),
                type=row.get("type", "forward"),
            )
        print(
            f"[OK] Red reconstruida desde CSVs en: {build_dir} "
            f"({G.number_of_nodes()} nodos, {G.number_of_edges()} aristas)"
        )

    meta_path = os.path.join(build_dir, "metadata.json")
    metadata = None
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    return G, metadata


def check_cache_fresh(metadata, source_files):
    """
    Compara los hashes SHA-256 actuales de los archivos fuente contra los
    registrados en metadata.json. Imprime advertencia si la fuente cambió.
    """
    if not metadata or "source_files" not in metadata:
        return
    expected = {item["path"]: item["sha256"] for item in metadata["source_files"]}
    for path in source_files:
        if not os.path.exists(path):
            print(f"[!] Archivo fuente no disponible para verificar freshness: {path}")
            continue
        current = file_sha256(path)
        if path in expected and expected[path] != current:
            print(
                f"[!] AVISO: el archivo fuente cambió desde la construcción de la caché."
            )
            print(f"    ruta         : {path}")
            print(f"    sha256 cache : {expected[path]}")
            print(f"    sha256 ahora : {current}")
            print(
                "    Vuelve a ejecutar cogload_network.py para refrescar la caché."
            )
        elif path in expected:
            print(f"[OK] Caché vigente para: {path}")
