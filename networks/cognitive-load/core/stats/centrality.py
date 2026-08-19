"""
centrality.py

Análisis completo de la red: distribución de grado, asortatividad,
comunidades Louvain, k-core decomposition y centralidades de nodo.
"""

from collections import defaultdict

import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.community import louvain_communities


# ---------------------------------------------------------------------------
# Distribución de grado
# ---------------------------------------------------------------------------

def compute_degree_distribution(G):
    """
    Calcula la distribución de grado (in, out, total) por nodo.

    Retorna un DataFrame con columnas: node_id, word, wordnum, sentnum,
    in_degree, out_degree, total_degree.
    """
    rows = []
    for n, d in G.nodes(data=True):
        rows.append({
            "node_id": n,
            "word": d.get("word", ""),
            "wordnum": d.get("wordnum", 0),
            "sentnum": d.get("sentnum", 1),
            "in_degree": G.in_degree(n),
            "out_degree": G.out_degree(n),
            "total_degree": G.degree(n),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Asortatividad
# ---------------------------------------------------------------------------

def compute_assortativity(G):
    """
    Calcula el coeficiente de asortatividad por grado (in, out, total).

    Para cada variante intenta nx.degree_assortativity_coefficient().
    Retorna dict con coeficiente y p-value por variante.
    """
    results = {}

    # Total degree assortativity
    try:
        coef, pval = nx.degree_assortativity_coefficient(G)
        results["total"] = {"coefficient": round(coef, 6), "p_value": round(pval, 6)}
    except Exception:
        results["total"] = {"coefficient": 0.0, "p_value": 1.0}

    # In-degree assortativity
    try:
        coef, pval = nx.degree_assortativity_coefficient(G, x="in", y="in")
        results["in"] = {"coefficient": round(coef, 6), "p_value": round(pval, 6)}
    except Exception:
        results["in"] = {"coefficient": 0.0, "p_value": 1.0}

    # Out-degree assortativity
    try:
        coef, pval = nx.degree_assortativity_coefficient(G, x="out", y="out")
        results["out"] = {"coefficient": round(coef, 6), "p_value": round(pval, 6)}
    except Exception:
        results["out"] = {"coefficient": 0.0, "p_value": 1.0}

    return results


def compute_assortativity_neighbor_degree(G):
    """
    Para el scatter de asortatividad: grado del nodo vs grado promedio de vecinos.

    Retorna DataFrame con node_id, degree, mean_neighbor_degree.
    """
    rows = []
    for n in G.nodes():
        total_deg = G.degree(n)
        neighbors = set(G.successors(n)) | set(G.predecessors(n))
        if neighbors:
            neighbor_deg = np.mean([G.degree(nb) for nb in neighbors])
        else:
            neighbor_deg = 0.0
        rows.append({
            "node_id": n,
            "degree": total_deg,
            "mean_neighbor_degree": neighbor_deg,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Comunidades Louvain
# ---------------------------------------------------------------------------

def compute_louvain_communities(G, seed=42):
    """
    Detecta comunidades con el algoritmo de Louvain.

    Retorna:
      - community_map: dict {node: community_id}
      - community_summary: lista de dicts con stats por comunidad
      - modularity_score: float
    """
    if G.number_of_nodes() == 0:
        return {}, [], 0.0

    weight_attr = "mean_dps_abs" if G.number_of_edges() > 0 else None
    kwargs = {"seed": seed}
    if weight_attr:
        kwargs["weight"] = weight_attr

    communities_list = list(louvain_communities(G, **kwargs))
    modularity_score = nx.community.modularity(
        G, communities_list, weight=weight_attr
    )

    community_map = {}
    community_summary = []
    for idx, comm in enumerate(communities_list):
        nodes_in_comm = list(comm)
        words = [G.nodes[n].get("word", n) for n in nodes_in_comm]
        wordnums = [G.nodes[n].get("wordnum", 0) for n in nodes_in_comm]
        ps_vals = [
            G.nodes[n].get("mean_ps_z", G.nodes[n].get("mean_ps", 0.0))
            for n in nodes_in_comm
        ]
        ps_nonzero = [v for v in ps_vals if v != 0.0]
        mean_ps = float(np.mean(ps_nonzero)) if ps_nonzero else 0.0

        for node in nodes_in_comm:
            community_map[node] = idx
        community_summary.append({
            "community_id": idx,
            "size": len(comm),
            "mean_signal": round(mean_ps, 4),
            "words_sample": ", ".join(words[:10]),
            "wordnum_range": f"{min(wordnums)}-{max(wordnums)}" if wordnums else "",
        })

    return community_map, community_summary, round(modularity_score, 4)


# ---------------------------------------------------------------------------
# K-core decomposition (in, out, total)
# ---------------------------------------------------------------------------

def _kcore_by_degree(G, mode="total"):
    """
    K-core decomposition custom para grafos dirigidos.

    mode: 'in', 'out', o 'total'.
    Retorna dict {node: core_number}.
    """
    if mode == "in":
        degree_func = G.in_degree
    elif mode == "out":
        degree_func = G.out_degree
    else:
        degree_func = G.degree

    core = {}
    remaining = set(G.nodes())
    if not remaining:
        return core

    current_k = 0
    deg = {n: degree_func(n) for n in remaining}

    while remaining:
        min_deg = min(deg.values())
        current_k = max(current_k, min_deg)

        changed = True
        while changed:
            changed = False
            to_remove = [n for n in list(remaining) if deg.get(n, 0) < current_k]
            if to_remove:
                changed = True
                for n in to_remove:
                    remaining.discard(n)
                deg = {n: degree_func(n) for n in remaining}

        for n in remaining:
            core[n] = current_k

        if not remaining:
            break
        current_k += 1
        deg = {n: degree_func(n) for n in remaining}

    return core


def compute_kcore_decomposition(G):
    """
    K-core decomposition por in-degree, out-degree y total.

    Retorna dict con tres sub-dicts y un DataFrame combinado.
    """
    kcore_in = _kcore_by_degree(G, "in")
    kcore_out = _kcore_by_degree(G, "out")
    kcore_total = _kcore_by_degree(G, "total")

    rows = []
    for n in G.nodes():
        rows.append({
            "node_id": n,
            "word": G.nodes[n].get("word", ""),
            "wordnum": G.nodes[n].get("wordnum", 0),
            "kcore_in": kcore_in.get(n, 0),
            "kcore_out": kcore_out.get(n, 0),
            "kcore_total": kcore_total.get(n, 0),
        })

    return {
        "in": kcore_in,
        "out": kcore_out,
        "total": kcore_total,
    }, pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Centralidades
# ---------------------------------------------------------------------------

def compute_all_centralities(G):
    """
    Calcula todas las centralidades disponibles para un DiGraph.

    Centralidades calculadas:
      - degree (total)
      - in_degree
      - out_degree
      - betweenness
      - closeness
      - pagerank (ponderado por mean_dps_abs)
      - eigenvector (fallback a Graph.to_undirected() si falla en DiGraph)

    Retorna dict {centrality_name: {node: value}} y DataFrame combinado.
    """
    centralities = {}

    # Degree centrality (total, in, out)
    centralities["degree"] = nx.degree_centrality(G)
    centralities["in_degree"] = nx.in_degree_centrality(G)
    centralities["out_degree"] = nx.out_degree_centrality(G)

    # Betweenness centrality
    centralities["betweenness"] = nx.betweenness_centrality(
        G, weight="mean_dps_abs", normalized=True
    )

    # Closeness centrality
    centralities["closeness"] = nx.closeness_centrality(G)

    # PageRank
    weight_attr = "mean_dps_abs" if G.number_of_edges() > 0 else None
    centralities["pagerank"] = nx.pagerank(
        G, weight=weight_attr, alpha=0.85
    )

    # Eigenvector centrality — fallback a undirected si falla
    try:
        centralities["eigenvector"] = nx.eigenvector_centrality(
            G, max_iter=1000, tol=1e-06
        )
    except nx.PowerIterationFailedConvergence:
        try:
            G_undirected = G.to_undirected()
            centralities["eigenvector"] = nx.eigenvector_centrality(
                G_undirected, max_iter=1000, tol=1e-06
            )
        except Exception:
            centralities["eigenvector"] = {n: 0.0 for n in G.nodes()}

    # Construir DataFrame
    rows = []
    for n in G.nodes():
        row = {
            "node_id": n,
            "word": G.nodes[n].get("word", ""),
            "wordnum": G.nodes[n].get("wordnum", 0),
            "sentnum": G.nodes[n].get("sentnum", 1),
        }
        for cname, cdict in centralities.items():
            row[cname] = round(cdict.get(n, 0.0), 6)
        rows.append(row)

    return centralities, pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------

def build_centrality_rankings(centrality_dict, top_n=10):
    """
    Construye rankings top-N por cada centralidad.

    Retorna DataFrame con columnas: rank, centrality, node_id, word, value.
    """
    rows = []
    for cname, cdict in centrality_dict.items():
        sorted_nodes = sorted(cdict.items(), key=lambda x: -x[1])
        for rank, (node, value) in enumerate(sorted_nodes[:top_n], 1):
            rows.append({
                "rank": rank,
                "centrality": cname,
                "node_id": node,
                "word": node.split(":", 1)[1] if ":" in node else node,
                "value": round(value, 6),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Correlaciones entre centralidades
# ---------------------------------------------------------------------------

def compute_centrality_correlations(centrality_dict):
    """
    Matriz de correlación de Spearman entre todas las centralidades.

    Retorna DataFrame con la matriz de correlación.
    """
    if not centrality_dict:
        return pd.DataFrame()

    df = pd.DataFrame(centrality_dict)
    corr_matrix = df.corr(method="spearman")
    return corr_matrix.round(4)
