"""
networks/reading-pattern-mds/core/distances.py

Distancias por pares entre perfiles de condiciones:
- Jensen–Shannon: sqrt(JSD) es una métrica verdadera; masa sobre aristas
  alineadas por unión (falta = 0).
Matrices escritas como CSV (distances/dist_<variant>.csv).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import paths


def js_distance(v: np.ndarray, w: np.ndarray) -> float:
    """Distancia J-S (sqrt) entre dos distribuciones (misma base, suman 1)."""
    p, q = v, w
    m = 0.5 * (p + q)
    def _kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))
    jsd = 0.5 * _kl(p, m) + 0.5 * _kl(q, m)
    return float(np.sqrt(max(jsd, 0.0)))


def pairwise_js_matrix(profile_df: pd.DataFrame, conditions: list[str]) -> pd.DataFrame:
    """
    profile_df: condición × arista (cada fila ~ suma 1).
    Retorna matriz cuadrada de distancia J-S entre las condiciones pedidas.
    """
    M = profile_df.loc[conditions].to_numpy(dtype=float)
    n = len(conditions)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = js_distance(M[i], M[j])
            D[i, j] = D[j, i] = d
    return pd.DataFrame(D, index=conditions, columns=conditions)


def save_distance_matrix(matrix: pd.DataFrame, name: str, mode: str) -> Path:
    out = paths.distances_dir(mode) / f"dist_{name}.csv"
    matrix.round(6).to_csv(out)
    return out
