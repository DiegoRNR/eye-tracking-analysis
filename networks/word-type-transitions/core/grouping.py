"""
networks/word-type-transitions/core/grouping.py

División de lectores por comprensión lectora (accuracy) DENTRO de cada grupo
lingüístico: Q1 = peor cuartil (accuracy <= p25), Q4 = mejor cuartil (>= p75).
El centro se descarta para máximo contraste (misma lógica que comp-groups).
"""

from __future__ import annotations

from typing import Dict, Tuple

MIN_GROUP_N = 4  # importado desde paths en network_builder; aquí solo referencia


def quartile_groups(accuracy, min_n: int = 4) -> Tuple[Dict[str, str], Dict]:
    """
    accuracy: pd.Series uniform_id -> accuracy.
    Retorna ({uniform_id: 'Q1'|'Q4'}, summary) — sujetos del centro → None.
    Si el grupo completo tiene n < min_n*2 no se divide (summary lo indica).
    """
    import numpy as np
    import pandas as pd

    acc = pd.Series(accuracy).astype(float).dropna()
    if acc.empty:
        return {}, {"n": 0, "split": False}
    q1, q3 = acc.quantile(0.25), acc.quantile(0.75)
    groups: Dict[str, str] = {}
    for u, v in acc.items():
        if v <= q1:
            groups[u] = "Q1"
        elif v >= q3:
            groups[u] = "Q4"
    n_q1 = sum(1 for v in groups.values() if v == "Q1")
    n_q4 = sum(1 for v in groups.values() if v == "Q4")
    summary = {
        "n_total": int(len(acc)),
        "q25": float(q1),
        "q75": float(q3),
        "n_Q1": n_q1,
        "n_Q4": n_q4,
        "split": n_q1 >= min_n and n_q4 >= min_n,
        "acc_mean_Q1": float(acc[[u for u, g in groups.items() if g == "Q1"]].mean()) if n_q1 else None,
        "acc_mean_Q4": float(acc[[u for u, g in groups.items() if g == "Q4"]].mean()) if n_q4 else None,
    }
    return groups, summary
