"""
core/

Librería interna de la red de comparación por familias lingüísticas.
Re-exporta SOLO la API pública vía `__all__`.
"""

from .language_groups import (
    ALL_FAMILIES,
    FAMILY_LABELS,
    LANG_TO_FAMILY,
    all_langs,
    family_of,
    langs_without_ps,
    resolve_group,
)
from .data_io import (
    load_accuracy,
    load_fixations,
    load_fixations_by_group,
    load_fixations_from_cache_metadata,
    normalize_session_ps,
    summarize_accuracy,
)
from .network_builder import build_group_network, build_prefix
from .paths import file_sha256
from .persistence import (
    check_cache_fresh,
    load_built_network,
    save_built_network,
)
from .visualization import visualize_group_network
from .interactive_viz import visualize_group_network_interactive
from .comparison import run_comparison
from .stats import group_stats_from_cache

__all__ = [
    # language_groups
    "ALL_FAMILIES",
    "FAMILY_LABELS",
    "LANG_TO_FAMILY",
    "all_langs",
    "family_of",
    "langs_without_ps",
    "resolve_group",
    # data_io
    "load_accuracy",
    "load_fixations",
    "load_fixations_by_group",
    "load_fixations_from_cache_metadata",
    "normalize_session_ps",
    "summarize_accuracy",
    # network_builder
    "build_group_network",
    "build_prefix",
    # paths
    "file_sha256",
    # persistence
    "check_cache_fresh",
    "load_built_network",
    "save_built_network",
    # visualization
    "visualize_group_network",
    "visualize_group_network_interactive",
    # comparison
    "run_comparison",
    # stats
    "group_stats_from_cache",
]
