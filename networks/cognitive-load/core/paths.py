"""
paths.py

Rutas a los datasets MECO L2 y utilidades de hashing de archivos fuente.
"""

import hashlib
import os


WAVE_PATHS = {
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


def resolve_wave_paths(wave):
    """Resuelve las rutas de CSV para la(s) ola(s) solicitada(s)."""
    if wave == "both":
        return [WAVE_PATHS[1], WAVE_PATHS[2]]
    if wave in (1, "1"):
        return [WAVE_PATHS[1]]
    if wave in (2, "2"):
        return [WAVE_PATHS[2]]
    raise ValueError(f"Valor de --wave inválido: {wave!r}. Use 1, 2 o 'both'.")


def file_sha256(path, block_size=65536):
    """Calcula el hash SHA-256 de un archivo para detectar cambios en la fuente."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()
