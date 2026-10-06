"""Secao Series temporais: FipeZAP e previsao do ARIMA; erro por horizonte (ARIMA x LSTM x gradient boosting)."""
from __future__ import annotations

import os

import pandas as pd
import plotly.graph_objects as go

from src.visualization import dados, tema
from src.visualization.estrutura import Bloco, Secao, ausente

COLUNAS = {"nacional": "fipezap_nacional_res_venda_preco_m2", "SJC": "fipezap_sjc_res_venda_preco_m2"}
ROTULO = {"nacional": "Brasil (índice nacional)", "SJC": "São José dos Campos"}
COR = {"nacional": tema.PALETA[0], "SJC": tema.PALETA[1]}


def _rgba(hexa: str, alfa: float) -> str:
    h = hexa.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alfa})"


def _historico() -> Bloco:
    p = dados.painel_series()
    if p is None:
        return ausente("FipeZAP e previsão", "painel_mensal_referencia.csv", "python main.py series-painel")
    fig = go.Figure()
    for chave, col in COLUNAS.items():
        s = p[["data_ref", col]].dropna()
        fig.add_trace(go.Scatter(x=s["data_ref"], y=s[col], mode="lines", name=ROTULO[chave], line=dict(color=COR[chave], width=2),
                                 hovertemplate="%{x|%b/%Y}: R$ %{y:,.0f}/m²<extra>" + ROTULO[chave] + "</extra>"))
        prev = dados.csv(os.path.join(dados.ARIMA, f"arima_{chave}_nominal_previsao.csv"))
        if prev is None:
            continue
        x = pd.to_datetime(prev["mes de referencia"])
        fig.add_trace(go.Scatter(x=pd.concat([x, x[::-1]]), y=pd.concat([prev["limite superior (95%)"], prev["limite inferior (95%)"][::-1]]), fill="toself",
                                 fillcolor=_rgba(COR[chave], 0.18), line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=x, y=prev["previsao"], mode="lines", name=f"Previsão ARIMA — {ROTULO[chave]}", line=dict(color=COR[chave], width=2, dash="dash"),
                                 hovertemplate="%{x|%b/%Y}: R$ %{y:,.0f}/m² (previsão)<extra></extra>"))
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.06))
    fig.update_yaxes(title="R$/m² (preço de venda residencial)", tickformat=",.0f")
    return Bloco("Preço de venda FipeZAP e previsão do ARIMA(0,2,3)",
                 "Índice nacional (desde 2008) e de São José dos Campos (desde 2018), a proxy mais próxima de Jacareí, que o FipeZAP não cobre. "
                 "A faixa é o intervalo de 95% do ARIMA: ele é largo em SJC e, nos testes, não é calibrado (conservador no nacional, estreito demais em SJC). "
                 "Use o controle abaixo do gráfico para aproximar um período.", tema.base(fig, 480), largura="cheia",
                 fonte="data/processed/series/painel_mensal_referencia.csv, reports/results/arima/arima_*_previsao.csv")


def _erro_por_horizonte() -> Bloco:
    fig = go.Figure()
    achou = False
    for chave in COLUNAS:
        m = dados.csv(os.path.join(dados.LSTM, f"lstm_{chave}_metricas.csv"))
        if m is None:
            continue
        achou = True
        for i, (modelo, g) in enumerate(m.groupby("modelo", sort=False)):
            g = g.sort_values("h (meses)")
            destaque = modelo.startswith("ARIMA")
            fig.add_trace(tema.grupo(go.Scatter(
                x=g["h (meses)"], y=g["MAPE (%)"], mode="lines+markers", name=modelo,
                line=dict(color=tema.PALETA[i % 8], width=3.2 if destaque else 1.8), marker=dict(size=8 if destaque else 6),
                customdata=g[["RMSE relativo ao ARIMA", "n origens"]].to_numpy(),
                hovertemplate="horizonte %{x} meses: MAPE %{y:.2f}%<br>RMSE relativo ao ARIMA: %{customdata[0]:.2f}<br>origens de teste: %{customdata[1]}<extra>" + modelo + "</extra>"), chave))
    if not achou:
        return ausente("Erro por horizonte", "lstm_*_metricas.csv", "python main.py lstm")
    fig.update_xaxes(title="horizonte da previsão (meses)", tickvals=[1, 3, 6, 12])
    fig.update_yaxes(title="erro percentual médio (MAPE, %)")
    return Bloco("ARIMA x LSTM x gradient boosting: erro por horizonte",
                 "Walk-forward com janela expansiva. No índice nacional o ARIMA (linha grossa) ganha de todos. Em SJC as redes e o gradient boosting erram menos aos 6 e 12 meses, "
                 "mas sem significância estatística (poucas origens de teste). Nenhum modelo é uniformemente melhor.", tema.base(fig, 480),
                 opcoes=tuple(COLUNAS), fonte="reports/results/lstm/lstm_{nacional,SJC}_metricas.csv")


def secao() -> Secao:
    return Secao("series", "Séries temporais",
                 "Índice FipeZAP (preço de venda residencial) e modelos de previsão: ARIMA, LSTM e gradient boosting global em painel de 50 cidades.",
                 [_historico(), _erro_por_horizonte()])
