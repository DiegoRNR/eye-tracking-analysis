"""
networks/word-type-transitions/core

API pública de la red de transición entre tipos de palabra (diseño 2×2:
{L1 nativo, L2 inglés} × {Q1, Q4} por comprensión; carga cognitiva = duración).
"""

from . import paths  # noqa: F401
from .grouping import quartile_groups
from .network_builder import build_condition, build_condition_all_modes, iter_conditions
from .stats import bh_adjust, compare_conditions, graph_metrics, perm_test

__all__ = [
    "paths",
    "quartile_groups",
    "build_condition",
    "build_condition_all_modes",
    "iter_conditions",
    "perm_test",
    "bh_adjust",
    "compare_conditions",
    "graph_metrics",
]
