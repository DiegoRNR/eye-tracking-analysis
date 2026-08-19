"""
network_builder.py

Construcción de la red dirigida ponderada de carga cognitiva y naming de builds.

Modos de aristas:
  - textual:      solo adyacentes lineales (wordnum -> wordnum+1)
  - temporal:     todas las transiciones en orden cronológico
  - refixations:  relecturas de la misma palabra (wordnum == wordnum)
  - regressions:  saltos hacia atrás (wordnum_j < wordnum_i)
"""

from collections import defaultdict

import networkx as nx
import numpy as np

from .data_io import _session_key

_VALID_EDGE_MODES = ("textual", "temporal", "refixations", "regressions")


def build_cogload_network(
    fixations,
    groupby="all",
    text_label="CogLoad Network",
    min_ps_obs=2,
    edge_mode="temporal",
    edge_window=4,
    within_sentence=False,
):
    """
    Construye una red dirigida ponderada de carga cognitiva.

    Nodos: palabras (identificadas por wordnum:word).

    Aristas (modo `edge_mode`):
      - 'textual':      solo w_i -> w_{i+1} adyacentes en el texto.
      - 'temporal':     todas las transiciones en orden cronológico.
      - 'refixations':  solo relecturas: a.wordnum == b.wordnum.
      - 'regressions':  solo backward: b.wordnum < a.wordnum.

    Con --per-sentence, solo se enlazan fijaciones dentro de la misma oración.

    Pesos de arista:
      - mean_dps_abs: media de |PS(b) - PS(a)| entre sesiones
      - mean_dps_signed: media de PS(b) - PS(a) entre sesiones
      - weight: alias de mean_dps_abs (compatibilidad con networkx)
    """
    if edge_mode not in _VALID_EDGE_MODES:
        raise ValueError(
            f"edge_mode inválido: {edge_mode!r}. Use {_VALID_EDGE_MODES}."
        )

    G = nx.DiGraph(name=text_label)

    sessions = defaultdict(list)
    for fix in fixations:
        sessions[_session_key(fix, groupby)].append(fix)

    # --- Nodos ---
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

    # --- Aristas ---
    edge_dps_abs_sum = defaultdict(float)
    edge_dps_signed_sum = defaultdict(float)
    edge_count = defaultdict(int)
    edge_type = {}
    edge_sessions = defaultdict(set)

    for sess_key, fix_list in sessions.items():
        if edge_mode == "textual":
            _build_textual_edges(
                fix_list, sess_key, within_sentence,
                edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
            )
        else:
            _build_temporal_edges(
                fix_list, sess_key, edge_mode, within_sentence,
                edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
            )

    for (u, v), c in edge_count.items():
        mean_dps_abs = edge_dps_abs_sum[(u, v)] / c if c > 0 else 0.0
        mean_dps_signed = edge_dps_signed_sum[(u, v)] / c if c > 0 else 0.0
        G.add_edge(
            u,
            v,
            mean_dps_abs=mean_dps_abs,
            mean_dps_signed=mean_dps_signed,
            weight=mean_dps_abs,
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


def _build_textual_edges(
    fix_list, sess_key, within_sentence,
    edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
):
    """
    Aristas de adyacencia textual: solo wordnum -> wordnum+1.

    Solo crea aristas entre palabras consecutivas en el orden del texto.
    No refleja la navegación del lector; representa la estructura lineal.
    """
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

    for _, items in sentence_iter:
        items.sort(key=lambda f: (f["wordnum"], f["fixid"]))
        seen_pairs = set()

        # Construir mapa wordnum -> word (primer fixid)
        word_map = {}
        for f in items:
            wn = f["wordnum"]
            if wn not in word_map:
                word_map[wn] = f"{wn}:{f['word']}"

        # Crear aristas solo entre wordnum consecutivos
        sorted_wordnums = sorted(word_map.keys())
        for i in range(len(sorted_wordnums) - 1):
            wn_a = sorted_wordnums[i]
            wn_b = sorted_wordnums[i + 1]
            if wn_b != wn_a + 1:
                continue
            u = word_map[wn_a]
            v = word_map[wn_b]
            if (u, v) in seen_pairs:
                continue
            seen_pairs.add((u, v))

            # Usar PS promedio de cada palabra para el delta
            ps_a = np.mean([f["ps"] for f in items if f["wordnum"] == wn_a and f["ps"] > 0])
            ps_b = np.mean([f["ps"] for f in items if f["wordnum"] == wn_b and f["ps"] > 0])

            # Crear fijaciones dummy para _add_edge
            a_dummy = {"ps": ps_a}
            b_dummy = {"ps": ps_b}
            _add_edge(u, v, a_dummy, b_dummy, sess_key, "forward",
                      edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions)


def _build_temporal_edges(
    fix_list, sess_key, edge_mode, within_sentence,
    edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
):
    """
    Aristas en orden temporal cronológico (start), con filtro por modo.

    Filtros por edge_mode:
      - temporal:      sin filtro (todas las transiciones)
      - refixations:   solo a.wordnum == b.wordnum
      - regressions:   solo b.wordnum < a.wordnum
    """
    fix_list_sorted = sorted(fix_list, key=lambda f: f["start"])

    if within_sentence:
        current_sentence = None
        sentence_buffer = []
        for f in fix_list_sorted:
            if f["sentnum"] != current_sentence:
                if sentence_buffer:
                    _process_temporal_pairs(
                        sentence_buffer, sess_key, edge_mode,
                        edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
                    )
                sentence_buffer = [f]
                current_sentence = f["sentnum"]
            else:
                sentence_buffer.append(f)
        if sentence_buffer:
            _process_temporal_pairs(
                sentence_buffer, sess_key, edge_mode,
                edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
            )
    else:
        _process_temporal_pairs(
            fix_list_sorted, sess_key, edge_mode,
            edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
        )


def _process_temporal_pairs(
    items, sess_key, edge_mode,
    edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions,
):
    """Procesa pares consecutivos en orden temporal, aplicando filtro por modo."""
    seen_pairs = set()
    for i in range(len(items) - 1):
        a = items[i]
        b = items[i + 1]
        if a["ps"] <= 0 or b["ps"] <= 0:
            continue
        u = f"{a['wordnum']}:{a['word']}"
        v = f"{b['wordnum']}:{b['word']}"

        # Para refixations, permitir self-loops (misma palabra visitada de nuevo)
        if edge_mode != "refixations" and u == v:
            continue

        if (u, v) in seen_pairs:
            continue

        # Filtro por modo
        if edge_mode == "refixations" and a["wordnum"] != b["wordnum"]:
            continue
        if edge_mode == "regressions" and b["wordnum"] >= a["wordnum"]:
            continue
        # temporal: sin filtro adicional

        seen_pairs.add((u, v))

        if b["wordnum"] > a["wordnum"]:
            etype = "forward"
        elif b["wordnum"] < a["wordnum"]:
            etype = "regression"
        else:
            etype = "same-word"

        _add_edge(u, v, a, b, sess_key, etype,
                  edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions)


def _add_edge(u, v, a, b, sess_key, etype,
              edge_dps_abs_sum, edge_dps_signed_sum, edge_count, edge_type, edge_sessions):
    """Agrega una arista a los acumuladores."""
    delta_signed = b["ps"] - a["ps"]
    delta_abs = abs(delta_signed)
    edge_dps_abs_sum[(u, v)] += delta_abs
    edge_dps_signed_sum[(u, v)] += delta_signed
    edge_count[(u, v)] += 1
    edge_sessions[(u, v)].add(sess_key)
    edge_type[(u, v)] = etype


def build_prefix(args, within_sentence=False):
    """Genera el prefijo del build a partir de los argumentos del CLI."""
    parts = [f"cogload_trial{args.trialid}"]
    parts.append(f"w{args.wave}")
    parts.append(args.normalize)
    if args.edge_mode == "temporal" and args.edge_window != 4:
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
