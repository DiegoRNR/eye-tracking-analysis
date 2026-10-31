"""
networks/scanpath/core

Library code for the per-text scanpath network pipeline (L2 only).
Entry point: scanpath_texts.py at the parent directory.
"""

from .data_io import load_l2_accuracy, load_l2_fixations, quartile_groups
from .network_builder import build_text_network
from .paths import (
    CONDITION_LANGS,
    MIN_GROUP_N,
    OUTPUT_DIR,
    QUARTILES,
    TEXTS,
    network_anim_dir,
    network_dir,
    quartile_dir,
)
from .temporal_viz import write_grid_wrapper as write_anim_wrapper
from .temporal_viz import write_text_network_anim
from .visualization import write_grid_wrapper as write_static_wrapper
from .visualization import write_text_network_static

__all__ = [
    "CONDITION_LANGS",
    "MIN_GROUP_N",
    "OUTPUT_DIR",
    "QUARTILES",
    "TEXTS",
    "build_text_network",
    "load_l2_accuracy",
    "load_l2_fixations",
    "network_anim_dir",
    "network_dir",
    "quartile_dir",
    "quartile_groups",
    "write_anim_wrapper",
    "write_static_wrapper",
    "write_text_network_anim",
    "write_text_network_static",
]
