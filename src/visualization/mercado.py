"""Secao Mercado: o que os anuncios de Jacarei mostram (mapa por setor, bairros, distribuicao)."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.visualization import dados, mapa, tema
from src.visualization.estrutura import Bloco, Secao, ausente

MIN_BAIRRO = 30


def _mapa_setores() -> Bloco:
    t = dados.eda("setores_preco.csv")
    if t is None or dados.setores_geojson() is None:
        return ausente("Mapa do R$/m² por setor", "setores_preco.csv e jacarei_setores_2022.gpkg", "python main.py mapa-setores")
    t = t.rename(columns={"CD_SETOR": "setor"})
    por_seg = {}
    for seg in dados.SEGMENTOS:
        d = t[["setor", f"mediana_{seg}", f"p25_{seg}", f"p75_{seg}", f"n_{seg}", "NM_DIST"]].copy()
        d.columns = ["setor", "mediana", "p25", "p75", "n", "distrito"]
        por_seg[seg] = d
    todas = pd.concat([d["mediana"] for d in por_seg.values()]).dropna()
    r = lambda x: f"{x:,.0f}".replace(",", ".")
    doc = mapa.coropleta(por_seg, "mediana", lambda x: f"<b>{x['distrito']}</b><br>mediana: R$ {r(x['mediana'])}/m²<br>25%–75%: R$ {r(x['p25'])} – {r(x['p75'])}<br>anúncios: {x['n']:.0f}",
                         tema.SEQUENCIAL, "R$/m² (mediana)", float(todas.quantile(0.02)), float(todas.quantile(0.98)))
    return Bloco("Mapa do R$/m² por setor censitário",
                 "Mediana do preço pedido por m² em cada setor do Censo 2022 (só setores com anúncios suficientes; os demais ficam em cinza). "
                 "Passe o mouse para ver a faixa de 25% a 75% e o número de anúncios; use os botões do mapa para alternar apartamento e casa. "
                 "Mapa de fundo: Esri (precisa de internet).", html=doc, altura=580, largura="cheia", fonte="reports/results/eda/setores_preco.csv")


def _bairros() -> Bloco:
    fig = go.Figure()
    for seg in dados.SEGMENTOS:
        d = dados.anuncios(seg)
        if d is None:
            return ausente("R$/m² por bairro", f"{seg}.csv", "python main.py vivareal-prep")
        g = d.groupby("neighborhood")["preco_m2"].agg(n="size", mediana="median", p25=lambda s: s.quantile(.25), p75=lambda s: s.quantile(.75))
        g = g[g["n"] >= MIN_BAIRRO].sort_values("mediana").tail(25)
        fig.add_trace(tema.grupo(go.Bar(
            y=g.index, x=g["mediana"], orientation="h", marker_color=tema.COR_SEGMENTO[seg], name=tema.ROTULO_SEGMENTO[seg],
            error_x=dict(type="data", symmetric=False, array=g["p75"] - g["mediana"], arrayminus=g["mediana"] - g["p25"], thickness=1.2, width=3),
            customdata=np.column_stack([g["n"], g["p25"], g["p75"]]),
            hovertemplate="<b>%{y}</b><br>mediana: R$ %{x:,.0f}/m²<br>25%–75%: R$ %{customdata[1]:,.0f} – %{customdata[2]:,.0f}<br>anúncios: %{customdata[0]}<extra></extra>"), seg))
    fig.update_xaxes(title="R$/m² (mediana; barra de erro = 25% a 75%)", tickformat=",.0f")
    fig.update_yaxes(tickfont_size=11)
    return Bloco("R$/m² por bairro (25 maiores em preço)",
                 f"Bairros com {MIN_BAIRRO}+ anúncios, ordenados pela mediana. A barra de erro mostra a dispersão dentro do bairro: ela é grande, "
                 "o que mostra que o bairro sozinho não define o preço.", tema.base(fig, 560, legenda=False), opcoes=dados.SEGMENTOS,
                 fonte="data/processed/vivareal/{apartamento,casa}.csv")


def _distribuicao() -> Bloco:
    fig = go.Figure()
    for seg in dados.SEGMENTOS:
        d = dados.anuncios(seg)
        if d is None:
            return ausente("Distribuição do R$/m²", f"{seg}.csv", "python main.py vivareal-prep")
        fig.add_trace(go.Box(y=d["preco_m2"], name=tema.ROTULO_SEGMENTO[seg], marker_color=tema.COR_SEGMENTO[seg], boxmean=True, line_width=1.5,
                             hovertemplate="R$ %{y:,.0f}/m²<extra></extra>"))
    fig.update_yaxes(title="R$/m² pedido", tickformat=",.0f")
    return Bloco("Distribuição do preço por m²",
                 "Caixa = 25% a 75%, linha = mediana, losango tracejado = média; pontos = anúncios fora da faixa usual. "
                 "Apartamentos são mais caros por m² e mais concentrados que casas.", tema.base(fig, 420, legenda=False),
                 fonte="data/processed/vivareal/{apartamento,casa}.csv")


def secao() -> Secao:
    return Secao("mercado", "Mercado de Jacareí",
                 "Fotografia dos anúncios do VivaReal coletados em março de 2026 (preços pedidos, não de venda), após limpeza e remoção de duplicatas.",
                 [_mapa_setores(), _bairros(), _distribuicao()])
