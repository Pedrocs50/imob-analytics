"""Paleta e layout base. Cores categoricas na ordem fixa do metodo (azul, laranja, agua...); as tres primeiras validam em
todos os pares (mapas e dispersoes). Sequencial: um tom (azul). Divergente: azul <-> vermelho com meio cinza."""
from __future__ import annotations

import plotly.graph_objects as go

PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
COR_SEGMENTO = {"apartamento": PALETA[0], "casa": PALETA[1], "residencial": PALETA[2]}
SEQUENCIAL = [[0.0, "#cde2fb"], [0.25, "#86b6ef"], [0.5, "#3987e5"], [0.75, "#1c5cab"], [1.0, "#0d366b"]]
DIVERGENTE = [[0.0, "#1c5cab"], [0.25, "#86b6ef"], [0.5, "#f0efec"], [0.75, "#f09a98"], [1.0, "#d03b3b"]]
CINZA_NEUTRO = "rgba(128,128,128,0.18)"
FONTE = "system-ui, -apple-system, 'Segoe UI', sans-serif"
ROTULO_SEGMENTO = {"apartamento": "Apartamento", "casa": "Casa", "residencial": "Residencial"}


def base(fig: go.Figure, altura: int = 420, legenda: bool = True) -> go.Figure:
    """Layout comum: fundo transparente (a pagina define o fundo), fonte do sistema, grade discreta, margens enxutas.
    As cores do texto e da grade sao trocadas pelo JS do painel conforme o tema."""
    fig.update_layout(
        height=altura, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONTE, size=12), showlegend=legenda, hoverlabel=dict(font_family=FONTE),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), colorway=PALETA,
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, zeroline=False, automargin=True)
    fig.update_yaxes(showgrid=True, gridwidth=1, zeroline=False, automargin=True)
    return fig


def grupo(trace, nome: str):
    """Marca o traco como pertencente a um grupo do seletor do cartao."""
    trace.meta = {"grupo": nome}
    return trace

ROTULO_OPCAO = {**ROTULO_SEGMENTO, "nacional": "Índice nacional", "SJC": "São José dos Campos"}
