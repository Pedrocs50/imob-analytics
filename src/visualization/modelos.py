"""Secao Modelos: como a precificacao evoluiu, desempenho final, valor estimado x pedido e calibracao dos intervalos."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.visualization import dados, tema
from src.visualization.estrutura import Bloco, Secao, ausente

SEGMENTOS3 = ("apartamento", "casa", "residencial")
# (nome na tabela de origem, rotulo no grafico): etapas em ordem; as duas ultimas vem de modelos_avancados_metricas.csv
ETAPAS_GEO = [("OLS base (sem coordenadas)", "Regressão linear (referência)"),
              ("OLS + vizinhos (coord. imputadas)", "Linear + preço dos vizinhos"),
              ("Gradient boosting sem coordenadas", "Gradient boosting, sem coordenadas"),
              ("Gradient boosting com lat/lon imputadas", "+ coordenadas imputadas"),
              ("Gradient boosting imputadas + vizinhos + setor + Censo", "+ vizinhos, setor IBGE e Censo"),
              ("GB completo + terreno e texto", "+ terreno e texto do anúncio")]
ETAPAS_AV = [("LightGBM, ajustado (Optuna)", "LightGBM ajustado (Optuna)"), ("Conjunto (media dos 3 ajustados)", "Conjunto final (3 modelos)")]


def _evolucao() -> Bloco:
    geo, av = dados.eda("regressao_geo_metricas.csv"), dados.eda("modelos_avancados_metricas.csv")
    if geo is None or av is None:
        return ausente("Evolução do R²", "regressao_geo_metricas.csv e modelos_avancados_metricas.csv", "python main.py reg-geo e modelos-avancados")
    temporal = geo[geo["validacao"].str.contains("temporal") & (geo["subconjunto"] == "todos os anuncios")]
    linhas = []
    for tabela, etapas in ((temporal, ETAPAS_GEO), (av, ETAPAS_AV)):
        for nome, rotulo in etapas:
            for seg in SEGMENTOS3:
                r = tabela[(tabela["modelo"] == nome) & (tabela["segmento"] == seg)]
                if len(r):
                    linhas.append({"etapa": rotulo, "segmento": seg, "R2": float(r["R2"].iloc[0]), "MAE": float(r["MAE"].iloc[0])})
    d = pd.DataFrame(linhas)
    ordem = [r for _, r in ETAPAS_GEO + ETAPAS_AV]
    fig = go.Figure()
    for seg in SEGMENTOS3:
        g = d[d["segmento"] == seg].set_index("etapa").reindex(ordem).dropna()
        fig.add_trace(go.Bar(y=g.index, x=g["R2"], orientation="h", name=tema.ROTULO_SEGMENTO[seg], marker_color=tema.COR_SEGMENTO[seg],
                             customdata=g["MAE"],
                             hovertemplate="<b>%{y}</b><br>R² = %{x:.3f}<br>MAE = R$ %{customdata:,.0f}/m²<extra>" + tema.ROTULO_SEGMENTO[seg] + "</extra>"))
    fig.update_yaxes(autorange="reversed", tickfont_size=11)
    fig.update_xaxes(title="R² no teste temporal (25% mais recentes)", range=[0.4, 0.85])
    fig.update_layout(barmode="group", bargap=0.25)
    return Bloco("Evolução do R² da precificação",
                 "Cada barra é o R² (quanto da variação do R$/m² o modelo explica) no teste mais exigente, com os anúncios mais recentes. "
                 "O maior salto veio de trocar o modelo linear por árvores; depois, de informação nova (terreno, texto, condomínio) e do ajuste de parâmetros. "
                 "As etapas até “terreno e texto” vêm da execução do `reg-geo`; as duas últimas, do `modelos-avancados` (já com as variáveis de condomínio e contexto).",
                 tema.base(fig, 520), largura="cheia", fonte="reports/results/eda/regressao_geo_metricas.csv, modelos_avancados_metricas.csv")


def _metricas() -> Bloco:
    av = dados.eda("modelos_avancados_metricas.csv")
    if av is None:
        return ausente("Desempenho dos modelos finais", "modelos_avancados_metricas.csv", "python main.py modelos-avancados")
    av = av.copy()
    av["modelo"] = (av["modelo"].str.replace("parametros padrao", "padrão").str.replace("ajustado (Optuna)", "ajustado", regex=False)
                    .str.replace("Conjunto (media dos 3 ajustados)", "Conjunto dos 3 ajustados", regex=False))
    fig = go.Figure()
    for seg in SEGMENTOS3:
        g = av[av["segmento"] == seg]
        fig.add_trace(go.Bar(y=g["modelo"], x=g["R2"], orientation="h", name=tema.ROTULO_SEGMENTO[seg], marker_color=tema.COR_SEGMENTO[seg],
                             customdata=np.column_stack([g["MAE"], g["MAPE (%)"], g["RMSE"]]),
                             hovertemplate="<b>%{y}</b><br>R² = %{x:.3f}<br>MAE = R$ %{customdata[0]:,.0f}/m²<br>MAPE = %{customdata[1]:.1f}%<br>"
                                           "RMSE = R$ %{customdata[2]:,.0f}/m²<extra>" + tema.ROTULO_SEGMENTO[seg] + "</extra>"))
    fig.update_yaxes(autorange="reversed", tickfont_size=11)
    fig.update_xaxes(title="R² no teste temporal", range=[0.6, 0.85])
    fig.update_layout(barmode="group", bargap=0.25)
    return Bloco("Modelos finais: padrão x ajustado x conjunto",
                 "HistGradientBoosting, LightGBM e CatBoost com parâmetros padrão e ajustados (busca bayesiana, só no treino), e a média dos três. "
                 "O ajuste rende +0,01 a +0,02; o conjunto só ganha com clareza nos apartamentos.", tema.base(fig, 460),
                 fonte="reports/results/eda/modelos_avancados_metricas.csv")


def _real_estimado() -> Bloco:
    p, iv = dados.projecao_anuncios(), dados.eda("modelos_avancados_intervalos.csv")
    if p is None or iv is None:
        return ausente("Preço pedido x valor estimado", "projecao_anuncios.csv e modelos_avancados_intervalos.csv", "python main.py projecao")
    fig = go.Figure()
    for seg in dados.SEGMENTOS:
        d = p[p["segmento"] == seg]
        q = float(iv[(iv["segmento"] == seg) & (np.isclose(iv["nivel nominal"], 0.8))]["erro relativo no quantil"].iloc[0])
        lim = [float(d["preco_m2_estimado_mar2026"].min()), float(d["preco_m2_estimado_mar2026"].max())]
        fig.add_trace(tema.grupo(go.Scattergl(
            x=d["preco_m2_estimado_mar2026"], y=d["preco_m2_pedido"], mode="markers", name="anúncios",
            marker=dict(size=4, opacity=0.35, color=tema.COR_SEGMENTO[seg]),
            customdata=np.column_stack([d["neighborhood"].fillna("—"), d["area_m2"]]),
            hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]:.0f} m²)<br>estimado: R$ %{x:,.0f}/m²<br>pedido: R$ %{y:,.0f}/m²<extra></extra>"), seg))
        for nome, f, dash in (("estimado = pedido", 1.0, "solid"), (f"faixa de 80% (±{q:.0%})", 1 + q, "dash"), ("", 1 - q, "dash")):
            fig.add_trace(tema.grupo(go.Scatter(x=lim, y=[f * lim[0], f * lim[1]], mode="lines", name=nome or "faixa de 80%", showlegend=bool(nome),
                                                 line=dict(color="gray", width=1.4, dash=dash), hoverinfo="skip"), seg))
    fig.update_xaxes(title="valor estimado pelo modelo (R$/m², fora da amostra)", tickformat=",.0f")
    fig.update_yaxes(title="preço pedido no anúncio (R$/m²)", tickformat=",.0f")
    return Bloco("Preço pedido x valor estimado",
                 "Cada ponto é um anúncio. O valor estimado é uma previsão fora da amostra (o modelo nunca viu aquele anúncio). "
                 "Pontos acima da diagonal estão pedindo mais que o estimado; a faixa tracejada é o intervalo de 80% do modelo.",
                 tema.base(fig, 480), opcoes=dados.SEGMENTOS, fonte="data/processed/vivareal/projecao_anuncios.csv, modelos_avancados_intervalos.csv")


def _intervalos() -> Bloco:
    iv = dados.eda("modelos_avancados_intervalos.csv")
    if iv is None:
        return ausente("Calibração dos intervalos", "modelos_avancados_intervalos.csv", "python main.py modelos-avancados")
    t = pd.DataFrame({"Segmento": iv["segmento"].map(tema.ROTULO_SEGMENTO),
                      "Nível nominal": (iv["nivel nominal"] * 100).round(0).astype(int).astype(str) + "%",
                      "Cobertura no teste": (iv["cobertura no teste temporal"] * 100).round(1).astype(str) + "%",
                      "Erro relativo do intervalo": "±" + (iv["erro relativo no quantil"] * 100).round(1).astype(str) + "%",
                      "Largura média (R$/m²)": iv["largura media (R$/m2)"].round(0).map("{:,.0f}".format)})
    return Bloco("Os intervalos de previsão são confiáveis?",
                 "Intervalos conformais: o quantil do erro relativo fora da amostra no treino. Se calibrados, a cobertura no teste fica perto do nível nominal. "
                 "Aqui ficam 1 a 2 pontos acima (levemente conservadores). O erro de avaliar um imóvel isolado é grande: ±18% a ±24% (80%).",
                 tabela=t, fonte="reports/results/eda/modelos_avancados_intervalos.csv")


def secao() -> Secao:
    return Secao("modelos", "Modelos de precificação",
                 "Previsão do R$/m² de um anúncio a partir das características do imóvel e da localização (previsão transversal, não no tempo).",
                 [_evolucao(), _metricas(), _real_estimado(), _intervalos()])
