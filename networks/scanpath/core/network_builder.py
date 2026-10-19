"""
networks/scanpath/core/network_builder.py

Red de scanpath POR TEXTO (L2), pooled sobre los sujetos de un cuartil.

- Nodos: palabras del texto, id "wordnum:word". Atributos: fix_count,
  mean_dur, mean_ps, sentnum.
- Aristas: transiciones consecutivas del ojo entre palabras (sacadas),
  pooled. Las filas con blink==1 cortan la secuencia (sin transición a
  través de un blink y sin contribuir a nodos). Refijaciones consecutivas
  sobre la MISMA palabra (u == v) NO generan arista.
- Eventos (para la animación): cada transición individual con
  t = posición de la fijación destino dentro de la lectura del texto por
  ese sujeto, normalizada 0-1 sobre el n de fijaciones 'in' no-blink.
"""

from __future__ import annotations

from collections import defaultdict
from typing import List, Tuple

import networkx as nx
import pandas as pd


def build_text_network(fix_text: pd.DataFrame, text_label: str) -> dict:
    """
    fix_text: fijaciones 'in' de UN texto ya filtradas a los sujetos del
    cuartil (columnas de data_io.load_l2_fixations), >= 1 sujeto.

    Retorna dict con:
      G            nx.DiGraph (nodos palabra, aristas con count/type)
      events       [{u, v, t, uid, fixid}] ordenados por (t, uid, fixid)
      n_subjects   sujetos con fijaciones en el texto
      n_transitions
    """
    G = nx.DiGraph(name=text_label)

    node_stats: dict = defaultdict(
        lambda: {
            "word": "",
            "wordnum": 0,
            "sentnum": 1,
            "fix_count": 0,
            "sum_dur": 0.0,
            "ps_sum": 0.0,
            "ps_n": 0,
        }
    )
    edge_count: dict = defaultdict(int)
    edge_type: dict = {}
    events: List[dict] = []
    subjects = set()
    n_transitions = 0

    for uid, g in fix_text.groupby("uniform_id", sort=False):
        subjects.add(uid)

        # secuencia no-blink del sujeto en este texto:
        # (node_id, wordnum, fixid, sentnum)
        seq: List[Tuple[str, int, int, int]] = []
        for r in g.itertuples(index=False):
            if int(r.blink) == 1:
                continue
            word = str(r.word)
            wordnum = int(r.wordnum)
            node_id = f"{wordnum}:{word}"
            seq.append((node_id, wordnum, int(r.fixid), int(r.sentnum)))

            nd = node_stats[node_id]
            nd["word"] = word
            nd["wordnum"] = wordnum
            nd["sentnum"] = int(r.sentnum)
            nd["fix_count"] += 1
            nd["sum_dur"] += float(r.dur)
            ps = float(r.ps)
            if ps > 0:
                nd["ps_sum"] += ps
                nd["ps_n"] += 1

        n_fix = len(seq)
        for i in range(n_fix - 1):
            u, wu, _, _ = seq[i]
            v, wv, f2, _ = seq[i + 1]
            if u == v:
                continue  # refijación consecutiva: sin arista
            edge_count[(u, v)] += 1
            edge_type[(u, v)] = "forward" if wv > wu else "regression"
            n_transitions += 1
            events.append(
                {
                    "u": u,
                    "v": v,
                    "t": (i + 1) / n_fix,
                    "uid": uid,
                    "fixid": f2,
                }
            )

    for node_id, nd in node_stats.items():
        G.add_node(
            node_id,
            word=nd["word"],
            wordnum=nd["wordnum"],
            sentnum=nd["sentnum"],
            fix_count=nd["fix_count"],
            mean_dur=nd["sum_dur"] / nd["fix_count"] if nd["fix_count"] else 0.0,
            mean_ps=nd["ps_sum"] / nd["ps_n"] if nd["ps_n"] else 0.0,
            ps_obs=nd["ps_n"],
        )

    for (u, v), c in edge_count.items():
        G.add_edge(u, v, count=c, weight=c, type=edge_type[(u, v)])

    events.sort(key=lambda e: (e["t"], e["uid"], e["fixid"]))
    G.graph["events"] = events
    return {
        "G": G,
        "events": events,
        "n_subjects": len(subjects),
        "n_transitions": n_transitions,
    }
