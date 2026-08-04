"""
stats/

Cálculo de métricas, cascadas, modularidad, exports y plots para la Red de
Carga Cognitiva Pupilo-dilatada sobre el dataset MECO L2.
"""

from .cascades import detect_cognitive_load_cascades
from .exports import export_cogload_report
from .metrics import compute_cogload_metrics
from .modularity import compute_effort_modularity
from .orchestrator import stats_from_cache
from .viz import visualize_cogload_cascades, visualize_community_along_text

__all__ = [
    "compute_cogload_metrics",
    "compute_effort_modularity",
    "detect_cognitive_load_cascades",
    "export_cogload_report",
    "stats_from_cache",
    "visualize_cogload_cascades",
    "visualize_community_along_text",
]
