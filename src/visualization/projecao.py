"""Secao Projecao: cenarios de tendencia, projecao do R$/m2 por segmento e premio do preco pedido sobre o estimado por setor."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.visualization import dados, mapa, tema
from src.visualization.estrutura import Bloco, Secao, ausente

HORIZONTES = (3, 6, 12)


def _cenarios() -> Bloco:
    t = dados.eda("projecao_cenarios_tendencia.csv")
    if t is None:
        return ausente("Cenários de tendência", "projecao_cenarios_tendencia.csv", "python main.py projecao")
    fig = go.Figure()
    for i, (cen, g) in enumerate(t.groupby("cenario", sort=False)):
        g = g.sort_values("h")
        y = (np.exp(g["variacao"]) - 1) * 100
        tem_ic = g["inf"].notna().all()
        ic = np.column_stack([(np.exp(g["inf"]) - 1) * 100, (np.exp(g["sup"]) - 1) * 100]) if tem_ic else np.full((len(g), 2), np.nan)
        fig.add_trace(go.Scatter(
            x=g["h"], y=y, mode="lines+markers", name=cen, line=dict(color=tema.PALETA[i], width=2.4 if "SJC" in cen and "ARIMA" in cen else 1.8), marker=dict(size=8),
            error_y=dict(type="data", symmetric=False, array=ic[:, 1] - y, arrayminus=y - ic[:, 0], thickness=1.2, width=4, visible=bool(tem_ic)) if tem_ic else None,
            customdata=ic, hovertemplate="em %{x} meses: %{y:+.1f}%" + ("<br>IC 95%: %{customdata[0]:+.1f}% a %{customdata[1]:+.1f}%" if tem_ic else "") + "<extra>" + cen + "</extra>"))
    fig.update_xaxes(title="meses após o último índice publicado", tickvals=list(HORIZONTES))
    fig.update_yaxes(title="variação projetada do R$/m² (%)", ticksuffix="%")
    return Bloco("Cenários de tendência do índice",
                 "Variação esperada do R$/m² a partir do último índice publicado (ago/2026). Os três cenários concordam na direção (alta de 6% a 10% em 12 meses). "
                 "A barra de erro é o IC de 95% do ARIMA; o de SJC é bem largo.", tema.base(fig, 440), fonte="reports/results/eda/projecao_cenarios_tendencia.csv")


def _por_segmento() -> Bloco:
    p, t = dados.projecao_anuncios(), dados.eda("projecao_cenarios_tendencia.csv")
    if p is None or t is None:
        return ausente("Projeção por segmento", "projecao_anuncios.csv", "python main.py projecao")
    cols = [("preco_m2_pedido", "Pedido\n(mar/2026)"), ("preco_m2_estimado_hoje", "Estimado\nhoje"), ("preco_m2_proj_3m", "+3 meses"),
            ("preco_m2_proj_6m", "+6 meses"), ("preco_m2_proj_12m", "+12 meses")]
    fig = go.Figure()
    for seg in dados.SEGMENTOS:
        d = p[p["segmento"] == seg]
        y = [float(d[c].median()) for c, _ in cols]
        fig.add_trace(go.Scatter(x=[r.replace("\n", " ") for _, r in cols], y=y, mode="lines+markers", name=tema.ROTULO_SEGMENTO[seg],
                                 line=dict(color=tema.COR_SEGMENTO[seg], width=2.4), marker=dict(size=8),
                                 hovertemplate="%{x}: R$ %{y:,.0f}/m²<extra>" + tema.ROTULO_SEGMENTO[seg] + "</extra>"))
    fig.update_yaxes(title="R$/m² (mediana dos anúncios)", tickformat=",.0f")
    return Bloco("Projeção do R$/m² por segmento (cenário central)",
                 "Mediana do valor estimado de cada anúncio, levado até o último índice (variação observada de SJC) e projetado com o ARIMA de SJC. "
                 "A incerteza do valor de um imóvel isolado (±17% a ±23%) é muito maior que a da tendência. Premissa: Jacareí acompanha SJC e todos os imóveis variam igual.",
                 tema.base(fig, 440), fonte="data/processed/vivareal/projecao_anuncios.csv")


def _premio() -> Bloco:
    t = dados.eda("projecao_por_setor.csv")
    if t is None or dados.setores_geojson() is None:
        return ausente("Preço pedido x estimado por setor", "projecao_por_setor.csv", "python main.py projecao")
    por_seg = {}
    for seg in dados.SEGMENTOS:
        d = t[(t["segmento"] == seg) & (t["anuncios"] >= 5)].copy()
        d["premio_pct"] = d["premio_mediano"] * 100
        por_seg[seg] = d[["setor", "premio_pct", "anuncios", "pedido_mediana", "estimado_mediana"]]
    r = lambda x: f"{x:,.0f}".replace(",", ".")
    doc = mapa.coropleta(por_seg, "premio_pct", lambda x: f"<b>{x['premio_pct']:+.1f}%</b> pedido sobre o estimado<br>pedido: R$ {r(x['pedido_mediana'])}/m²<br>estimado: R$ {r(x['estimado_mediana'])}/m²<br>anúncios: {x['anuncios']:.0f}",
                         tema.DIVERGENTE, "pedido − estimado (%)", -30, 30, formato="{:+,.0f}%")
    return Bloco("Onde se pede mais (ou menos) que o valor estimado",
                 "Diferença mediana entre o preço pedido e o valor estimado pelo modelo, por setor com 5+ anúncios. Vermelho = pedem acima do estimado; azul = abaixo. "
                 "Setores com poucos anúncios mostram valores extremos: interprete os de 20+ anúncios. Use os botões do mapa para alternar apartamento e casa.",
                 html=doc, altura=580, largura="cheia", fonte="reports/results/eda/projecao_por_setor.csv")


def secao() -> Secao:
    return Secao("projecao", "Projeção de preço de Jacareí",
                 "Valor estimado de cada anúncio (modelo de precificação) combinado com a tendência do FipeZAP de São José dos Campos.",
                 [_cenarios(), _por_segmento(), _premio()])
