"""
networks/reading-pattern-mds/core/dashboard.py

Dashboard HTML autocontenido (filtros client-side, sin servidor):

- Pestaña "MDS map": scatter Plotly con coordenadas del embedding GLOBAL
  (MDS clásico sobre TODAS las condiciones del dataset), filtrable por
  lengua (checkboxes), sesión (L1/L2), dataset (all | Q1 | Q4 | Q1+Q4),
  cohortes nativos (en_ca/en_uk), líneas de enlace y modo de color
  (por lengua | por distancia lingüística).
- Pestaña "Distancia lingüística": x = lang_to_en.csv, y = J-S de lectura
  (media de cohortes | en_ca | en_uk), línea OLS + Pearson/Spearman del
  corte visible (distances/corr_linguistic_reading.csv).
- Pestaña "Info": método.

Los datos (ambos modos: temporal/regression) van embebidos como JSON y el
archivo se abre directo en el navegador (plotly.js por CDN).

Se genera en output/reading_patterns_dashboard.html.
"""

from __future__ import annotations

import json
from string import Template

import pandas as pd

from . import lingdistance, paths
from .mds import classical_mds
from .viz import _lang_palette

_DATASETS = {
    "full": "dist_full_all.csv",
    "quartile": "dist_quartile_all.csv",
}


def _points_from(D: pd.DataFrame, emb: pd.DataFrame, ling: dict[str, float]) -> list[dict]:
    rows = []
    for cond in D.index:
        parts = cond.split("-")
        session, lang = parts[0], parts[1]
        quart = parts[2] if len(parts) > 2 else None
        is_ref = lang in paths.EN_REFS.values()
        d = {
            "id": cond,
            "lang": lang,
            "label": paths.fig_label(lang),
            "session": session,
            "quartile": quart,
            "ref": is_ref,
            "x": round(float(emb.loc[cond, "mds1"]), 5),
            "y": round(float(emb.loc[cond, "mds2"]), 5),
            "jsd_en_ca": None,
            "jsd_en_uk": None,
            "ling": ling.get(lang),
        }
        q = f"-{quart}" if quart else ""
        for ref, ref_code in paths.EN_REFS.items():
            col = f"{session}-{ref_code}{q}"
            if col in D.columns:
                d[f"jsd_{ref}"] = round(float(D.loc[cond, col]), 4)
        dm = [v for v in (d["jsd_en_ca"], d["jsd_en_uk"]) if v is not None]
        d["jsd_mean"] = round(sum(dm) / len(dm), 4) if dm else None
        rows.append(d)
    return rows


def _mode_payload(mode: str) -> dict:
    ddir = paths.distances_dir(mode)
    ling = lingdistance.load_distances()
    payload = {"corr": [], "ling": ling, "full": [], "quartile": [], "stress": {}}
    for key, fname in _DATASETS.items():
        D = pd.read_csv(ddir / fname, index_col=0)
        emb, stress = classical_mds(D)
        payload[key] = _points_from(D, emb, ling)
        payload["stress"][key] = round(stress, 4)
    corr_path = ddir / "corr_linguistic_reading.csv"
    if corr_path.exists():
        payload["corr"] = pd.read_csv(corr_path).to_dict("records")
    return payload


def build_payload() -> dict:
    out = {}
    palette = _lang_palette(paths.target_langs())
    out["palette"] = {g: "#{:02x}{:02x}{:02x}".format(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)) for g, c in palette.items()}
    out["refs"] = dict(paths.EN_REFS)
    for mode in ("temporal", "regression"):
        if (paths.profiles_dir(mode) / "profiles_full.csv").exists():
            out[mode] = _mode_payload(mode)
    return out


TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Reading patterns MDS - dinámico</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
 :root { --bg:#fafafa; --panel:#ffffff; --border:#ddd; }
 * { box-sizing:border-box; }
 body { margin:0; font:13px/1.45 -apple-system, "Segoe UI", sans-serif; background:var(--bg); display:flex; height:100vh; }
 aside { width:270px; min-width:270px; background:var(--panel); border-right:1px solid var(--border); overflow-y:auto; padding:12px; }
 main { flex:1; display:flex; flex-direction:column; min-width:0; }
 .tabs { display:flex; gap:4px; padding:8px 10px 0; background:var(--panel); border-bottom:1px solid var(--border); }
 .tabs button { border:1px solid var(--border); border-bottom:none; background:#eee; padding:6px 14px; border-radius:6px 6px 0 0; cursor:pointer; font-size:13px; }
 .tabs button.on { background:#fff; font-weight:600; }
 .tab { flex:1; display:none; min-height:0; flex-direction:column; }
 .tab.on { display:flex; }
 .plotwrap { flex:1; min-height:0; display:flex; flex-direction:column; }
 #corr-plot, #mds-plot { height:calc(100vh - 46px); }
 h4 { margin:10px 0 4px; font-size:12.5px; text-transform:uppercase; letter-spacing:.04em; color:#555; }
 label { user-select:none; cursor:pointer; display:inline-flex; align-items:center; gap:4px; padding:1px 3px; border-radius:4px; }
 label:hover { background:#f0f0f0; }
 .btnrow { display:flex; gap:4px; margin:4px 0; }
 .btnrow button, select, input[type=text] { font-size:12px; }
 .btnrow button { border:1px solid var(--border); background:#fff; border-radius:4px; padding:2px 8px; cursor:pointer; }
 .hidden { display:none; }
 .swatch { width:10px; height:10px; border-radius:2px; display:inline-block; }
 input[type=checkbox] { margin:0; }
 .langs { max-height:300px; overflow-y:auto; border:1px solid var(--border); border-radius:4px; padding:4px; }
 .info { padding:20px; overflow-y:auto; max-width:900px; background:var(--panel); margin:14px; border-radius:8px; border:1px solid var(--border);}
 .info h2 { margin-top:0; }
 #corr-note { padding:4px 12px; font-size:12px; color:#444; }
</style>
</head>
<body>
<aside>
  <h4>Modo</h4>
  <select id="mode"><option value="temporal">temporal</option><option value="regression">regression</option></select>
  <h4>Lengua (grupos no ingleses)</h4>
  <div class="btnrow">
    <button id="lang-all">todas</button><button id="lang-none">ninguna</button>
  </div>
  <input type="text" id="lang-search" placeholder="filtrar..." style="width:100%">
  <div class="langs" id="lang-list"></div>
  <h4>Sesión</h4>
  <label><input type="checkbox" id="s-L1" checked> L1 (lectura nativa)</label><br>
  <label><input type="checkbox" id="s-L2" checked> L2 (lectura en inglés)</label>
  <h4>Cuartiles</h4>
  <div>
    <label><input type="radio" name="ds" value="all" checked> todos los sujetos</label><br>
    <label><input type="radio" name="ds" value="q1"> Q1 (cuartil bajo)</label><br>
    <label><input type="radio" name="ds" value="q4"> Q4 (cuartil alto)</label><br>
    <label><input type="radio" name="ds" value="both"> Q1 + Q4</label>
  </div>
  <h4>Cohortes nativos</h4>
  <label><input type="checkbox" id="r-en_ca" checked> en_ca (en, wave 1)</label><br>
  <label><input type="checkbox" id="r-en_uk" checked> en_uk (wave 2)</label>
  <h4>Vista</h4>
  <label><input type="checkbox" id="v-lines" checked> líneas de enlace</label><br>
  <label><input type="checkbox" id="v-labels"> etiquetas de puntos</label><br>
  Color: <select id="v-color"><option value="lang">por lengua</option><option value="ling">distancia lingüística</option></select>
  <h4>Correlación (pestaña 2)</h4>
  y = <select id="c-agg"><option value="jsd_mean">J-S media cohortes</option><option value="jsd_en_ca">J-S en_ca</option><option value="jsd_en_uk">J-S en_uk</option></select>
</aside>
<main>
  <div class="tabs">
    <button data-tab="mds" class="on">MDS map</button>
    <button data-tab="corr">Distancia lingüística</button>
    <button data-tab="info">Info</button>
  </div>
  <div class="tab on" id="tab-mds"><div class="plotwrap"><div id="mds-plot"></div></div></div>
  <div class="tab" id="tab-corr">
    <div class="plotwrap"><div id="corr-plot"></div><div id="corr-note"></div></div>
  </div>
  <div class="tab" id="tab-info"><div class="info">$INFO_HTML</div></div>
</main>
<script>
const DATA = $PAYLOAD;
const state = { langs: new Set(Object.keys(DATA.palette)), lines: true, labels: false };

function ds() {
  const v = document.querySelector('input[name=ds]:checked').value;
  return v === 'all' ? 'full' : 'quartile';
}
function quarts() {
  const v = document.querySelector('input[name=ds]:checked').value;
  return { q1: ['Q1'], q4: ['Q4'], both: ['Q1', 'Q4'], all: [null] }[v];
}
function refKey(lang) { return lang === 'en' ? 'en_ca' : 'en_uk'; }
function visiblePoints() {
  const m = DATA[document.getElementById('mode').value];
  const qs = quarts(), keepS = ['L1','L2'].filter(s => document.getElementById('s-' + s).checked);
  const keepR = ['en_ca','en_uk'].filter(r => document.getElementById('r-' + r).checked);
  return m[ds()].filter(p => {
    if (!keepS.includes(p.session)) return false;
    if (!qs.includes(p.quartile)) return false;
    if (p.ref) return keepR.includes(refKey(p.lang));
    return state.langs.has(p.lang);
  });
}
function hex(c) { return DATA.palette[c] || '#333'; }
function drawMDS() {
  const pts = visiblePoints();
  const mode = document.getElementById('mode').value;
  const m = DATA[mode];
  const colorMode = document.getElementById('v-color').value;
  const lingVals = pts.filter(p => !p.ref && p.ling != null).map(p => p.ling);
  const lmin = lingVals.length ? Math.min.apply(null, lingVals) : 0;
  const lmax = lingVals.length ? Math.max.apply(null, lingVals) : 100;

  const xs = [], ys = [], cols = [], syms = [], hov = [];
  pts.forEach(p => {
    xs.push(p.x); ys.push(p.y);
    let c;
    if (colorMode === 'ling') c = p.ling != null ? p.ling : null;
    else c = p.ref ? '#333333' : hex(p.lang);
    cols.push(c);
    let marker = p.ref ? 'star' : (p.session === 'L1' ? 'circle' : 'triangle-up');
    if (p.quartile === 'Q1') marker += '-open';
    syms.push(marker);
    const dparts = [];
    if (p.jsd_en_ca != null) dparts.push('J-S en_ca=' + p.jsd_en_ca.toFixed(3));
    if (p.jsd_en_uk != null) dparts.push('J-S en_uk=' + p.jsd_en_uk.toFixed(3));
    if (p.jsd_mean != null) dparts.push('media=' + p.jsd_mean.toFixed(3));
    if (p.ling != null) dparts.push('dist ling=' + p.ling.toFixed(1));
    hov.push('<b>' + p.label + '</b> ' + p.lang + '<br>' + p.session + (p.quartile ? ' ' + p.quartile : ' (todos)') + '<br>' + dparts.join('<br>'));
  });
  const marker = {
    size: pts.map(p => p.ref ? 18 : 11),
    color: cols,
    symbol: syms,
    line: { color: colorMode === 'ling' ? '#555' : '#fff', width: 1 },
    colorscale: colorMode === 'ling' ? 'Viridis' : undefined,
    cmin: colorMode === 'ling' ? lmin : undefined,
    cmax: colorMode === 'ling' ? lmax : undefined,
    colorbar: colorMode === 'ling' ? { title: 'dist ling<br>(0-100)', thickness: 12 } : undefined,
    showscale: colorMode === 'ling',
  };
  const traces = [];
  if (state.lines) {
    const seen = new Set();
    pts.forEach(p => {
      let other = null;
      if (!p.ref && p.quartile == null) other = p.session === 'L1' ? 'L2-' + p.lang : 'L1-' + p.lang;
      else if (!p.ref && p.quartile) other = p.session + '-' + p.lang + '-' + (p.quartile === 'Q1' ? 'Q4' : 'Q1');
      if (!other || seen.has(p.id) || seen.has(other)) return;
      const o = pts.find(q => q.id === other);
      if (!o) return;
      seen.add(p.id); seen.add(other);
      traces.push({ type: 'scatter', mode: 'lines', x: [p.x, o.x], y: [p.y, o.y],
        line: { color: colorMode === 'ling' ? 'rgba(120,120,120,.45)' : hex(p.lang), width: 1.4 },
        opacity: .55, hoverinfo: 'skip', showlegend: false });
    });
  }
  traces.push({ type: 'scatter', mode: state.labels ? 'markers+text' : 'markers',
    text: state.labels ? pts.map(p => (p.ref ? '' : p.label + ' ' + p.session + (p.quartile ? ' ' + p.quartile : ''))) : undefined,
    textposition: 'top center', textfont: { size: 8 },
    x: xs, y: ys, marker: marker, hovertemplate: '%{hovertext}<extra></extra>', hovertext: hov,
    showlegend: false });
  const stress = m.stress[ds()];
  const layout = {
    title: 'MDS clásico · distancia J-S · ' + document.getElementById('mode').value + ' · ' +
      document.querySelector('input[name=ds]:checked').value + ' · stress-1=' + stress.toFixed(3),
    xaxis: { title: 'Dimensión MDS 1' }, yaxis: { title: 'Dimensión MDS 2' },
    hovermode: 'closest', margin: { t: 60, b: 50, l: 50, r: 20 },
  };
  Plotly.react('mds-plot', traces, layout, { responsive: true, displaylogo: false });
}

function drawCorr() {
  const m = DATA[document.getElementById('mode').value];
  const agg = document.getElementById('c-agg').value;
  const dsV = document.querySelector('input[name=ds]:checked').value;
  const keepS = ['L1','L2'].filter(s => document.getElementById('s-' + s).checked);
  const pts = m[ds()].filter(p => !p.ref && keepS.includes(p.session) && quarts().includes(p.quartile) && p.ling != null && p[agg] != null);
  const colorMode = document.getElementById('v-color').value;
  const xs = pts.map(p => p.ling), ys = pts.map(p => p[agg]);
  const colors = pts.map(p => colorMode === 'ling' ? p.ling : hex(p.lang));
  const traces = [{ type: 'scatter', mode: 'markers+text',
    text: pts.map(p => p.label + ' ' + p.session + (p.quartile ? ' ' + p.quartile : '')),
    textposition: 'top center', textfont: { size: 8 },
    x: xs, y: ys,
    marker: { size: 10, color: colors, colorscale: colorMode === 'ling' ? 'Viridis' : undefined,
      line: { color: '#fff', width: 1 },
      colorbar: colorMode === 'ling' ? { title: 'dist ling<br>(0-100)', thickness: 12 } : undefined,
      showscale: colorMode === 'ling' },
    hovertemplate: '%{hovertext}<extra></extra>',
    hovertext: pts.map(p => '<b>' + p.label + '</b> ' + p.lang + ' ' + p.session + (p.quartile ? ' ' + p.quartile : '') + '<br>dist ling=' + p.ling.toFixed(1) + '<br>' + agg + '=' + p[agg].toFixed(3)),
    showlegend: false }];
  let note = aggNote(keepS, dsV, agg, m);
  if (pts.length > 2) {
    const n = pts.length, sx = xs.reduce((a, b) => a + b), sy = ys.reduce((a, b) => a + b);
    const sxy = xs.map((x, i) => x * ys[i]).reduce((a, b) => a + b);
    const sxx = xs.map(x => x * x).reduce((a, b) => a + b);
    const b = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    const a = (sy - b * sx) / n;
    const x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
    traces.push({ type: 'scatter', mode: 'lines', x: [x0, x1],
      y: [a + b * x0, a + b * x1], line: { color: '#888', dash: 'dash' },
      hoverinfo: 'skip', showlegend: false });
  }
  const layout = {
    title: 'Distancia lingüística al inglés vs lectura (J-S a nativos) · ' +
      document.getElementById('mode').value + ' · ' + dsV,
    xaxis: { title: 'Distancia lingüística (lang_to_en.csv, 0-100)' },
    yaxis: { title: agg === 'jsd_mean' ? 'J-S media (en_ca, en_uk)' : 'J-S ' + agg.slice(4) },
    hovermode: 'closest', margin: { t: 60, b: 50, l: 55, r: 20 },
  };
  Plotly.react('corr-plot', traces, layout, { responsive: true, displaylogo: false });
  document.getElementById('corr-note').innerHTML = note;
}
function aggNote(keepS, dsV, agg, m) {
  const aggName = agg === 'jsd_mean' ? 'mean' : agg.slice(4);
  const corrs = m.corr.filter(c => keepS.includes(c.session) &&
    c.quartile === dsV.replace('q1', 'Q1').replace('q4', 'Q4') &&
    (dsV === 'all' ? c.quartile === 'all' : c.quartile !== 'all') &&
    c.aggregate === aggName);
  const dsName = dsV === 'all' ? 'all' : dsV.toUpperCase();
  return '<b>Pearson/Spearman</b> (corte: ' + (keepS.join('+') || '-') + ' · ' + dsName + ' · ' + aggName + '): ' +
    (corrs.map(c => '<b>' + c.session + '</b> r=' + c.pearson_r + ' (p=' + c.pearson_p + '), ρ=' + c.spearman_rho + ' (p=' + c.spearman_p + '), n=' + c.n).join(' &nbsp;·&nbsp; ') || 'sin datos');
}

function buildLangList() {
  const box = document.getElementById('lang-list');
  box.innerHTML = '';
  Object.keys(DATA.palette).sort().forEach(g => {
    const l = document.createElement('label');
    l.innerHTML = '<input type="checkbox" checked> <span class="swatch" style="background:' + hex(g) + '"></span> ' + g;
    l.querySelector('input').onchange = ev => {
      if (ev.target.checked) state.langs.add(g); else state.langs.delete(g);
      refresh();
    };
    l.dataset.lang = g;
    box.appendChild(l);
  });
  document.getElementById('lang-search').oninput = e => {
    const q = e.target.value.toLowerCase();
    box.querySelectorAll('label').forEach(l => {
      l.classList.toggle('hidden', l.dataset.lang.indexOf(q) === -1);
    });
  };
}
function refresh() { drawMDS(); drawCorr(); }

document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => {
  document.querySelectorAll('.tabs button').forEach(x => x.classList.remove('on'));
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('on'));
  b.classList.add('on');
  document.getElementById('tab-' + b.dataset.tab).classList.add('on');
  if (b.dataset.tab === 'corr') drawCorr(); else if (b.dataset.tab === 'mds') drawMDS();
});
document.getElementById('mode').onchange = refresh;
document.querySelectorAll('input[id^=s-],input[id^=r-],input[name=ds]').forEach(el => el.onchange = refresh);
document.getElementById('v-lines').onchange = e => { state.lines = e.target.checked; refresh(); };
document.getElementById('v-labels').onchange = e => { state.labels = e.target.checked; refresh(); };
document.getElementById('v-color').onchange = refresh;
document.getElementById('c-agg').onchange = refresh;
document.getElementById('lang-all').onclick = () => { document.querySelectorAll('#lang-list input').forEach(i => i.checked = true); state.langs = new Set(Object.keys(DATA.palette)); refresh(); };
document.getElementById('lang-none').onclick = () => { document.querySelectorAll('#lang-list input').forEach(i => i.checked = false); state.langs = new Set(); refresh(); };

buildLangList();
drawMDS();
</script>
</body>
</html>
""")

INFO_HTML = """<h2>Método</h2>
<p><b>Características:</b> distribuciones de transición entre tipos de palabra
(NOUN->VERB, ...; espacio FUSED de 11 nodos) calculadas con la misma lógica
que <i>networks/word-type-transitions</i> (fijaciones "in", ruptura en
parpadeos, conteos pooled por sujeto sobre 12 textos; fila-normalizado y masa
global re-normalizada a 1).</p>
<p><b>Distancia:</b> Jensen-Shannon (raíz cuadrada = métrica) entre las
distribuciones pooled alineadas por unión de aristas.</p>
<p><b>MDS:</b> clásico (Torgerson, determinista) sobre la matriz de distancias
de TODAS las condiciones del dataset; las coordenadas del dashboard son fijas
y el filtrado solo oculta/muestra puntos (los subsets son comparables entre
sí).</p>
<p><b>Referencias nativas:</b> en_ca (grupo "en", wave 1) y en_uk (wave 2).
Por diseño, L1 se compara solo con referencias L1 y L2 con referencias L2
(mismos textos/tipo de sesión). Las marcas de referencia son ★.</p>
<p><b>Cuartiles:</b> Q1 = accuracy &le; p25 (peor), Q4 = &ge; p75 (mejor); el
centro se descarta (igual que word-type-transitions).</p>
<p><b>Distancia lingüística:</b> lang_to_en.csv (raíz del repo), mapeada a
grupos: Ge→ge/ge_po/ge_zu, no→no/no_w2, ru→ru/ru_mo, sp→sp/sp_ch,
hi→hi_iiith/hi_iitk, ch→ch_s/ch_t, Tr→tr/tr_w2, Se→se, etc. La pestaña de
correlación usa la media de las distancias J-S a en_ca y en_uk (o una sola
cohorte si se elige).</p>
<p><b>Archivos de respaldo:</b> output/&lt;mode&gt;/distances/ (matrices J-S,
distance_to_native.csv, corr_linguistic_reading.csv,
lang_linguistic_distance.csv) y output/&lt;mode&gt;/profiles/.</p>
"""


def generate_dashboard() -> dict:
    """Genera el dashboard HTML y recalcula las correlaciones por modo."""
    payload = build_payload()
    stats = {}
    for mode in ("temporal", "regression"):
        if mode not in payload:
            continue
        lingdistance.save_table(mode)
        corr = lingdistance.correlations(mode)
        payload[mode]["corr"] = corr.to_dict("records")
        stats[mode] = {
            "n_full": len(payload[mode]["full"]),
            "n_quartile": len(payload[mode]["quartile"]),
            "stress_full": payload[mode]["stress"]["full"],
        }
    html = TEMPLATE.substitute(PAYLOAD=json.dumps(payload, ensure_ascii=False), INFO_HTML=INFO_HTML)
    out_path = paths.OUTPUT_DIR / "reading_patterns_dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"[dashboard] {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")
    for mode, s in stats.items():
        print(
            f"[dashboard] {mode}: full={s['n_full']} quart={s['n_quartile']} "
            f"stress_full={s['stress_full']}"
        )
    return stats
