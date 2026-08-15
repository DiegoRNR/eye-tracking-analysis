"""
network_builder.py

Construcción de la red dirigida de regresiones.

A diferencia de cognitive-load / language-comparison, el scanpath se
reconstruye en **orden temporal** (`start`), no por posición en el texto. Eso
es lo que permite que existan aristas hacia atrás.

Tipado de arista:
  forward            v.wordnum > u.wordnum
  regression-local   v.wordnum < u.wordnum, misma oración
  regression-global  v.wordnum < u.wordnum, cruza frontera de oración

Las refijaciones (v.wordnum == u.wordnum) NO generan self-loop: se acumulan
como atributo de nodo `n_refix`, para no distorsionar los grados.
"""

from collections import defaultdict

import networkx as nx
import numpy as np


def reconstruct_scanpath(fixations):
    """
    Agrupa las fijaciones por sesión y las ordena en orden temporal.

    Retorna dict {session_id: [fijaciones ordenadas por (start, fixid)]}.
    """
    sessions = defaultdict(list)
    for f in fixations:
        sessions[f["session_id"]].append(f)
    for items in sessions.values():
        items.sort(key=lambda f: (f["start"], f["fixid"]))
    return dict(sessions)


def classify_saccade(a, b):
    """
    Clasifica la sacada a → b.

    Retorna 'refixation', 'forward', 'regression-local' o 'regression-global'.
    """
    if b["wordnum"] == a["wordnum"]:
        return "refixation"
    if b["wordnum"] > a["wordnum"]:
        return "forward"
    return "regression-local" if b["sentnum"] == a["sentnum"] else "regression-global"


def build_regression_network(
    fixations,
    min_rate=0.02,
    text_label="Regression Network",
):
    """
    Construye el DiGraph tipado a partir de las fijaciones de un grupo.

    `min_rate`: poda las aristas soportadas por menos de esa fracción de
    lectores. Con 0 no se poda.

    Retorna (G, report) donde `report` resume conteos y la concordancia con las
    columnas `word.reg.*` de MECO.
    """
    sessions = reconstruct_scanpath(fixations)
    n_participants = len(sessions)
    if n_participants == 0:
        return nx.DiGraph(name=text_label), {}

    node_fix = defaultdict(int)
    node_dwell = defaultdict(float)
    node_refix = defaultdict(int)
    node_reg_in = defaultdict(int)
    node_reg_out = defaultdict(int)
    node_first_pass = defaultdict(float)
    node_ps = defaultdict(list)
    node_sessions = defaultdict(set)
    node_meta = {}

    edge_count = defaultdict(int)
    edge_sessions = defaultdict(set)
    edge_amp = defaultdict(list)
    edge_dur_target = defaultdict(list)
    edge_type = {}

    scan_reg_pairs = set()
    meco_reg_pairs = set()
    n_refix_total = 0
    type_counts = defaultdict(int)

    for sid, items in sessions.items():
        for f in items:
            nid = f"{f['wordnum']}:{f['word']}"
            node_meta.setdefault(
                nid,
                {
                    "word": f["word"],
                    "wordnum": f["wordnum"],
                    "sentnum": f["sentnum"],
                },
            )
            node_fix[nid] += 1
            node_dwell[nid] += f["dur"]
            node_sessions[nid].add(sid)
            if f["ps"] is not None and f["ps"] > 0:
                node_ps[nid].append(f["ps"])
            if f["run"] == 1:
                node_first_pass[nid] += f["dur"]

            # Regresiones según las columnas propias de MECO (validación cruzada).
            if f["meco_reg_out"] == 1 and f["meco_reg_to"] is not None:
                meco_reg_pairs.add((f["wordnum"], f["meco_reg_to"]))

        for a, b in zip(items[:-1], items[1:]):
            kind = classify_saccade(a, b)
            u = f"{a['wordnum']}:{a['word']}"
            v = f"{b['wordnum']}:{b['word']}"

            if kind == "refixation":
                node_refix[u] += 1
                n_refix_total += 1
                continue

            type_counts[kind] += 1
            if kind.startswith("regression"):
                node_reg_out[u] += 1
                node_reg_in[v] += 1
                scan_reg_pairs.add((a["wordnum"], b["wordnum"]))

            key = (u, v)
            edge_count[key] += 1
            edge_sessions[key].add(sid)
            edge_amp[key].append(abs(b["wordnum"] - a["wordnum"]))
            edge_dur_target[key].append(b["dur"])
            edge_type[key] = kind

    G = nx.DiGraph(name=text_label)

    for nid, meta in node_meta.items():
        ps_vals = node_ps[nid]
        seen = len(node_sessions[nid])
        G.add_node(
            nid,
            word=meta["word"],
            wordnum=meta["wordnum"],
            sentnum=meta["sentnum"],
            fix_count=node_fix[nid],
            dwell_total=round(node_dwell[nid], 2),
            mean_dur=round(node_dwell[nid] / node_fix[nid], 2) if node_fix[nid] else 0.0,
            first_pass_dur=round(node_first_pass[nid], 2),
            n_refix=node_refix[nid],
            refix_rate=round(node_refix[nid] / n_participants, 4),
            reg_in=node_reg_in[nid],
            reg_out=node_reg_out[nid],
            reg_in_rate=round(node_reg_in[nid] / n_participants, 4),
            reg_out_rate=round(node_reg_out[nid] / n_participants, 4),
            n_sessions_seen=seen,
            seen_rate=round(seen / n_participants, 4),
            mean_ps=round(float(np.mean(ps_vals)), 2) if ps_vals else 0.0,
            ps_obs=len(ps_vals),
        )

    n_pruned = 0
    for (u, v), count in edge_count.items():
        n_sessions = len(edge_sessions[(u, v)])
        rate = n_sessions / n_participants
        if rate < min_rate:
            n_pruned += 1
            continue
        G.add_edge(
            u,
            v,
            type=edge_type[(u, v)],
            count=count,
            n_sessions=n_sessions,
            rate=round(rate, 4),
            amplitude=round(float(np.mean(edge_amp[(u, v)])), 2),
            mean_dur_target=round(float(np.mean(edge_dur_target[(u, v)])), 1),
        )

    kept = defaultdict(int)
    for _, _, d in G.edges(data=True):
        kept[d["type"]] += 1

    n_reg_edges = kept["regression-local"] + kept["regression-global"]
    n_sacc = sum(type_counts.values())

    agreement = None
    if scan_reg_pairs and meco_reg_pairs:
        agreement = round(
            len(scan_reg_pairs & meco_reg_pairs) / len(scan_reg_pairs | meco_reg_pairs), 4
        )

    report = {
        "n_participants": n_participants,
        "n_saccades": n_sacc,
        "n_refixations": n_refix_total,
        "refix_share": round(n_refix_total / (n_sacc + n_refix_total), 4) if n_sacc else 0.0,
        "regression_share": round(
            (type_counts["regression-local"] + type_counts["regression-global"]) / n_sacc, 4
        ) if n_sacc else 0.0,
        "n_edges_forward": kept["forward"],
        "n_edges_regression_local": kept["regression-local"],
        "n_edges_regression_global": kept["regression-global"],
        "n_edges_regression": n_reg_edges,
        "n_edges_pruned": n_pruned,
        "reciprocity": round(nx.reciprocity(G), 4) if G.number_of_edges() else 0.0,
        "reg_source_agreement": agreement,
        "min_rate": min_rate,
    }

    G.graph.update(report)

    print(
        f"--> Red de regresiones construida (orden temporal): "
        f"{G.number_of_nodes()} nodos, {G.number_of_edges()} aristas "
        f"({kept['forward']} forward, {n_reg_edges} regresión), "
        f"reciprocidad {report['reciprocity']}"
    )
    if n_pruned:
        print(f"--> {n_pruned} arista(s) podadas por rate < {min_rate}")
    if agreement is not None:
        print(f"--> Concordancia scanpath vs word.reg.* de MECO: {agreement:.3f} (Jaccard)")

    return G, report


def build_prefix(lang_group, trialid, wave, edge_weight, group_langs):
    """
    Genera el prefijo del build.

    Ej: regcomp_trial4_w1_rate_germanic_langs-du-en-ge-no
    """
    parts = [f"regcomp_trial{trialid}", f"w{wave}", edge_weight, str(lang_group)]
    if group_langs:
        parts.append(f"langs-{'-'.join(sorted(group_langs))}")
    return "_".join(parts)
