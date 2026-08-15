"""
core/

Librería interna de la red de regresiones por familia lingüística.
Re-exporta SOLO la API pública vía `__all__`.
"""

from .comparison import run_comparison
from .data_io import (
    filter_discordant_sessions,
    load_accuracy_for,
    load_scanpath_fixations,
    summarize_accuracy_for,
)
from .interactive_viz import visualize_regression_network_interactive
from .network_builder import (
    build_prefix,
    build_regression_network,
    classify_saccade,
    reconstruct_scanpath,
)
from .orchestrator import build_families, resolve_families
from .persistence import (
    check_cache_fresh,
    load_built_network,
    save_built_network,
)

__all__ = [
    # comparison
    "run_comparison",
    # data_io
    "filter_discordant_sessions",
    "load_accuracy_for",
    "load_scanpath_fixations",
    "summarize_accuracy_for",
    # network_builder
    "build_prefix",
    "build_regression_network",
    "classify_saccade",
    "reconstruct_scanpath",
    # orchestrator
    "build_families",
    "resolve_families",
    # persistence
    "check_cache_fresh",
    "load_built_network",
    "save_built_network",
    # interactive_viz
    "visualize_regression_network_interactive",
]
