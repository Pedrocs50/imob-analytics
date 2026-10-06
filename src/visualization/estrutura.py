from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go


@dataclass
class Bloco:
    """Um cartao do painel: titulo, texto de leitura, e um grafico OU uma tabela.

    - `opcoes`: rotulos de um seletor; cada traco do grafico declara seu grupo em `meta={"grupo": ...}` e so os do grupo escolhido
      ficam visiveis (os tracos sem grupo aparecem sempre).
    - `largura`: "meia" (duas por linha) ou "cheia".
    - `fonte`: arquivo(s) de onde vem o dado, mostrado no rodape do cartao.
    """

    titulo: str
    texto: str
    figura: go.Figure | None = None
    html: str = ""  # documento HTML completo mostrado num iframe (mapas em Leaflet)
    altura: int = 560  # altura do iframe, quando `html` e usado
    tabela: pd.DataFrame | None = None
    opcoes: tuple[str, ...] = ()
    largura: str = "meia"
    fonte: str = ""
    aviso: str = ""  # preenchido quando a fonte nao existe


@dataclass
class Secao:
    id: str
    titulo: str
    resumo: str
    blocos: list[Bloco] = field(default_factory=list)


def ausente(titulo: str, fonte: str, comando: str) -> Bloco:
    """Bloco no lugar de um grafico cuja fonte nao existe; diz como gerar."""
    return Bloco(titulo, "", aviso=f"Fonte não encontrada: {fonte}. Gere com `{comando}`.", fonte=fonte)
