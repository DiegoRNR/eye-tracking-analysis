"""
networks/reading-pattern-mds/core/mds.py

Escalamiento multidimensional CLÁSICO (Torgerson) determinista:
1) D -> D² (squared), doble centrado, auto-descomposición simétrica (eigh).
2) Proyección a 2 componentes con autovalores más grandes (recortados a 0).
3) stress-1 (Kruskal) evaluado con las mismas coordenadas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def classical_mds(dist: pd.DataFrame, n_components: int = 2) -> tuple[pd.DataFrame, float]:
    D = dist.to_numpy(dtype=float)
    n = D.shape[0]
    if n < 2:
        raise ValueError("MDS requiere >= 2 condiciones")
    D2 = D**2
    J = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * J @ D2 @ J
    w, V = np.linalg.eigh(B)
    w = np.clip(w, 0, None)
    idx = np.argsort(w)[::-1][:n_components]
    coords = V[:, idx] * np.sqrt(w[idx])
    if coords.shape[1] < n_components:
        coords = np.hstack([coords, np.zeros((n, n_components - coords.shape[1]))])
    # stress-1 (Kruskal) con distancias de la configuración
    Dm = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    iu = np.triu_indices(n, 1)
    stress = float(np.sqrt(np.sum((D[iu] - Dm[iu]) ** 2) / np.sum(D[iu] ** 2)))
    emb = pd.DataFrame(
        coords[:, :n_components], index=dist.index, columns=["mds1", "mds2"][: coords.shape[1]]
    )
    return emb, stress
