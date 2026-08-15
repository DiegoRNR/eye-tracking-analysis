"""
_langcomp.py

Carga el paquete `core` de networks/language-comparison bajo el alias
`langcomp_core` para reutilizar su capa de agrupación por familia, la carga de
`accuracy` y las rutas a los CSVs de MECO L2.

Es necesario el alias porque ambos paquetes se llaman `core` y un import
directo colisionaría (mismo patrón que usa language-comparison para cargar
cognitive-load como `cogload_core`).
"""

import importlib.util
import os
import sys

_LANGCOMP_CORE_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "language-comparison",
        "core",
    )
)

_langcomp_core = None


def get_langcomp_core():
    """Carga networks/language-comparison/core bajo el alias `langcomp_core`."""
    global _langcomp_core
    if _langcomp_core is not None:
        return _langcomp_core
    if "langcomp_core" in sys.modules:
        _langcomp_core = sys.modules["langcomp_core"]
        return _langcomp_core

    spec = importlib.util.spec_from_file_location(
        "langcomp_core",
        os.path.join(_LANGCOMP_CORE_DIR, "__init__.py"),
        submodule_search_locations=[_LANGCOMP_CORE_DIR],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["langcomp_core"] = mod
    spec.loader.exec_module(mod)
    _langcomp_core = mod
    return mod
