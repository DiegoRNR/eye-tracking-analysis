"""
metrics.py

Métricas a nivel de nodo y de red para la red de carga cognitiva.
"""

import numpy as np

from ._common import _signal_field


def compute_cogload_metrics(G, top_decile=0.10):
    """
    Calcula métricas a nivel de nodo y de red para la red de carga cognitiva.

    Usa los z-scores de PS por sesión (`mean_ps_z`) como señal primaria de carga.
    Los nodos con `mean_ps_z` no calculado (normalización desactivada) caen
    todos a 0, en cuyo caso se hace fallback a `mean_ps`.

    Métricas por nodo añadidas a G:
        strength_in, strength_out, ps_zscore, is_ps_peak
    """
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    if n_nodes == 0:
        return {}

    max_possible = n_nodes * (n_nodes - 1)
    density = (n_edges / max_possible) if max_possible > 0 else 0.0

    in_strength = {n: 0.0 for n in G.nodes}
    out_strength = {n: 0.0 for n in G.nodes}
    for u, v, d in G.edges(data=True):
        w = d.get("mean_dps", 0.0)
        out_strength[u] += w
        in_strength[v] += w

    signal_key = _signal_field(G)
    ps_values = np.array(
        [d.get(signal_key, 0.0) for _, d in G.nodes(data=True)], dtype=float
    )
    ps_nonzero = ps_values[ps_values > 0] if signal_key == "mean_ps" else ps_values
    if ps_nonzero.size > 0:
        ps_mean = float(np.mean(ps_nonzero))
        ps_std = float(np.std(ps_nonzero, ddof=0)) if ps_nonzero.size > 1 else 0.0
    else:
        ps_mean, ps_std = 0.0, 0.0

    raw_ps_values = np.array(
        [d.get("mean_ps", 0.0) for _, d in G.nodes(data=True)], dtype=float
    )
    raw_ps_nonzero = raw_ps_values[raw_ps_values > 0]

    dps_values = np.array(
        [d.get("mean_dps", 0.0) for _, _, d in G.edges(data=True)], dtype=float
    )

    threshold = (
        np.quantile(ps_nonzero, 1 - top_decile) if ps_nonzero.size else 0.0
    )

    for n, d in G.nodes(data=True):
        d["strength_in"] = in_strength.get(n, 0.0)
        d["strength_out"] = out_strength.get(n, 0.0)
        mp = d.get(signal_key, 0.0)
        d["ps_zscore"] = (mp - ps_mean) / ps_std if ps_std > 0 else 0.0
        d["is_ps_peak"] = bool(mp > 0 and mp >= threshold) if signal_key == "mean_ps" else bool(mp >= threshold)

    metrics = {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "density": round(density, 4),
        "signal_field": signal_key,
        "mean_dps": round(float(np.mean(dps_values)) if dps_values.size else 0.0, 4),
        "max_dps": round(float(np.max(dps_values)) if dps_values.size else 0.0, 4),
        "mean_signal": round(ps_mean, 4),
        "signal_std": round(ps_std, 4),
        "signal_range": round(
            float(np.ptp(ps_nonzero)) if ps_nonzero.size else 0.0, 4
        ),
        "mean_ps_raw": round(
            float(np.mean(raw_ps_nonzero)) if raw_ps_nonzero.size else 0.0, 4
        ),
        "ps_range_raw": round(
            float(np.ptp(raw_ps_nonzero)) if raw_ps_nonzero.size else 0.0, 4
        ),
        "n_ps_peaks": int(sum(1 for _, d in G.nodes(data=True) if d.get("is_ps_peak"))),
    }
    return metrics
