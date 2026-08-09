"""
cascades.py

Detección de picos de PS y de cascadas de carga cognitiva para la red por
grupo de lenguas.
"""

from collections import defaultdict

import networkx as nx
import numpy as np
from scipy.signal import find_peaks
from scipy.stats import ttest_1samp


def find_ps_peaks(timeseries, distance=3, prominence=None):
    """
    Detecta picos en una serie temporal de PS usando scipy.signal.find_peaks.
    """
    if timeseries is None or len(timeseries) < 3:
        return np.array([], dtype=int)
    kwargs = {"distance": distance}
    if prominence is not None:
        kwargs["prominence"] = prominence
    peaks, _ = find_peaks(timeseries, **kwargs)
    return peaks


def detect_group_cascades(
    fixations, G, window=4, z_thresh=1.0, p_thresh=0.05, peak_distance=3
):
    """
    Detecta cascadas de carga cognitiva: picos de PS seguidos de una ventana
    de palabras con PS significativamente por encima de la línea base.

    Usa el campo `ps_z` de cada fijación (z-score por sesión). Si no está
    presente, cae a `ps` crudo. Para cada sesión construye la serie temporal
    mean_ps_z por wordnum, suavizada con media móvil de 3 muestras, detecta
    picos con scipy.signal.find_peaks, y evalúa con ttest_1samp si la ventana
    posterior al pico está por encima de la línea base pre-pico.
    """
    if not fixations:
        return []

    use_z = bool(fixations[0].get("has_z", False))
    signal_field = "ps_z" if use_z else "ps"

    by_session = defaultdict(list)
    for f in fixations:
        by_session[(f["uniform_id"], f["lang"], f["trialid"], f["wave"])].append(f)

    cascades = []
    for sess_key, items in by_session.items():
        items_sorted = sorted(
            items, key=lambda f: (f["sentnum"], f["wordnum"], f["fixid"])
        )

        per_word = defaultdict(list)
        for f in items_sorted:
            if use_z:
                per_word[(f["sentnum"], f["wordnum"])].append(f.get("ps_z", 0.0))
            else:
                if f["ps"] > 0:
                    per_word[(f["sentnum"], f["wordnum"])].append(f["ps"])

        if not per_word:
            continue

        ordered_keys = sorted(per_word.keys())
        wordnums = [k[1] for k in ordered_keys]
        sents = [k[0] for k in ordered_keys]
        means = np.array([np.mean(per_word[k]) for k in ordered_keys], dtype=float)

        if len(means) < peak_distance + window + 1:
            continue

        smoothed = np.convolve(means, np.ones(3) / 3, mode="same")

        z_norm = (smoothed - np.mean(smoothed)) / (np.std(smoothed) + 1e-9)
        peak_idx = find_ps_peaks(smoothed, distance=peak_distance)
        if use_z:
            peaks = [int(p) for p in peak_idx if smoothed[p] > z_thresh and p < len(means) - window]
        else:
            peaks = [int(p) for p in peak_idx if z_norm[p] > z_thresh and p < len(means) - window]

        for p in peaks:
            baseline = smoothed[max(0, p - 3):p]
            post = smoothed[p + 1 : p + 1 + window]
            if len(post) < 2 or len(baseline) < 1:
                continue
            t_stat, p_value = ttest_1samp(post, popmean=float(np.mean(baseline)))
            is_cascade = bool(p_value < p_thresh and t_stat > 0)

            cascades.append(
                {
                    "uniform_id": sess_key[0],
                    "lang": sess_key[1],
                    "trialid": sess_key[2],
                    "wave": sess_key[3],
                    "peak_sentnum": int(sents[p]),
                    "peak_wordnum": int(wordnums[p]),
                    "peak_ps": round(float(smoothed[p]), 4),
                    "window_mean_signal": round(float(np.mean(post)), 4),
                    "baseline_mean_signal": round(float(np.mean(baseline)), 4),
                    "signal_field": signal_field,
                    "window_size": int(window),
                    "p_value": round(float(p_value), 4),
                    "t_stat": round(float(t_stat), 4),
                    "is_cascade": is_cascade,
                    "propagation_depth": -1,
                }
            )

    return cascades
