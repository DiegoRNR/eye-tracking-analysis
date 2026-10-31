"""
networks/reading-pattern-mds/core/_wtt.py

Bootstrap del package `core` de networks/word-type-transitions bajo el alias
`wttcore` (evita el conflicto de nombres con este `core`), y re-exportación de
la API compartida. Así las distribuciones de transición usan EXACTAMENTE la
misma lógica/filtros que la red de referencia.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .paths import WTT_ROOT

_loaded = False


def load_wtt():
    """Registra el package core de word-type-transitions como `wttcore`."""
    global _loaded
    if _loaded:
        return sys.modules["wttcore"]
    name = "wttcore"
    if name in sys.modules:
        _loaded = True
        return sys.modules[name]
    pkg_init = WTT_ROOT / "core" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "wttcore", pkg_init, submodule_search_locations=[str(WTT_ROOT / "core")]
    )
    pkg = importlib.util.module_from_spec(spec)
    sys.modules[name] = pkg
    spec.loader.exec_module(pkg)
    _loaded = True
    return pkg


def shared():
    """Retorna (data_io, label_map, grouping, network_builder) del core reutilizado."""
    load_wtt()
    from wttcore import data_io, grouping, label_map, network_builder, paths

    return data_io, label_map, grouping, network_builder, paths
