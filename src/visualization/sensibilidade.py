"""Secao Sensibilidade (meta 7 no painel): o que mais pesa no preco e o que muda ao alterar uma caracteristica."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from src.visualization import dados, tema
from src.visualization.estrutura import Bloco, Secao, ausente


def _grupos() -> Bloco:
    d = dados.eda("sens_grupos.csv")
    if d is None:
        return ausente("O que mais pesa no preço", "sens_grupos.csv", "python main.py sensibilidade")
    fig = go.Figure()
    for seg in dados.SEGMENTOS:
        g = d[d["segmento"] == seg].sort_values("aumento do MAE (R$/m2)")
        fig.add_trace(tema.grupo(go.Bar(
            y=g["grupo"], x=g["aumento do MAE (R$/m2)"], orientation="h", marker_color=tema.COR_SEGMENTO[seg], name=tema.ROTULO_SEGMENTO[seg],
            error_x=dict(type="data", array=g["desvio"], thickness=1.2, width=3), customdata=np.column_stack([g["aumento relativo (%)"], g["colunas"]]),
            hovertemplate="<b>%{y}</b><br>erro sobe R$ %{x:,.0f}/m² (+%{customdata[0]:.0f}%)<br>colunas no grupo: %{customdata[1]}<extra></extra>"), seg))
    fig.update_xaxes(title="aumento do erro médio (R$/m²) ao embaralhar o grupo")
    return Bloco("O que mais pesa no preço",
                 "Quanto o erro do modelo sobe quando um grupo de variáveis é embaralhado (teste temporal). Apartamentos dependem da localização fina "
                 "(coordenadas e preço dos vizinhos); casas, do bairro, do tamanho, do condomínio e do terreno. Grupos correlacionados se dividem o efeito, "
                 "e o texto tem 150 colunas: leia como “traz informação”, não como a variável mais forte.", tema.base(fig, 420, legenda=False),
                 opcoes=dados.SEGMENTOS, fonte="reports/results/eda/sens_grupos.csv")


def _cenarios() -> Bloco:
    d = dados.eda("sens_cenarios.csv")
    if d is None:
        return ausente("E se o imóvel mudasse?", "sens_cenarios.csv", "python main.py sensibilidade")
    fig = go.Figure()
    ordem = list(dict.fromkeys(d["cenario"]))
    for seg in dados.SEGMENTOS:
        g = d[d["segmento"] == seg].set_index("cenario").reindex(ordem).dropna(subset=["variacao mediana do R$/m2 (%)"])
        fig.add_trace(tema.grupo(go.Bar(
            y=g.index, x=g["variacao mediana do R$/m2 (%)"], orientation="h", marker_color=tema.COR_SEGMENTO[seg], name=tema.ROTULO_SEGMENTO[seg],
            error_x=dict(type="data", symmetric=False, array=g["q75 (%)"] - g["variacao mediana do R$/m2 (%)"], arrayminus=g["variacao mediana do R$/m2 (%)"] - g["q25 (%)"],
                         thickness=1.2, width=3),
            customdata=np.column_stack([g["q25 (%)"], g["q75 (%)"], g["variacao mediana do preco total (R$)"], g["imoveis"]]),
            hovertemplate="<b>%{y}</b><br>R$/m²: %{x:+.1f}% (25%–75%: %{customdata[0]:+.1f}% a %{customdata[1]:+.1f}%)<br>preço total: %{customdata[2]:+,.0f} R$<br>imóveis: %{customdata[3]}<extra></extra>"), seg))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="variação mediana do R$/m² (%)")
    return Bloco("E se o imóvel mudasse?",
                 "Efeito mediano de mudar uma característica mantendo o resto. Mais área aumenta o preço total mas reduz o R$/m² (economia de escala); "
                 "a suíte é o grande diferencial dos apartamentos; casa em condomínio vale ~7% mais. A barra de erro é a faixa de 25% a 75% entre os imóveis. "
                 "São associações aprendidas dos anúncios, não efeitos causais.", tema.base(fig, 420, legenda=False), opcoes=dados.SEGMENTOS,
                 fonte="reports/results/eda/sens_cenarios.csv")


def _curvas() -> Bloco:
    d = dados.eda("sens_curvas.csv")
    if d is None:
        return ausente("R$/m² pela área", "sens_curvas.csv", "python main.py sensibilidade")
    fig = go.Figure()
    for seg in dados.SEGMENTOS:
        g = d[d["segmento"] == seg]
        for i, (suites, h) in enumerate(g.groupby("suites")):
            fig.add_trace(tema.grupo(go.Scatter(
                x=h["area_m2"], y=h["R$/m2"], mode="lines+markers", name=f"{int(suites)} suíte(s)", line=dict(color=tema.PALETA[i], width=2), marker=dict(size=6),
                hovertemplate="%{x:.0f} m²: R$ %{y:,.0f}/m²<extra>" + f"{int(suites)} suíte(s)" + "</extra>"), seg))
    fig.update_xaxes(title="área útil (m²)")
    fig.update_yaxes(title="R$/m² estimado", tickformat=",.0f")
    return Bloco("R$/m² pela área e pelo número de suítes",
                 "Imóvel de referência (medianas do segmento) no bairro mais frequente, variando a área. O R$/m² cai com a área (nas casas, forte até ~300 m² e depois quase plano). "
                 "Os degraus são típicos de modelos de árvores; a curva real é mais suave.", tema.base(fig, 420), opcoes=dados.SEGMENTOS,
                 fonte="reports/results/eda/sens_curvas.csv")


def _bairros() -> Bloco:
    d = dados.eda("sens_bairros.csv")
    if d is None:
        return ausente("Mesmo imóvel, bairros diferentes", "sens_bairros.csv", "python main.py sensibilidade")
    col = "R$/m2 do imovel de referencia"
    fig = go.Figure()
    for seg in dados.SEGMENTOS:
        g = d[d["segmento"] == seg].sort_values(col).tail(25)
        fig.add_trace(tema.grupo(go.Bar(
            y=g["bairro"], x=g[col], orientation="h", marker_color=tema.COR_SEGMENTO[seg], name=tema.ROTULO_SEGMENTO[seg],
            customdata=np.column_stack([g["anuncios"], g["R$/m2 mediano dos anuncios"]]),
            hovertemplate="<b>%{y}</b><br>imóvel de referência: R$ %{x:,.0f}/m²<br>mediana dos anúncios: R$ %{customdata[1]:,.0f}/m² (%{customdata[0]} anúncios)<extra></extra>"), seg))
    fig.update_xaxes(title="R$/m² estimado do imóvel de referência", tickformat=",.0f")
    fig.update_yaxes(tickfont_size=11)
    return Bloco("O mesmo imóvel em bairros diferentes (25 mais caros)",
                 "Um imóvel típico do segmento colocado em cada bairro com 30+ anúncios: isola o efeito da localização do efeito das características. "
                 "Em casas, o imóvel de referência não é em condomínio; por isso bairros “Condomínio…” não são diretamente comparáveis à mediana dos seus anúncios.",
                 tema.base(fig, 560, legenda=False), opcoes=dados.SEGMENTOS, fonte="reports/results/eda/sens_bairros.csv")


def secao() -> Secao:
    return Secao("sensibilidade", "Sensibilidade e relevância das variáveis",
                 "Análise do modelo final de precificação: o que pesa mais no preço e o efeito de mudar área, suíte, vaga, terreno e bairro.",
                 [_grupos(), _cenarios(), _curvas(), _bairros()])
