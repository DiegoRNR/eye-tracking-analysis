"""
networks/scanpath/core/dashboard.py

Colector de datos + generador del dashboard HTML auto-contenido de scanpath.

Dos formas de ver una red de (lang, cuartil, texto):
  - 'w'  palabra: nodos = palabras del texto en layout de mapa de lectura
                  (x = posición en la oración, y = oración).
  - 't'  tipo:    nodos = categorías gramaticales (categoria_gramatical de
                  words_classified.csv), layout de muelle (spring, determinista).

Cada celda serializa nodos, aristas dirigidas pooled y el momento de la PRIMERA
travesía de cada arista (t 0-1) para la animación.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict

import networkx as nx
import pandas as pd

from .data_io import load_l2_accuracy, load_l2_fixations, quartile_groups
from .network_builder import build_text_network
from .paths import CONDITION_LANGS, OUTPUT_DIR, TEXTS
from .visualization import _node_positions

REPO_ROOT = Path(__file__).resolve().parents[3]
WORDS_CLASSIFIED_CSV = REPO_ROOT / "data" / "benchmark" / "words_classified.csv"

CATEGORY_ORDER = [
    "Sustantivo", "Verbo", "Adjetivo", "Adverbio", "Preposición",
    "Artículo", "Conjunción", "Pronombre", "Numeral", "Determinante",
    "Partícula", "Otro",
]
CAT_KEY = {c: i for i, c in enumerate(CATEGORY_ORDER)}

WORDS_CLASSIFIED_CACHE: Dict | None = None


def load_word_classifications() -> Dict[tuple, str]:
    """{(trialid, ianum): categoria_gramatical} — ianum == wordnum."""
    global WORDS_CLASSIFIED_CACHE
    if WORDS_CLASSIFIED_CACHE is None:
        df = pd.read_csv(
            WORDS_CLASSIFIED_CSV,
            usecols=["trialid", "ianum", "categoria_gramatical"],
        )
        df = df.dropna(subset=["trialid", "ianum", "categoria_gramatical"])
        WORDS_CLASSIFIED_CACHE = {
            (int(t), int(i)): str(c)
            for t, i, c in zip(df["trialid"], df["ianum"], df["categoria_gramatical"])
        }
    return WORDS_CLASSIFIED_CACHE


def _first_passage(events) -> dict:
    """Primera travesía por arista: {(u, v): t}."""
    first: dict = {}
    for e in events:
        key = (e["u"], e["v"])
        if key not in first or e["t"] < first[key]:
            first[key] = e["t"]
    return first


def serialize_word_cell(res: dict, textid: int) -> dict:
    """Celda grano 'palabra' para el dashboard."""
    G = res["G"]
    pos, _rows, _maxdx = _node_positions(G)

    nodes = []
    idx: Dict[str, int] = {}
    for n, d in G.nodes(data=True):
        idx[n] = len(nodes)
        nodes.append([
            d.get("word", n),                 # 0 palabra
            int(d.get("wordnum", 0)),         # 1 wordnum
            int(d.get("sentnum", 1)),         # 2 sentnum
            int(d.get("fix_count", 0)),       # 3 fijaciones
            round(float(d.get("mean_ps", 0.0)), 1) if d.get("ps_obs", 0) > 0 else None,  # 4 ps
            round(float(d.get("mean_dur", 0.0))),  # 5 dur ms
            round(pos[n][0], 1),              # 6 x
            round(pos[n][1], 1),              # 7 y
        ])

    first = _first_passage(res["events"])
    edges = []
    for u, v, d in G.edges(data=True):
        e_first = first.get((u, v), None)
        edges.append([
            idx[u], idx[v],
            int(d.get("count", 1)),           # 2 transiciones
            round(float(e_first), 4) if e_first is not None else None,  # 3 primera travesía
        ])

    return {
        "tn": textid,
        "n": res["n_subjects"],
        "nt": res["n_transitions"],
        "nw": len(nodes),
        "ne": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def serialize_type_cell(res: dict, textid: int, wordcat: Dict[tuple, str]) -> dict:
    """
    Celda grano 'tipo': transiciones agregadas entre categorías gramaticales.
    Layout de muelle (spring, determinista) calculado offline.
    """
    G = res["G"]

    # (categoría → stats) y aristas tipo→tipo
    cat_stats = {}
    type_pairs: Dict[tuple, dict] = {}
    first = _first_passage(res["events"])

    for n, d in G.nodes(data=True):
        wordnum = int(d.get("wordnum", 0))
        cat = wordcat.get((textid, wordnum), "Otro")
        st = cat_stats.setdefault(
            cat, {"fc": 0, "ps_sum": 0.0, "ps_n": 0, "nw": 0}
        )
        st["fc"] += int(d.get("fix_count", 0))
        if d.get("ps_obs", 0) > 0:
            st["ps_sum"] += float(d.get("mean_ps", 0.0)) * int(d["ps_obs"])
            st["ps_n"] += int(d["ps_obs"])
        st["nw"] += 1

    for (u, v) in G.edges:
        wu = int(G.nodes[u]["wordnum"])
        wv = int(G.nodes[v]["wordnum"])
        cu = wordcat.get((textid, wu), "Otro")
        cv = wordcat.get((textid, wv), "Otro")
        count = int(G.edges[u, v].get("count", 1))
        is_reg = wv < wu
        tp = type_pairs.setdefault((cu, cv), {"n_f": 0, "n_r": 0, "t": None})
        tp["n_r" if is_reg else "n_f"] += count
        tf = first.get((u, v))
        if tf is not None and (tp["t"] is None or tf < tp["t"]):
            tp["t"] = tf

    nodes = []
    idx = {}
    for cat in CATEGORY_ORDER:
        if cat not in cat_stats:
            continue
        st = cat_stats[cat]
        idx[cat] = len(nodes)
        nodes.append([
            cat,                                                     # 0 categoría
            st["fc"],                                                # 1 fijaciones
            round(st["ps_sum"] / st["ps_n"], 1) if st["ps_n"] else None,  # 2 ps
            st["nw"],                                                # 3 palabras
            None,                                                    # 4 x (spring)
            None,                                                    # 5 y (spring)
        ])

    edges = []
    for (cu, cv), tp in type_pairs.items():
        edges.append([
            idx[cu], idx[cv],
            tp["n_f"] + tp["n_r"],                    # 2 transiciones
            round(tp["t"], 4) if tp["t"] is not None else None,  # 3 primera travesía
            1 if tp["n_r"] > tp["n_f"] else 0,        # 4 regresión dominante
        ])

    # layout de muelle determinista sobre la red agregada de tipos
    Gt = nx.DiGraph()
    for i, nd in enumerate(nodes):
        Gt.add_node(i, weight=max(1, nd[1]))
    for (cu, cv), tp in type_pairs.items():
        Gt.add_edge(idx[cu], idx[cv], weight=max(1, tp["n_f"] + tp["n_r"]))
    k = 1.6 / max(1.0, len(nodes) ** 0.5)
    pos = nx.spring_layout(Gt, seed=42, k=k, iterations=300, weight="weight")
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    xs0, ys0 = min(xs), min(ys)
    dx = (max(xs) - xs0) or 1.0
    dy = (max(ys) - ys0) or 1.0
    for i, nd in enumerate(nodes):
        nd[4] = round((pos[i][0] - xs0) / dx * 1000, 1)
        nd[5] = round((pos[i][1] - ys0) / dy * 800, 1)

    return {
        "tn": textid,
        "n": res["n_subjects"],
        "nt": sum(e[2] for e in edges),
        "nw": len(nodes),
        "ne": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def collect(langs, quartiles=("Q1", "Q4")) -> dict:
    """Colecta todas las celdas (grano palabra y tipo) de las lenguas dadas."""
    cat = load_word_classifications()
    data = {
        "cats": CATEGORY_ORDER,
        "langs": {},
        "cells": {},
        "tcells": {},
    }
    for lang in langs:
        try:
            acc = load_l2_accuracy(lang)
        except FileNotFoundError:
            print(f"[dash] {lang}: sin accuracy — omitido")
            continue
        groups, gsum = quartile_groups(acc)
        if not gsum.get("split"):
            print(
                f"[dash] {lang}: cuartiles no disponibles (n={gsum.get('n_total', 0)}) — omitido"
            )
            continue
        data["langs"][lang] = {
            "n_Q1": gsum["n_Q1"], "n_Q4": gsum["n_Q4"],
            "q25": round(gsum["q25"], 3), "q75": round(gsum["q75"], 3),
        }
        print(f"[dash] {lang}: Q1={gsum['n_Q1']} Q4={gsum['n_Q4']}")
        try:
            fix_all = load_l2_fixations(lang)
        except FileNotFoundError:
            continue
        for quartile in quartiles:
            subjects = {u for u, g in groups.items() if g == quartile}
            fix_q = fix_all[fix_all["uniform_id"].isin(subjects)]
            for tn in TEXTS:
                fix_t = fix_q[fix_q["textid"] == tn]
                if fix_t.empty:
                    continue
                res = build_text_network(fix_t, text_label=f"dash_{lang}_{quartile}_t{tn}")
                if res["G"].number_of_nodes() == 0:
                    continue
                key = f"{lang}|{quartile}|{tn}"
                data["cells"][key] = serialize_word_cell(res, tn)
                data["tcells"][key] = serialize_type_cell(res, tn, cat)
    return data


def generate_dashboard(langs: list[str] | None = None, out_name: str = "scanpath_dashboard.html") -> Path:
    """Genera el HTML auto-contenido con el JSON embebido."""
    if langs is None:
        langs = list(CONDITION_LANGS)
    data = collect(langs)

    template_path = Path(__file__).resolve().parent / "dashboard_template.html"
    template = template_path.read_text(encoding="utf-8")
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    html = template.replace("__DATA__", blob)

    out = OUTPUT_DIR / out_name
    out.write_text(html, encoding="utf-8")
    mb = out.stat().st_size / 1e6
    print(f"[dash] escrito {out} ({mb:.1f} MB · {len(data['cells'])} celdas)")
    return out
