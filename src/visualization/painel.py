"""Monta o painel interativo: um unico HTML (plotly.js embutido, funciona offline) com abas, KPIs e tema claro/escuro."""
from __future__ import annotations

import html
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs, get_plotlyjs_version

from src.visualization import dados, mapa, mercado, modelos, projecao, sensibilidade, series, tema
from src.visualization.estrutura import Bloco, Secao

SAIDA = os.path.join("reports", "figures", "painel_interativo.html")
REPO_URL = "https://github.com/Pedrocs50/imob-analytics"
DESCRICAO = "Análise e previsão do mercado imobiliário de Jacareí-SP: precificação de imóveis, séries temporais do índice FipeZAP e projeção de preço."
CONFIG_PLOTLY = {"displaylogo": False, "responsive": True, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
                 "toImageButtonOptions": {"format": "png", "scale": 2}}


# ----------------------------------------------------------------------------- resumo
def _kpis() -> list[tuple[str, str, str]]:
    """(valor, rotulo, nota) calculados dos resultados salvos; o que nao existir e omitido."""
    k = []
    apt, casa = dados.anuncios("apartamento"), dados.anuncios("casa")
    if apt is not None and casa is not None:
        k.append((f"{len(apt) + len(casa):,}".replace(",", "."), "anúncios analisados", f"{len(apt):,} apartamentos e {len(casa):,} casas".replace(",", ".")))
    av = dados.eda("modelos_avancados_metricas.csv")
    if av is not None:
        c = av[av["modelo"].str.startswith("Conjunto")].set_index("segmento")
        if {"apartamento", "casa"} <= set(c.index):
            k.append((f"{c.loc['apartamento', 'R2']:.2f} · {c.loc['casa', 'R2']:.2f}".replace(".", ","), "R² da precificação (apto · casa)", "teste temporal, conjunto final de modelos"))
            k.append((f"{c.loc['apartamento', 'MAPE (%)']:.0f}% · {c.loc['casa', 'MAPE (%)']:.0f}%", "erro típico por imóvel (apto · casa)", "MAPE no teste temporal"))
    m = dados.csv(os.path.join(dados.ARIMA, "arima_nacional_nominal_metricas.csv"))
    if m is not None:
        r = m[(m["h (meses)"] == 12) & (m["modelo"] == "arima")]
        if len(r):
            k.append((f"{r['MAPE (%)'].iloc[0]:.2f}%".replace(".", ","), "erro do ARIMA em 12 meses", "índice FipeZAP nacional (walk-forward)"))
    t = dados.eda("projecao_cenarios_tendencia.csv")
    if t is not None:
        r = t[(t["cenario"] == "ARIMA SJC") & (t["h"] == 12)]
        if len(r):
            k.append((f"{(np.exp(r['variacao'].iloc[0]) - 1) * 100:+.1f}%".replace(".", ","), "tendência do R$/m² em 12 meses", "cenário central (ARIMA de SJC)"))
    return k


def _resumo(secoes: list[Secao]) -> str:
    kpis = "".join(f'<div class="kpi"><div class="kpi-v">{html.escape(v)}</div><div class="kpi-r">{html.escape(r)}</div><div class="kpi-n">{html.escape(n)}</div></div>' for v, r, n in _kpis())
    guia = "".join(f'<li><b>{html.escape(s.titulo)}</b> — {html.escape(s.resumo)}</li>' for s in secoes)
    return f"""
<div class="kpis">{kpis}</div>
<div class="grade">
  <section class="cartao"><h3>Como navegar</h3><ul class="lista">{guia}</ul>
    <p class="nota">Em vários gráficos há um seletor (apartamento / casa, ou Brasil / São José dos Campos) logo acima. Passe o mouse para ver detalhes; use a barra do canto do gráfico para ampliar ou salvar a imagem.</p></section>
  <section class="cartao"><h3>Leia com cuidado</h3><ul class="lista">
    <li>Os dados são <b>preços pedidos</b> em anúncios (não de venda), coletados num único dia (março/2026).</li>
    <li>O FipeZAP <b>não tem Jacareí</b>: a tendência usa São José dos Campos (ou o índice nacional) como referência; é uma premissa.</li>
    <li>O R² e os intervalos valem para anúncios novos do mesmo tipo; o valor de um imóvel isolado tem erro típico de ±8% a ±15%.</li>
    <li>Sensibilidade e “e se” descrevem associações aprendidas dos anúncios, <b>não efeitos causais</b>.</li>
    <li>Resultados negativos fazem parte do estudo (ex.: LSTM não supera o ARIMA no índice nacional; aluguel e IPTU não ajudaram).</li></ul>
    <p class="nota">Gerado por <code>python main.py painel</code> em {datetime.now():%d/%m/%Y %H:%M}, a partir dos resultados salvos (nada é recalculado). Detalhes: <code>docs/PAINEL_INTERATIVO.md</code>.</p></section>
</div>"""


# ----------------------------------------------------------------------------- blocos
class _Contador:
    n = 0


def _bloco_html(b: Bloco) -> str:
    _Contador.n += 1
    uid = f"g{_Contador.n}"
    classe = "cartao cheia" if b.largura == "cheia" else "cartao"
    cab = f'<h3>{html.escape(b.titulo)}</h3>'
    if b.aviso:
        return f'<section class="{classe}">{cab}<p class="aviso">{html.escape(b.aviso)}</p></section>'
    texto = f'<p class="texto">{html.escape(b.texto)}</p>'.replace("`", "")
    controle = ""
    if b.opcoes:
        botoes = "".join(f'<button type="button" class="seg{" ativo" if i == 0 else ""}" data-alvo="{uid}" data-grupo="{html.escape(o)}" aria-pressed="{"true" if i == 0 else "false"}">'
                         f'{html.escape(tema.ROTULO_OPCAO.get(o, o))}</button>' for i, o in enumerate(b.opcoes))
        controle = f'<div class="segmentos" role="group" aria-label="Escolher grupo">{botoes}</div>'
    if b.html:
        corpo = mapa.iframe(b.html, b.altura, b.titulo)
    elif b.figura is not None:
        fig = go.Figure(b.figura)
        if b.opcoes:  # so o primeiro grupo comeca visivel
            for t in fig.data:
                meta = getattr(t, "meta", None)
                if isinstance(meta, dict) and meta.get("grupo") not in (None, b.opcoes[0]):
                    t.visible = False
        # o grafico so e desenhado quando a aba abre (criar mapas e graficos numa aba escondida da tamanho errado)
        corpo = f'<div id="{uid}" class="plotly-tardio"></div><script type="application/json" id="{uid}-fig">{fig.to_json().replace("</", "<" + chr(92) + "/")}</script>'
    elif b.tabela is not None:
        corpo = _tabela_html(b.tabela)
    else:
        corpo = ""
    fonte = f'<p class="fonte">Fonte: {html.escape(b.fonte)}</p>' if b.fonte else ""
    return f'<section class="{classe}">{cab}{texto}{controle}<div class="corpo">{corpo}</div>{fonte}</section>'


def _tabela_html(t: pd.DataFrame) -> str:
    cab = "".join(f"<th>{html.escape(str(c))}</th>" for c in t.columns)
    linhas = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r) + "</tr>" for r in t.itertuples(index=False))
    return f'<div class="rolagem"><table><thead><tr>{cab}</tr></thead><tbody>{linhas}</tbody></table></div>'


def _secao_html(s: Secao, ativa: bool) -> str:
    blocos = "".join(_bloco_html(b) for b in s.blocos)
    return (f'<div class="painel{" ativo" if ativa else ""}" id="aba-{s.id}" role="tabpanel"><h2>{html.escape(s.titulo)}</h2>'
            f'<p class="resumo">{html.escape(s.resumo)}</p><div class="grade">{blocos}</div></div>')


# ----------------------------------------------------------------------------- pagina
CSS = """
:root{color-scheme:light;--bg:#f9f9f7;--card:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--line:#e1e0d9;--axis:#c3c2b7;--acc:#2a78d6;--ring:rgba(11,11,11,.10)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--bg:#0d0d0d;--card:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--axis:#383835;--acc:#3987e5;--ring:rgba(255,255,255,.10)}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#0d0d0d;--card:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--axis:#383835;--acc:#3987e5;--ring:rgba(255,255,255,.10)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:20px 16px 8px;max-width:1280px;margin:0 auto;display:flex;gap:16px;align-items:flex-start;justify-content:space-between}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--ink2);margin:0;font-size:14px}
#tema{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:6px 12px;cursor:pointer;font:inherit;font-size:13px}
nav{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
.abas{max-width:1280px;margin:0 auto;padding:0 16px;display:flex;gap:4px;overflow-x:auto}
.aba{border:0;background:none;color:var(--ink2);padding:12px 14px;cursor:pointer;font:inherit;font-weight:500;border-bottom:2px solid transparent;white-space:nowrap}
.aba:hover{color:var(--ink)}.aba[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--acc)}
main{max-width:1280px;margin:0 auto;padding:20px 16px 48px}
.painel{display:none}.painel.ativo{display:block}h2{font-size:18px;margin:0 0 4px}.resumo{color:var(--ink2);margin:0 0 16px;max-width:80ch}
.grade{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.cheia{grid-column:1/-1}
.cartao{background:var(--card);border:1px solid var(--ring);border-radius:12px;padding:16px;min-width:0}
.corpo{overflow:hidden;max-width:100%}.cartao h3{font-size:15px;margin:0 0 6px}.texto{color:var(--ink2);font-size:13px;margin:0 0 10px}.fonte{color:var(--muted);font-size:11px;margin:8px 0 0}
.aviso{color:var(--ink2);border-left:3px solid #fab219;padding-left:10px;font-size:13px}.nota{color:var(--muted);font-size:12px;margin:10px 0 0}
.segmentos{display:flex;gap:6px;margin:0 0 8px;flex-wrap:wrap}.seg{border:1px solid var(--line);background:none;color:var(--ink2);border-radius:999px;padding:4px 12px;cursor:pointer;font:inherit;font-size:13px}
.seg.ativo{background:var(--acc);border-color:var(--acc);color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-bottom:16px}
.kpi{background:var(--card);border:1px solid var(--ring);border-radius:12px;padding:14px}.kpi-v{font-size:26px;font-weight:600}.kpi-r{font-size:13px;margin-top:2px}.kpi-n{color:var(--muted);font-size:11px;margin-top:2px}
.lista{margin:0;padding-left:18px;color:var(--ink2);font-size:13px}.lista li{margin:4px 0}code{background:var(--line);padding:1px 5px;border-radius:4px;font-size:12px}
.rolagem{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}th{color:var(--ink2);font-weight:600}
header .acoes{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.link{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:6px 12px;font-size:13px;text-decoration:none}.link:hover{border-color:var(--acc)}
footer{max-width:1280px;margin:0 auto;padding:0 16px 32px;color:var(--muted);font-size:12px}footer a{color:var(--acc)}
@media (max-width:800px){.grade{grid-template-columns:minmax(0,1fr)}header{flex-direction:column}}
"""

JS = """
const CONFIG = __CONFIG__;
const raiz = document.documentElement;
function tema(){ const t = raiz.getAttribute('data-theme'); return t || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); }
function aplicarTema(escopo){
  const css = getComputedStyle(raiz), ink = css.getPropertyValue('--ink2').trim(), grade = css.getPropertyValue('--line').trim(), eixo = css.getPropertyValue('--axis').trim();
  (escopo || document).querySelectorAll('.js-plotly-plot').forEach(gd => {
    const u = {'font.color': ink};
    if (gd.layout && gd.layout.xaxis) Object.assign(u, {'xaxis.gridcolor': grade, 'yaxis.gridcolor': grade, 'xaxis.linecolor': eixo, 'yaxis.linecolor': eixo});
    try { Plotly.relayout(gd, u); } catch (e) {}
  });
  document.querySelectorAll('iframe.mapa-tardio.pronto').forEach(f => { try { f.contentWindow.postMessage({tema: tema()}, '*'); } catch (e) {} });
  document.getElementById('tema').textContent = tema() === 'dark' ? 'Tema claro' : 'Tema escuro';
}
document.getElementById('tema').addEventListener('click', () => {
  const novo = tema() === 'dark' ? 'light' : 'dark'; raiz.setAttribute('data-theme', novo);
  try { localStorage.setItem('tema-painel', novo); } catch (e) {} aplicarTema();
});
try { const salvo = localStorage.getItem('tema-painel'); if (salvo) raiz.setAttribute('data-theme', salvo); } catch (e) {}
function larguraDe(div){ return Math.max(280, Math.floor(div.parentElement.getBoundingClientRect().width || div.parentElement.clientWidth || 700)); }
function ajustar(gd){
  const w = larguraDe(gd);
  if (w > 280 && gd._fullLayout && Math.abs(w - gd._fullLayout.width) > 2) Plotly.relayout(gd, {width: w});
}
function desenhar(painel){
  // desenha so os graficos ainda nao criados; a aba ja esta visivel, entao eles nascem com a largura certa
  const novos = [...painel.querySelectorAll('.plotly-tardio:not(.pronto)')];
  novos.forEach(div => {
    const fig = JSON.parse(document.getElementById(div.id + '-fig').textContent);
    div.classList.add('pronto');
    fig.layout.width = larguraDe(div);  // largura real explicita: sem ela o Plotly assume 700 e o mapa de fundo nao se corrige depois
    Plotly.newPlot(div, fig.data, fig.layout, CONFIG);
  });
  if (novos.length) aplicarTema(painel);
  // mapas (Leaflet) ficam em iframes carregados so quando a aba abre
  painel.querySelectorAll('iframe.mapa-tardio:not([src]):not(.pronto)').forEach(f => {
    f.classList.add('pronto'); f.addEventListener('load', () => f.contentWindow.postMessage({tema: tema()}, '*')); f.srcdoc = f.dataset.srcdoc;
  });
}
function redimensionar(painel){ painel.querySelectorAll('.js-plotly-plot').forEach(ajustar); }
// so reajusta quando a janela muda de tamanho (reajustar durante o carregamento do mapa de fundo o quebra)
let _espera; window.addEventListener('resize', () => { clearTimeout(_espera); _espera = setTimeout(() => { const p = document.querySelector('.painel.ativo'); if (p) redimensionar(p); }, 250); });
function abrir(id, empurrar){
  document.querySelectorAll('.painel').forEach(p => p.classList.toggle('ativo', p.id === 'aba-' + id));
  document.querySelectorAll('.aba').forEach(a => a.setAttribute('aria-selected', a.dataset.aba === id ? 'true' : 'false'));
  const p = document.getElementById('aba-' + id); if (p) desenhar(p);
  if (empurrar) history.replaceState(null, '', '#' + id);
}
document.querySelectorAll('.aba').forEach(a => a.addEventListener('click', () => abrir(a.dataset.aba, true)));
document.querySelectorAll('.seg').forEach(b => b.addEventListener('click', () => {
  const gd = document.getElementById(b.dataset.alvo), g = b.dataset.grupo;
  const vis = gd.data.map(t => !(t.meta && t.meta.grupo) || t.meta.grupo === g);
  Plotly.restyle(gd, {visible: vis});
  b.parentElement.querySelectorAll('.seg').forEach(o => { const on = o === b; o.classList.toggle('ativo', on); o.setAttribute('aria-pressed', on); });
}));
window.addEventListener('load', () => { aplicarTema(); abrir((location.hash.slice(1) && document.getElementById('aba-' + location.hash.slice(1))) ? location.hash.slice(1) : 'resumo', false); const h = location.hash.slice(1); if (h && document.getElementById('aba-' + h)) abrir(h, false); });
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', aplicarTema);
"""


def montar(publico: bool = False) -> str:
    """`publico=True` gera a versao para a web (GitHub Pages): plotly.js vem de CDN (arquivo ~3x menor) e o cabecalho ganha links para o relatorio e o codigo."""
    secoes = [mercado.secao(), modelos.secao(), sensibilidade.secao(), series.secao(), projecao.secao()]
    rotulos = {"resumo": "Resumo", "mercado": "Mercado", "modelos": "Modelos", "sensibilidade": "Sensibilidade", "series": "Séries temporais", "projecao": "Projeção"}
    ids = ["resumo"] + [s.id for s in secoes]
    nav = "".join(f'<button type="button" class="aba" role="tab" data-aba="{i}" aria-selected="{"true" if k == 0 else "false"}">{html.escape(rotulos[i])}</button>' for k, i in enumerate(ids))
    paineis = (f'<div class="painel ativo" id="aba-resumo" role="tabpanel"><h2>Resumo</h2><p class="resumo">{html.escape(DESCRICAO)}</p>{_resumo(secoes)}</div>'
               + "".join(_secao_html(s, False) for s in secoes))
    plotly_js = (f'<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js" charset="utf-8"></script>' if publico else f"<script>{get_plotlyjs()}</script>")
    links = (f'<a class="link" href="index.html">Início</a><a class="link" href="relatorio.html">Relatório completo</a><a class="link" href="{REPO_URL}">Código no GitHub</a>' if publico else "")
    rodape = (f'<footer>Gerado em {datetime.now():%d/%m/%Y %H:%M} a partir dos resultados do projeto. Preços são <b>pedidos</b> em anúncios (não de venda); o FipeZAP não tem Jacareí. '
              f'Código e documentação: <a href="{REPO_URL}">{REPO_URL.split("github.com/")[1]}</a>.</footer>')
    meta = (f'<meta name="description" content="{html.escape(DESCRICAO)}"><meta property="og:title" content="Mercado imobiliário de Jacareí-SP — painel interativo">'
            f'<meta property="og:description" content="{html.escape(DESCRICAO)}"><meta property="og:type" content="website">')
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Painel — mercado imobiliário de Jacareí</title>{meta}<style>{CSS}</style>{plotly_js}</head><body>'
            f'<header><div><h1>Mercado imobiliário de Jacareí-SP</h1><p class="sub">Painel interativo da iniciação científica: precificação, séries temporais e projeção</p></div>'
            f'<div class="acoes">{links}<button id="tema" type="button">Tema escuro</button></div></header>'
            f'<nav><div class="abas" role="tablist">{nav}</div></nav><main>{paineis}</main>{rodape}'
            f'<script>{JS.replace("__CONFIG__", json.dumps(CONFIG_PLOTLY))}</script></body></html>')


def executar() -> str:
    pagina = montar()
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(pagina)
    print(f"[PAINEL] {SAIDA} ({len(pagina) / 1e6:.1f} MB)")
    return SAIDA
