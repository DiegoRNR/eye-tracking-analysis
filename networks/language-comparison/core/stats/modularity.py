"""
modularity.py

Comunidades de la red vía modularidad del esfuerzo (z-score de PS por
comunidad).
"""

import networkx as nx
import numpy as np

from ._common import _signal_field


def compute_effort_modularity(G, z_threshold=0.5):
    """
    Calcula la modularidad del esfuerzo usando greedy_modularity_communities.

    Usa `mean_ps_z` por nodo si está disponible, en caso contrario cae a
    `mean_ps` crudo. Etiqueta cada nodo con community_id y community_label
    según el z-score medio de la comunidad:
        high_stress  si mean_zscore > +z_threshold
        low_stress   si mean_zscore < -z_threshold
        neutral      en otro caso

    Devuelve además, por comunidad, mean_sentnum y sentnum_std.
    """
    if G.number_of_nodes() == 0:
        return [], 0.0

    if G.number_of_edges() == 0:
        communities = [set(G.nodes)]
        modularity_score = 0.0
    else:
        communities = list(
            nx.community.greedy_modularity_communities(G, weight="weight")
        )
        modularity_score = nx.community.modularity(G, communities, weight="weight")

    signal_key = _signal_field(G)
    has_z = signal_key == "mean_ps_z"
    if has_z:
        all_signal = [
            d.get("mean_ps_z", 0.0) for _, d in G.nodes(data=True)
        ]
    else:
        all_signal = [
            d.get("mean_ps", 0.0) for _, d in G.nodes(data=True) if d.get("mean_ps", 0) > 0
        ]
    global_mean = float(np.mean(all_signal)) if all_signal else 0.0
    global_std = float(np.std(all_signal, ddof=0)) if len(all_signal) > 1 else 0.0

    community_summary = []
    for idx, comm in enumerate(communities):
        sig_vals = [
            G.nodes[n].get(signal_key, 0.0)
            for n in comm
            if G.nodes[n].get(signal_key, 0) > 0
            or (signal_key == "mean_ps_z" and G.nodes[n].get(signal_key, 0) != 0.0)
        ]
        mean_sig = float(np.mean(sig_vals)) if sig_vals else 0.0
        z = (mean_sig - global_mean) / global_std if global_std > 0 else 0.0
        if z > z_threshold:
            label = "high_stress"
        elif z < -z_threshold:
            label = "low_stress"
        else:
            label = "neutral"
        for n in comm:
            G.nodes[n]["community_id"] = idx
            G.nodes[n]["community_label"] = label
        dps_vals = [
            d.get("mean_dps", 0.0)
            for u, v, d in G.edges(data=True)
            if u in comm and v in comm
        ]
        sentnums = [
            G.nodes[n].get("sentnum", 1) for n in comm if G.nodes[n].get("sentnum", 1) > 0
        ]
        mean_sentnum = float(np.mean(sentnums)) if sentnums else 0.0
        sentnum_std = float(np.std(sentnums, ddof=0)) if len(sentnums) > 1 else 0.0
        community_summary.append(
            {
                "community_id": idx,
                "label": label,
                "size": len(comm),
                "mean_signal": round(mean_sig, 4),
                "z_score": round(z, 4),
                "mean_internal_dps": round(float(np.mean(dps_vals)) if dps_vals else 0.0, 4),
                "mean_sentnum": round(mean_sentnum, 2),
                "sentnum_std": round(sentnum_std, 4),
            }
        )

    return community_summary, modularity_score
