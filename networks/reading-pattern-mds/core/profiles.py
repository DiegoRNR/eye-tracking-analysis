"""
networks/reading-pattern-mds/core/profiles.py

Distribuciones de transición pobladas (pooled) por condición, usando la MISMA
lógica de networks/word-type-transitions (importada como `wttcore`):

- Condición FULL: (session, lang) con TODOS los sujetos del grupo.
- Condición QUARTILE: (session, lang, Q1|Q4) con los sujetos del cuartil
  (p25/p75, descartando el centro — igual que word-type-transitions).

Pooled: conteos por sujeto (secuencias por sujeto×texto, ruptura en parpadeos,
filtros idénticos a network_builder._subject_transitions_and_attrs) se suman;
luego fila-normalización (prob. condicional de salida) y normalización global
del vector plano sobre el espacio de aristas  ->  distribución p(u->v).
"""

from __future__ import annotations

from collections import Counter
from typing import Optional

import pandas as pd

from ._wtt import shared


def _subjects_for(session: str, lang: str, quartile: Optional[str]) -> list[str]:
    data_io, _, grouping, _, _ = shared()
    acc = data_io.load_accuracy(session, lang)
    if quartile is None:
        return sorted(acc.index)
    groups, gsum = grouping.quartile_groups(acc)
    if not gsum.get("split"):
        raise RuntimeError(f"{session}-{lang}: cuartiles no disponibles (n insuficiente)")
    return sorted(u for u, q in groups.items() if q == quartile)


def condition_transition_counts(
    session: str, lang: str, mode: str, quartile: Optional[str] = None
) -> Counter:
    """Conteo pooled de transiciones pooled (u, v) de la condición."""
    _, _, _, network_builder, _ = shared()
    data_io, _, _, _, _ = shared()
    subjects = _subjects_for(session, lang, quartile)
    fix_all = data_io.load_fixations(session, lang)
    fix = fix_all[fix_all["uniform_id"].isin(subjects)]
    tmap = data_io.load_type_map(session, lang)
    per_par_edges, _ = network_builder._subject_transitions_and_attrs(fix, tmap, mode)
    pooled: Counter = Counter()
    for _, c in per_par_edges.items():
        pooled.update(c)
    return pooled


def condition_profile(
    session: str, lang: str, mode: str, quartile: Optional[str] = None
) -> pd.Series:
    """
    Vector de distribución p(u->v) de la condición:
    conteos pooled -> prob de fila -> masa global re-normalizada a 1.
    """
    _, _, _, network_builder, _ = shared()
    pooled = condition_transition_counts(session, lang, mode, quartile)
    row_probs = network_builder._probability_matrix(pooled)
    vec = pd.Series({f"{u}->{v}": p for (u, v), p in row_probs.items()}, dtype=float)
    total = vec.sum()
    if not total > 0:
        raise RuntimeError(f"perfil vacío para {session}-{lang}-{quartile} ({mode})")
    vec = vec / total
    vec.index.name = "edge"
    vec.name = condition_name(session, lang, quartile)
    # n de sujetos y fijaciones para QA
    return vec


def condition_name(session: str, lang: str, quartile: Optional[str]) -> str:
    return f"{session}-{lang}" if quartile is None else f"{session}-{lang}-{quartile}"


def build_profiles(mode: str, meta: dict) -> pd.DataFrame:
    """
    Genera TODOS los perfiles necesarios (full + quartile) y escribe
    profiles/profiles_full.csv y profiles/profiles_quartile.csv
    (condición × arista). Los/perfil Referencias en_*/se incluyen si los
    datos existen.
    """
    from . import paths

    _, _, _, _, wtt_paths = shared()
    paths.ensure_dirs(mode)

    langs_full = list(paths.target_langs()) + list(paths.EN_REFS.values())
    profiles_full: dict[str, pd.Series] = {}
    profiles_quart: dict[str, pd.Series] = {}

    for lang in langs_full:
        for session in ("L1", "L2"):
            cond = condition_name(session, lang, None)
            try:
                profiles_full[cond] = condition_profile(session, lang, mode, None)
                meta["profiles"][f"full/{cond}"] = {"ok": True}
            except Exception as e:  # noqa: BLE001 - continúa con el resto
                meta["profiles"][f"full/{cond}"] = {"ok": False, "error": str(e)}
                continue
            for q_col in paths.QUARTILES:
                cond_q = condition_name(session, lang, q_col)
                try:
                    profiles_quart[cond_q] = condition_profile(session, lang, mode, q_col)
                    meta["profiles"][f"q/{cond_q}"] = {"ok": True}
                except Exception as e:  # noqa: BLE001
                    meta["profiles"][f"q/{cond_q}"] = {"ok": False, "error": str(e)}
        n_q = sum(1 for k in profiles_quart if f"-{lang}-" in k)
        n_f = sum(1 for k in profiles_full if f"-{lang}" in k)
        print(
            f"[build] {lang}: full={n_f}"
            f", quartiles={n_q}"
        )

    full_df = pd.DataFrame.from_dict(profiles_full, orient="index").fillna(0.0).sort_index()
    full_df.index.name = "condition"
    full_df.to_csv(paths.profiles_dir(mode) / "profiles_full.csv")

    quart_df = pd.DataFrame.from_dict(profiles_quart, orient="index").fillna(0.0).sort_index()
    quart_df.index.name = "condition"
    quart_df.to_csv(paths.profiles_dir(mode) / "profiles_quartile.csv")
    return full_df, quart_df
