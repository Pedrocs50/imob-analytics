"""Mapa de coropletas por setor censitario de Jacarei em Leaflet (a mesma tecnologia do `mapa_setores_interativo.html`, que sempre funcionou).

Gera um documento HTML completo que o painel coloca num iframe. Dentro dele: mapa de fundo (Carto, claro/escuro), setores coloridos pelo valor,
tooltip, legenda e botoes para alternar o segmento. Leaflet e os tiles (Esri World Street Map) vem da internet; sem internet o mapa nao carrega (aviso no proprio iframe).
"""
from __future__ import annotations

import html as _html
import json
from typing import Callable

import pandas as pd

from src.visualization import dados, tema

LEAFLET = "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist"

DOC = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="__LEAFLET__/leaflet.css"><script src="__LEAFLET__/leaflet.js"></script>
<style>
html,body{height:100%;margin:0;font:13px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}#mapa{height:100%;background:#e8e7e1}
body.dark #mapa{background:#1a1a19}body.dark .leaflet-tile-pane{filter:invert(1) hue-rotate(180deg) brightness(.85) contrast(.9)}
.caixa{background:rgba(255,255,255,.92);color:#1a1a19;border-radius:8px;padding:6px 8px;box-shadow:0 1px 4px rgba(0,0,0,.3)}
body.dark .caixa{background:rgba(26,26,25,.92);color:#f3f2ee}
.botoes{display:flex;gap:6px}.botoes button{border:1px solid #c3c2b7;background:transparent;color:inherit;border-radius:999px;padding:4px 12px;cursor:pointer;font:inherit}
.botoes button.ativo{background:#2a78d6;border-color:#2a78d6;color:#fff}
.legenda{min-width:150px}.barra{height:10px;border-radius:5px;margin:4px 0}.eixo{display:flex;justify-content:space-between;font-size:11px;opacity:.85}
.aviso{position:absolute;inset:0;display:none;align-items:center;justify-content:center;text-align:center;padding:16px}
</style></head><body><div id="mapa"></div><div id="aviso" class="aviso caixa">Não foi possível carregar o mapa (precisa de internet para o mapa de fundo).</div>
<script type="application/json" id="dados">__DADOS__</script>
<script>
if (typeof L === 'undefined') { document.getElementById('aviso').style.display = 'flex'; } else {
const D = JSON.parse(document.getElementById('dados').textContent);
const mapa = L.map('mapa', {zoomSnap: 0.25}).setView([-23.30, -45.96], 11);
// Esri World Street Map: tiles reais sem chave e sem exigir 'referer' (o OpenStreetMap bloqueia paginas abertas de arquivo/iframe e o Carto passou a exigir chave).
// No tema escuro o proprio CSS inverte as cores dos tiles.
const fundo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {maxZoom: 19, attribution: 'Tiles &copy; Esri'}).addTo(mapa);
let seg = D.segmentos[0][0], camada = null, enquadrado = false;
function hex(c){ return [parseInt(c.slice(1,3),16), parseInt(c.slice(3,5),16), parseInt(c.slice(5,7),16)]; }
function cor(v){
  const t = Math.max(0, Math.min(1, (v - D.zmin) / (D.zmax - D.zmin))), s = D.cores;
  for (let i = 1; i < s.length; i++) if (t <= s[i][0]) {
    const a = hex(s[i-1][1]), b = hex(s[i][1]), u = (t - s[i-1][0]) / (s[i][0] - s[i-1][0]);
    return 'rgb(' + a.map((x, k) => Math.round(x + (b[k] - x) * u)).join(',') + ')';
  }
  return s[s.length-1][1];
}
function tema(t){ document.body.classList.toggle('dark', t === 'dark'); }
function desenhar(){
  if (camada) mapa.removeLayer(camada);
  const dd = D.dados[seg];
  camada = L.geoJSON(D.geo, {
    style: f => { const d = dd[f.properties.CD_SETOR]; return d ? {fillColor: cor(d.v), fillOpacity: .78, color: '#ffffff', weight: .7} : {fillColor: '#808080', fillOpacity: .08, color: '#6e6e6e', weight: .4, opacity: .5}; },
    onEachFeature: (f, l) => { const d = dd[f.properties.CD_SETOR]; if (d) l.bindTooltip(d.t, {sticky: true}); }
  }).addTo(mapa);
}
function enquadrar(){ mapa.invalidateSize(); if (D.limites) mapa.fitBounds(D.limites); enquadrado = true; }
// botoes de segmento
const Botoes = L.control({position: 'topleft'});
Botoes.onAdd = () => { const el = L.DomUtil.create('div', 'caixa botoes'); L.DomEvent.disableClickPropagation(el);
  D.segmentos.forEach(([k, rot], i) => { const b = L.DomUtil.create('button', i === 0 ? 'ativo' : '', el); b.textContent = rot; b.onclick = () => { seg = k; el.querySelectorAll('button').forEach(o => o.classList.toggle('ativo', o === b)); desenhar(); }; }); return el; };
Botoes.addTo(mapa);
// legenda
const Legenda = L.control({position: 'bottomright'});
Legenda.onAdd = () => { const el = L.DomUtil.create('div', 'caixa legenda'); const grad = D.cores.map(s => s[1] + ' ' + (s[0] * 100) + '%').join(',');
  el.innerHTML = '<div>' + D.barra + '</div><div class="barra" style="background:linear-gradient(90deg,' + grad + ')"></div><div class="eixo"><span>' + D.rotulo_min + '</span><span>' + D.rotulo_max + '</span></div>'; return el; };
Legenda.addTo(mapa);
const sistema = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
tema(sistema); desenhar();
// o iframe pode estar escondido (aba fechada) quando carrega: enquadra quando ganhar tamanho
function quandoVisivel(){ if (mapa.getSize().x > 50 && !enquadrado) enquadrar(); else mapa.invalidateSize(); }
window.addEventListener('resize', quandoVisivel); setTimeout(quandoVisivel, 50); setTimeout(quandoVisivel, 600);
if (window.ResizeObserver) new ResizeObserver(() => { if (mapa.getSize().x !== document.getElementById('mapa').clientWidth) { mapa.invalidateSize(); if (!enquadrado || mapa.getSize().x > 50) enquadrar(); } }).observe(document.getElementById('mapa'));
window.addEventListener('message', e => { if (e.data && e.data.tema) tema(e.data.tema); });
}
</script></body></html>"""


def coropleta(por_segmento: dict[str, pd.DataFrame], valor: str, tooltip: Callable[[pd.Series], str], escala: list, barra: str,
              zmin: float, zmax: float, formato: str = "{:,.0f}") -> str | None:
    """Documento HTML do mapa. `por_segmento[seg]` tem a coluna `setor` e as demais; `tooltip(linha)` devolve o HTML do tooltip do setor."""
    geo = dados.setores_geojson()
    if geo is None:
        return None
    pacote = {"geo": geo, "cores": escala, "zmin": zmin, "zmax": zmax, "barra": barra,
              "rotulo_min": formato.format(zmin).replace(",", "."), "rotulo_max": formato.format(zmax).replace(",", "."),
              "segmentos": [[s, tema.ROTULO_SEGMENTO[s]] for s in por_segmento], "dados": {}}
    for seg, d in por_segmento.items():
        d = d.dropna(subset=[valor])
        ids = d["setor"].astype("int64").astype(str)  # o codigo do setor tem 15 digitos; como float viraria "...0" e nao casaria com o contorno
        pacote["dados"][seg] = {i: {"v": float(r[valor]), "t": tooltip(r)} for i, (_, r) in zip(ids, d.iterrows())}
    com_dado = {s for v in pacote["dados"].values() for s in v}
    lim = dados.limites_setores(com_dado)
    pacote["limites"] = [[lim[1][0], lim[0][0]], [lim[1][1], lim[0][1]]] if lim else None  # [[sul, oeste], [norte, leste]]
    corpo = json.dumps(pacote, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return DOC.replace("__LEAFLET__", LEAFLET).replace("__DADOS__", corpo)


def iframe(documento: str, altura: int, titulo: str) -> str:
    """Iframe com o documento em `data-srcdoc`: o painel so o carrega quando a aba abre (um mapa escondido nasce sem tamanho)."""
    return (f'<iframe class="mapa-tardio" title="{_html.escape(titulo)}" data-srcdoc="{_html.escape(documento, quote=True)}" '
            f'style="width:100%;height:{altura}px;border:0;border-radius:8px" loading="lazy"></iframe>')
