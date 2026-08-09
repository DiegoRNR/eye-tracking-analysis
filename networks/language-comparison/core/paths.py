"""
paths.py

Rutas a los CSVs de fijación y comprensión de MECO L2, y utilidades de
hashing de archivos fuente.
"""

import hashlib
import os


FIXATION_WAVE_PATHS = {
    1: os.path.join(
        "data",
        "MECO-L2_version-2.2",
        "wave-1",
        "primary-data",
        "eye-tracking",
        "joint_l2_fixation_trimmed_report_2.2.csv",
    ),
    2: os.path.join(
        "data",
        "MECO-L2_version-2.2",
        "wave-2",
        "primary-data",
        "eye-tracking",
        "joint_fix_trimmed_L2_wave2_version2.2.csv",
    ),
}

COMPREHENSION_WAVE_PATHS = {
    1: os.path.join(
        "data",
        "MECO-L2_version-2.2",
        "wave-1",
        "primary-data",
        "comprehension",
        "joint.comp.l2.csv",
    ),
    2: os.path.join(
        "data",
        "MECO-L2_version-2.2",
        "wave-2",
        "primary-data",
        "comprehension",
        "joint_comp_L2_Wave2_trimmed.csv",
    ),
}


def resolve_fixation_paths(wave):
    """Resuelve las rutas de los CSVs de fijación para la(s) ola(s) pedida(s)."""
    if wave == "both":
        return [FIXATION_WAVE_PATHS[1], FIXATION_WAVE_PATHS[2]]
    if wave in (1, "1"):
        return [FIXATION_WAVE_PATHS[1]]
    if wave in (2, "2"):
        return [FIXATION_WAVE_PATHS[2]]
    raise ValueError(f"Valor de --wave inválido: {wave!r}. Use 1, 2 o 'both'.")


def resolve_comprehension_paths(wave):
    """Resuelve las rutas de los CSVs de comprensión para la(s) ola(s) pedida(s)."""
    if wave == "both":
        return [COMPREHENSION_WAVE_PATHS[1], COMPREHENSION_WAVE_PATHS[2]]
    if wave in (1, "1"):
        return [COMPREHENSION_WAVE_PATHS[1]]
    if wave in (2, "2"):
        return [COMPREHENSION_WAVE_PATHS[2]]
    raise ValueError(f"Valor de --wave inválido: {wave!r}. Use 1, 2 o 'both'.")


def wave_of_path(path):
    """Devuelve la ola (1 o 2) a partir de la ruta de un CSV."""
    return 1 if "wave-1" in path else 2


def file_sha256(path, block_size=65536):
    """Calcula el hash SHA-256 de un archivo para detectar cambios en la fuente."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()
