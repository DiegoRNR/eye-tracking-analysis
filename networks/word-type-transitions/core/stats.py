"""
networks/word-type-transitions/core/stats.py

Estadística de contraste entre condiciones:
- Test de permutación por arista (emparejado por sujeto cuando hay ≥5 pares
  comunes: sign-flip; si no, permutación independiente), N_PERM=2000.
- Corrección Benjamini–Hochberg (FDR).
- Métricas de red por condición: densidad, PageRank, in/out strength.
"""

from __future__ import annotations

from typing import Dict, Tuple

import networkx as nx
import numpy as np
import pandas as pd

N_PERM = 2000
RNG_SEED = 20260928


def perm_test(a: pd.Series, b: pd.Series) -> Tuple[float, float, str, int]:
    """
    a, b: valores por sujeto (índice = uniform_id), NaN = ausente.
    Retorna (media_diff_a_minus_b, p_value, tipo_test, n_usado).
    """
    av, bv = a.dropna(), b.dropna()
    if len(av) < 4 or len(bv) < 4:
        return (np.nan, np.nan, "insufficient_n", 0)
    common = av.index.intersection(bv.index)
    rng = np.random.default_rng(RNG_SEED)
    if len(common) >= 5:
        d = av.loc[common].values - bv.loc[common].values
        obs = float(d.mean())
        n = len(d)
        signs = rng.choice([-1.0, 1.0], size=(N_PERM, n))
        null = (signs * d).mean(axis=1)
        return obs, float((np.abs(null) >= abs(obs)).mean()), "paired_signflip", n
    obs = float(av.mean() - bv.mean())
    pool = np.concatenate([av.values, bv.values])
    na = len(av)
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        p = rng.permutation(pool)
        null[i] = p[:na].mean() - p[na:].mean()
    return obs, float((np.abs(null) >= abs(obs)).mean()), "independent", min(len(av), len(bv))


def bh_adjust(pvals: pd.Series) -> pd.Series:
    """
    Benjamini–Hochberg step-up: adj_i = min_{j>=i} (p_j · m / j) sobre los p
    ordenados ascendentemente (monótona desde el mayor hacia el menor).
    """
    p = pvals.dropna()
    if p.empty:
        return pvals
    order = p.sort_values()  # ascendente
    m = len(order)
    scaled = order * m / np.arange(1, m + 1)
    adj_sorted = scaled[::-1].cummin()[::-1].clip(0, 1)  # running min desde el final
    return adj_sorted.reindex(p.index).reindex(pvals.index)


def compare_conditions(
    pp_a: pd.DataFrame, pp_b: pd.DataFrame, label_a: str, label_b: str
) -> pd.DataFrame:
    """
    Compara dos condiciones arista a arista sobre las matrices per-participant.
    diff = media_A − media_B; p por permutación; BH-FDR.
    """
    edges = sorted(set(pp_a.columns) | set(pp_b.columns))
    rows = []
    for e in edges:
        a = pp_a[e] if e in pp_a.columns else pd.Series(np.nan, index=pp_a.index)
        b = pp_b[e] if e in pp_b.columns else pd.Series(np.nan, index=pp_b.index)
        diff, p, test, n = perm_test(a, b)
        rows.append(
            {
                "edge": e,
                f"mean_{label_a}": float(a.mean()) if a.notna().any() else np.nan,
                f"mean_{label_b}": float(b.mean()) if b.notna().any() else np.nan,
                "diff": diff,
                "p_perm": p,
                "test": test,
                "n_used": n,
                f"n_{label_a}": int(a.notna().sum()),
                f"n_{label_b}": int(b.notna().sum()),
            }
        )
    df = pd.DataFrame(rows)
    df["p_bh"] = bh_adjust(df["p_perm"]).values
    df["significant_fdr_0.05"] = df["p_bh"] < 0.05
    return df


def graph_metrics(matrix: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """PageRank, in/out strength por nodo y densidad del grafo dirigido ponderado."""
    G = nx.DiGraph()
    G.add_nodes_from(matrix.index)
    for u in matrix.index:
        for v in matrix.columns:
            w = float(matrix.loc[u, v])
            if u != v and w > 0:
                G.add_edge(u, v, weight=w)
    density = nx.density(G)
    if G.number_of_edges():
        pr = nx.pagerank(G, weight="weight")
    else:
        pr = {n: 0.0 for n in G.nodes}
    df = pd.DataFrame(
        {
            "pagerank": pr,
            "in_strength": {n: G.in_degree(n, weight="weight") for n in G.nodes},
            "out_strength": {n: G.out_degree(n, weight="weight") for n in G.nodes},
        }
    )
    df.index.name = "node"
    return df, density
