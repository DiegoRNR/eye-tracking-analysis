"""
orchestrator.py

Coordina la construcción de redes de regresión por familia lingüística.

Lee el CSV de fijaciones **una sola vez** para todas las familias del wave y
luego reparte las fijaciones por familia, en lugar de releer el archivo por
cada grupo.
"""

import json
import os
from collections import OrderedDict

from ._langcomp import get_langcomp_core
from .data_io import (
    filter_discordant_sessions,
    load_accuracy_for,
    load_scanpath_fixations,
    summarize_accuracy_for,
)
from .interactive_viz import visualize_regression_network_interactive
from .network_builder import build_prefix, build_regression_network
from .persistence import check_cache_fresh, save_built_network


def resolve_families(wave, lang_group):
    """
    Resuelve la lista de familias a construir para el wave.

    `lang_group` puede ser 'all', un nombre de familia, o una lista.
    Descarta las familias sin lenguas presentes en la ola.
    """
    lc = get_langcomp_core()

    if lang_group in (None, "all"):
        candidates = list(lc.ALL_FAMILIES)
    elif isinstance(lang_group, str):
        candidates = [lang_group]
    else:
        candidates = list(lang_group)

    families = []
    for fam in candidates:
        if fam not in lc.ALL_FAMILIES:
            print(f"[!] Familia desconocida, se omite: {fam}")
            continue
        if not lc.resolve_group(fam, wave):
            print(f"[!] Familia '{fam}' sin lenguas en wave {wave}; se omite.")
            continue
        families.append(fam)
    return families


def find_existing_build(outdir, trialid, wave, edge_weight, lang_group):
    """Busca un build ya generado para esa familia bajo `outdir`."""
    if not os.path.isdir(outdir):
        return None
    pattern = f"regcomp_trial{trialid}_w{wave}_{edge_weight}_{lang_group}"
    for name in sorted(os.listdir(outdir)):
        if name != pattern and not name.startswith(pattern + "_langs-"):
            continue
        meta_path = os.path.join(outdir, name, "metadata.json")
        if os.path.exists(meta_path):
            return os.path.join(outdir, name)
    return None


def build_families(
    lang_group,
    trialid,
    wave,
    edge_weight="rate",
    min_rate=0.02,
    filter_discordant=True,
    outdir=None,
    do_interactive=True,
    reuse_cache=False,
):
    """
    Construye (o reutiliza) la red de cada familia pedida.

    Retorna OrderedDict {familia: (build_dir, metadata)}.
    """
    lc = get_langcomp_core()
    wave = int(wave)
    outdir = outdir or os.path.join("networks", "regression-comparison", "output")

    families = resolve_families(wave, lang_group)
    if not families:
        print(f"[!] Ninguna familia pedida tiene lenguas en wave {wave}.")
        return OrderedDict()

    lang_map = {fam: lc.resolve_group(fam, wave) for fam in families}
    results = OrderedDict()
    pending = []

    if reuse_cache:
        for fam in families:
            existing = find_existing_build(outdir, trialid, wave, edge_weight, fam)
            if existing is None:
                pending.append(fam)
                continue
            with open(os.path.join(existing, "metadata.json"), "r", encoding="utf-8") as f:
                meta = json.load(f)
            check_cache_fresh(meta, [s["path"] for s in meta.get("source_files", [])])
            print(f"--> Reutilizando build existente para '{fam}': {existing}")
            results[fam] = (existing, meta)
    else:
        pending = list(families)

    if pending:
        needed = sorted({l for fam in pending for l in lang_map[fam]})
        fixations_all, fix_files = load_scanpath_fixations(wave, needed, trialid)
        if not fixations_all:
            print("[!] Sin fijaciones. ¿Corriste scripts/convert_rda_to_csv.R?")
        else:
            acc_map, comp_files = load_accuracy_for(wave, needed)
            source_files = list(fix_files) + list(comp_files)
            for fam in pending:
                out = _build_one(
                    fam,
                    lang_map[fam],
                    fixations_all,
                    acc_map,
                    source_files,
                    trialid=trialid,
                    wave=wave,
                    edge_weight=edge_weight,
                    min_rate=min_rate,
                    filter_discordant=filter_discordant,
                    outdir=outdir,
                    do_interactive=do_interactive,
                )
                if out is not None:
                    results[fam] = out

    # Respeta el orden canónico de familias.
    ordered = OrderedDict()
    for fam in families:
        if fam in results:
            ordered[fam] = results[fam]
    return ordered


def _build_one(
    family,
    langs,
    fixations_all,
    acc_map,
    source_files,
    trialid,
    wave,
    edge_weight,
    min_rate,
    filter_discordant,
    outdir,
    do_interactive,
):
    """Construye, persiste y renderiza la red de una familia."""
    lc = get_langcomp_core()
    label = lc.FAMILY_LABELS.get(family, family)

    lang_set = set(langs)
    fixations = [f for f in fixations_all if f["lang"] in lang_set]
    if not fixations:
        print(f"[!] Familia '{family}' sin fijaciones en wave {wave}; se omite.")
        return None

    print(f"\n{'=' * 62}\n[{label}] langs={sorted(lang_set)}\n{'=' * 62}")

    discarded = []
    if filter_discordant:
        fixations, discarded = filter_discordant_sessions(fixations)
    if not fixations:
        print(f"[!] Familia '{family}' quedó sin fijaciones tras el filtro; se omite.")
        return None

    G, report = build_regression_network(
        fixations,
        min_rate=min_rate,
        text_label=f"Regression-Comparison_{family}_Trial_{trialid}",
    )
    if G.number_of_nodes() == 0:
        print(f"[!] Red vacía para '{family}'; se omite.")
        return None

    session_ids = {f["session_id"] for f in fixations}
    acc_summary, n_participants, n_with_acc = summarize_accuracy_for(acc_map, session_ids)

    prefix = build_prefix(family, trialid, wave, edge_weight, sorted(lang_set))
    build_dir = save_built_network(
        G,
        output_dir=outdir,
        prefix=prefix,
        source_files=source_files,
        wave=wave,
        trialid=trialid,
        lang_group=family,
        languages=sorted(lang_set),
        accuracy_summary=acc_summary,
        n_participants=n_participants,
        n_with_accuracy=n_with_acc,
        discarded_sessions=discarded,
        edge_weight=edge_weight,
        report=report,
    )

    if do_interactive:
        acc_txt = (
            f"accuracy {acc_summary['mean']:.3f}"
            if acc_summary["mean"] is not None
            else "accuracy n/d"
        )
        subtitle = (
            f"{label} · trial {trialid} · wave {wave} · "
            f"{n_participants} lectores · {acc_txt} · "
            f"{report['n_edges_forward']} avances / "
            f"{report['n_edges_regression']} regresiones · "
            f"reciprocidad {report['reciprocity']}"
        )
        visualize_regression_network_interactive(G, build_dir, prefix, subtitle=subtitle)

    with open(os.path.join(build_dir, "metadata.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    return build_dir, meta
