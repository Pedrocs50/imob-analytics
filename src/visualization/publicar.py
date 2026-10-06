"""`python main.py publicar`: monta a pasta `site/` (versao para a web do painel e do relatorio) para o GitHub Pages.

O site e estatico e **nao leva dados**: o painel e o relatorio ja trazem os resultados dentro (graficos, tabelas, medianas por setor e os pontos preco x
estimado, sem identificadores de anuncio nem dados de anunciantes). O workflow `.github/workflows/pages.yml` publica o conteudo de `site/` quando ele muda no `main`.
"""
from __future__ import annotations

import html
import os
import shutil

from src.reporting import relatorio
from src.visualization import painel

SITE = "site"
URL_SITE = "https://pedrocs50.github.io/imob-analytics/"


def _index() -> str:
    kpis = "".join(f'<div class="kpi"><div class="kpi-v">{html.escape(v)}</div><div class="kpi-r">{html.escape(r)}</div><div class="kpi-n">{html.escape(n)}</div></div>' for v, r, n in painel._kpis())
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mercado imobiliário de Jacareí-SP — iniciação científica</title>
<meta name="description" content="{html.escape(painel.DESCRICAO)}"><meta property="og:title" content="Mercado imobiliário de Jacareí-SP"><meta property="og:description" content="{html.escape(painel.DESCRICAO)}">
<style>{painel.CSS}
.hero{{max-width:880px;margin:0 auto;padding:40px 16px 8px}}.hero h1{{font-size:30px}}.hero p{{color:var(--ink2);max-width:70ch}}
.botoes{{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}}.botao{{background:var(--acc);color:#fff;border-radius:10px;padding:12px 20px;text-decoration:none;font-weight:600}}
.botao.sec{{background:var(--card);color:var(--ink);border:1px solid var(--line)}}</style></head><body>
<div class="hero"><h1>Mercado imobiliário de Jacareí-SP</h1>
<p>Iniciação científica: <b>precificação</b> de imóveis com gradient boosting, <b>séries temporais</b> do índice FipeZAP (ARIMA, LSTM) e <b>projeção de preço</b>, com comparação com trabalhos publicados.</p>
<div class="botoes"><a class="botao" href="painel.html">Abrir o painel interativo</a><a class="botao sec" href="relatorio.html">Ler o relatório completo</a><a class="botao sec" href="{painel.REPO_URL}">Código e documentação</a></div></div>
<main style="max-width:880px"><div class="kpis">{kpis}</div>
<section class="cartao"><h3>Leia com cuidado</h3><ul class="lista">
<li>Os dados são <b>preços pedidos</b> em anúncios de um único dia (março/2026), não preços de venda.</li>
<li>O FipeZAP <b>não tem Jacareí</b>: a tendência usa São José dos Campos (ou o índice nacional) como referência; é uma premissa.</li>
<li>Sensibilidade e cenários “e se” são associações aprendidas dos anúncios, não efeitos causais.</li></ul></section></main>
<footer>Site gerado por <code>python main.py publicar</code>. O painel e o relatório trazem os resultados; os dados brutos (base do orientador) não são publicados.</footer></body></html>"""


def executar() -> str:
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, "painel.html"), "w", encoding="utf-8") as f:
        f.write(painel.montar(publico=True))
    texto, avisos = relatorio.montar()
    with open(os.path.join(SITE, "relatorio.html"), "w", encoding="utf-8") as f:
        f.write(relatorio.pagina_html(texto, voltar=True))
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(_index())
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    tamanho = sum(os.path.getsize(os.path.join(SITE, n)) for n in ("index.html", "painel.html", "relatorio.html")) / 1e6
    print(f"[PUBLICAR] {SITE}/ pronto ({tamanho:.1f} MB): index.html, painel.html, relatorio.html; {len(avisos)} aviso(s) de consistência do relatório")
    print(f"[PUBLICAR] depois de commitar e enviar `{SITE}/` e `.github/`, o site fica em {URL_SITE}")
    return SITE
