"""
_common.py

Helpers privados compartidos por los módulos del paquete `stats`.
"""


def _signal_field(G):
    """Devuelve 'mean_ps_z' si los nodos tienen z-scores, si no 'mean_ps'."""
    has_z = any(
        d.get("mean_ps_z", 0.0) != 0.0 or d.get("ps_z_std", 0.0) != 0.0
        for _, d in G.nodes(data=True)
    )
    return "mean_ps_z" if has_z else "mean_ps"
