"""
networks/word-type-transitions/core/network_builder.py

Construcción de redes de transición entre tipos de palabra para el diseño
2×2 por grupo lingüístico: {L1 nativo, L2 inglés} × {Q1 peor, Q4 mejor}.

Para cada condición (session-lang-quartile) y modo (temporal/regression):
- Fijaciones 'in' de los sujetos del cuartil, secuencias por sujeto×texto con
  ruptura en parpadeos.
- temporal: todas las transiciones consecutivas (auto-bucles incluidos).
  regression: solo target wordnum < source wordnum.
- Por sujeto: matriz de PROBABILIDADES (fila normalizada) agregando textos.
- Red de grupo: conteos POOLED fila-normalizados.
- Atributos de nodo (carga cognitiva = duración): mean_dur (duración media de
  fijación), dwell_share (proporción de dwell total), n_fix — por sujeto y
  promediados en el grupo (media y mediana).

Eventos temporales: `condition_events()` expone cada transición individual
(par de fijaciones consecutivas) con t = posición de la fijación destino
dentro de su lectura (uniform_id × textid), normalizada 0-1. Alimenta la
animación temporal (temporal_viz.py).
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .data_io import load_accuracy, load_fixations, load_type_map
from .grouping import quartile_groups
from .label_map import FUSED_ORDER
from .paths import (
    CH_VARIANTS,
    CONDITION_LANGS,
    LANGS_W1,
    MIN_GROUP_N,
    MODES,
    QUARTILES,
    SESSIONS,
)


def _probability_matrix(counter: Counter) -> Dict[Tuple[str, str], float]:
    """Normaliza conteos por fila (probabilidad condicional de salida)."""
    row_out = Counter()
    for (u, _), n in counter.items():
        row_out[u] += n
    return {k: n / row_out[k[0]] for k, n in counter.items() if row_out[k[0]]}


def _subject_transitions_and_attrs(
    fix: pd.DataFrame, tmap: Dict[Tuple[int, int], str], mode: str,
    events: List[dict] | None = None,
) -> Tuple[Dict[str, Counter], Dict[str, Dict[str, Dict[str, float]]]]:
    """
    Por uniform_id: (1) conteo de transiciones agregando textos;
    (2) atributos por tipo: n_fix, sum_dur, mean_dur, dwell_share.
    Las fijaciones con blink==1 cortan la secuencia.

    Si `events` es una lista, además registra cada transición individual
    (par de fijaciones consecutivas clasificadas, tras rupturas por blink)
    con t = posición de la fijación destino dentro de la lectura
    (uniform_id × textid), normalizada por el n de fijaciones clasificadas.
    """
    per_par_edges: Dict[str, Counter] = {}
    per_par_nodes: Dict[str, Dict[str, Dict[str, float]]] = {}

    fix = fix.sort_values(["uniform_id", "textid", "start", "fixid"])
    for (uid, _tid), g in fix.groupby(["uniform_id", "textid"], sort=False):
        segs: List[List[Tuple[int, str, float]]] = [[]]
        node_acc = per_par_nodes.setdefault(
            uid, {t: {"n_fix": 0.0, "sum_dur": 0.0} for t in FUSED_ORDER}
        )
        n_mapped = 0
        for r in g.itertuples(index=False):
            if int(r.blink) == 1:
                segs.append([])
                continue
            t = tmap.get((_tid, int(r.wordnum)))
            if t is None:
                continue
            segs[-1].append((int(r.wordnum), t, float(r.dur), int(r.fixid), n_mapped))
            n_mapped += 1
            acc = node_acc.setdefault(t, {"n_fix": 0.0, "sum_dur": 0.0})
            acc["n_fix"] += 1.0
            acc["sum_dur"] += float(r.dur)
        c = Counter()
        for seq in segs:
            for (w1, t1, d1, _f1, _i1), (w2, t2, d2, f2, i2) in zip(seq, seq[1:]):
                if mode == "regression" and w2 >= w1:
                    continue
                c[(t1, t2)] += 1
                if events is not None:
                    events.append(
                        {
                            "u": t1,
                            "v": t2,
                            "t": (i2 + 1) / n_mapped if n_mapped else 0.0,
                            "dur1": d1,
                            "dur2": d2,
                            "uid": uid,
                            "textid": int(_tid),
                            "wordnum1": w1,
                            "wordnum2": w2,
                            "fixid": f2,
                        }
                    )
        if uid in per_par_edges:
            per_par_edges[uid].update(c)
        else:
            per_par_edges[uid] = c

    # derivar mean_dur y dwell_share por sujeto
    for uid, acc in per_par_nodes.items():
        total_dur = sum(a["sum_dur"] for a in acc.values()) or 1.0
        for t, a in acc.items():
            a["mean_dur"] = a["sum_dur"] / a["n_fix"] if a["n_fix"] else np.nan
            a["dwell_share"] = a["sum_dur"] / total_dur if a["sum_dur"] else np.nan
    return per_par_edges, per_par_nodes


def build_condition(session: str, lang: str, quartile: str, mode: str):
    """
    Construye la red de una condición. Retorna dict con:
    group (Series edge->prob), group_matrix (DataFrame NxN),
    per_participant (DataFrame sujeto×arista), node_attrs (DataFrame por nodo),
    summary (dict con n sujetos, etc.).
    """
    tmap = load_type_map(session, lang)
    fix_all = load_fixations(session, lang)
    acc = load_accuracy(session, lang)
    groups, gsum = quartile_groups(acc, min_n=MIN_GROUP_N)
    subjects = [u for u, q in groups.items() if q == quartile]
    fix = fix_all[fix_all["uniform_id"].isin(subjects)]

    per_par_edges, per_par_nodes = _subject_transitions_and_attrs(fix, tmap, mode)

    pooled_counts: Counter = Counter()
    rows = {}
    for uid, c in per_par_edges.items():
        pooled_counts.update(c)
        rows[uid] = {f"{u}->{v}": p for (u, v), p in _probability_matrix(c).items()}
    pp_df = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    pp_df.index.name = "uniform_id"

    pooled_probs = _probability_matrix(pooled_counts)
    nodes = sorted({n for e in pooled_probs for n in e}, key=FUSED_ORDER.index)
    group = pd.Series(
        {f"{u}->{v}": p for (u, v), p in sorted(pooled_probs.items())}, name="transition_prob"
    ).sort_index()
    group.index.name = "edge"

    group_matrix = pd.DataFrame(0.0, index=nodes, columns=nodes)
    for (u, v), p in pooled_probs.items():
        group_matrix.loc[u, v] = p

    # atributos de nodo: media/mediana entre sujetos con observaciones del tipo
    node_rows = []
    for t in nodes:
        vals = [acc_t[t] for acc_t in per_par_nodes.values() if t in acc_t and acc_t[t]["n_fix"] > 0]
        if not vals:
            continue
        mean_durs = [v["mean_dur"] for v in vals]
        shares = [v["dwell_share"] for v in vals]
        nfix = [v["n_fix"] for v in vals]
        node_rows.append(
            {
                "node": t,
                "n_fixations": int(sum(nfix)),
                "mean_dur_ms": float(np.nanmean(mean_durs)),
                "median_dur_ms": float(np.nanmedian(mean_durs)),
                "dwell_share": float(np.nanmean(shares)),
                "n_subjects": len(vals),
            }
        )
    node_attrs = pd.DataFrame(node_rows).set_index("node")

    summary = {
        "n_subjects": len(subjects),
        "n_edges": int(pp_df.shape[1]),
        "group_edges_nonzero": int((group > 0).sum()),
        "acc_quartiles": gsum,
        "mode": mode,
    }
    return {
        "group": group,
        "group_matrix": group_matrix,
        "per_participant": pp_df,
        "node_attrs": node_attrs,
        "pooled_counts": pooled_counts,
        "summary": summary,
        "subjects": subjects,
    }


def build_condition_all_modes(session: str, lang: str, quartile: str):
    return {mode: build_condition(session, lang, quartile, mode) for mode in MODES}


def condition_events(session: str, lang: str, quartile: str, mode: str) -> List[dict]:
    """
    Eventos de transición de los sujetos del cuartil, pooled sobre textos:
    cada transición consecutiva clasificada (misma lógica/ filtros que
    build_condition) con t = progreso de lectura 0-1 de la fijación destino
    dentro de su (uniform_id, textid). Ordenados por (t, uid, textid, fixid).
    """
    tmap = load_type_map(session, lang)
    fix_all = load_fixations(session, lang)
    acc = load_accuracy(session, lang)
    groups, _ = quartile_groups(acc, min_n=MIN_GROUP_N)
    subjects = [u for u, q in groups.items() if q == quartile]
    fix = fix_all[fix_all["uniform_id"].isin(subjects)]

    events: List[dict] = []
    _subject_transitions_and_attrs(fix, tmap, mode, events=events)
    events.sort(key=lambda e: (e["t"], e["uid"], e["textid"], e["fixid"]))
    return events


def iter_conditions():
    """Yield (session, lang, quartile) para todas las combinaciones del diseño."""
    for session in SESSIONS:
        for lang in CONDITION_LANGS:
            for q in QUARTILES:
                yield session, lang, q
