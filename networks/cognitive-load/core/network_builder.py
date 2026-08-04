"""
network_builder.py

Construcción de la red dirigida ponderada de carga cognitiva y naming de builds.
"""

from collections import defaultdict

import networkx as nx
import numpy as np

from .data_io import _session_key


def build_cogload_network(
    fixations,
    groupby="all",
    text_label="CogLoad Network",
    min_ps_obs=2,
    edge_mode="sequential",
    edge_window=4,
    within_sentence=False,
):
    """
    Construye una red dirigida ponderada de carga cognitiva a partir de fijaciones.

    Asume que el campo `ps` de cada fijación es un valor numérico de tamaño
    pupilar (average pupil size por fijación, en píxeles de cámara del EyeLink,
    ojo dominante). El pipeline no depende de las unidades específicas
    (px vs mm) ni de si es diámetro vs área — la normalización intra-sesión
    absorbe la línea base. Ver la especificación completa y las citas a
    popEye source en `data/MECO-L2_version-2.2/POPEYE_DATA_SPEC.md`.

    Nodos: palabras (identificadas por wordnum:word), con métricas de PS crudo
    y z-score por sesión (si la normalización fue activada).

    Aristas (modo `edge_mode`):
      - 'sequential' (default): pares adyacentes en el orden de fijación de
        la sesión. Sin el flag --per-sentence, la lista ordenada incluye
        palabras de oraciones distintas, por lo que se enlaza w → w_next
        cruzando fronteras de oración.
      - 'window':                palabra i → i+1, i+2, ..., i+edge_window
                                 (dentro del ámbito de iteración).
      - 'regression':            en modo full-text, pares adyacentes en el
                                 ORDEN TEMPORAL de la sesión (no de texto)
                                 filtrados por b.wordnum < a.wordnum y
                                 b.sentnum < a.sentnum. Esto captura saltos
                                 hacia atrás entre oraciones (que no son
                                 adyacentes en orden de texto).
                                 En modo per-sentence, pares adyacentes en
                                 orden de texto con b.wordnum < a.wordnum
                                 (re-lectura dentro de la oración).

    Alcance de las aristas (parámetro `within_sentence`):
      - False (default): texto completo, se permiten aristas cruzando
        oraciones.
      - True:           aristas restringidas a dentro de la misma oración.

    En todos los modos el peso es la media de |PS(w2) - PS(w1)| entre sesiones.
    """
    if edge_mode not in ("sequential", "window", "regression"):
        raise ValueError(
            f"edge_mode inválido: {edge_mode!r}. Use 'sequential', 'window' o 'regression'."
        )
    G = nx.DiGraph(name=text_label)

    sessions = defaultdict(list)
    for fix in fixations:
        sessions[_session_key(fix, groupby)].append(fix)

    node_data = defaultdict(
        lambda: {
            "word": "",
            "wordnum": 0,
            "sentnum": 1,
            "fix_count": 0,
            "dwell_total": 0.0,
            "ps_list": [],
            "psz_list": [],
        }
    )
    for fix in fixations:
        node_id = f"{fix['wordnum']}:{fix['word']}"
        nd = node_data[node_id]
        nd["word"] = fix["word"]
        nd["wordnum"] = fix["wordnum"]
        nd["sentnum"] = fix["sentnum"]
        nd["fix_count"] += 1
        nd["dwell_total"] += fix["dur"]
        if fix["ps"] > 0:
            nd["ps_list"].append(fix["ps"])
            nd["psz_list"].append(fix.get("ps_z", 0.0))

    for node_id, d in node_data.items():
        ps_list = d["ps_list"]
        psz_list = d["psz_list"]
        obs = len(ps_list)
        mean_ps = float(np.mean(ps_list)) if obs > 0 else 0.0
        ps_std = float(np.std(ps_list, ddof=0)) if obs > 1 else 0.0
        ps_max = float(np.max(ps_list)) if obs > 0 else 0.0
        mean_psz = float(np.mean(psz_list)) if psz_list else 0.0
        psz_std = float(np.std(psz_list, ddof=0)) if len(psz_list) > 1 else 0.0
        psz_max = float(np.max(psz_list)) if psz_list else 0.0
        mean_dur = d["dwell_total"] / d["fix_count"] if d["fix_count"] > 0 else 0.0
        G.add_node(
            node_id,
            word=d["word"],
            wordnum=d["wordnum"],
            sentnum=d["sentnum"],
            fix_count=d["fix_count"],
            dwell_total=d["dwell_total"],
            mean_dur=mean_dur,
            mean_ps=mean_ps,
            ps_std=ps_std,
            ps_max=ps_max,
            ps_obs=obs,
            mean_ps_z=mean_psz,
            ps_z_std=psz_std,
            ps_z_max=psz_max,
        )

    edge_dps_sum = defaultdict(float)
    edge_count = defaultdict(int)
    edge_type = {}
    edge_sessions = defaultdict(set)

    for sess_key, fix_list in sessions.items():
        fix_list_sorted = sorted(
            fix_list, key=lambda f: (f["sentnum"], f["wordnum"], f["fixid"])
        )

        if within_sentence:
            per_sentence = defaultdict(list)
            for f in fix_list_sorted:
                per_sentence[f["sentnum"]].append(f)
            sentence_iter = list(per_sentence.items())
        else:
            sentence_iter = [(None, fix_list_sorted)]

        if edge_mode == "window":
            for _, items in sentence_iter:
                items.sort(key=lambda f: (f["wordnum"], f["fixid"]))
                seen_words = {}
                for f in items:
                    if f["ps"] <= 0:
                        continue
                    wid = f"{f['wordnum']}:{f['word']}"
                    if wid not in seen_words:
                        seen_words[wid] = []
                    seen_words[wid].append(f)
                unique_words = list(seen_words.keys())
                for i, u in enumerate(unique_words):
                    ps_u = np.mean([f["ps"] for f in seen_words[u]])
                    for j in range(i + 1, min(i + 1 + edge_window, len(unique_words))):
                        v = unique_words[j]
                        ps_v = np.mean([f["ps"] for f in seen_words[v]])
                        delta = abs(ps_v - ps_u)
                        edge_dps_sum[(u, v)] += delta
                        edge_count[(u, v)] += 1
                        edge_sessions[(u, v)].add(sess_key)
                        hop = j - i
                        edge_type[(u, v)] = f"forward+{hop}"
            continue

        if edge_mode == "regression" and not within_sentence:
            fix_list_time = sorted(fix_list, key=lambda f: f["start"])
            seen_pairs = set()
            for i in range(len(fix_list_time) - 1):
                a = fix_list_time[i]
                b = fix_list_time[i + 1]
                if a["ps"] <= 0 or b["ps"] <= 0:
                    continue
                u = f"{a['wordnum']}:{a['word']}"
                v = f"{b['wordnum']}:{b['word']}"
                if u == v:
                    continue
                if (u, v) in seen_pairs:
                    continue
                seen_pairs.add((u, v))
                if not (b["wordnum"] < a["wordnum"] and b["sentnum"] < a["sentnum"]):
                    continue
                delta = abs(b["ps"] - a["ps"])
                edge_dps_sum[(u, v)] += delta
                edge_count[(u, v)] += 1
                edge_sessions[(u, v)].add(sess_key)
                edge_type[(u, v)] = "regression"
            continue

        for _, items in sentence_iter:
            items.sort(key=lambda f: (f["wordnum"], f["fixid"]))
            seen_pairs = set()
            for i in range(len(items) - 1):
                a = items[i]
                b = items[i + 1]
                if a["ps"] <= 0 or b["ps"] <= 0:
                    continue
                u = f"{a['wordnum']}:{a['word']}"
                v = f"{b['wordnum']}:{b['word']}"
                if u == v:
                    continue
                if (u, v) in seen_pairs:
                    continue
                seen_pairs.add((u, v))
                if edge_mode == "regression":
                    if not (b["wordnum"] < a["wordnum"] and b["sentnum"] < a["sentnum"]):
                        continue
                delta = abs(b["ps"] - a["ps"])
                edge_dps_sum[(u, v)] += delta
                edge_count[(u, v)] += 1
                edge_sessions[(u, v)].add(sess_key)
                if b["wordnum"] > a["wordnum"]:
                    edge_type[(u, v)] = "forward"
                elif b["wordnum"] < a["wordnum"]:
                    edge_type[(u, v)] = "regression"
                else:
                    edge_type[(u, v)] = "same-word"

    for (u, v), c in edge_count.items():
        mean_dps = edge_dps_sum[(u, v)] / c if c > 0 else 0.0
        G.add_edge(
            u,
            v,
            mean_dps=mean_dps,
            count=c,
            n_sessions=len(edge_sessions[(u, v)]),
            type=edge_type.get((u, v), "forward"),
        )

    G.graph["edge_mode"] = edge_mode
    G.graph["edge_window"] = edge_window
    G.graph["within_sentence"] = within_sentence
    print(
        f"--> Red construida ({edge_mode}, "
        f"{'per-sentence' if within_sentence else 'full-text'}): "
        f"{G.number_of_nodes()} nodos, {G.number_of_edges()} aristas"
    )
    return G


def build_prefix(args, within_sentence=False):
    """Genera el prefijo del build a partir de los argumentos del CLI."""
    parts = [f"cogload_trial{args.trialid}"]
    parts.append(f"w{args.wave}")
    parts.append(args.normalize)
    if args.edge_mode == "window":
        parts.append(f"w{args.edge_window}")
    else:
        parts.append(args.edge_mode)
    if args.lang:
        parts.append(f"lang{args.lang}")
    if args.subid:
        parts.append(f"sub{args.subid}")
    if within_sentence:
        parts.append("persent")
    return "_".join(parts)
