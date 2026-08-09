"""
stats/

Cálculo de métricas, cascadas, modularidad, exports y plots para la Red de
Carga Cognitiva por Familias Lingüísticas sobre el dataset MECO L2.
"""

from .cascades import detect_group_cascades
from .exports import export_group_report
from .metrics import compute_group_metrics
from .modularity import compute_effort_modularity
from .orchestrator import group_stats_from_cache
from .viz import (
    visualize_group_cascades,
    visualize_group_community_along_text,
)

__all__ = [
    "compute_group_metrics",
    "compute_effort_modularity",
    "detect_group_cascades",
    "export_group_report",
    "group_stats_from_cache",
    "visualize_group_cascades",
    "visualize_group_community_along_text",
]
