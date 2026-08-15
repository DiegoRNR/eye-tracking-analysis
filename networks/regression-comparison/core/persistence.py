"""
persistence.py

Serialización de la red de regresiones a CSV/pickle/GraphML/JSON.

Sigue el esquema canónico de `networks/README.md`: cada build vive en
`output/<prefix>/` y `metadata.json` registra los hashes SHA-256 de las
fuentes para invalidar la caché.
"""

import csv
import json
import os
import pickle
from datetime import datetime, timezone

import networkx as nx

from ._langcomp import get_langcomp_core

_NODE_COLUMNS = [
    "node_id", "word", "wordnum", "sentnum", "fix_count", "dwell_total",
    "mean_dur", "first_pass_dur", "n_refix", "refix_rate", "reg_in", "reg_out",
    "reg_in_rate", "reg_out_rate", "n_sessions_seen", "seen_rate", "mean_ps",
    "ps_obs",
]

_EDGE_COLUMNS = [
    "source", "target", "type", "count", "n_sessions", "rate", "amplitude",
    "mean_dur_target",
]


def save_built_network(
    G,
    output_dir,
    prefix,
    source_files,
    wave,
    trialid,
    lang_group,
    languages,
    accuracy_summary,
    n_participants,
    n_with_accuracy,
    discarded_sessions,
    edge_weight,
    report,
):
    """
    Persiste la red y sus metadatos en `output_dir/prefix/`.

    Crea nodes.csv, edges.csv, graph.pkl, network.graphml y metadata.json.
    """
    get_langcomp_core()
    from langcomp_core.paths import file_sha256

    build_dir = os.path.join(output_dir, prefix)
    os.makedirs(build_dir, exist_ok=True)

    nodes_path = os.path.join(build_dir, "nodes.csv")
    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(_NODE_COLUMNS)
        for n, d in sorted(G.nodes(data=True), key=lambda x: x[1].get("wordnum", 0)):
            w.writerow([n] + [d.get(c, "") for c in _NODE_COLUMNS[1:]])
    print(f"[OK] Nodos guardados en: {nodes_path}")

    edges_path = os.path.join(build_dir, "edges.csv")
    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(_EDGE_COLUMNS)
        for u, v, d in G.edges(data=True):
            w.writerow([u, v] + [d.get(c, "") for c in _EDGE_COLUMNS[2:]])
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
        "wave": wave,
        "trialid": trialid,
        "lang_group": lang_group,
        "languages": languages,
        "n_participants": n_participants,
        "n_with_accuracy": n_with_accuracy,
        "n_sessions_discarded": len(discarded_sessions),
        "discarded_sessions": discarded_sessions,
        "accuracy": accuracy_summary,
        "edge_mode": "scanpath-temporal",
        "edge_weight": edge_weight,
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source_files": [{"path": p, "sha256": file_sha256(p)} for p in source_files],
    }
    metadata.update(report)

    meta_path = os.path.join(build_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"[OK] Metadatos guardados en: {meta_path}")

    return build_dir


def load_built_network(build_dir):
    """Carga una red persistida desde graph.pkl y su metadata.json."""
    pkl_path = os.path.join(build_dir, "graph.pkl")
    if not os.path.exists(pkl_path):
        raise FileNotFoundError(f"No se encontró graph.pkl en: {build_dir}")
    with open(pkl_path, "rb") as f:
        G = pickle.load(f)

    meta_path = os.path.join(build_dir, "metadata.json")
    metadata = None
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    print(f"[OK] Red cargada desde: {pkl_path}")
    return G, metadata


def check_cache_fresh(metadata, source_files):
    """Compara hashes SHA-256 actuales contra los registrados en metadata.json."""
    get_langcomp_core()
    from langcomp_core.paths import file_sha256

    if not metadata or "source_files" not in metadata:
        return False
    expected = {item["path"]: item["sha256"] for item in metadata["source_files"]}
    fresh = True
    for path in source_files:
        if not os.path.exists(path):
            print(f"[!] Archivo fuente no disponible: {path}")
            fresh = False
            continue
        if path in expected and expected[path] != file_sha256(path):
            print(f"[!] AVISO: el archivo fuente cambió desde la construcción: {path}")
            fresh = False
    return fresh
