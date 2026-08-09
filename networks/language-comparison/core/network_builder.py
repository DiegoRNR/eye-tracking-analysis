"""
network_builder.py

Construcción de la red de carga cognitiva por grupo de lenguas.

Reusa `build_cogload_network` de networks/cognitive-load (API pública) para
evitar duplicar la lógica de construcción. El grafo resultante es un
networkx.DiGraph con nodos = palabras y aristas = ΔPS secuenciales.

El paquete `core` de cognitive-load se carga bajo el alias `cogload_core`
para evitar la colisión de nombre con este paquete `core`.
"""

import importlib.util
import os
import sys

_COGLOAD_CORE_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "cognitive-load",
        "core",
    )
)

_cogload_core = None


def _get_cogload_core():
    """Carga networks/cognitive-load/core bajo el alias `cogload_core`."""
    global _cogload_core
    if _cogload_core is not None:
        return _cogload_core
    if "cogload_core" in sys.modules:
        _cogload_core = sys.modules["cogload_core"]
        return _cogload_core

    spec = importlib.util.spec_from_file_location(
        "cogload_core",
        os.path.join(_COGLOAD_CORE_DIR, "__init__.py"),
        submodule_search_locations=[_COGLOAD_CORE_DIR],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cogload_core"] = mod
    spec.loader.exec_module(mod)
    _cogload_core = mod
    return mod


def build_group_network(
    fixations,
    groupby="all",
    text_label="Language-Comparison Network",
):
    """
    Construye la red de carga cognitiva para un grupo de lenguas.

    Igual que cognitive-load en modo sequential: pares adyacentes en el orden
    de fijación de la sesión, peso = |PS(w2) − PS(w1)| promedio entre sesiones.
    """
    cogload_core = _get_cogload_core()
    return cogload_core.build_cogload_network(
        fixations,
        groupby=groupby,
        text_label=text_label,
        edge_mode="sequential",
        edge_window=4,
        within_sentence=False,
    )


def build_prefix(lang_group, trialid, wave, normalize, group_langs, ps_absent_langs):
    """
    Genera el prefijo del build a partir de los parámetros del grupo.

    Ej: langcomp_trial4_w1_zscore_germanic
    """
    parts = [f"langcomp_trial{trialid}"]
    parts.append(f"w{wave}")
    parts.append(normalize)
    if ps_absent_langs:
        parts.append(f"nops-{'-'.join(sorted(ps_absent_langs))}")
    parts.append(f"{lang_group}")
    if group_langs:
        parts.append(f"langs-{'-'.join(sorted(group_langs))}")
    return "_".join(parts)
